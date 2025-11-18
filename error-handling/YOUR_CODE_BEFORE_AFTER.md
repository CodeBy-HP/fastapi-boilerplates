# Your Code: Before vs After

## Your Original Code ❌

```python
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to create movie: {str(e)}",  # ← PROBLEM!
    )
```

### Problems with This:

1. **Security Risk** - Exposes internal error messages to clients
2. **No Logging** - You have no record of what went wrong
3. **Information Leakage** - Could expose database details, file paths, etc.
4. **Poor User Experience** - Technical errors aren't user-friendly

### What Could Be Exposed:

```python
# If database fails:
detail="Failed to create movie: Connection refused for postgresql://admin:password@localhost:5432/movies"

# If file system fails:
detail="Failed to create movie: Permission denied: /var/www/app/uploads/movies/..."

# If validation fails:
detail="Failed to create movie: invalid literal for int() with base 10: 'abc'"
```

**Attackers love this!** They learn about your system architecture.

---

## Recommended Code ✅

```python
from core.logger import get_logger

logger = get_logger("routes.movies")

@router.post("/movies")
async def create_movie(movie_data: dict):
    try:
        # Your business logic
        result = await db.create_movie(movie_data)
        logger.info(f"Movie created successfully: {result.id}")
        return result
        
    except ValueError as e:
        # Client errors (bad input)
        logger.warning(f"Invalid movie data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie data provided"  # Generic, safe
        )
        
    except Exception as e:
        # Server errors (unexpected)
        logger.error(f"Failed to create movie: {e}", exc_info=True)  # ← Full details in logs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the movie"  # ← Safe message to client
        )
```

### Benefits:

1. ✅ **Secure** - Internal details stay in logs, not in HTTP responses
2. ✅ **Debuggable** - Full error details logged with stack trace
3. ✅ **User-Friendly** - Clear, generic messages to clients
4. ✅ **Professional** - Follows industry best practices

---

## Side-by-Side Comparison

### Scenario: Database Connection Fails

#### Your Original Approach ❌

**Code:**
```python
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Failed to create movie: {str(e)}"
    )
```

**What Client Sees:**
```json
{
  "detail": "Failed to create movie: Connection refused for postgresql://myuser:secretpass@db.internal:5432/movies_db timeout after 30s"
}
```

**Problems:**
- 🔴 Database server exposed: `db.internal:5432`
- 🔴 Database name exposed: `movies_db`
- 🔴 Username exposed: `myuser`
- 🔴 System configuration exposed: `timeout after 30s`
- 🔴 You have no logs to debug this later

---

#### Recommended Approach ✅

**Code:**
```python
except Exception as e:
    logger.error(f"Database error creating movie: {e}", exc_info=True)
    raise HTTPException(
        status_code=503,
        detail="Service temporarily unavailable. Please try again later."
    )
```

**What Client Sees:**
```json
{
  "detail": "Service temporarily unavailable. Please try again later."
}
```

**What You See in Logs (logs/app.log):**
```
2025-11-18 14:30:15 | ERROR | app.routes.movies | create_movie:45 | Database error creating movie: Connection refused
Traceback (most recent call last):
  File "/app/routes/movies.py", line 42, in create_movie
    result = await db.create_movie(movie_data)
  File "/app/database.py", line 156, in create_movie
    conn = await self.pool.acquire()
asyncpg.exceptions.ConnectionDoesNotExistError: Connection refused for postgresql://myuser:secretpass@db.internal:5432/movies_db timeout after 30s
```

**Benefits:**
- ✅ Client gets user-friendly message
- ✅ You get full details in logs for debugging
- ✅ No sensitive data exposed to client
- ✅ You can debug the issue later

---

## Different Error Types

### 1. Validation Error (Client's Fault)

#### ❌ Your Way
```python
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Failed to create movie: {str(e)}"
    )
# Client sees: "Failed to create movie: Title must be at least 3 characters"
# Problem: Wrong status code (should be 400, not 500)
```

#### ✅ Better Way
```python
except ValueError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(
        status_code=400,
        detail="Invalid movie data: title must be at least 3 characters"
    )
# Client sees proper 400 error with clear message
# You have logs showing what happened
```

---

### 2. Resource Not Found

#### ❌ Your Way
```python
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Failed to create movie: {str(e)}"
    )
# Client sees: "Failed to create movie: Genre with ID 999 not found in table genres"
# Problem: Exposes table name, wrong status code
```

#### ✅ Better Way
```python
except ValueError as e:
    logger.info(f"Genre not found: {e}")  # INFO level (not really an error)
    raise HTTPException(
        status_code=404,
        detail="Genre not found"
    )
# Client sees proper 404 with clean message
# No table names exposed
```

---

### 3. External API Failure

#### ❌ Your Way
```python
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Failed to create movie: {str(e)}"
    )
# Client sees: "Failed to create movie: API key invalid for https://api.themoviedb.org/3/movie?api_key=abc123xyz"
# Problem: Exposes API endpoint and key!
```

#### ✅ Better Way
```python
except ConnectionError as e:
    logger.error(f"TMDB API failed: {e}", exc_info=True)
    raise HTTPException(
        status_code=503,
        detail="Movie database temporarily unavailable"
    )
# Client sees generic message
# You have full details in logs
# API key not exposed
```

---

## Quick Reference

| Your Current Code | Problem | Recommended Code |
|------------------|---------|------------------|
| `detail=f"Error: {str(e)}"` | Exposes internals | `detail="Service error"` + `logger.error()` |
| Always 500 status | Wrong codes | Use 400 (client), 404 (not found), 503 (unavailable), etc. |
| No logging | Can't debug | `logger.error(exc_info=True)` |
| One catch-all | No granularity | Catch specific exceptions |

---

## The Template to Use

**Copy and paste this template for all your routes:**

```python
from fastapi import APIRouter, HTTPException, status
from core.logger import get_logger

logger = get_logger("routes.MODULE_NAME")  # Change MODULE_NAME
router = APIRouter()

@router.post("/your-endpoint")
async def your_function(data: dict):
    try:
        # Your business logic here
        result = await do_something(data)
        logger.info(f"Success: {result.id}")
        return result
        
    except ValueError as e:
        # Client errors - bad input
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"  # Generic
        )
        
    except HTTPException:
        # Already an HTTPException - just re-raise
        raise
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"  # Generic
        )
```

---

## Answer to Your Question

> "should i use them or are they excessive and instead use logger"

**Answer: Use BOTH!**

- **Don't** just raise HTTPException with `str(e)` - that's a security risk
- **Don't** just log without raising HTTPException - client won't know what happened
- **Do** log detailed errors AND raise HTTPException with safe messages
- **Do** use different exception types for different status codes

Think of it this way:
- `logger` = Your debugging tool (private)
- `HTTPException` = Your communication with client (public)

You need both! 🎯

---

See `ERROR_HANDLING_GUIDE.md` for more examples!
