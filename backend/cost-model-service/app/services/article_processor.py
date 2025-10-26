"""
Background processing service for articles.
Handles async OpenAI API calls for metadata extraction and cost model generation.
Also integrates with Weaviate for similar article search via RAG.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.cost_model import CostModel
from app.models.index import Index
from app.models.order import Order
from app.services.openai_client import analyze_product_specification
from app.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)

LABOR_INDEX_NAME = "Arbeitskosten Deutschland [€/h] (Eurostat)"
ELECTRICITY_INDEX_NAME = "Strom [€/MWh] (Finanzen.net)"


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

        # Step 1: Ingest into Weaviate first to find similar products
        similar_article_ids = []
        similar_products_context = None
        
        try:
            weaviate_service = get_weaviate_service()
            
            # Ingest the document into Weaviate
            logger.info(f"Ingesting document for article {article_id} into Weaviate")
            ingested = weaviate_service.ingest_document(
                article_id=article_id,
                article_name=article.article_name,
                file_content=spec_bytes,
                filename=spec_filename,
            )
            
            if ingested:
                # Find similar articles
                logger.info(f"Finding similar articles for article {article_id}b")
                similar_article_ids = weaviate_service.find_similar_articles(article_id)
                
                if similar_article_ids:
                    logger.info(
                        f"Found {len(similar_article_ids)} similar articles: {similar_article_ids}"
                    )
                    
                    # Fetch cost models of similar articles to use as context
                    similar_articles = await db.execute(
                        select(Article).where(Article.id.in_(similar_article_ids))
                    )
                    similar_context_parts = []
                    
                    for similar_article in similar_articles.scalars():
                        # Get cost models for this similar article
                        cost_models_result = await db.execute(
                            select(CostModel, Index)
                            .join(Index, CostModel.index_id == Index.id)
                            .where(CostModel.article_id == similar_article.id)
                        )
                        cost_models = cost_models_result.all()
                        
                        if cost_models:
                            context_part = f"Similar Product: {similar_article.article_name}"
                            if similar_article.unit_weight:
                                context_part += f" (Total weight: {similar_article.unit_weight * 1000:.2f}g)"
                            context_part += "\nMaterial composition:"
                            
                            for cost_model, index in cost_models:
                                context_part += f"\n  - {index.name}: {cost_model.part:.2f}g"
                            
                            similar_context_parts.append(context_part)
                    
                    if similar_context_parts:
                        similar_products_context = "\n\n".join(similar_context_parts)
                        logger.info(f"Prepared context from {len(similar_context_parts)} similar products")
                else:
                    logger.info(f"No similar articles found for article {article_id}")
            else:
                logger.warning(f"Failed to ingest document for article {article_id} into Weaviate")
                
        except Exception as weaviate_error:
            # Don't fail the entire processing if Weaviate fails
            logger.warning(
                f"Weaviate integration failed for article {article_id}: {weaviate_error}",
                exc_info=True
            )

        # Step 2: Analyze the product specification using OpenAI with similar products context
        # Determine latest observed article price from orders (if any)
        async def _latest_article_price() -> float | None:
            stmt = (
                select(Order.price)
                .where(
                    or_(
                        Order.article_id == article_id,
                        Order.article_name == article.article_name,
                    )
                )
                .order_by(Order.order_date.desc())
            )
            result = await db.execute(stmt)
            price_value = result.scalars().first()
            return float(price_value) if price_value is not None else None

        price_hint = await _latest_article_price()

        context_notes: list[str] = []
        if article.description:
            context_notes.append(f"Description: {article.description}")
        if article.comment:
            context_notes.append(f"Notes: {article.comment}")
        if article.unit_weight:
            context_notes.append(f"Unit weight: {float(article.unit_weight):.4f} kg")
        article_context = " ".join(context_notes) if context_notes else None

        # Analyze the product specification using OpenAI structured outputs
        logger.info(f"Analyzing product specification for article {article_id}")
        if similar_products_context:
            logger.info("Using similar products as context for analysis")
        
        try:
            analysis = analyze_product_specification(
                file_content=spec_bytes,
                filename=spec_filename,
                similar_products_context=similar_products_context,
                article_price_eur=price_hint,
                article_context=article_context,
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

            # Add labor cost contribution if provided (as direct EUR value)
            labor_cost_eur = (
                float(analysis.labor_cost_eur)
                if analysis.labor_cost_eur and analysis.labor_cost_eur > 0
                else None
            )
            if labor_cost_eur:
                labor_index = indices_by_name.get(LABOR_INDEX_NAME)
                if labor_index:
                    db.add(
                        CostModel(
                            article_id=article_id,
                            index_id=labor_index.id,
                            part=1.0,  # Quantity is 1 unit, actual cost is in direct_cost_eur
                            direct_cost_eur=round(labor_cost_eur, 4),
                        )
                    )
                    created_count += 1
                    logger.info(
                        f"  Added labor cost: {labor_cost_eur:.2f} EUR"
                    )
                else:
                    logger.warning(
                        "Labor index '%s' not found in DB; skipping labor contribution",
                        LABOR_INDEX_NAME,
                    )

            # Add electricity cost contribution if provided (as direct EUR value)
            electricity_cost_eur = (
                float(analysis.electricity_cost_eur)
                if analysis.electricity_cost_eur and analysis.electricity_cost_eur > 0
                else None
            )
            if electricity_cost_eur:
                energy_index = indices_by_name.get(ELECTRICITY_INDEX_NAME)
                if energy_index:
                    db.add(
                        CostModel(
                            article_id=article_id,
                            index_id=energy_index.id,
                            part=1.0,  # Quantity is 1 unit, actual cost is in direct_cost_eur
                            direct_cost_eur=round(electricity_cost_eur, 4),
                        )
                    )
                    created_count += 1
                    logger.info(
                        f"  Added electricity cost: {electricity_cost_eur:.2f} EUR"
                    )
                else:
                    logger.warning(
                        "Electricity index '%s' not found in DB; skipping electricity contribution",
                        ELECTRICITY_INDEX_NAME,
                    )
            
            # Add other manufacturing costs if provided (as direct EUR value)
            other_costs_eur = (
                float(analysis.other_manufacturing_costs_eur)
                if analysis.other_manufacturing_costs_eur and analysis.other_manufacturing_costs_eur > 0
                else None
            )
            if other_costs_eur:
                # Use a generic "other costs" placeholder index (we'll use any available index as a marker)
                # If we don't have a suitable index, we could create a sentinel, but for now we'll just skip
                # Actually, let's just use the first available index as a placeholder since we're using direct_cost_eur
                if indices_by_name:
                    placeholder_index = next(iter(indices_by_name.values()))
                    db.add(
                        CostModel(
                            article_id=article_id,
                            index_id=placeholder_index.id,
                            part=0.0,  # Part is 0 to indicate this is a direct cost, not quantity-based
                            direct_cost_eur=round(other_costs_eur, 4),
                        )
                    )
                    created_count += 1
                    logger.info(
                        f"  Added other manufacturing costs: {other_costs_eur:.2f} EUR"
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

        # Store similar articles if we found any
        if similar_article_ids:
            article.similar_articles = similar_article_ids
            logger.info(
                f"Stored {len(similar_article_ids)} similar articles for article {article_id}"
            )

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
