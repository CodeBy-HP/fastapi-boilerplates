# 🛡️ Try-Except Block Best Practices

Production-ready exception handling patterns for FastAPI applications. Write robust, maintainable error handling code.

## 🎯 What This Module Provides

A complete reference for handling exceptions correctly in FastAPI:

- ✅ When and how to use try-except blocks
- ✅ Production-ready patterns for different scenarios
- ✅ Common mistakes and how to avoid them
- ✅ Security best practices

## ⚡ The Golden Rules

1. **Don't catch HTTPException** - Let FastAPI handle them
2. **Never expose internal errors** to clients
3. **Always log unexpected errors** with context
4. **Be specific** with exception types
5. **Use custom exceptions** for business logic errors

---

## 🚀 Quick Start

### Basic Pattern

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    try:
        # Business logic here
        product = await Product.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    
    except HTTPException:
        # ✅ Re-raise HTTP exceptions - don't wrap them!
        raise
    
    except Exception as e:
        # ✅ Log internal errors, return generic message
        logger.error(f"Failed to get product {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 📚 Core Patterns

### Pattern 1: The Standard Try-Except Structure

**Use for:** Most FastAPI endpoints

```python
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        # 1. Input validation
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID required")
        
        # 2. Business logic
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 3. Return success
        return user
    
    except HTTPException:
        # Always re-raise - these are intentional
        raise
    
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Error fetching user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Key Points:**
- ✅ Specific business errors become HTTP exceptions
- ✅ HTTPException is re-raised immediately
- ✅ Unexpected errors are logged with full traceback
- ✅ Client sees generic error message (security!)

---

### Pattern 2: Nested Try-Except for Multiple Operations

**Use for:** Operations with multiple failure points

```python
@router.post("/orders")
async def create_order(order_data: OrderCreate):
    try:
        # Validate user
        try:
            user = await User.get(order_data.user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User lookup failed: {e}")
            raise HTTPException(status_code=500, detail="User validation failed")
        
        # Validate product
        try:
            product = await Product.get(order_data.product_id)
            if not product or not product.in_stock:
                raise HTTPException(status_code=400, detail="Product unavailable")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Product lookup failed: {e}")
            raise HTTPException(status_code=500, detail="Product validation failed")
        
        # Create order
        try:
            order = Order(**order_data.model_dump())
            await order.insert()
            return order
        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to create order")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in create_order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Benefits:**
- ✅ Each operation has specific error handling
- ✅ More informative logs
- ✅ Better debugging experience

---

### Pattern 3: Custom Exceptions for Business Logic

**Use for:** Reusable business logic across multiple endpoints

```python
# Define custom exceptions
class ProductNotFoundError(Exception):
    """Raised when product doesn't exist"""
    pass

class InsufficientStockError(Exception):
    """Raised when product is out of stock"""
    pass

class InvalidProductIDError(Exception):
    """Raised when product ID format is invalid"""
    pass

# Business logic function
async def get_product_or_fail(product_id: str) -> Product:
    """
    Get product or raise custom exception.
    Reusable across multiple endpoints.
    """
    try:
        object_id = PydanticObjectId(product_id)
    except Exception:
        raise InvalidProductIDError(f"Invalid product ID: {product_id}")
    
    product = await Product.get(object_id)
    if not product:
        raise ProductNotFoundError(f"Product {product_id} not found")
    
    return product

# Endpoint using custom exceptions
@router.get("/products/{product_id}")
async def get_product(product_id: str):
    try:
        product = await get_product_or_fail(product_id)
        return product
    
    except InvalidProductIDError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Benefits:**
- ✅ Reusable business logic
- ✅ Clear separation of concerns
- ✅ Type-safe exception handling
- ✅ Easier testing

---

### Pattern 4: Database Operations with Rollback

**Use for:** Operations requiring transactions

```python
@router.post("/transfer")
async def transfer_funds(transfer: TransferRequest):
    try:
        # Start transaction (pseudo-code, adjust for your DB)
        async with database.transaction():
            # Debit from account
            try:
                sender = await Account.get(transfer.from_account)
                if sender.balance < transfer.amount:
                    raise HTTPException(
                        status_code=400,
                        detail="Insufficient funds"
                    )
                sender.balance -= transfer.amount
                await sender.save()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to debit account: {e}")
                raise HTTPException(status_code=500, detail="Transfer failed")
            
            # Credit to account
            try:
                receiver = await Account.get(transfer.to_account)
                receiver.balance += transfer.amount
                await receiver.save()
            except Exception as e:
                logger.error(f"Failed to credit account: {e}")
                # Transaction will auto-rollback
                raise HTTPException(status_code=500, detail="Transfer failed")
        
        return {"status": "success", "transaction_id": "..."}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Transfer error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

### Pattern 5: External API Calls

**Use for:** Third-party API integrations

```python
import httpx
from httpx import TimeoutException, HTTPStatusError

@router.get("/weather/{city}")
async def get_weather(city: str):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"https://api.weather.com/v1/weather",
                    params={"city": city}
                )
                response.raise_for_status()
                return response.json()
            
            except TimeoutException:
                logger.warning(f"Weather API timeout for city: {city}")
                raise HTTPException(
                    status_code=504,
                    detail="Weather service temporarily unavailable"
                )
            
            except HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Weather data not found for {city}"
                    )
                logger.error(f"Weather API error: {e}")
                raise HTTPException(
                    status_code=502,
                    detail="Weather service error"
                )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error fetching weather: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Key Points:**
- ✅ Specific timeout handling
- ✅ Different status codes for different failures
- ✅ Appropriate HTTP status codes (502, 504)

---

### Pattern 6: File Operations

**Use for:** File uploads, processing

```python
from pathlib import Path
import aiofiles

@router.post("/upload")
async def upload_file(file: UploadFile):
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if file.size > 10_000_000:  # 10MB
            raise HTTPException(status_code=400, detail="File too large")
        
        # Save file
        file_path = Path(f"uploads/{file.filename}")
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        except PermissionError:
            logger.error(f"Permission denied writing to {file_path}")
            raise HTTPException(
                status_code=500,
                detail="File save failed - permission error"
            )
        except OSError as e:
            logger.error(f"OS error saving file: {e}")
            raise HTTPException(
                status_code=500,
                detail="File save failed"
            )
        
        return {"filename": file.filename, "size": file.size}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

### Pattern 7: Validation with Pydantic

**Use for:** Complex validation beyond Pydantic's built-in validators

```python
from pydantic import ValidationError

@router.post("/products")
async def create_product(data: dict):
    try:
        # Parse and validate
        try:
            product_data = ProductCreate(**data)
        except ValidationError as e:
            # ✅ Pydantic errors are user errors - return 400
            logger.info(f"Validation error: {e}")
            raise HTTPException(
                status_code=400,
                detail=e.errors()
            )
        
        # Additional business validation
        if product_data.price < product_data.cost:
            raise HTTPException(
                status_code=400,
                detail="Price cannot be less than cost"
            )
        
        # Create product
        product = Product(**product_data.model_dump())
        await product.insert()
        return product
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error creating product: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🚨 Common Mistakes & Anti-Patterns

### ❌ MISTAKE 1: Catching HTTPException

```python
# ❌ WRONG - Hides the real status code!
try:
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
except Exception as e:
    # This catches HTTPException too!
    raise HTTPException(status_code=500, detail="Error")
```

```python
# ✅ RIGHT - Re-raise HTTPException
try:
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
except HTTPException:
    raise  # Re-raise immediately
except Exception as e:
    raise HTTPException(status_code=500, detail="Error")
```

---

### ❌ MISTAKE 2: Exposing Internal Details

```python
# ❌ WRONG - Exposes database structure!
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Database error: {str(e)}"  # ❌ Security risk!
    )
```

```python
# ✅ RIGHT - Generic message, log details
except Exception as e:
    logger.error(f"Database error: {e}", exc_info=True)  # ✅ Log it
    raise HTTPException(
        status_code=500,
        detail="Internal server error"  # ✅ Generic message
    )
```

---

### ❌ MISTAKE 3: Bare Except Clause

```python
# ❌ WRONG - Catches everything, even system exits!
try:
    product = await Product.get(id)
except:  # ❌ Too broad!
    raise HTTPException(status_code=500, detail="Error")
```

```python
# ✅ RIGHT - Specific exception types
try:
    product = await Product.get(id)
except HTTPException:
    raise
except Exception as e:  # ✅ Specific enough
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Error")
```

---

### ❌ MISTAKE 4: Not Logging Errors

```python
# ❌ WRONG - Silent failure, hard to debug!
except Exception as e:
    raise HTTPException(status_code=500, detail="Error")
```

```python
# ✅ RIGHT - Log with context
except Exception as e:
    logger.error(
        f"Failed to process order {order_id}: {e}",
        exc_info=True,  # ✅ Include full traceback
        extra={"order_id": order_id, "user_id": user_id}
    )
    raise HTTPException(status_code=500, detail="Error")
```

---

### ❌ MISTAKE 5: Swallowing Exceptions

```python
# ❌ WRONG - Exception is lost!
try:
    await send_email(user.email)
except Exception:
    pass  # ❌ Email failure is invisible!
```

```python
# ✅ RIGHT - Log and handle appropriately
try:
    await send_email(user.email)
except Exception as e:
    # Log but don't fail the request if email is non-critical
    logger.warning(f"Failed to send email to {user.email}: {e}")
    # Continue processing...
```

---

## 🎯 Best Practices Checklist

When writing try-except blocks:

- [ ] **Always re-raise HTTPException** - Don't wrap them
- [ ] **Log unexpected errors** with `exc_info=True` for full traceback
- [ ] **Never expose internal details** in error messages to clients
- [ ] **Be specific** - Catch specific exception types when possible
- [ ] **Use custom exceptions** for business logic errors
- [ ] **Include context** in log messages (user_id, order_id, etc.)
- [ ] **Return appropriate HTTP status codes** (400, 404, 500, 502, 504)
- [ ] **Don't use bare except** - Always specify `except Exception as e`
- [ ] **Consider retries** for transient failures (network, database)
- [ ] **Clean up resources** - Use context managers or finally blocks

---

## 🔐 Security Best Practices

### 1. Never Leak Internal Information

```python
# ❌ WRONG
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ✅ RIGHT
except Exception as e:
    logger.error(f"Internal error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Sanitize User Input in Logs

```python
# ⚠️ Be careful logging user input
except Exception as e:
    # Don't log passwords, tokens, etc.
    safe_data = {k: v for k, v in data.items() if k not in ['password', 'token']}
    logger.error(f"Error processing {safe_data}: {e}")
```

### 3. Rate Limit Error Responses

```python
# Consider rate limiting to prevent error-based attacks
from slowapi import Limiter

@limiter.limit("5/minute")
@router.post("/login")
async def login(credentials: LoginRequest):
    try:
        # Login logic
        pass
    except InvalidCredentialsError:
        # Limited to 5 attempts per minute
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

---

## 📊 HTTP Status Code Guide

Use the right status code for each error type:

| Status Code | Use When | Example |
|-------------|----------|---------|
| **400** | Client error (bad request) | Invalid input, validation error |
| **401** | Authentication required | Missing or invalid token |
| **403** | Forbidden (authenticated but not authorized) | User lacks permission |
| **404** | Resource not found | Product, user doesn't exist |
| **409** | Conflict | Duplicate email, username taken |
| **422** | Unprocessable entity | Pydantic validation errors |
| **429** | Too many requests | Rate limit exceeded |
| **500** | Internal server error | Unexpected database error |
| **502** | Bad gateway | External API returned error |
| **503** | Service unavailable | Database down, maintenance |
| **504** | Gateway timeout | External API timeout |

---

## 📚 Further Reading

- **`example.py`** - Complete working examples
- **`QUICK_REFERENCE.md`** - Fast lookup cheat sheet
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)

---

## 🎓 Summary

**Key Takeaways:**

1. **Always re-raise HTTPException** - These are intentional errors
2. **Log internal errors with context** - Include IDs, user info
3. **Return generic error messages** - Never expose internals
4. **Use custom exceptions** - For reusable business logic
5. **Choose appropriate status codes** - 400s for client, 500s for server

**Remember:** Good exception handling makes your API robust, debuggable, and secure!
