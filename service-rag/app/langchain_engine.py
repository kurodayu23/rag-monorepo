"""根据检索上下文选择回答或拒答的 LCEL 管线。"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

def query_with_langchain(question: str, context: list[str], model_name: str) -> str:
    """模型判断上下文是否充分；该判断不保证消除幻觉。"""
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnableBranch
        from langchain_community.chat_models import ChatOllama
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "LangChain dependencies missing. Run: pip install langchain-core langchain-community"
        ) from exc

    llm = ChatOllama(model=model_name, temperature=0.1)

    eval_prompt = ChatPromptTemplate.from_template(
        """Determine if the provided context contains sufficient information to answer the question.
Context: {context}
Question: {question}

Reply with precisely 'yes' or 'no' (lowercase). No explanation."""
    )
    
    context_evaluator = eval_prompt | llm | StrOutputParser() | (lambda x: x.strip().lower() == "yes")

    answering_prompt = ChatPromptTemplate.from_template(
        """You are a professional enterprise assistant. Answer the user's question strictly using the context provided below.
If the context contains code, structure the output elegantly.
        
<context>
{context}
</context>

Question: {question}
Answer:"""
    )
    
    answering_chain = answering_prompt | llm | StrOutputParser()

    fallback_chain = (
        lambda x: "Insufficient information in the retrieved context to answer this query safely. Generation aborted to prevent hallucination."
    )

    master_chain = RunnableBranch(
        (context_evaluator, answering_chain),
        fallback_chain,
    )

    # Execute Graph
    context_block = "\n".join(f"- {item}" for item in context)
    logger.info("Executing LCEL conditional routing graph for RAG...")
    
    return master_chain.invoke({"context": context_block, "question": question})

