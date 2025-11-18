"""
Example route to demonstrate logger usage in API endpoints
"""

from fastapi import APIRouter, HTTPException
from core.logger import get_logger

# logger config should be already setup in main file or use setup_logger() in this file first with the config
# Get logger for this module
logger = get_logger("routes.example")

router = APIRouter(prefix="/example", tags=["Example"])


@router.get("/info")
async def example_info():
    """Example endpoint demonstrating INFO level logging"""
    logger.info("Example info endpoint accessed")
    return {"message": "Check your logs!", "level": "INFO"}


@router.get("/warning")
async def example_warning():
    """Example endpoint demonstrating WARNING level logging"""
    logger.warning("This is a warning - user accessed potentially deprecated endpoint")
    return {"message": "This endpoint may be deprecated soon", "level": "WARNING"}


@router.get("/error")
async def example_error():
    """Example endpoint demonstrating ERROR level logging"""
    logger.error("User triggered an error endpoint")
    raise HTTPException(status_code=500, detail="Example error - check logs")


@router.get("/process/{item_id}")
async def process_item(item_id: int):
    """Example of logging throughout a process"""
    logger.info(f"Processing item with ID: {item_id}")
    
    try:
        # Simulate some processing
        logger.debug(f"Validating item {item_id}")
        
        if item_id < 0:
            logger.warning(f"Invalid item ID received: {item_id}")
            raise ValueError("Item ID must be positive")
        
        logger.debug(f"Item {item_id} validated successfully")
        logger.info(f"Item {item_id} processed successfully")
        
        return {
            "item_id": item_id,
            "status": "processed",
            "message": "Check logs to see the processing flow"
        }
        
    except ValueError as e:
        logger.error(f"Validation error for item {item_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
