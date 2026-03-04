# devmind-core/core/memory/vector_store.py
"""
Memoria vectorial para DevMind Core usando ChromaDB.

Proporciona almacenamiento y recuperación semántica de:
- Código y snippets
- Decisiones arquitectónicas
- Conversaciones y contexto
- Documentación y referencias

Compatible con ChromaDB 1.1.1+
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pathlib import Path
from datetime import datetime
import hashlib
import logging

from langchain_ollama import OllamaEmbeddings

# ✅ CORREGIDO: Imports para ChromaDB 1.1.1
try:
    from chromadb import PersistentClient, HttpClient
    from chromadb.config import Settings
except ImportError:
    raise ImportError(
        "ChromaDB 1.x es requerido. Instalá: uv pip install 'chromadb>=1.0.0'"
    )

logger = logging.getLogger(__name__)


class MemoryCategory(str, Enum):
    """Categorías de memoria para filtrado y organización"""
    CODE = "code"  # Snippets y archivos de código
    DECISIONS = "decisions"  # Decisiones arquitectónicas (ADRs)
    CONVERSATIONS = "conversations"  # Historial de chat con usuario
    REQUIREMENTS = "requirements"  # Requisitos y user stories
    DOCUMENTATION = "documentation"  # Docs técnicas y referencias
    BUGS = "bugs"  # Reportes y fixes de bugs
    TOOLS = "tools"  # Herramientas creadas por el agente
    GENERAL = "general"  # Contenido misceláneo


class VectorMemory:
    """
    Memoria vectorial basada en ChromaDB para contexto semántico.

    Características:
    - Embeddings locales con Ollama (nomic-embed-text)
    - Filtrado por categoría, proyecto y metadata
    - Persistencia en disco
    - Búsqueda por similitud coseno
    - Compatible con ChromaDB 1.1.1+
    """

    DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
    DEFAULT_OLLAMA_URL = "http://localhost:11434"
    DEFAULT_CHROMA_URL = "http://localhost:8000"

    def __init__(
            self,
            project_id: str,
            chroma_url: str = None,
            ollama_url: str = None,
            embedding_model: str = None,
            persist_directory: str = None
    ):
        """
        Inicializa la memoria vectorial.

        Args:
            project_id: ID único del proyecto
            chroma_url: URL del servidor ChromaDB (opcional)
            ollama_url: URL del servidor Ollama
            embedding_model: Modelo de embeddings a usar
            persist_directory: Directorio para persistencia local
        """
        self.project_id = project_id
        self.collection_name = f"devmind_{project_id}"

        self.ollama_url = ollama_url or self.DEFAULT_OLLAMA_URL
        self.embedding_model = embedding_model or self.DEFAULT_EMBEDDING_MODEL

        # Inicializar embeddings con Ollama
        self._embeddings = OllamaEmbeddings(
            model=self.embedding_model,
            base_url=self.ollama_url
        )

        # ✅ CORREGIDO: Conectar a ChromaDB 1.1.1
        self._client = self._init_chroma_client(persist_directory)

        # ✅ CORREGIDO: API actualizada para obtener/crear colección
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "project_id": self.project_id,
                "created_at": datetime.now().isoformat(),
                "embedding_model": self.embedding_model
            }
        )

        logger.info(f"VectorMemory initialized for project {project_id}")

    def _init_chroma_client(self, persist_directory: str = None):
        """
        Inicializa cliente ChromaDB 1.1.1 (HTTP o persistente).

        ✅ CORREGIDO para ChromaDB 1.1.1 - usa PersistentClient
        """
        # Usar modo persistente local por defecto (más confiable para desarrollo)
        if persist_directory:
            persist_dir = Path(persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using persistent ChromaDB at: {persist_dir}")
            return PersistentClient(path=str(persist_dir))

        # Directorio por defecto si no se especifica
        default_persist_dir = Path.home() / ".devmind" / "chroma_db" / self.project_id
        default_persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Using default persistent ChromaDB at: {default_persist_dir}")
        return PersistentClient(path=str(default_persist_dir))

    def store(
            self,
            content: str,
            metadata: Dict[str, Any] = None,
            category: MemoryCategory = MemoryCategory.GENERAL,
            doc_id: str = None
    ) -> str:
        """
        Almacena contenido en memoria vectorial.

        Args:
            content: Texto a almacenar
            metadata: Metadata adicional para filtrado
            category: Categoría para organización
            doc_id: ID personalizado (se genera si None)

        Returns:
            ID del documento almacenado
        """
        # Generar ID único si no se proporciona
        if doc_id is None:
            content_hash = hashlib.md5(
                f"{self.project_id}:{content[:200]}".encode()
            ).hexdigest()
            doc_id = f"{category.value}_{content_hash}"

        # Preparar metadata completa
        full_metadata = {
            **(metadata or {}),
            "project_id": self.project_id,
            "category": category.value,
            "doc_id": doc_id,
            "content_length": len(content),
            "stored_at": datetime.now().isoformat()
        }

        # Generar embedding y almacenar
        try:
            embedding = self._embeddings.embed_query(content)

            # ✅ API actualizada para ChromaDB 1.x
            self._collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[full_metadata]
            )

            logger.debug(f"Stored memory: {doc_id} ({category.value})")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    def retrieve(
            self,
            query: str,
            categories: Optional[List[MemoryCategory]] = None,
            limit: int = 10,
            min_similarity: float = 0.0,
            metadata_filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera contenido relevante por similitud semántica.

        Args:
            query: Texto de búsqueda
            categories: Filtrar por categorías específicas
            limit: Máximo resultados a retornar
            min_similarity: Umbral mínimo de similitud (0-1)
            metadata_filter: Filtros adicionales por metadata

        Returns:
            Lista de resultados con contenido, metadata y score
        """
        # Preparar filtro where
        where_filter = {"project_id": self.project_id}

        if categories:
            where_filter["category"] = {
                "$in": [c.value for c in categories]
            }

        if metadata_filter:
            where_filter.update(metadata_filter)

        # Generar embedding de query y buscar
        try:
            query_embedding = self._embeddings.embed_query(query)

            # ✅ API actualizada para ChromaDB 1.x
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            # Formatear resultados
            formatted = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - (distance / 2)  # Convertir distancia coseno a similitud

                    if similarity >= min_similarity:
                        formatted.append({
                            "content": doc,
                            "metadata": results["metadatas"][0][i],
                            "similarity": round(similarity, 4),
                            "category": results["metadatas"][0][i].get("category")
                        })

            # Ordenar por similitud descendente
            formatted.sort(key=lambda x: x["similarity"], reverse=True)

            logger.debug(f"Retrieved {len(formatted)} memories for query: {query[:50]}...")
            return formatted

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    def store_code_snapshot(
            self,
            file_path: str,
            content: str,
            commit_hash: str = None,
            language: str = None
    ) -> str:
        """Guarda snapshot de código para referencia futura"""
        return self.store(
            content=content,
            metadata={
                "file_path": file_path,
                "commit": commit_hash,
                "language": language,
                "type": "code_snapshot"
            },
            category=MemoryCategory.CODE,
            doc_id=f"code_{hashlib.md5(file_path.encode()).hexdigest()}"
        )

    def store_decision(
            self,
            title: str,
            decision: str,
            context: str = "",
            alternatives: List[str] = None,
            consequences: str = ""
    ) -> str:
        """Guarda decisión arquitectónica (ADR)"""
        content = f"DECISIÓN: {title}\n\nContexto: {context}\n\nDecisión: {decision}\n\nConsecuencias: {consequences}"
        if alternatives:
            content += f"\n\nAlternativas consideradas: {', '.join(alternatives)}"

        return self.store(
            content=content,
            metadata={
                "title": title,
                "decision": decision,
                "alternatives": alternatives or [],
                "type": "architecture_decision"
            },
            category=MemoryCategory.DECISIONS,
            doc_id=f"decision_{hashlib.md5(title.encode()).hexdigest()}"
        )

    def store_conversation(
            self,
            user_message: str,
            agent_response: str,
            intent: str = None,
            task_id: str = None
    ) -> str:
        """Guarda intercambio de conversación"""
        content = f"User: {user_message}\n\nAgent: {agent_response}"

        return self.store(
            content=content,
            metadata={
                "user_message": user_message,
                "agent_response": agent_response,
                "intent": intent,
                "task_id": task_id,
                "type": "conversation_turn"
            },
            category=MemoryCategory.CONVERSATIONS
        )

    def get_project_knowledge(
            self,
            query: str,
            include_categories: Optional[List[MemoryCategory]] = None
    ) -> str:
        """Obtiene conocimiento consolidado del proyecto"""
        results = self.retrieve(
            query=query,
            categories=include_categories,
            limit=15,
            min_similarity=0.3
        )

        if not results:
            return ""

        # Agrupar por categoría
        by_category: Dict[str, List[str]] = {}
        for r in results:
            cat = r["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f"- {r['content'][:300]}...")

        # Construir string de contexto
        context_parts = []
        for category, items in by_category.items():
            context_parts.append(f"\n## {category.upper()}")
            context_parts.extend(items[:5])

        return "\n".join(context_parts)

    def delete(self, doc_id: str) -> bool:
        """Elimina un documento por ID"""
        try:
            self._collection.delete(ids=[doc_id])
            logger.debug(f"Deleted memory: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    def clear(self, category: MemoryCategory = None) -> int:
        """Limpia memoria, opcionalmente por categoría"""
        try:
            if category:
                results = self._collection.get(
                    where={"category": category.value},
                    include=["metadatas"]
                )
                ids_to_delete = results["ids"] if results["ids"] else []
                if ids_to_delete:
                    self._collection.delete(ids=ids_to_delete)
                    return len(ids_to_delete)
                return 0
            else:
                # Resetear colección
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.create_collection(
                    name=self.collection_name,
                    metadata={"project_id": self.project_id}
                )
                return -1
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria"""
        try:
            count = self._collection.count()

            categories = {}
            for cat in MemoryCategory:
                results = self._collection.get(
                    where={"category": cat.value},
                    include=["metadatas"]
                )
                if results and results["ids"]:
                    categories[cat.value] = len(results["ids"])

            return {
                "project_id": self.project_id,
                "total_documents": count,
                "by_category": categories,
                "embedding_model": self.embedding_model,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

    def __repr__(self) -> str:
        return f"VectorMemory(project={self.project_id}, collection={self.collection_name})"