# FastAPI Logger Boilerplate

A production-ready, drag-and-drop logging solution for FastAPI applications with colored console output, file rotation, and zero Uvicorn conflicts.

## 📦 Quick Start

### 1. **Copy Files**
```bash
# Copy these two files to your project:
logger.py
.env.example  # rename to .env or merge with your existing .env
```

### 2. **Configure** (`.env`)
```env
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_USE_COLORS=true
```

### 3. **Initialize** (in your `main.py` or `app.py`)
```python
from logger import setup_logger, get_logger, LoggerConfig
import os

# Setup logger on app startup
config = LoggerConfig(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "logs"),
    log_to_console=os.getenv("LOG_TO_CONSOLE", "true").lower() == "true",
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
    use_colors=os.getenv("LOG_USE_COLORS", "true").lower() == "true",
)
setup_logger(config)

logger = get_logger("main")
logger.info("Application started")
```

### 4. **Use Anywhere**
```python
from logger import get_logger

logger = get_logger("routes.users")
logger.info("User endpoint accessed")
```

---

## 📖 Usage

### **Basic Logging**
```python
from logger import get_logger

logger = get_logger("my_module")

logger.debug("Detailed info for debugging")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

### **In API Routes**
```python
from fastapi import APIRouter, HTTPException
from logger import get_logger

logger = get_logger("routes.products")
router = APIRouter()

@router.get("/products/{id}")
async def get_product(id: int):
    logger.info(f"Fetching product {id}")
    try:
        # Your logic
        return {"id": id}
    except Exception as e:
        logger.error(f"Failed to fetch product: {e}", exc_info=True)
        raise HTTPException(500, "Internal error")
```

### **With Exception Tracebacks**
```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)  # Full traceback
```

### **Module-Specific Loggers**
```python
# Good practice: use descriptive names
get_logger("routes.auth")       # Authentication routes
get_logger("services.database") # Database service
get_logger("tasks.email")       # Email background tasks
```

---

## ⚙️ Configuration

### **Environment Variables**
| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Minimum log level |
| `LOG_DIR` | any path | logs | Log files directory |
| `LOG_TO_CONSOLE` | true/false | true | Console output |
| `LOG_TO_FILE` | true/false | true | File output |
| `LOG_USE_COLORS` | true/false | true | Colored console logs |

### **Advanced Configuration**
```python
from logger import LoggerConfig, setup_logger

config = LoggerConfig(
    logger_name="app",
    log_level="DEBUG",
    log_dir="custom_logs",
    max_file_size=20 * 1024 * 1024,  # 20MB
    backup_count=10,                  # Keep 10 backup files
    use_colors=True
)
setup_logger(config)
```

---

## 📁 Log Files

Generated in `LOG_DIR` (default: `logs/`):
- **`app.log`** - All logs (INFO, WARNING, ERROR, etc.)
- **`app_error.log`** - Errors and critical only

Files auto-rotate at 10MB (configurable) with 5 backups retained.

---

## ✨ Features

✅ **Drag & Drop** - Just copy `logger.py` to your project  
✅ **Zero Conflicts** - Works alongside Uvicorn without interference  
✅ **Colored Output** - Beautiful, readable console logs  
✅ **File Rotation** - Automatic log file management  
✅ **Separate Error Logs** - Quick error tracking  
✅ **Fully Customizable** - Via environment or code  
✅ **Production Ready** - Used in production environments  

---

## 🔍 How It Works with Uvicorn

Your app has **two independent logging systems**:

| Logger | Purpose | Logs |
|--------|---------|------|
| **Uvicorn** | HTTP layer | `GET /api HTTP/1.1 200 OK` |
| **This Logger** | App logic | `Processing order #123` |

**No conflicts** because:
- Uses separate logger namespace (`app.*` vs `uvicorn.*`)
- `propagate=False` prevents log mixing
- Independent formatters and handlers

**Console output:**
```
# Uvicorn
INFO:     Uvicorn running on http://127.0.0.1:8000

# Your logger (colored)
2025-11-18 10:30:45 | INFO     | app.main | main:startup:12 | Application started
```

---

## 📝 Best Practices

### ✅ Do
```python
# Log business logic with context
logger.info(f"Processing payment for order {order_id}")
logger.warning(f"Low stock alert: {product.name}")

# Log errors with tracebacks
logger.error("Payment failed", exc_info=True)

# Use descriptive module names
logger = get_logger("services.payment")
```

### ❌ Don't
```python
# Don't log what Uvicorn already logs
logger.info("GET request received")  # Uvicorn does this

# Don't log sensitive data
logger.info(f"Password: {password}")  # Security risk
```

---

## 🛠️ Examples

### **Startup Logging**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from logger import get_logger

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting...")
    # Startup logic
    yield
    logger.info("Application shutting down...")

app = FastAPI(lifespan=lifespan)
```

### **Middleware Logging**
```python
from fastapi import Request
from logger import get_logger
import time

logger = get_logger("middleware")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start
    logger.info(f"Response: {response.status_code} | {duration:.2f}s")
    return response
```

### **Background Task Logging**
```python
from logger import get_logger

logger = get_logger("tasks.email")

async def send_email(email: str):
    logger.info(f"Sending email to {email}")
    try:
        # Email logic
        logger.info(f"Email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Email failed: {e}", exc_info=True)
```

---

## 🚀 Production Tips

- Use `INFO` or `WARNING` level in production
- Use `DEBUG` only in development
- Monitor `app_error.log` for issues
- Set up log aggregation (e.g., ELK, CloudWatch) for log files
- Rotate logs regularly or increase backup count

---

## 📄 License

Free to use in your projects. No attribution required.

---

## 🤝 Support

Issues? Questions? Just check the examples above or tweak `LoggerConfig` to your needs.

**Happy Logging! 🎉**
