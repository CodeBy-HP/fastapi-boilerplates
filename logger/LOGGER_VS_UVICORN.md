# Logger vs Uvicorn - How They Work Together

## The Setup

Your FastAPI application now has **two independent logging systems**:

1. **Uvicorn Logger** (built-in) - Handles HTTP requests/responses
2. **Custom App Logger** (your logger) - Handles your application logic

## What Each Logger Does

### Uvicorn Logger (Automatic)
- ✅ HTTP request logs (GET, POST, etc.)
- ✅ Server startup/shutdown messages
- ✅ Response status codes
- ✅ Request processing time

**Example Uvicorn output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     127.0.0.1:54321 - "GET / HTTP/1.1" 200 OK
```

### Your Custom Logger (What You Created)
- ✅ Application business logic
- ✅ Data processing steps
- ✅ Custom warnings and errors
- ✅ Debug information
- ✅ Database operations
- ✅ External API calls
- ✅ Any custom events you want to track

**Example custom logger output:**
```
2025-11-18 13:13:06 | INFO     | app.main | main:lifespan:26 | Starting Product-Inventory-API v1.0.0
2025-11-18 13:13:10 | INFO     | app.routes.products | products:get_products:15 | Fetching all products
2025-11-18 13:13:11 | WARNING  | app.services.cache | cache:get:42 | Cache miss for key: products_list
```

## Example: Complete Request Flow

When a user visits `GET /products/123`:

```
# Uvicorn logs the HTTP request:
INFO:     127.0.0.1:54321 - "GET /products/123 HTTP/1.1" 200 OK

# Your logger logs the application logic:
2025-11-18 14:30:15 | INFO     | app.routes.products | products:get_product:28 | Fetching product 123
2025-11-18 14:30:15 | DEBUG    | app.services.db | db:query:56 | Executing query: SELECT * FROM products WHERE id=123
2025-11-18 14:30:16 | INFO     | app.routes.products | products:get_product:35 | Product 123 found successfully
```

**Result:** You get both HTTP-level info (from Uvicorn) AND application-level info (from your logger)!

## Why They Don't Interfere

### Technical Explanation

```python
# Uvicorn uses the root logger
uvicorn_logger = logging.getLogger("uvicorn")

# Your app uses a separate logger with propagation disabled
app_logger = logging.getLogger("app")
app_logger.propagate = False  # ← This is the key!
```

**What `propagate = False` does:**
- Prevents your logs from bubbling up to the root logger
- Keeps your logs separate from Uvicorn's logs
- Allows independent formatting and handling

### Logger Hierarchy

```
Root Logger
├── uvicorn (Uvicorn's logs)
│   ├── uvicorn.access
│   └── uvicorn.error
└── app (Your logs) [propagate=False]
    ├── app.main
    ├── app.routes.products
    ├── app.services.database
    └── app.utils.validators
```

Because `propagate=False`, the "app" branch is independent!

## Console Output Example

When you run your application, you'll see both:

```bash
# Uvicorn startup messages (white/default color)
INFO:     Will watch for changes in these directories: ['/path/to/project']
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles

# Your custom startup log (colored green for INFO)
2025-11-18 14:45:23 | INFO     | app.main | main:lifespan:26 | Starting Product-Inventory-API v1.0.0

# Uvicorn request log (white/default)
INFO:     127.0.0.1:54321 - "GET / HTTP/1.1" 200 OK

# Your custom endpoint log (colored green for INFO)
2025-11-18 14:45:30 | INFO     | app.main | main:root:47 | Root endpoint accessed
```

## Customization Options

### Change Your Logger Level Without Affecting Uvicorn

```env
# Your logger
LOG_LEVEL=DEBUG  # Show detailed app logs

# Uvicorn keeps its default INFO level
```

### Change Uvicorn Level Without Affecting Your Logger

```bash
# Run with different Uvicorn log level
uvicorn app.main:app --log-level warning
```

Your app logger continues with its configured level!

## File Logs vs Console Logs

### Console (Terminal)
- Shows both Uvicorn and your logs
- Your logs have colors
- Uvicorn logs are plain

### Log Files (logs/app.log)
- **Only your application logs** (not Uvicorn's)
- No Uvicorn request logs
- This is by design - keeps your app logs clean

If you want Uvicorn logs in files, configure Uvicorn separately:
```bash
uvicorn app.main:app --log-config logging_config.json
```

## Best Practices

### ✅ DO

```python
# Log business logic
logger.info("Processing payment for order 123")
logger.warning("Low inventory alert for product 456")
logger.error("Failed to connect to payment gateway")

# Log important state changes
logger.info("User authenticated successfully")
logger.info("Database migration completed")

# Log with context
logger.info(f"Sending email to {user.email}")
```

### ❌ DON'T

```python
# Don't log what Uvicorn already logs
logger.info("GET request received")  # Uvicorn does this
logger.info("Response sent")  # Uvicorn does this

# Don't duplicate HTTP info
logger.info(f"Status code: 200")  # Uvicorn handles this
```

## Quick Comparison

| Aspect | Uvicorn Logger | Your Custom Logger |
|--------|---------------|-------------------|
| **Purpose** | HTTP protocol layer | Application logic |
| **Logs What** | Requests, responses, status codes | Business logic, data processing |
| **Configuration** | Via Uvicorn CLI options | Via .env or LoggerConfig |
| **Log Files** | Not by default | Yes (logs/app.log) |
| **Colors** | No | Yes (configurable) |
| **Format** | Fixed Uvicorn format | Customizable |
| **When Active** | Only when server runs | Anytime logger is imported |

## Summary

🎯 **Key Point:** They're **complementary**, not competing!

- **Uvicorn** = "What HTTP requests are coming in?"
- **Your Logger** = "What is my application doing with those requests?"

Together, they give you complete visibility:
1. HTTP traffic (Uvicorn)
2. Application behavior (Your logger)

Both work perfectly side-by-side without any conflicts! 🎉
