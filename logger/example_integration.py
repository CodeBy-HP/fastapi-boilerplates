"""
Example: How to integrate the logger in your FastAPI application

This file shows the complete integration process.
Copy this pattern to your main.py or app.py file.
"""

from fastapi import FastAPI, APIRouter, HTTPException
from contextlib import asynccontextmanager
import os

# Import the logger
from .logger import setup_logger, get_logger, LoggerConfig


# ============================================
# 1. SETUP LOGGER (Do this first, before creating the app)
# ============================================
config = LoggerConfig(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "logs"),
    log_to_console=os.getenv("LOG_TO_CONSOLE", "true").lower() == "true",
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
    use_colors=os.getenv("LOG_USE_COLORS", "true").lower() == "true",
)
setup_logger(config)

# Get logger for main module
logger = get_logger("main")


# ============================================
# 2. CREATE FASTAPI APP WITH LIFESPAN LOGGING
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with logging"""
    logger.info("🚀 Application starting up...")
    # Add your startup logic here (DB connections, etc.)
    yield
    logger.info("🛑 Application shutting down...")
    # Add your shutdown logic here


app = FastAPI(
    title="My API",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================
# 3. USE LOGGER IN ROUTES
# ============================================
router = APIRouter(prefix="/api", tags=["Example"])

# Get logger for routes module
route_logger = get_logger("routes.example")


@router.get("/")
async def root():
    """Example root endpoint"""
    route_logger.info("Root endpoint accessed")
    return {"message": "Hello World", "status": "ok"}


@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """Example endpoint with logging"""
    route_logger.info(f"Fetching item: {item_id}")
    
    try:
        # Simulate some processing
        if item_id < 0:
            route_logger.warning(f"Invalid item_id received: {item_id}")
            raise ValueError("Item ID must be positive")
        
        route_logger.debug(f"Item {item_id} processed successfully")
        return {"item_id": item_id, "status": "found"}
        
    except ValueError as e:
        route_logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        route_logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process")
async def process_data(data: dict):
    """Example POST endpoint with error handling"""
    route_logger.info(f"Processing data: {data.get('name', 'unknown')}")
    
    try:
        # Your processing logic
        route_logger.debug(f"Data validated: {data}")
        # Simulate processing
        result = {"processed": True, "data": data}
        route_logger.info("Data processed successfully")
        return result
        
    except Exception as e:
        route_logger.error(f"Processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Processing failed")


# ============================================
# 4. OPTIONAL: MIDDLEWARE FOR REQUEST LOGGING
# ============================================
from fastapi import Request
import time

middleware_logger = get_logger("middleware")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Log incoming request
    middleware_logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    middleware_logger.info(
        f"← {request.method} {request.url.path} | "
        f"Status: {response.status_code} | Duration: {duration:.3f}s"
    )
    
    return response


# ============================================
# 5. INCLUDE ROUTER
# ============================================
app.include_router(router)


# ============================================
# 6. RUN THE APPLICATION
# ============================================
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "example_integration:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )


"""
TO USE IN YOUR PROJECT:
1. Copy logger.py to your project root or a core/utils folder
2. Copy .env.example and rename to .env (or add variables to existing .env)
3. Copy the setup code from sections 1-2 above to your main.py
4. Import and use get_logger() in any module:
   
   from logger import get_logger
   logger = get_logger("your_module_name")
   logger.info("Your message")

That's it! Check logs/ directory for log files.
"""
