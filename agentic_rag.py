from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from rag_engine import RAGService


class AgentState(TypedDict):
    question: str
    search_query: str
    documents: list[Document]
    answer: str
    sources :list[dict]
    relevant: bool
    attempts: int
    rag: RAGService
    chat_history: list[dict]


def create_rag(uploaded_files):
    rag = RAGService()

    files = []

    for uploaded_file in uploaded_files:

        file_bytes = uploaded_file.getvalue()

        class UploadedFile:
            def __init__(self, name, file_bytes):
                self.name = name
                self.file_bytes = file_bytes

            def getvalue(self):
                return self.file_bytes

        files.append(
            UploadedFile(
                uploaded_file.name,
                file_bytes
            )
        )

    rag.build_index(files)

    return rag

def retrieve(state: AgentState):
    print("\n--- RETRIEVE NODE ---")

    rag = state["rag"]
    search_query = state["search_query"]
    chat_history = state["chat_history"]

    if chat_history:
        previous_context = "\n".join(
            f"Q: {item['question']}\nA: {item['answer']}"
            for item in chat_history[-3:]
        )

        search_query = (
            previous_context
            + "\nCurrent question: "
            + search_query
        )

    documents = rag.retriever.invoke(search_query)

    print("Documents found:", len(documents))

    return {
        "documents": documents,
        "attempts": state["attempts"] + 1
    }


def evaluate(state: AgentState):
    print("\n--- EVALUATE NODE ---")

    rag = state["rag"]
    question = state["question"]
    documents = state["documents"]

    context = "\n\n".join(
        doc.page_content
        for doc in documents
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are a strict document relevance evaluator.

Your job is to decide whether the retrieved documents
contain information that can directly answer the user's question.

Rules:

1. Compare the QUESTION with the RETRIEVED DOCUMENTS carefully.
2. Return YES only if the documents contain information
   that is directly relevant to answering the question.
3. If the documents are about a different topic, return NO.
4. Do not use outside knowledge.
5. Do not assume that documents are relevant just because
   they contain technical or general information.
6. If the question asks about a person, fact, topic, or event
   that does not appear in the documents, return NO.
7. Return ONLY one word:

YES

or

NO
"""
        ),
        (
            "human",
            """
QUESTION:
{question}

RETRIEVED DOCUMENTS:
{context}
"""
        )
    ])

    chain = prompt | rag.llm | StrOutputParser()

    result = chain.invoke({
        "question": question,
        "context": context
    })

    result = result.strip().upper()

    relevant = result == "YES"

    print("Evaluator result:", result)
    print("Relevant:", relevant)

    return {
        "relevant": relevant
    }

def retry_retrieve(state: AgentState):
    print("\n--- RETRY SEARCH ---")

    question = state["question"]

    new_query = (
        question
        + " purpose goals objectives mission architecture capabilities"
    )

    print("New search query:")
    print(new_query)

    return {
        "search_query": new_query
    }

def answer(state: AgentState):
    print("\n--- ANSWER NODE ---")
    rag = state["rag"]
    question = state["question"]
    documents = state["documents"]

    context_blocks = []
    sources = []

    seen_sources = set()

    for i, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")

        context_blocks.append(
            f"""
[Source {i}: {source}, Page {page}]
{doc.page_content}
"""
        )

        source_key = (source, page)

        if source_key not in seen_sources:
            seen_sources.add(source_key)

            sources.append({
                "source": source,
                "page": page
            })

    context = "\n\n".join(context_blocks)

    result = rag.answer_chain.invoke({
        "context": context,
        "question": question
    })

    print("Answer generated.")

    return {
        "answer": result,
        "sources": sources
    }

def decide_next(state: AgentState):
    print("\n--- DECISION ---")
    if state["relevant"]:
        print("Relevant documents → ANSWER")
        return "answer"
    if state["attempts"] >= 2:
        print("Maximum attempts reached → ANSWER")
        return "answer"
    print("Documents not relevant → RETRY")
    return "retry"


graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieve)
graph.add_node("evaluate", evaluate)
graph.add_node("retry", retry_retrieve)
graph.add_node("answer", answer)
graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "evaluate")
graph.add_conditional_edges(
    "evaluate",
    decide_next,
    {
        "answer": "answer",
        "retry": "retry"
    }
)

graph.add_edge("retry", "retrieve")
graph.add_edge("answer", END)
agentic_rag = graph.compile()