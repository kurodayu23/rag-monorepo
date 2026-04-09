import logging

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma

logging.basicConfig(level=logging.INFO)


class LangChainRAGPipeline:
    """
    LangChain 版本的 RAG 示例（用于面试讲“RAG + LangChain”）。

    说明：
    - 这里用 Ollama 做本地 LLM
    - 向量库使用 Chroma（持久化到 persist_directory）
    - embeddings 默认走 HuggingFace 模型，会触发模型下载；你可以按实际网络情况调整
    """

    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        ollama_model: str = "gemma:4b",
    ):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
        )
        self.llm = Ollama(model=ollama_model)

    def query(self, user_input: str, top_k: int = 3) -> str:
        prompt = ChatPromptTemplate.from_template(
            """
Answer the following question based only on the provided context.

<context>
{context}
</context>

Question: {input}
"""
        )

        document_chain = create_stuff_documents_chain(self.llm, prompt)
        retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        logging.info("Executing LangChain RAG chain...")
        response = retrieval_chain.invoke({"input": user_input})
        return str(response["answer"])

