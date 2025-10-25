"""
Background processing service for articles.
Handles async OpenAI API calls for metadata extraction (unit weight only).
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services.openai_client import extract_metadata_from_file

logger = logging.getLogger(__name__)


async def process_article_async(article_id: int, db: AsyncSession) -> None:
    """
    Background task to process an article:
    1. Extract unit weight from the product specification file
    2. Update article with extracted unit weight
    
    Args:
        article_id: ID of the article to process
        db: Database session
    """
    logger.info(f"Starting background processing for article {article_id}")
    
    try:
        # Fetch the article
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        
        if not article:
            logger.error(f"Article {article_id} not found")
            return
        
        # Update status to processing
        article.processing_status = "processing"
        article.processing_started_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Step 1: Extract weight from product specification file
        logger.info(f"Extracting weight for article {article_id}")
        weight_data = {}
        
        if article.product_specification_file and article.product_specification_filename:
            try:
                weight_data = extract_metadata_from_file(
                    file_content=article.product_specification_file,
                    filename=article.product_specification_filename
                )
                logger.info(f"Extracted weight data: {weight_data}")
            except Exception as e:
                logger.error(f"Error extracting weight: {e}", exc_info=True)
                # Continue processing even if weight extraction fails
        
        # Step 2: Update article with extracted weight (convert grams to kg for storage)
        if weight_data.get("unit_weight_grams") is not None:
            weight_grams = float(weight_data["unit_weight_grams"])
            # Store as kilograms in the database
            article.unit_weight = weight_grams / 1000.0
            logger.info(f"Updated article {article_id} with unit_weight: {article.unit_weight} kg ({weight_grams}g)")
        await db.commit()
        await db.refresh(article)

        # Mark processing as completed
        article.processing_status = "completed"
        article.processing_completed_at = datetime.now(timezone.utc)
        await db.commit()
        
        logger.info(f"Successfully completed processing for article {article_id}")
        
    except Exception as e:
        logger.error(f"Error processing article {article_id}: {e}", exc_info=True)
        
        # Mark as failed and store error
        try:
            result = await db.execute(select(Article).where(Article.id == article_id))
            article = result.scalar_one_or_none()
            
            if article:
                article.processing_status = "failed"
                article.processing_error = str(e)
                article.processing_completed_at = datetime.now(timezone.utc)
                await db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating article status to failed: {commit_error}")

