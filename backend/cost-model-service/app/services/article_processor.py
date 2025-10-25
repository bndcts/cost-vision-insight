"""
Background processing service for articles.
Handles async OpenAI API calls for metadata extraction and cost model generation.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.cost_model import CostModel
from app.models.index import Index
from app.services.openai_client import analyze_product_specification

logger = logging.getLogger(__name__)


async def process_article_async(article_id: int, db: AsyncSession) -> None:
    """
    Background task to process an article:
    1. Analyze product specification file using OpenAI
    2. Extract unit weight and material composition
    3. Update article with extracted data
    4. Generate and store cost model parts
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

        spec_bytes = article.product_specification_file
        spec_filename = article.product_specification_filename

        if not spec_bytes or not spec_filename:
            logger.warning(f"Article {article_id} has no product specification file")
            article.processing_status = "failed"
            article.processing_error = "No product specification file provided"
            article.processing_completed_at = datetime.now(timezone.utc)
            await db.commit()
            return

        # Analyze the product specification using OpenAI structured outputs
        logger.info(f"Analyzing product specification for article {article_id}")
        try:
            analysis = analyze_product_specification(
                file_content=spec_bytes,
                filename=spec_filename,
            )
        except Exception as exc:
            logger.error(f"Error analyzing product specification: {exc}", exc_info=True)
            article.processing_status = "failed"
            article.processing_error = str(exc)
            article.processing_completed_at = datetime.now(timezone.utc)
            await db.commit()
            return

        # Update article with extracted weight (convert grams to kg for storage)
        if analysis.total_weight_grams and analysis.total_weight_grams > 0:
            article.unit_weight = analysis.total_weight_grams / 1000.0
            logger.info(
                "Updated article %s with unit_weight: %.6f kg (%.2f g)",
                article_id,
                article.unit_weight,
                analysis.total_weight_grams,
            )
        await db.commit()

        # Create cost models from the analyzed materials
        if analysis.indices:
            # Get all indices from database by name for mapping
            indices_stmt = select(Index).order_by(Index.name.asc(), Index.date.desc())
            indices_result = await db.execute(indices_stmt)
            indices_by_name: dict[str, Index] = {}
            for idx in indices_result.scalars():
                if idx.name not in indices_by_name:
                    indices_by_name[idx.name] = idx

            # Remove existing cost models for the article
            await db.execute(delete(CostModel).where(CostModel.article_id == article_id))

            # Create new cost models
            created_count = 0
            for material_index in analysis.indices:
                # Map the IndexName enum value to database index
                index_name = material_index.index_name.value
                db_index = indices_by_name.get(index_name)
                
                if not db_index:
                    logger.warning(
                        f"Index '{index_name}' not found in database, skipping"
                    )
                    continue
                
                if material_index.quantity_grams <= 0:
                    logger.warning(
                        f"Invalid quantity {material_index.quantity_grams}g for {index_name}, skipping"
                    )
                    continue

                db.add(
                    CostModel(
                        article_id=article_id,
                        index_id=db_index.id,
                        part=round(material_index.quantity_grams, 4),
                    )
                )
                created_count += 1
                logger.info(
                    f"  Added cost model: {index_name} = {material_index.quantity_grams:.2f}g"
                )

            await db.commit()
            logger.info(
                f"Stored {created_count} cost model parts for article {article_id}"
            )
            
            total_grams = sum(m.quantity_grams for m in analysis.indices)
            logger.info(
                f"Total material weight for article {article_id}: {total_grams:.2f}g"
            )
        else:
            logger.info(f"No materials extracted for article {article_id}")

        # Mark processing as completed
        article.processing_status = "completed"
        article.processing_completed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(f"Successfully completed processing for article {article_id}")

    except Exception as e:  # pragma: no cover - defensive
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
        except Exception as commit_error:  # pragma: no cover - defensive
            logger.error(f"Error updating article status to failed: {commit_error}")
