import os
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from pypdf import PdfReader

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq


load_dotenv()


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-120b"


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:

    print(f"Loading embedding model: {EMBEDDING_MODEL}")

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def load_uploaded_documents(uploaded_files: Iterable) -> list[Document]:

    documents = []

    for uploaded_file in uploaded_files:

        file_bytes = uploaded_file.getvalue()

        temp_path = Path(f"/tmp/{uuid.uuid4().hex}.pdf")
        temp_path.write_bytes(file_bytes)

        reader = PdfReader(str(temp_path))

   
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                documents.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "source": uploaded_file.name,
                            "page": page_number,
                        }
                    )
                )

        temp_path.unlink(missing_ok=True)

    return documents


def format_context(documents: list[Document]) -> str:

    return "\n\n".join(
        document.page_content
        for document in documents
    )


class RAGService:

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        top_k: int = 4
    ) -> None:

        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY is not set")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.embedding_model = get_embedding_model()

        self.llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0,
            max_retries=2
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are answering questions using only the provided context.

If the answer cannot be found in the context, say exactly:

I couldn't find that information in the uploaded documents.

Context:
{context}

Question:
{question}
"""
        )

        self.answer_chain = prompt | self.llm | StrOutputParser()

        self.vector_store = None
        self.retriever = None

        self.documents = []
        self.chunks = []

    def build_index(self, uploaded_files: Iterable) -> dict:

        self.documents = load_uploaded_documents(uploaded_files)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
        )

        self.chunks = splitter.split_documents(
            self.documents
        )

        collection_name = f"rag_demo_{uuid.uuid4().hex}"

        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_model,
        )

        self.vector_store.add_documents(
            documents=self.chunks
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": self.top_k
            },
        )

        embedding_dimension = len(
            self.embedding_model.embed_query(
                "dimension check"
            )
        )

        return {
            "documents": len(self.documents),
            "chunks": len(self.chunks),
            "embedding_dimension": embedding_dimension,
            "embedding_model": EMBEDDING_MODEL,
            "llm_model": GROQ_MODEL,
        }

    def ask(self, question: str) -> tuple[str, list[Document]]:

        if self.retriever is None:
            raise RuntimeError(
                "Please process documents before asking question"
            )

        retrieved_docs = self.retriever.invoke(
            question
        )

        context = format_context(
            retrieved_docs
        )

        answer = self.answer_chain.invoke(
            {
                "context": context,
                "question": question
            }
        )
        evaluation_record = {
            "user_input": question,
            "retrieved_contexts": [
                doc.page_content for doc in retrieved_docs
            ],
            "response": answer
        }

    
        return answer, retrieved_docs