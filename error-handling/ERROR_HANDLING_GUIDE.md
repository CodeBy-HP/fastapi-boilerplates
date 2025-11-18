# Exception Handling Best Practices

## TL;DR

**Use BOTH logging AND HTTPException:**
- **Logger** = Records what happened (for developers)
- **HTTPException** = Tells client what went wrong (for API consumers)

## The Golden Rule

```python
try:
    # Your code
    pass
except SpecificException as e:
    logger.error(f"Detailed internal error: {e}", exc_info=True)  # For you
    raise HTTPException(status_code=500, detail="Safe message")   # For client
```

## Quick Comparison

| Aspect | Logger | HTTPException |
|--------|--------|---------------|
| **Purpose** | Debug & monitor | Inform client |
| **Audience** | Developers | API consumers |
| **Content** | Detailed, technical | User-friendly, safe |
| **Can include** | Stack traces, DB errors | Generic messages |
| **Security** | Private (log files) | Public (HTTP response) |

## Pattern 1: Client Errors (4xx)

**Use when:** User sent bad data

```python
from core.logger import get_logger
logger = get_logger("routes.users")

try:
    if age < 0:
        logger.warning(f"Invalid age provided: {age}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age must be positive"
        )
except HTTPException:
    raise  # Re-raise HTTPExceptions as-is
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="An error occurred"  # Generic!
    )
```

## Pattern 2: Server Errors (5xx)

**Use when:** Something broke on your side

```python
try:
    result = await database.query()
    logger.info("Query successful")
    return result
    
except ConnectionError as e:
    # Log FULL details for debugging
    logger.error(f"DB connection failed: {e}", exc_info=True)
    
    # Return GENERIC message to client
    raise HTTPException(
        status_code=503,
        detail="Service temporarily unavailable"
    )
```

## Pattern 3: Not Found (404)

**Use when:** Resource doesn't exist

```python
try:
    user = await get_user(user_id)
    if not user:
        logger.info(f"User {user_id} not found")  # INFO, not ERROR
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found"
        )
    return user
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Error retrieving user")
```

## Security: What NOT to Do

### ❌ BAD - Exposes Internal Errors

```python
try:
    result = 1 / 0
except Exception as e:
    # DON'T DO THIS!
    raise HTTPException(
        status_code=500,
        detail=f"Error: {str(e)}"  # Shows "division by zero"!
    )
```

**Problems:**
- Exposes internal implementation
- Could leak sensitive data
- Helps attackers understand your system
- Not user-friendly

### ✅ GOOD - Safe and Informative

```python
try:
    result = calculate_price(items)
except ZeroDivisionError as e:
    # Log detailed error internally
    logger.error(f"Price calculation failed: {e}", exc_info=True)
    
    # Return safe message to client
    raise HTTPException(
        status_code=500,
        detail="Unable to calculate price. Please try again."
    )
```

## When to Use Which Log Level

### `logger.debug()`
- Detailed diagnostic info
- Only in development (LOG_LEVEL=DEBUG)
- Example: "Query params: {params}"

### `logger.info()`
- Normal operations
- Success confirmations
- Example: "User 123 logged in"

### `logger.warning()`
- Expected errors (validation, business rules)
- Approaching limits
- Example: "Invalid email format: {email}"

### `logger.error()`
- Unexpected errors
- System failures
- **Always use `exc_info=True`** for stack trace
- Example: "Database connection failed"

### `logger.critical()`
- System-wide failures
- Requires immediate attention
- Example: "All database replicas down"

## Complete Example

```python
from fastapi import APIRouter, HTTPException, status
from core.logger import get_logger

logger = get_logger("routes.movies")
router = APIRouter()

@router.post("/movies")
async def create_movie(movie_data: dict):
    try:
        # Validation (client error)
        if not movie_data.get("title"):
            logger.warning("Movie creation attempted without title")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title is required"
            )
        
        # Business logic
        movie = await db.create_movie(movie_data)
        logger.info(f"Movie created: {movie.id}")
        return movie
        
    except HTTPException:
        # Re-raise client errors as-is
        raise
        
    except ConnectionError as e:
        # Infrastructure error
        logger.error(f"DB error creating movie: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create movie"
        )
```

## Benefits of This Approach

### For Developers (Logs)
✅ Full error details in log files  
✅ Stack traces for debugging  
✅ Context about what happened  
✅ Searchable history  

### For API Consumers (HTTPException)
✅ Appropriate HTTP status codes  
✅ User-friendly error messages  
✅ No sensitive data exposed  
✅ Actionable information  

### For Security
✅ Internal details stay internal  
✅ Attackers can't learn system internals  
✅ Compliant with security best practices  

## When You DON'T Need try/except

Simple endpoints that can't fail:

```python
@router.get("/health")
async def health_check():
    logger.debug("Health check")
    return {"status": "ok"}
```

Static data:

```python
@router.get("/")
async def root():
    return {"message": "Welcome"}
```

## Summary

| Scenario | Logger Level | HTTPException | Message Type |
|----------|--------------|---------------|--------------|
| Invalid input | `warning` | 400 | Specific |
| Not found | `info` | 404 | Specific |
| DB error | `error` | 503 | Generic |
| Unexpected | `error` | 500 | Generic |
| Success | `info` | - | - |

**Always remember:**
1. Log detailed errors internally (`logger.error()`)
2. Return safe messages to clients (`HTTPException`)
3. Never expose internal errors in HTTP responses
4. Use `exc_info=True` for full stack traces in logs

See `app/routes/error_handling_examples.py` for complete code examples!
