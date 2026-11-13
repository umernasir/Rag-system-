import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel

from agentic_rag import create_rag, agentic_rag


load_dotenv()

app = FastAPI(
    title="Government AI Cloud API",
    version="1.0.0"
)


SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set in .env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


DEMO_USERNAME = "admin"

DEMO_PASSWORD_HASH = password_hash.hash(
    "admin123"
)


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str


class QuestionRequest(BaseModel):
    question: str


rag_instance = None


def authenticate_user(username, password):

    if username != DEMO_USERNAME:
        return None

    if not password_hash.verify(
        password,
        DEMO_PASSWORD_HASH
    ):
        return None

    return User(username=username)


def create_access_token(username):

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": username,
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme)
    ]
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except InvalidTokenError:

        raise credentials_exception

    if username != DEMO_USERNAME:
        raise credentials_exception

    return User(username=username)


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/login", response_model=Token)
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ]
):

    user = authenticate_user(
        form_data.username,
        form_data.password
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    token = create_access_token(
        user.username
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/me")
async def me(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):

    return {
        "username": current_user.username
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ] = None
):

    global rag_instance

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    file_bytes = await file.read()

    class UploadedFile:

        def __init__(
            self,
            name,
            file_bytes
        ):

            self.name = name
            self.file_bytes = file_bytes

        def getvalue(self):

            return self.file_bytes

    uploaded_file = UploadedFile(
        file.filename,
        file_bytes
    )

    rag_instance = create_rag(
        uploaded_file
    )

    return {
        "filename": file.filename,
        "message": "Document processed successfully",
        "documents": len(rag_instance.documents),
        "chunks": len(rag_instance.chunks)
    }


@app.post("/ask")
async def ask_question(
    request: QuestionRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):

    if rag_instance is None:

        raise HTTPException(
            status_code=400,
            detail="Please upload a document first"
        )

    state = {

        "question": request.question,

        "search_query": request.question,

        "documents": [],

        "answer": "",

        "relevant": False,

        "attempts": 0,

        "rag": rag_instance
    }

    result = agentic_rag.invoke(state)

    return {

        "question": request.question,

        "answer": result["answer"],

        "attempts": result["attempts"],

        "documents_retrieved": len(
            result["documents"]
        )
    }


@app.get("/documents")
async def documents(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):

    if rag_instance is None:

        raise HTTPException(
            status_code=400,
            detail="No document uploaded"
        )

    return {
        "documents": [
            {
                "source": doc.metadata.get(
                    "source",
                    "unknown"
                )
            }
            for doc in rag_instance.documents
        ]
    }


@app.get("/stats")
async def stats(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):

    if rag_instance is None:

        return {
            "indexed": False,
            "documents": 0,
            "chunks": 0
        }

    return {
        "indexed": True,
        "documents": len(rag_instance.documents),
        "chunks": len(rag_instance.chunks),
        "top_k": rag_instance.top_k
    }