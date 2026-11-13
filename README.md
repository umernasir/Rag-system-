# Agentic RAG System

An Agentic Retrieval-Augmented Generation (RAG) system built using **LangChain, LangGraph, FastAPI, Streamlit, and Groq LLMs**.

This project implements an intelligent document question-answering system that retrieves relevant information from uploaded PDF documents, evaluates retrieved content, and retries retrieval when the results are not sufficiently relevant.

## Features

- **PDF Document Upload:** Upload PDF documents for question answering.
- **Retrieval-Augmented Generation:** Retrieve relevant document chunks to generate context-aware answers.
- **Agentic Workflow:** Use LangGraph to manage the retrieval, evaluation, retry, and answer-generation process.
- **Relevance Evaluation:** Evaluate whether retrieved documents are relevant to the user's question.
- **Query Rewriting:** Improve search queries when the retrieved context is not relevant.
- **Retry Mechanism:** Retry retrieval with an improved query, subject to a maximum attempt limit.
- **Conversational Memory:** Maintain conversation history for contextual follow-up questions.
- **Source-Aware Answers:** Return document sources and page information with answers.
- **REST API:** Expose functionality through FastAPI endpoints.
- **Streamlit Interface:** Provide a user-friendly interface for interacting with the system.

## Architecture

The system follows an agentic retrieval workflow:

1. User uploads PDF documents.
2. Documents are processed and split into smaller chunks.
3. Text embeddings are generated using a Hugging Face embedding model.
4. Document chunks are stored in ChromaDB.
5. User submits a question.
6. LangGraph executes the retrieval workflow.
7. Retrieved documents are evaluated for relevance.
8. If documents are not relevant, the search query is improved and retrieval is retried.
9. Relevant context is passed to the LLM.
10. The system generates an answer with source information.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| LangChain | RAG components and LLM integration |
| LangGraph | Agentic workflow orchestration |
| Groq | LLM inference |
| Hugging Face | Text embeddings |
| ChromaDB | Vector storage and similarity search |
| FastAPI | Backend REST API |
| Streamlit | User interface |
| PyPDF | PDF document processing |
| JWT | Authentication |

## Project Structure

```text
agentic-rag-system/
│
├── agentic_rag.py       # LangGraph agentic workflow
├── rag_engine.py        # RAG engine and document processing
├── rag_evaluate.py      # RAG evaluation module
├── api.py               # FastAPI backend
├── app.py               # Streamlit frontend
│
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── .gitignore           # Git ignored files
└── README.md            # Project documentation
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/agentic-rag-system.git
```

### 2. Navigate to the Project

```bash
cd agentic-rag-system
```

### 3. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root directory using `.env.example` as a reference.

```env
GROQ_API_KEY=your_groq_api_key
JWT_SECRET_KEY=your_jwt_secret_key
```

Replace the placeholder values with your own credentials.

**Important:** Never upload your actual `.env` file or API keys to GitHub.

## Running the Application

### 1. Start the FastAPI Backend

```bash
uvicorn api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation:

```text
http://127.0.0.1:8000/docs
```

### 2. Start the Streamlit Frontend

Open another terminal, activate the virtual environment, and run:

```bash
streamlit run app.py
```

The Streamlit interface will open in your browser.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API health |
| POST | `/login` | User authentication |
| GET | `/me` | Get authenticated user information |
| POST | `/upload` | Upload PDF documents |
| POST | `/ask` | Ask questions about documents |
| GET | `/documents` | List uploaded documents |
| GET | `/stats` | Get document statistics |
| DELETE | `/conversation` | Clear conversation history |

## Agentic RAG Workflow

The main workflow is designed around four key stages:

- **Retrieve:** Search for relevant document chunks.
- **Evaluate:** Check whether retrieved documents answer the user's question.
- **Rewrite and Retry:** Improve the search query if retrieval is insufficient.
- **Generate:** Produce an answer using relevant retrieved context.

## Security Notes

- Store API keys and secret values in your local `.env` file.
- Do not commit `.env`, virtual environments, or private documents.
- Replace demo authentication credentials before using the application in production.
- Use a strong, randomly generated JWT secret in production.

## Future Improvements

- Advanced retrieval evaluation.
- Improved query rewriting strategies.
- Reranking for better retrieval quality.
- More robust authentication and authorization.
- Production deployment and monitoring.

## Author

Developed as an AI Engineering project focused on Agentic RAG, document retrieval, and LLM-powered question answering.
