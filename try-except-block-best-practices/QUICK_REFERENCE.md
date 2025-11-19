# 🎯 Quick Reference: Try-Except Cheat Sheet

> **Fast lookup guide** - Bookmark this for quick reminders!

## ⚡ The Golden Rules

1. **ALWAYS re-raise HTTPException** - Don't wrap them
2. **NEVER expose internal errors** to clients
3. **ALWAYS log unexpected errors** with context
4. **BE specific** with exception types
5. **USE custom exceptions** for business logic

---

## 📋 Standard Pattern

```python
@app.get("/items/{id}")
async def get_item(id: str):
    try:
        # Business logic
        if not id:
            raise HTTPException(status_code=400, detail="ID required")
        
        item = await Item.get(id)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        
        return item
    
    except HTTPException:
        raise  # ✅ Always re-raise!
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)  # ✅ Log it
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🔄 Common Patterns

### Pattern 1: Simple Endpoint
```python
try:
    # Validate
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid input")
    
    # Query
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    
    return user

except HTTPException:
    raise

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Pattern 2: Nested Operations
```python
try:
    # First operation
    try:
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User lookup failed: {e}")
        raise HTTPException(status_code=500, detail="User validation failed")
    
    # Second operation
    try:
        order = await Order.create(user_id=user.id)
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(status_code=500, detail="Order failed")

except HTTPException:
    raise

except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Pattern 3: Custom Exceptions
```python
# Define custom exceptions
class ProductNotFoundError(Exception):
    pass

class InvalidProductIDError(Exception):
    pass

# Business logic
async def get_product_or_fail(product_id: str):
    if not product_id:
        raise InvalidProductIDError(f"Invalid ID: {product_id}")
    
    product = await Product.get(product_id)
    if not product:
        raise ProductNotFoundError(f"Product {product_id} not found")
    
    return product

# Endpoint
@app.get("/products/{id}")
async def get_product(id: str):
    try:
        product = await get_product_or_fail(id)
        return product
    
    except InvalidProductIDError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Pattern 4: External API
```python
try:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(api_url)
            response.raise_for_status()
            return response.json()
        
        except httpx.TimeoutException:
            logger.warning("API timeout")
            raise HTTPException(status_code=504, detail="Service timeout")
        
        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e}")
            raise HTTPException(status_code=502, detail="External service error")

except HTTPException:
    raise

except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Pattern 5: File Operations
```python
try:
    # Validate
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file")
    
    # Save
    try:
        with open(path, 'wb') as f:
            f.write(content)
    except PermissionError:
        logger.error("Permission denied")
        raise HTTPException(status_code=500, detail="Save failed")
    except OSError as e:
        logger.error(f"OS error: {e}")
        raise HTTPException(status_code=500, detail="Save failed")
    
    return {"filename": file.filename}

except HTTPException:
    raise

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Pattern 6: Validation
```python
try:
    try:
        data = ProductCreate(**raw_data)
    except ValidationError as e:
        logger.info(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=400, detail=e.errors())
    
    # Business validation
    if data.price < data.cost:
        raise HTTPException(status_code=400, detail="Invalid price")
    
    product = Product(**data.model_dump())
    await product.insert()
    return product

except HTTPException:
    raise

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🚨 Common Mistakes

### ❌ MISTAKE 1: Catching HTTPException
```python
# ❌ WRONG
try:
    raise HTTPException(status_code=404, detail="Not found")
except Exception as e:  # Catches HTTPException too!
    raise HTTPException(status_code=500, detail="Error")
```

```python
# ✅ RIGHT
try:
    raise HTTPException(status_code=404, detail="Not found")
except HTTPException:
    raise  # Re-raise immediately
except Exception as e:
    raise HTTPException(status_code=500, detail="Error")
```

### ❌ MISTAKE 2: Exposing Details
```python
# ❌ WRONG - Security risk!
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

```python
# ✅ RIGHT
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # Log it
    raise HTTPException(status_code=500, detail="Internal server error")
```

### ❌ MISTAKE 3: Bare Except
```python
# ❌ WRONG - Too broad!
except:
    raise HTTPException(status_code=500, detail="Error")
```

```python
# ✅ RIGHT
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Error")
```

### ❌ MISTAKE 4: Not Logging
```python
# ❌ WRONG - Silent failure!
except Exception:
    raise HTTPException(status_code=500, detail="Error")
```

```python
# ✅ RIGHT
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # Full traceback
    raise HTTPException(status_code=500, detail="Error")
```

### ❌ MISTAKE 5: Swallowing Exceptions
```python
# ❌ WRONG - Lost exception!
try:
    await send_email()
except Exception:
    pass  # Gone forever!
```

```python
# ✅ RIGHT
try:
    await send_email()
except Exception as e:
    logger.warning(f"Email failed: {e}")
    # Continue if non-critical
```

---

## 📊 HTTP Status Codes

| Code | Use When | Example |
|------|----------|---------|
| **400** | Bad request (client error) | Invalid input, validation |
| **401** | Authentication required | No/invalid token |
| **403** | Forbidden | No permission |
| **404** | Not found | Resource doesn't exist |
| **409** | Conflict | Duplicate entry |
| **422** | Validation error | Pydantic errors |
| **429** | Rate limit | Too many requests |
| **500** | Internal error | Unexpected DB error |
| **502** | Bad gateway | External API error |
| **503** | Unavailable | DB down |
| **504** | Timeout | External API timeout |

---

## ✅ Checklist

When writing try-except:

- [ ] Re-raise HTTPException immediately
- [ ] Log errors with `exc_info=True`
- [ ] Return generic message to client
- [ ] Use specific exception types
- [ ] Include context in logs (IDs, etc.)
- [ ] Use appropriate status codes
- [ ] Don't use bare except
- [ ] Never expose internal details

---

## 🎯 Quick Decision Tree

```
Is it an expected error (user input, not found)?
├─ YES: Raise HTTPException directly
│  └─ Let outer except HTTPException re-raise it
└─ NO: Is it an unexpected error?
   └─ YES: Catch in except Exception
      ├─ Log with exc_info=True
      └─ Raise HTTPException(500) with generic message
```

---

## 📚 See Also

- **`README.md`** - Full guide with examples
- **`example.py`** - Complete working code
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)

---

**Remember:** Re-raise HTTPException, log internals, mask errors from clients!
