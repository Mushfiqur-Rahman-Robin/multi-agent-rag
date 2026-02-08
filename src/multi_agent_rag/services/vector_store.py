"""
Vector store service for the multi-agent RAG system.

Handles document ingestion, similarity search, and knowledge base management
using ChromaDB and OpenAI Embeddings. Integrated with Redis for caching.
"""

import os
from pathlib import Path

import anyio
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.multi_agent_rag.core.config import (
    CACHE_INVALIDATE_ON_KB_UPDATE,
    CHROMA_DB_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    OPENAI_API_KEY,
    UPLOAD_CLEANUP,
    VECTOR_MODEL,
    VECTOR_SEARCH_K,
)
from src.multi_agent_rag.core.logging_config import logger

# Import cache service
try:
    from src.multi_agent_rag.services.cache_service import cache_service
except ImportError:
    cache_service = None


class VectorStoreService:
    """
    Service for managing the vector database (ChromaDB) and document ingestion.
    """

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=VECTOR_MODEL, openai_api_key=OPENAI_API_KEY
        )
        self.persist_directory = str(CHROMA_DB_DIR)
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="aura_knowledge_base",
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )

    async def ingest_file(self, file_path: str) -> bool:
        """
        Index a file into the vector database.
        """
        from src.multi_agent_rag.services.cost_service import cost_service

        logger.info(f"Ingesting file into vector store: {file_path}")
        path = Path(file_path)

        try:
            if path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(file_path)
            elif path.suffix.lower() in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            else:
                loader = TextLoader(file_path)

            documents = await anyio.to_thread.run_sync(loader.load)

            # Estimate cost
            total_chars = sum(len(doc.page_content) for doc in documents)
            est_tokens = total_chars // 4
            cost = cost_service.calculate_embedding_cost(VECTOR_MODEL, est_tokens)
            logger.info(f"Embedding Ingestion: ~{est_tokens} tokens, Cost: ${cost}")

            splits = self.text_splitter.split_documents(documents)
            await anyio.to_thread.run_sync(self.vector_store.add_documents, splits)
            logger.info(f"Successfully indexed {len(splits)} chunks from {file_path}")

            # Invalidate caches if enabled
            if CACHE_INVALIDATE_ON_KB_UPDATE and cache_service:
                await cache_service.on_knowledge_base_update()

            # Cleanup File
            if UPLOAD_CLEANUP:
                try:
                    await anyio.to_thread.run_sync(os.remove, file_path)
                    logger.info(f"Cleaned up uploaded file: {file_path}")
                except OSError as e:
                    logger.warning(f"Failed to cleanup file {file_path}: {e}")

            return True
        except Exception as e:
            logger.error(f"Failed to ingest file {file_path}: {e}")
            return False

    async def search(self, query: str, k: int | None = None) -> str:
        """
        Search the vector store for relevant snippets. Supports caching.
        """
        if k is None:
            k = VECTOR_SEARCH_K

        # Check cache first
        if cache_service and cache_service.is_available:
            cached_result = await cache_service.get_vector_cache(query)
            if cached_result:
                logger.info(f"Vector search cache HIT for: {query[:50]}...")
                return cached_result

        from src.multi_agent_rag.services.cost_service import cost_service

        logger.info(f"Searching vector store for: {query}")
        try:
            # Estimate query cost
            est_tokens = len(query) // 4
            cost = cost_service.calculate_embedding_cost(VECTOR_MODEL, est_tokens)
            logger.info(f"Embedding Query: ~{est_tokens} tokens, Cost: ${cost}")

            results = await anyio.to_thread.run_sync(
                lambda: self.vector_store.similarity_search(query, k=k)
            )
            if not results:
                return ""

            context = "\n\n---\n\n".join([doc.page_content for doc in results])

            # Store in cache
            if cache_service and cache_service.is_available:
                await cache_service.set_vector_cache(query, context)

            return context
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return ""

    async def list_documents(self) -> list[str]:
        """List distinct filenames in the vector store."""
        try:
            data = await anyio.to_thread.run_sync(self.vector_store.get)
            metadatas = data["metadatas"]
            unique_files = set()
            for m in metadatas:
                if m and "source" in m:
                    filename = os.path.basename(m["source"])
                    unique_files.add(filename)
            return list(unique_files)
        except Exception as e:
            logger.error(f"Failed to list docs: {e}")
            return []

    async def delete_document(self, filename: str) -> bool:
        """Delete a document by filename and invalidate cache."""
        try:
            data = await anyio.to_thread.run_sync(self.vector_store.get)
            ids_to_delete = []
            for i, meta in enumerate(data["metadatas"]):
                if meta and "source" in meta:
                    if os.path.basename(meta["source"]) == filename:
                        ids_to_delete.append(data["ids"][i])

            if ids_to_delete:
                await anyio.to_thread.run_sync(self.vector_store.delete, ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} chunks for {filename}")

                # Invalidate caches
                if CACHE_INVALIDATE_ON_KB_UPDATE and cache_service:
                    await cache_service.on_knowledge_base_update()

                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete doc {filename}: {e}")
            return False


# Singleton instance
vector_store_service = VectorStoreService()
