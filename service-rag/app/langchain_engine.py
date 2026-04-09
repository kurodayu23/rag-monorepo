"""Optional LangChain-backed answer generation for service-rag."""
from __future__ import annotations


def query_with_langchain(question: str, context: list[str], model_name: str) -> str:
    """
    Build a small LangChain runnable graph from already-retrieved context.

    This function intentionally uses lazy imports so CI can run without
    LangChain dependencies when `RAG_ENGINE=native`.
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_community.chat_models import ChatOllama
    except Exception as exc:  # pragma: no cover - only hit when deps missing
        raise RuntimeError(
            "LangChain dependencies are missing. Install langchain-core, "
            "langchain-community, and langchain."
        ) from exc

    prompt = ChatPromptTemplate.from_template(
        """
        Answer based only on the context below.

        Context:
        {context}

        Question: {question}
        """.strip()
    )

    llm = ChatOllama(model=model_name, temperature=0.1)
    chain = prompt | llm | StrOutputParser()
    context_block = "\n".join(f"- {item}" for item in context)
    return chain.invoke({"context": context_block, "question": question})
