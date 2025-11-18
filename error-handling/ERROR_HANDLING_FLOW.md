# Error Handling Flow - Visual Guide

## The Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Makes Request                      │
│                  POST /movies {"title": "..."}               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Endpoint                          │
│                                                               │
│  @router.post("/movies")                                     │
│  async def create_movie(data: dict):                         │
│      try:                                                     │
│          # Your code here                                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                  │
              SUCCESS                ERROR
                    │                  │
                    ▼                  ▼
         ┌──────────────────┐  ┌──────────────────────┐
         │                  │  │  Exception Occurs     │
         │  Return Result   │  │  (ValueError, etc.)   │
         │                  │  │                       │
         └────────┬─────────┘  └──────────┬───────────┘
                  │                       │
                  │                       ▼
                  │            ┌──────────────────────────────┐
                  │            │  Logger Records Error        │
                  │            │                              │
                  │            │  logger.error(               │
                  │            │    "DB failed: {e}",        │
                  │            │    exc_info=True  ← Full trace
                  │            │  )                           │
                  │            │                              │
                  │            │  Saved to:                   │
                  │            │  • logs/app.log              │
                  │            │  • logs/app_error.log        │
                  │            └──────────┬───────────────────┘
                  │                       │
                  │                       ▼
                  │            ┌──────────────────────────────┐
                  │            │  HTTPException Raised        │
                  │            │                              │
                  │            │  raise HTTPException(        │
                  │            │    status_code=500,          │
                  │            │    detail="Service error" ←Safe
                  │            │  )                           │
                  │            └──────────┬───────────────────┘
                  │                       │
                  ▼                       ▼
         ┌────────────────────────────────────────┐
         │     Response Sent to Client            │
         │                                        │
         │  SUCCESS:                ERROR:        │
         │  {                       {             │
         │    "id": 123,             "detail":    │
         │    "title": "..."         "Service    │
         │  }                        error"       │
         │                           }            │
         └────────────────────────────────────────┘
```

## What Happens Where

### 1️⃣ In Your Code (Developer View)

```python
try:
    result = await database.create_movie(data)
    logger.info("Movie created: {result.id}")  # ← Logged to files
    return result  # ← Sent to client
    
except ConnectionError as e:
    # This happens in your server (not visible to client)
    logger.error(f"Database connection failed: {e}", exc_info=True)
    #                                              ↑
    #                            Full stack trace in logs
    
    # This is sent to the client
    raise HTTPException(
        status_code=503,
        detail="Service temporarily unavailable"  # ← Safe message
    )
```

### 2️⃣ Log File (logs/app.log)

```
2025-11-18 14:30:15 | ERROR | app.routes.movies | create_movie:45 | Database connection failed: Connection timeout
Traceback (most recent call last):
  File "routes/movies.py", line 42, in create_movie
    result = await database.create_movie(data)
  File "database.py", line 123, in create_movie
    conn = await self.pool.acquire()
ConnectionError: Connection timeout
```

### 3️⃣ HTTP Response (Client Receives)

```json
{
  "detail": "Service temporarily unavailable"
}
```

**Status Code:** 503 Service Unavailable

## Side-by-Side Comparison

### What Developer Sees (Logs)

```
2025-11-18 14:30:15 | ERROR | app.routes.movies | create_movie:45 | 
Database connection failed: Connection timeout at line 123 in database.py
Pool: max_size=10, current=10, timeout=30s
Connection string: postgresql://localhost:5432/mydb
Stack trace: [... full details ...]
```

### What Client Sees (HTTP Response)

```json
{
  "detail": "Service temporarily unavailable"
}
```

**Notice:** Client doesn't see database details, connection strings, or stack traces!

## The Two Audiences

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  LOGGER (Internal - For Developers)                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    │
│  Audience: You and your team                            │
│  Location: Log files (logs/app.log)                     │
│  Content:  Full technical details                       │
│  Purpose:  Debug and fix issues                         │
│  Security: Private, can include sensitive data          │
│                                                          │
│  Examples:                                              │
│  • "DB query failed: SELECT * FROM users WHERE..."      │
│  • "Redis connection timeout at 192.168.1.100:6379"     │
│  • Full stack traces with line numbers                  │
│  • Variable values and system state                     │
│                                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                                                          │
│  HTTPException (External - For API Consumers)           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    │
│  Audience: Your API users/clients                       │
│  Location: HTTP response                                │
│  Content:  User-friendly, safe messages                 │
│  Purpose:  Inform client what went wrong                │
│  Security: Public, must NOT include sensitive data      │
│                                                          │
│  Examples:                                              │
│  • "Service temporarily unavailable"                    │
│  • "Invalid email format"                               │
│  • "Resource not found"                                 │
│  • "Authentication required"                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Decision Tree: When to Use What

```
Exception occurred
       │
       ▼
Is it an HTTPException already?
       │
       ├─ YES → Just re-raise it
       │         raise
       │
       └─ NO → Continue...
              │
              ▼
       Is it a client error?
       (Bad input, validation, etc.)
              │
              ├─ YES → Log at WARNING level
              │         logger.warning("Invalid data: {e}")
              │         raise HTTPException(400, "Invalid data")
              │
              └─ NO → Continue...
                     │
                     ▼
              Is it expected?
              (Not found, already exists, etc.)
                     │
                     ├─ YES → Log at INFO level
                     │         logger.info("User not found: {id}")
                     │         raise HTTPException(404, "Not found")
                     │
                     └─ NO → Server/unexpected error
                            │
                            ▼
                     Log at ERROR level with trace
                     logger.error("Error: {e}", exc_info=True)
                     raise HTTPException(500, "Generic message")
```

## Real-World Example

### Scenario: Creating a Movie with Invalid Data

```python
# Request
POST /movies
{
  "title": "",  # Empty title (invalid!)
  "year": 2025
}

# What happens in code:
try:
    if not data.get("title"):
        logger.warning("Empty title provided")  # ← To log files
        raise HTTPException(
            status_code=400,
            detail="Title is required"  # ← To client
        )
```

**Log file shows:**
```
2025-11-18 14:30:15 | WARNING | app.routes.movies | create_movie:28 | Empty title provided
```

**Client receives:**
```json
HTTP 400 Bad Request
{
  "detail": "Title is required"
}
```

### Scenario: Database Connection Failure

```python
# What happens in code:
try:
    movie = await db.create_movie(data)
except ConnectionError as e:
    logger.error(f"DB failed: {e}", exc_info=True)  # ← Full details to logs
    raise HTTPException(
        status_code=503,
        detail="Service unavailable"  # ← Generic message to client
    )
```

**Log file shows:**
```
2025-11-18 14:30:15 | ERROR | app.routes.movies | create_movie:45 | DB failed: Connection timeout
Traceback (most recent call last):
  [... full stack trace with line numbers ...]
ConnectionError: Could not connect to postgresql://localhost:5432/movies
  Connection refused
  Attempted 3 retries
```

**Client receives:**
```json
HTTP 503 Service Unavailable
{
  "detail": "Service unavailable"
}
```

**Notice:** Client doesn't see the database connection string or retry details!

## Summary

**Always use BOTH:**

1. **`logger.error()`** → Records technical details for debugging
2. **`raise HTTPException()`** → Returns safe message to client

**Never expose:**
- Database connection strings
- File paths
- Stack traces
- Internal variable values
- System configuration

**Always include in logs:**
- Full error details
- Stack traces (`exc_info=True`)
- Contextual information
- Timestamps and module names

This gives you the best of both worlds: detailed debugging info + secure API responses! 🎯
