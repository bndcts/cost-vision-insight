from typing import Optional
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleRead
from app.services.article_processor import process_article_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def analyze_article(
    background_tasks: BackgroundTasks,
    articleName: str = Form(...),
    description: Optional[str] = Form(None),
    productSpecification: UploadFile = File(...),
    drawing: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze an article and store it in the database with uploaded files.
    
    This endpoint:
    1. Creates the article immediately with status "processing"
    2. Returns the article with its ID
    3. Starts background processing to:
       - Extract metadata from product specification (weight, material, etc.)
       - Generate cost models using OpenAI
    
    Use GET /articles/{id} to poll for processing status and results.
    
    Accepts:
    - articleName: Name of the article (required)
    - description: Optional description
    - productSpecification: Product specification file (required)
    - drawing: Drawing file (optional)
    
    Returns the newly created article with id, processing_status="processing".
    """
    
    logger.info(f"Received analyze request for article: {articleName}")
    logger.info(f"Description: {description}")
    logger.info(f"Spec file: {productSpecification.filename}")
    logger.info(f"Drawing file: {drawing.filename if drawing else 'None'}")
    
    try:
        # Read product specification file
        spec_content = await productSpecification.read()
        spec_filename = productSpecification.filename
        
        # Read drawing file if provided
        drawing_content = None
        drawing_filename = None
        if drawing and drawing.filename:
            drawing_content = await drawing.read()
            drawing_filename = drawing.filename
        
        # Create article in database with "processing" status
        logger.info(f"Creating article in database with processing status")
        article = Article(
            article_name=articleName,
            description=description,
            product_specification_file=spec_content,
            product_specification_filename=spec_filename,
            drawing_file=drawing_content,
            drawing_filename=drawing_filename,
            processing_status="processing",  # Set initial status
        )
        
        db.add(article)
        await db.commit()
        await db.refresh(article)
        
        logger.info(f"Successfully created article with ID: {article.id}")
        
        # Start background processing
        # Note: We need to create a new database session for the background task
        from app.db.session import SessionLocal
        
        async def background_processor():
            async with SessionLocal() as background_db:
                await process_article_async(article.id, background_db)
        
        background_tasks.add_task(background_processor)
        logger.info(f"Started background processing for article {article.id}")
        
        return article
        
    except IntegrityError as e:
        logger.error(f"Integrity error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Article with name '{articleName}' already exists",
        )
        
    except Exception as e:
        logger.error(f"Error processing article: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process article: {str(e)}",
        )

