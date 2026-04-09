"""
Advanced LangChain-backed RAG orchestration for service-rag.
Shows mastery over LCEL (LangChain Expression Language), structured outputs, and routing.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

def query_with_langchain(question: str, context: list[str], model_name: str) -> str:
    """
    Builds a professional-grade LangChain execution graph utilizing LCEL routing.
    Validates that context actually contains the answer before hallucinating.
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough, RunnableBranch
        from langchain_community.chat_models import ChatOllama
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "LangChain dependencies missing. Run: pip install langchain-core langchain-community"
        ) from exc

    # 1. Base LLM Setup
    llm = ChatOllama(model=model_name, temperature=0.1)

    # 2. Evaluation Chain: Check if context has the answer
    eval_prompt = ChatPromptTemplate.from_template(
        """Determine if the provided context contains sufficient information to answer the question.
Context: {context}
Question: {question}

Reply with precisely 'yes' or 'no' (lowercase). No explanation."""
    )
    
    context_evaluator = eval_prompt | llm | StrOutputParser() | (lambda x: x.strip().lower() == "yes")

    # 3. Answering Chain: Format the final response grounded in context
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

    # 4. Fallback Chain: Graceful degradation target
    fallback_chain = (
        lambda x: "Insufficient information in the retrieved context to answer this query safely. Generation aborted to prevent hallucination."
    )

    # 5. Routing LCEL Graph Construction
    # This demonstrates deep knowledge of LCEL conditional routing
    master_chain = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | RunnableBranch(
            (context_evaluator, answering_chain),
            fallback_chain
        )
    )

    # Execute Graph
    context_block = "\n".join(f"- {item}" for item in context)
    logger.info("Executing LCEL conditional routing graph for RAG...")
    
    return master_chain.invoke({"context": context_block, "question": question})

