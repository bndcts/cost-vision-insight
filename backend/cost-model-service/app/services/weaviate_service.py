"""
Weaviate service for document ingestion and similarity search.
Uses Weaviate's document API to directly embed PDFs for RAG-based similar article lookup.
"""
import logging
from typing import Optional

import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.init import AdditionalConfig
from weaviate.classes.query import MetadataQuery

from app.core.config import get_settings

logger = logging.getLogger(__name__)

ARTICLE_DOCUMENT_COLLECTION = "ArticleDocument"


class WeaviateService:
    """Service for managing article documents in Weaviate vector database."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[weaviate.WeaviateClient] = None
    
    def _get_client(self) -> Optional[weaviate.WeaviateClient]:
        """Get or create Weaviate client connection."""
        if not self.settings.weaviate_url:
            logger.warning("Weaviate URL not configured, skipping vector operations")
            return None
        
        if self._client is None:
            try:
                headers = {}
                if self.settings.openai_api_key:
                    headers["X-OpenAI-Api-Key"] = self.settings.openai_api_key
                
                auth = AuthApiKey(self.settings.weaviate_api_key) if self.settings.weaviate_api_key else None
                
                self._client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.settings.weaviate_url,
                    auth_credentials=auth,  # type: ignore[arg-type]
                    headers=headers or None,
                    additional_config=AdditionalConfig(timeout=(15, 60)),
                )
                
                # Ensure schema exists
                self._ensure_schema()
                
                logger.info("Successfully connected to Weaviate")
            except Exception as e:
                logger.error(f"Failed to connect to Weaviate: {e}", exc_info=True)
                return None
        
        return self._client
    
    def _ensure_schema(self):
        """Create the ArticleDocument collection if it doesn't exist."""
        client = self._client
        if not client:
            return
        
        if not client.collections.exists(ARTICLE_DOCUMENT_COLLECTION):
            logger.info(f"Creating Weaviate collection: {ARTICLE_DOCUMENT_COLLECTION}")
            client.collections.create(
                name=ARTICLE_DOCUMENT_COLLECTION,
                description="Product specification documents for similarity search",
                vectorizer_config=Configure.Vectorizer.text2vec_openai(),
                properties=[
                    Property(name="article_id", data_type=DataType.INT),
                    Property(name="article_name", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT),
                    Property(name="document_text", data_type=DataType.TEXT),  # Will be vectorized
                ],
            )
            logger.info(f"Created collection: {ARTICLE_DOCUMENT_COLLECTION}")
    
    def ingest_document(
        self,
        article_id: int,
        article_name: str,
        file_content: bytes,
        filename: str,
    ) -> bool:
        """
        Ingest a product specification document into Weaviate.
        
        Args:
            article_id: Database ID of the article
            article_name: Name of the article
            file_content: PDF file content as bytes
            filename: Name of the file
        
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        if not client:
            logger.warning("Weaviate not available, skipping document ingestion")
            return False
        
        try:
            collection = client.collections.get(ARTICLE_DOCUMENT_COLLECTION)
            
            # Use Weaviate's document ingestion
            # The text2vec-openai vectorizer will automatically extract and embed the document
            properties = {
                "article_id": article_id,
                "article_name": article_name,
                "filename": filename,
            }
            
            # For PDF documents, we need to extract text first
            # Weaviate's text2vec-openai works with text, not binary PDFs
            text_content = self._extract_text_from_pdf(file_content)
            if not text_content:
                logger.warning(f"Could not extract text from PDF for article {article_id}")
                return False
            
            # Add the extracted text as a property for vectorization
            all_properties = properties.copy()
            all_properties["document_text"] = text_content
            collection.data.insert(properties=all_properties)  # type: ignore
            
            logger.info(f"Successfully ingested document for article {article_id} into Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting document into Weaviate: {e}", exc_info=True)
            return False
    
    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            import fitz  # type: ignore # PyMuPDF
            
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc)
            doc.close()
            return text
        except ImportError:
            logger.warning("PyMuPDF not installed, cannot extract text from PDF")
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
            return ""
    
    def find_similar_articles(
        self,
        article_id: int,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> list[int]:
        """
        Find similar articles based on document embeddings.
        
        Args:
            article_id: ID of the article to find similar articles for
            top_k: Number of similar articles to return (default: from config)
            similarity_threshold: Minimum similarity score (default: from config)
        
        Returns:
            List of article IDs of similar articles
        """
        client = self._get_client()
        if not client:
            logger.warning("Weaviate not available, returning empty similar articles list")
            return []
        
        top_k = top_k or self.settings.weaviate_top_k
        similarity_threshold = similarity_threshold or self.settings.weaviate_similarity_threshold
        
        try:
            collection = client.collections.get(ARTICLE_DOCUMENT_COLLECTION)
            
            # First, find the UUID of the article
            response = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("article_id").equal(article_id),
                limit=1,
            )
            
            if not response.objects:
                logger.warning(f"Article {article_id} not found in Weaviate")
                return []
            
            source_uuid = response.objects[0].uuid
            
            # Now use near_object with the UUID
            similar = collection.query.near_object(
                near_object=source_uuid,
                limit=top_k + 1,  # +1 because we'll filter out the source article
                return_metadata=MetadataQuery(distance=True),
            )
            
            # Filter results
            similar_article_ids: list[int] = []
            for obj in similar.objects:
                # Skip the source article itself
                obj_article_id_raw = obj.properties.get("article_id")
                if not obj_article_id_raw or not isinstance(obj_article_id_raw, int):
                    continue
                obj_article_id = obj_article_id_raw
                if obj_article_id == article_id:
                    continue
                
                # Calculate similarity score (distance to similarity: 1 - distance)
                distance = obj.metadata.distance or 1.0
                similarity = 1.0 - distance
                
                if similarity >= similarity_threshold:
                    similar_article_ids.append(obj_article_id)
                    logger.info(
                        f"Found similar article: {obj_article_id} "
                        f"(similarity: {similarity:.3f})"
                    )
                
                if len(similar_article_ids) >= top_k:
                    break
            
            logger.info(
                f"Found {len(similar_article_ids)} similar articles for article {article_id}"
            )
            return similar_article_ids
            
        except Exception as e:
            logger.error(f"Error finding similar articles: {e}", exc_info=True)
            return []
    
    def close(self):
        """Close the Weaviate client connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("Closed Weaviate connection")
            except Exception as e:
                logger.error(f"Error closing Weaviate connection: {e}")
            finally:
                self._client = None


# Global instance
_weaviate_service: Optional[WeaviateService] = None


def get_weaviate_service() -> WeaviateService:
    """Get or create the global Weaviate service instance."""
    global _weaviate_service
    if _weaviate_service is None:
        _weaviate_service = WeaviateService()
    return _weaviate_service

