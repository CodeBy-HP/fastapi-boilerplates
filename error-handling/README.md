# FastAPI Error Handling Boilerplate

A production-ready error handling pattern for FastAPI that separates internal debugging (logs) from external communication (HTTP responses).

## 🎯 Core Principle

**Use BOTH logging AND HTTPException:**
- **Logger** → Records detailed errors for developers (in log files)
- **HTTPException** → Returns safe messages to API consumers (in HTTP response)

```python
try:
    result = await risky_operation()
except Exception as e:
    logger.error(f"Details: {e}", exc_info=True)  # For YOU (logs)
    raise HTTPException(500, "Safe message")       # For CLIENT (HTTP)
```

---

## 📦 Quick Start

### 1. **Copy the Pattern File**
```bash
# Copy the error handling module to your project
cp error_handlers.py <your-project>/
```

### 2. **Import and Use**
```python
from logger import get_logger  # Use your logger
from fastapi import HTTPException, status

logger = get_logger("routes.users")

@router.post("/users")
async def create_user(data: dict):
    try:
        result = await db.create_user(data)
        logger.info(f"User created: {result.id}")
        return result
    except ValueError as e:
        logger.warning(f"Invalid data: {e}")
        raise HTTPException(400, "Invalid user data")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to create user")
```

---

## 📖 The Standard Pattern

### **Pattern Template** (Copy this!)

```python
from fastapi import APIRouter, HTTPException, status
from logger import get_logger

logger = get_logger("routes.MODULE_NAME")
router = APIRouter()

@router.post("/endpoint")
async def endpoint_function(data: dict):
    try:
        # Your business logic
        result = await do_something(data)
        logger.info(f"Success: {result}")
        return result
        
    except ValueError as e:
        # Client errors (400) - validation, bad input
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
        
    except HTTPException:
        # Already handled - re-raise as-is
        raise
        
    except Exception as e:
        # Server errors (500) - unexpected issues
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"
        )
```

---

## 🔍 Error Handling Patterns

### **1. Client Errors (4xx) - User's Fault**

**When:** Invalid input, validation failures, missing fields

```python
@router.post("/users")
async def create_user(email: str, age: int):
    try:
        # Validate
        if "@" not in email:
            logger.warning(f"Invalid email: {email}")
            raise HTTPException(400, "Invalid email format")
        
        if age < 0:
            logger.warning(f"Invalid age: {age}")
            raise HTTPException(400, "Age must be positive")
        
        # Process
        user = await db.create_user(email, age)
        logger.info(f"User created: {user.id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to create user")
```

**Log Level:** `warning` (expected issue)  
**Status Code:** `400` Bad Request

---

### **2. Resource Not Found (404)**

**When:** Requested resource doesn't exist

```python
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        user = await db.get_user(user_id)
        
        if not user:
            logger.info(f"User not found: {user_id}")
            raise HTTPException(404, f"User {user_id} not found")
        
        logger.info(f"User retrieved: {user_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve user")
```

**Log Level:** `info` (expected behavior, not an error)  
**Status Code:** `404` Not Found

---

### **3. Server Errors (5xx) - Your Fault**

**When:** Database failures, external API errors, system issues

```python
@router.get("/products/{product_id}")
async def get_product(product_id: int):
    try:
        product = await db.get_product(product_id)
        logger.info(f"Product retrieved: {product_id}")
        return product
        
    except ConnectionError as e:
        # Log FULL details for debugging
        logger.error(f"Database connection failed: {e}", exc_info=True)
        
        # Return GENERIC message to client
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve product")
```

**Log Level:** `error` with `exc_info=True` (full stack trace)  
**Status Code:** `500` Internal Server Error or `503` Service Unavailable

---

### **4. External Service Failures**

**When:** Third-party API calls fail

```python
@router.post("/payments")
async def process_payment(amount: float):
    try:
        # Call payment gateway
        result = await payment_gateway.charge(amount)
        logger.info(f"Payment successful: ${amount}")
        return {"status": "success"}
        
    except PaymentGatewayError as e:
        # Log details (but NOT card numbers!)
        logger.error(f"Payment gateway error: {e}", exc_info=True)
        
        # Generic message to client
        raise HTTPException(
            status_code=502,
            detail="Payment processor unavailable"
        )
        
    except Exception as e:
        logger.error(f"Payment error: {e}", exc_info=True)
        raise HTTPException(500, "Payment processing failed")
```

**Log Level:** `error` with full context  
**Status Code:** `502` Bad Gateway or `503` Service Unavailable

---

## 🔒 Security: What NOT to Do

### ❌ **DANGEROUS - Exposes Internal Errors**

```python
try:
    result = await database.query()
except Exception as e:
    # DON'T DO THIS!
    raise HTTPException(
        status_code=500,
        detail=f"Error: {str(e)}"  # ← SECURITY RISK!
    )
```

**Client sees:**
```json
{
  "detail": "Error: Connection refused for postgresql://admin:password123@db.internal.com:5432/production_db timeout after 30s"
}
```

**Problems:**
- 🔴 Exposes database server location
- 🔴 Reveals database credentials
- 🔴 Shows internal architecture
- 🔴 Helps attackers understand your system
- 🔴 No logs for debugging

---

### ✅ **SECURE - Separates Internal/External**

```python
try:
    result = await database.query()
except Exception as e:
    # Log FULL details internally
    logger.error(f"Database error: {e}", exc_info=True)
    
    # Return SAFE message to client
    raise HTTPException(
        status_code=503,
        detail="Service temporarily unavailable"
    )
```

**Client sees:**
```json
{
  "detail": "Service temporarily unavailable"
}
```

