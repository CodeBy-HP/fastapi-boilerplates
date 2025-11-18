# Logger Usage Guide

This guide explains how to use the custom logger in your FastAPI application and how to port it to other projects.

## Features

✅ **Modular & Portable**: Easy to copy to other projects  
✅ **Customizable**: Configure via environment variables or code  
✅ **Non-Interfering**: Works alongside Uvicorn without conflicts  
✅ **Colored Output**: Beautiful console logs with colors  
✅ **File Rotation**: Automatic log file rotation  
✅ **Separate Error Logs**: Errors logged to separate file  

## Quick Start

### 1. Basic Usage in Your Application

```python
from core.logger import get_logger

# Get a logger for your module
logger = get_logger("my_module")

# Use it
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
logger.debug("This is a debug message")
```

### 2. Using in Different Modules

**In routes/products.py:**
```python
from fastapi import APIRouter
from core.logger import get_logger

logger = get_logger("routes.products")
router = APIRouter()

@router.get("/products")
async def get_products():
    logger.info("Fetching all products")
    # Your code here
    return {"products": []}
```

**In services/database.py:**
```python
from core.logger import get_logger

logger = get_logger("services.database")

async def connect_db():
    logger.info("Connecting to database...")
    try:
        # Connection logic
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
```

### 3. Configuration

You can customize the logger via environment variables in your `.env` file:

```env
# Logger Configuration
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs            # Directory for log files
LOG_TO_CONSOLE=true     # Enable console logging
LOG_TO_FILE=true        # Enable file logging
LOG_USE_COLORS=true     # Enable colored console output
```

### 4. Advanced Configuration

For more control, you can create custom configurations:

```python
from core.logger import LoggerConfig, setup_logger

# Custom configuration
config = LoggerConfig(
    logger_name="app",
    log_level="DEBUG",
    log_dir="custom_logs",
    log_to_console=True,
    log_to_file=True,
    max_file_size=20 * 1024 * 1024,  # 20 MB
    backup_count=10,
    use_colors=True,
)

setup_logger(config)
```

## Log Files

The logger creates two types of log files in the `logs/` directory:

1. **app.log** - All logs (INFO, WARNING, ERROR, etc.)
2. **app_error.log** - Only ERROR and CRITICAL logs

Files are automatically rotated when they reach the size limit.

## Copying to Other Projects

To use this logger in another project:

1. **Copy the logger module:**
   ```
   cp app/core/logger.py <new_project>/logger.py
   ```

2. **Add logger settings to your config:**
   ```python
   LOG_LEVEL: str = "INFO"
   LOG_DIR: str = "logs"
   LOG_TO_CONSOLE: bool = True
   LOG_TO_FILE: bool = True
   LOG_USE_COLORS: bool = True
   ```

3. **Initialize in your main file:**
   ```python
   from logger import setup_logger, get_logger, LoggerConfig
   
   config = LoggerConfig(log_level="INFO")
   setup_logger(config)
   
   logger = get_logger("main")
   logger.info("Application started")
   ```

That's it! The logger is completely self-contained.

## Examples

### Example 1: API Endpoint with Logging

```python
from fastapi import APIRouter, HTTPException
from core.logger import get_logger

logger = get_logger("api.users")
router = APIRouter()

@router.post("/users")
async def create_user(user_data: dict):
    logger.info(f"Creating new user: {user_data.get('email')}")
    
    try:
        # Your business logic
        logger.debug(f"User data validated: {user_data}")
        # ... create user ...
        logger.info(f"User created successfully: {user_data.get('email')}")
        return {"status": "success"}
    except ValueError as e:
        logger.warning(f"Invalid user data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Example 2: Background Task with Logging

```python
from core.logger import get_logger

logger = get_logger("tasks.email")

async def send_email_task(email: str, subject: str):
    logger.info(f"Starting email task for {email}")
    
    try:
        # Send email logic
        logger.debug(f"Email subject: {subject}")
        # ...
        logger.info(f"Email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}", exc_info=True)
```

### Example 3: Middleware with Logging

```python
from fastapi import Request
from core.logger import get_logger
import time

logger = get_logger("middleware.timing")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    logger.info(f"Request started: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"Request completed: {request.method} {request.url.path} "
        f"| Status: {response.status_code} | Duration: {duration:.2f}s"
    )
    
    return response
```

## Why This Doesn't Interfere with Uvicorn

1. **Separate Logger Instance**: Uses `logging.getLogger("app")` instead of root logger
2. **Propagation Disabled**: `logger.propagate = False` prevents logs from bubbling up
3. **Custom Handlers**: Uses its own handlers, doesn't modify Uvicorn's
4. **Different Logger Names**: App uses "app.*", Uvicorn uses "uvicorn.*"

This means:
- Uvicorn logs still appear normally
- Your app logs appear with your custom formatting
- No duplicate logs
- No interference between the two systems

## Tips

- Use `DEBUG` level during development
- Use `INFO` or `WARNING` in production
- Use module-specific loggers: `get_logger("module_name")`
- Add `exc_info=True` to log full tracebacks: `logger.error("Error", exc_info=True)`
- Check log files in `logs/` directory for persistent records
