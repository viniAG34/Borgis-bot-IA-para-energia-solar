"""
oraculo/utils.py

Responsabilidades separadas por classe (SOLID):
  - DocumentProcessor  : S — carrega e divide documentos
  - VectorStoreManager : S — cria/carrega o índice FAISS
  - AIQueryService     : S — consulta IA com RAG e streaming
  - consultar_ia_stream: façade pública usada pelas views
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Generator

from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# S — Processamento de documentos
# ---------------------------------------------------------------------------

class DocumentProcessor:
    """Carrega um PDF e divide em chunks prontos para embedding."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " "],
        )

    def load_pdf(self, caminho: str) -> list[Document]:
        loader = PyPDFLoader(caminho)
        return self._splitter.split_documents(loader.load())


# ---------------------------------------------------------------------------
# S — Gestão do VectorStore
# ---------------------------------------------------------------------------

class VectorStoreManager:
    """Cria e persiste o índice FAISS; carrega se já existir."""

    def __init__(self, store_path: str):
        self._store_path = store_path
        self._embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
        )

    def build(self, documentos: list[Document]) -> FAISS:
        store = FAISS.from_documents(documentos, self._embeddings)
        store.save_local(self._store_path)
        logger.info("VectorStore construído e salvo em %s", self._store_path)
        return store

    def load(self) -> FAISS:
        """Carrega índice existente. Levanta FileNotFoundError se ausente."""
        if not os.path.exists(self._store_path):
            raise FileNotFoundError(f"VectorStore não encontrado em: {self._store_path}")
        # allow_dangerous_deserialization é exigido pelo FAISS (usa pickle internamente).
        # O arquivo é gerado localmente por construir_vectorstore() — não por input externo.
        return FAISS.load_local(
            self._store_path,
            self._embeddings,
            allow_dangerous_deserialization=True,
        )

    def load_or_build(self, documentos_factory) -> FAISS:
        try:
            return self.load()
        except FileNotFoundError:
            logger.info("VectorStore ausente — construindo a partir do PDF.")
            return self.build(documentos_factory())


# ---------------------------------------------------------------------------
# D — Abstração do provider de IA (Open/Closed para trocar o modelo)
# ---------------------------------------------------------------------------

class BaseAIProvider(ABC):
    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        ...


class OpenAIProvider(BaseAIProvider):
    def get_llm(self) -> BaseChatModel:
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            streaming=True,
            openai_api_key=settings.OPENAI_API_KEY,
        )


# ---------------------------------------------------------------------------
# S — Consulta RAG com streaming
# ---------------------------------------------------------------------------

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "Você é Borgis, um assistente especialista em energia solar fotovoltaica. "
            "Responda de forma clara, objetiva e amigável, sempre em português brasileiro. "
            "Use apenas as informações do contexto abaixo. "
            "Se a resposta não estiver no contexto, diga educadamente que não tem essa informação.\n\n"
            "Contexto:\n{contexto}"
        ),
    ),
    ("human", "{pergunta}"),
])


class AIQueryService:
    """Recupera contexto via RAG e faz streaming de tokens."""

    def __init__(self, store_manager: VectorStoreManager, provider: BaseAIProvider):
        self._store_manager = store_manager
        self._provider = provider

    def stream(self, pergunta: str) -> Generator[str, None, None]:
        store = self._store_manager.load_or_build(self._get_documentos)
        docs = store.as_retriever(search_kwargs={"k": 4}).invoke(pergunta)
        contexto = "\n\n".join(doc.page_content for doc in docs)

        chain = _PROMPT | self._provider.get_llm()
        for chunk in chain.stream({"pergunta": pergunta, "contexto": contexto}):
            if chunk.content:
                yield chunk.content

    @staticmethod
    def _get_documentos() -> list[Document]:
        return DocumentProcessor().load_pdf(settings.PDF_SOLAR_PATH)


# ---------------------------------------------------------------------------
# Façade pública — usada pelas views
# ---------------------------------------------------------------------------

def _make_service() -> AIQueryService:
    manager = VectorStoreManager(settings.VECTORSTORE_PATH)
    return AIQueryService(manager, OpenAIProvider())


def consultar_ia_stream(pergunta: str) -> Generator[str, None, None]:
    return _make_service().stream(pergunta)


def construir_vectorstore() -> FAISS:
    processor = DocumentProcessor()
    manager = VectorStoreManager(settings.VECTORSTORE_PATH)
    documentos = processor.load_pdf(settings.PDF_SOLAR_PATH)
    return manager.build(documentos)
