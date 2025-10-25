"""
Background processing service for articles.
Handles async OpenAI API calls for metadata extraction and cost model generation.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.cost_model import CostModel
from app.models.index import Index
from app.services.openai_client import extract_metadata_from_file, generate_cost_models

logger = logging.getLogger(__name__)


async def process_article_async(article_id: int, db: AsyncSession) -> None:
    """
    Background task to process an article:
    1. Extract metadata from the product specification file
    2. Update article with extracted metadata
    3. Generate cost models using OpenAI
    4. Save cost models to database
    
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
        
        # Step 3: Fetch available indices
        logger.info("Fetching available indices for cost model generation")
        indices_result = await db.execute(select(Index))
        indices = list(indices_result.scalars().all())
        
        if not indices:
            logger.warning("No indices available for cost model generation")
            # Mark as completed even without cost models
            article.processing_status = "completed"
            article.processing_completed_at = datetime.now(timezone.utc)
            await db.commit()
            return
        
        # Prepare indices data for OpenAI
        indices_data = []
        for idx in indices:
            indices_data.append({
                "id": idx.id,
                "name": idx.name,
                "value": float(idx.value) if idx.value else 0.0
            })
        
        # Step 4: Generate cost models using OpenAI
        logger.info(f"Generating cost models for article {article_id}")
        try:
            cost_models_data = generate_cost_models(
                article_name=article.article_name,
                article_description=article.description,
                unit_weight=float(article.unit_weight) if article.unit_weight else None,
                available_indices=indices_data
            )
            logger.info(f"Generated {len(cost_models_data)} cost models")
        except Exception as e:
            logger.error(f"Error generating cost models: {e}", exc_info=True)
            cost_models_data = []
        
        # Step 5: Save cost models to database
        if cost_models_data:
            for cm_data in cost_models_data:
                try:
                    # Check if cost model already exists
                    existing_cm = await db.execute(
                        select(CostModel).where(
                            CostModel.article_id == article_id,
                            CostModel.index_id == cm_data["index_id"]
                        )
                    )
                    existing = existing_cm.scalar_one_or_none()
                    
                    if existing:
                        # Update existing cost model
                        existing.part = float(cm_data["part"])
                        logger.info(f"Updated cost model for article {article_id}, index {cm_data['index_id']}")
                    else:
                        # Create new cost model
                        cost_model = CostModel(
                            article_id=article_id,
                            index_id=cm_data["index_id"],
                            part=float(cm_data["part"])
                        )
                        db.add(cost_model)
                        logger.info(f"Created cost model for article {article_id}, index {cm_data['index_id']}")
                except Exception as e:
                    logger.error(f"Error saving cost model: {e}", exc_info=True)
                    continue
            
            await db.commit()
        
        # Step 6: Mark processing as completed
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

