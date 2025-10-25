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
from app.services.cost_model_builder import build_cost_model_parts
from app.services.openai_client import (
    extract_material_breakdown,
    extract_metadata_from_file,
)

logger = logging.getLogger(__name__)


async def process_article_async(article_id: int, db: AsyncSession) -> None:
    """
    Background task to process an article:
    1. Extract unit weight from the product specification file
    2. Update article with extracted unit weight
    3. Generate cost model parts based on material breakdown
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

        # Step 1: Extract weight from product specification file
        logger.info(f"Extracting weight for article {article_id}")
        weight_data: dict[str, float | None] = {}

        if spec_bytes and spec_filename:
            try:
                weight_data = extract_metadata_from_file(
                    file_content=spec_bytes, filename=spec_filename
                )
                logger.info(f"Extracted weight data: {weight_data}")
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Error extracting weight: {exc}", exc_info=True)
                # Continue processing even if weight extraction fails

        # Step 2: Update article with extracted weight (convert grams to kg for storage)
        if weight_data.get("unit_weight_grams") is not None:
            weight_grams = float(weight_data["unit_weight_grams"])
            # Store as kilograms in the database
            article.unit_weight = weight_grams / 1000.0
            logger.info(
                "Updated article %s with unit_weight: %.6f kg (%.2f g)",
                article_id,
                article.unit_weight,
                weight_grams,
            )
        await db.commit()
        await db.refresh(article)

        # Step 3: Generate cost models from material composition
        cost_model_parts = []
        if spec_bytes and spec_filename:
            try:
                materials = extract_material_breakdown(
                    file_content=spec_bytes,
                    filename=spec_filename,
                )
                cost_model_parts = await build_cost_model_parts(materials, db)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Error generating cost models: {exc}", exc_info=True)

        unit_weight_kg = float(article.unit_weight) if article.unit_weight is not None else None
        total_weight_grams = unit_weight_kg * 1000.0 if unit_weight_kg is not None else None

        if cost_model_parts:
            if total_weight_grams and total_weight_grams > 0:
                # Remove existing cost models for the article
                await db.execute(delete(CostModel).where(CostModel.article_id == article_id))
                for part in cost_model_parts:
                    grams = part.fraction * total_weight_grams
                    db.add(
                        CostModel(
                            article_id=article_id,
                            index_id=part.index_id,
                            part=round(grams, 4),
                        )
                    )
                await db.commit()
                logger.info(
                    "Stored %d cost model parts for article %s",
                    len(cost_model_parts),
                    article_id,
                )
                logger.info(
                    "Total grams represented for article %s: %.4f",
                    article_id,
                    sum(p.fraction for p in cost_model_parts) * total_weight_grams,
                )
            else:
                logger.warning(
                    "Skipping cost model persistence for article %s due to missing unit weight",
                    article_id,
                )
        else:
            logger.info("No cost model parts generated for article %s", article_id)

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