**Logs contain (private):**
```
2025-11-18 14:30:15 | ERROR | app.routes | get_data:42 | Database error: Connection refused
Traceback (most recent call last):
  File "routes.py", line 40, in get_data
    result = await database.query()
ConnectionError: Connection refused for postgresql://admin:password123@db.internal.com:5432/production_db
```

**Benefits:**
- ✅ Client gets helpful, safe message
- ✅ You get full debugging details in logs
- ✅ No sensitive data exposed
- ✅ Security maintained

---

## 📊 When to Use Which Log Level

| Level | When to Use | Example | HTTP Status |
|-------|-------------|---------|-------------|
| `debug()` | Development only | `"Query params: {params}"` | - |
| `info()` | Success, normal flow | `"User logged in: {id}"` | 200, 404 |
| `warning()` | Expected errors | `"Invalid email: {email}"` | 400 |
| `error()` | Unexpected errors | `"DB failed: {e}"` + `exc_info=True` | 500, 503 |
| `critical()` | System failures | `"All DB replicas down"` | 500, 503 |

---

## 📝 Complete Examples

### **Example 1: CRUD Endpoint**

```python
from fastapi import APIRouter, HTTPException, status
from logger import get_logger

logger = get_logger("routes.movies")
router = APIRouter()

@router.post("/movies")
async def create_movie(movie_data: dict):
    try:
        # Validation
        if not movie_data.get("title"):
            logger.warning("Movie creation attempted without title")
            raise HTTPException(400, "Title is required")
        
        # Business logic
        movie = await db.create_movie(movie_data)
        logger.info(f"Movie created: {movie.id}")
        return movie
        
    except HTTPException:
        raise
        
    except ConnectionError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(503, "Service temporarily unavailable")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to create movie")
```

---

### **Example 2: Multiple Validation Rules**

```python
@router.post("/register")
async def register_user(email: str, password: str, age: int):
    try:
        # Multiple validations
        errors = []
        
        if "@" not in email:
            errors.append("Invalid email format")
        
        if len(password) < 8:
            errors.append("Password must be 8+ characters")
        
        if age < 18:
            errors.append("Must be 18 or older")
        
        if errors:
            logger.warning(f"Validation failed: {errors}")
            raise HTTPException(400, {"errors": errors})
        
        # Create user
        user = await db.create_user(email, password, age)
        logger.info(f"User registered: {user.id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(500, "Registration failed")
```

---

### **Example 3: External API Integration**

```python
@router.get("/weather/{city}")
async def get_weather(city: str):
    try:
        # Call external weather API
        response = await weather_api.get(city)
        
        if response.status == 404:
            logger.info(f"City not found: {city}")
            raise HTTPException(404, f"City '{city}' not found")
        
        logger.info(f"Weather fetched for: {city}")
        return response.json()
        
    except HTTPException:
        raise
        
    except TimeoutError as e:
        logger.error(f"Weather API timeout: {e}", exc_info=True)
        raise HTTPException(504, "Weather service timeout")
        
    except Exception as e:
        logger.error(f"Weather API error: {e}", exc_info=True)
        raise HTTPException(503, "Weather service unavailable")
```

---

## 🎓 Best Practices Summary

### ✅ **Do This**

```python
# 1. Log detailed errors internally
logger.error(f"Database failed: {e}", exc_info=True)

# 2. Return generic messages to clients
raise HTTPException(500, "Service error")

# 3. Use specific exception types
except ValueError as e:  # Not just Exception

# 4. Use appropriate status codes
raise HTTPException(400, ...)  # Client error
raise HTTPException(500, ...)  # Server error

# 5. Add context to logs
logger.info(f"Processing order {order_id}")
```

### ❌ **Don't Do This**

```python
# 1. Don't expose internal errors
raise HTTPException(500, f"Error: {str(e)}")

# 2. Don't use wrong status codes
raise HTTPException(500, "Invalid input")  # Should be 400

# 3. Don't skip logging
raise HTTPException(500, "Error")  # No log!

# 4. Don't log sensitive data
logger.info(f"Password: {password}")  # Security risk

# 5. Don't use bare except
except:  # Too broad, use specific exceptions
```

---

## 📁 File Structure

```
error-handling/
├── error_handlers.py       # Error handling utilities (optional)
├── example_integration.py  # Complete working examples
└── README.md              # This file
```

---

## 🚀 Integration Checklist

- [ ] Copy error handling patterns to your routes
- [ ] Import logger: `from logger import get_logger`
- [ ] Set up logger for each module: `logger = get_logger("routes.MODULE")`
- [ ] Wrap route logic in try/except
- [ ] Log errors with `exc_info=True` for stack traces
- [ ] Return safe HTTPException messages to clients
- [ ] Use appropriate HTTP status codes (400, 404, 500, 503)
- [ ] Test error scenarios to verify logging works

---

## 🔄 Migration Guide

**From:**
```python
except Exception as e:
    raise HTTPException(500, f"Error: {str(e)}")
```

**To:**
```python
except ValueError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(400, "Invalid data")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(500, "An error occurred")
```

---

## 💡 Key Takeaways

1. **Always use BOTH** logger and HTTPException
2. **Log everything** with full details (`exc_info=True`)
3. **Never expose** internal errors to clients
4. **Use specific** exception types (ValueError, ConnectionError, etc.)
5. **Choose correct** HTTP status codes (400, 404, 500, 503)
6. **Keep messages** generic for clients, detailed for logs

---

## 📚 Additional Resources

- See `example_integration.py` for complete working examples
- Check your `logs/app_error.log` for error tracking
- Review FastAPI docs: https://fastapi.tiangolo.com/tutorial/handling-errors/

---

**Happy Error Handling! 🎉**
