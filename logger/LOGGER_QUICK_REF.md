# Logger Quick Reference 🚀

## Import and Use (Most Common)

```python
from core.logger import get_logger

logger = get_logger("module_name")
logger.info("Your message here")
```

## Log Levels (from least to most severe)

```python
logger.debug("Detailed diagnostic info")      # Development only
logger.info("General information")            # Normal operations
logger.warning("Something to watch")          # Potential issues
logger.error("Something went wrong")          # Errors that need attention
logger.critical("System failure")             # Critical problems
```

## Common Patterns

### Basic Usage
```python
from core.logger import get_logger
logger = get_logger("my_module")
logger.info("Application started")
```

### In API Routes
```python
from core.logger import get_logger
logger = get_logger("routes.users")

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    logger.info(f"Fetching user {user_id}")
    return {"user_id": user_id}
```

### With Exception Handling
```python
try:
    # Your code
    pass
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # Includes full traceback
```

### Module-Specific Logger Names
```python
# Use descriptive names to track logs by component
get_logger("routes.products")      # Product routes
get_logger("services.auth")        # Auth service
get_logger("database")             # Database operations
get_logger("utils.validators")     # Validation utilities
```

## Configuration (.env)

```env
LOG_LEVEL=INFO          # DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_DIR=logs           # Log files directory
LOG_TO_CONSOLE=true    # Show logs in console
LOG_TO_FILE=true       # Save logs to files
LOG_USE_COLORS=true    # Colored console output
```

## Log Files Location

- `logs/app.log` - All logs
- `logs/app_error.log` - Errors only

## Test the Logger

```bash
python test_logger.py
```

## Production Tips

✅ Use `INFO` or `WARNING` level in production  
✅ Use `DEBUG` in development  
✅ Always use module-specific names: `get_logger("module")`  
✅ Include context: `logger.info(f"Processing order {order_id}")`  
✅ Log exceptions: `logger.error("Failed", exc_info=True)`  
❌ Don't log sensitive data (passwords, tokens, etc.)  

## That's It!

The logger is already set up and ready to use. Just import and log! 📝
