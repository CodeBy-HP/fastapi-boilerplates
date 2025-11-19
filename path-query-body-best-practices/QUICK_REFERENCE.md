# 🚀 Path, Query & Body Parameters - Quick Reference

Fast lookup for common parameter patterns in FastAPI.

---

## 📋 Quick Decision Tree

```
Need to identify a SPECIFIC resource? → PATH parameter
    Example: /users/{user_id}, /orders/{order_id}

Need to FILTER/SORT/PAGINATE results? → QUERY parameter
    Example: /users?page=1&role=admin&sort=name

Need to SEND DATA to create/update? → BODY parameter
    Example: POST/PUT/PATCH with JSON payload
```

---

## 🎯 PATH Parameters

### Basic Template
```python
@router.get("/items/{item_id}")
async def get_item(
    item_id: str = Path(..., description="Item identifier")
):
    return {"item_id": item_id}
```

### With Validation
```python
from fastapi import Path

# String validation
product_id: str = Path(
    ...,
    min_length=3,
    max_length=50,
    regex="^PROD-[0-9]{6}$",
    description="Product ID (format: PROD-123456)"
)

# Number validation
user_id: int = Path(..., ge=1, le=999999, description="User ID (1-999999)")

# Multiple paths
@router.get("/users/{user_id}/posts/{post_id}")
async def get_post(
    user_id: int = Path(..., ge=1),
    post_id: int = Path(..., ge=1)
):
    ...
```

### Common Validations
| Validation | Usage | Example |
|------------|-------|---------|
| `min_length` | Minimum string length | `min_length=3` |
| `max_length` | Maximum string length | `max_length=50` |
| `regex` | Pattern matching | `regex="^[A-Z]{3}-[0-9]{6}$"` |
| `ge` | Greater than or equal | `ge=1` |
| `le` | Less than or equal | `le=1000` |
| `gt` | Greater than | `gt=0` |
| `lt` | Less than | `lt=100` |

---

## 🔍 QUERY Parameters

### Basic Template
```python
from fastapi import Query
from typing import Optional

@router.get("/items")
async def list_items(
    page: int = Query(1, ge=1),                    # Default: 1
    limit: int = Query(20, ge=1, le=100),          # Default: 20
    search: Optional[str] = Query(None)            # Optional
):
    return {"page": page, "limit": limit, "search": search}
```

### Common Patterns

#### Pagination
```python
page: int = Query(1, ge=1, description="Page number")
limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
```

#### Optional Filters
```python
category: Optional[str] = Query(None, max_length=100)
min_price: Optional[float] = Query(None, ge=0)
max_price: Optional[float] = Query(None, ge=0)
in_stock: Optional[bool] = Query(None)
```

#### Required Query (rare but possible)
```python
api_key: str = Query(..., min_length=32, max_length=32)
```

#### Lists/Arrays
```python
tags: List[str] = Query([], description="Filter by tags")
# Usage: /items?tags=new&tags=sale&tags=featured
```

#### Enums (Fixed Choices)
```python
from enum import Enum

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

sort: SortOrder = Query(SortOrder.desc, description="Sort order")
# Only accepts "asc" or "desc"
```

#### Dates/Strings with Pattern
```python
start_date: str = Query(
    ...,
    regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
    description="Date (YYYY-MM-DD)"
)
```

---

## 📦 BODY Parameters

### Pydantic Model (RECOMMENDED)
```python
from pydantic import BaseModel, Field, EmailStr

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    stock: int = Field(..., ge=0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Gaming Laptop",
                "price": 1299.99,
                "description": "High-performance laptop",
                "category": "Electronics",
                "stock": 50
            }
        }
    }

@router.post("/products")
async def create_product(product: ProductCreate):
    return {"id": "PROD-123", **product.model_dump()}
```

### Explicit Body Parameters (Simple Cases)
```python
from fastapi import Body

@router.post("/login")
async def login(
    username: str = Body(..., min_length=3),
    password: str = Body(..., min_length=8),
    remember_me: bool = Body(False)
):
    return {"username": username}
```

### Single Value with embed=True
```python
@router.post("/items/{item_id}/quantity")
async def update_quantity(
    item_id: str = Path(...),
    quantity: int = Body(..., embed=True, ge=1)
):
    # Body: {"quantity": 10}
    return {"item_id": item_id, "quantity": quantity}
```

### Partial Update Schema (for PATCH)
```python
class ProductUpdate(BaseModel):
    """All fields optional for partial updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    
@router.patch("/products/{product_id}")
async def partial_update(
    product_id: str = Path(...),
    product: ProductUpdate = Body(...)
):
    # Only update fields that were provided
    update_data = product.model_dump(exclude_none=True)
    return {"updated_fields": list(update_data.keys())}
```

---

## 🔗 Combining All Three

### Template
```python
@router.put("/resources/{resource_id}")
async def update_resource(
    # PATH - Which resource
    resource_id: str = Path(..., regex="^RES-[0-9]{6}$"),
    
    # BODY - What to update
    resource: ResourceUpdate = Body(...),
    
    # QUERY - Options/metadata
    notify: bool = Query(False),
    reason: Optional[str] = Query(None, max_length=200)
):
    return {
        "resource_id": resource_id,
        "updated": resource.model_dump(exclude_none=True),
        "notify": notify,
        "reason": reason
    }
```

### Common Use Cases
```python
# Create with options
POST /users?send_welcome_email=true
Body: {"email": "...", "name": "..."}

# Update specific resource with metadata
PUT /products/{product_id}?audit_reason=Price%20correction
Body: {"price": 999.99}

# Filter and paginate
GET /products?category=electronics&page=1&limit=20

# Nested resources
GET /users/{user_id}/posts/{post_id}
```

---

## 🛡️ Security Quick Checklist

```python
✅ String lengths
min_length=1, max_length=200  # Prevent empty and huge strings

✅ Numeric ranges
ge=0, le=1000  # Prevent negative or unreasonable numbers

✅ List sizes
tags: List[str] = Query([], max_items=10)  # Prevent DoS

✅ Regex patterns
regex="^[a-zA-Z0-9_-]+$"  # Prevent injection

✅ Enums for fixed choices
status: Status = Query(Status.active)  # Only allow predefined values

✅ Field validations
email: EmailStr  # Built-in email validation
```

---

## 📝 Common Field Validations

### Pydantic Field Constraints
```python
from pydantic import Field, EmailStr, HttpUrl

# Strings
name: str = Field(..., min_length=1, max_length=100)
username: str = Field(..., pattern="^[a-zA-Z0-9_]+$")

# Numbers
price: float = Field(..., gt=0, le=1000000)
quantity: int = Field(..., ge=0)
discount: float = Field(..., ge=0, le=100)  # 0-100%

# Email
email: EmailStr  # Validates email format

# URL
website: HttpUrl  # Validates URL format

# Optional with constraints
description: Optional[str] = Field(None, max_length=1000)
```

### Custom Validators
```python
from pydantic import BaseModel, validator

class Product(BaseModel):
    name: str
    price: float
    discount_price: Optional[float] = None
    
    @validator('discount_price')
    def discount_must_be_less_than_price(cls, v, values):
        if v is not None and 'price' in values and v >= values['price']:
            raise ValueError('Discount price must be less than regular price')
        return v
```

---

## 🎨 Complete CRUD Example

```python
# CREATE
@router.post("/products")
async def create(product: ProductCreate):
    """Body only"""
    return {"id": "PROD-123", **product.model_dump()}

# READ (single)
@router.get("/products/{product_id}")
async def get(product_id: str = Path(...)):
    """Path only"""
    return {"id": product_id, "name": "Product Name"}

# READ (list with filters)
@router.get("/products")
async def list_all(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None)
):
    """Query only"""
    return {"page": page, "limit": limit, "items": []}

# UPDATE (full)
@router.put("/products/{product_id}")
async def update(
    product_id: str = Path(...),
    product: ProductCreate = Body(...)
):
    """Path + Body"""
    return {"id": product_id, **product.model_dump()}

# UPDATE (partial)
@router.patch("/products/{product_id}")
async def partial_update(
    product_id: str = Path(...),
    product: ProductUpdate = Body(...)
):
    """Path + Body (optional fields)"""
    updates = product.model_dump(exclude_none=True)
    return {"id": product_id, "updated": updates}

# DELETE
@router.delete("/products/{product_id}")
async def delete(
    product_id: str = Path(...),
    soft_delete: bool = Query(True)
):
    """Path + Query"""
    return {"id": product_id, "soft_deleted": soft_delete}
```

---

## 💡 Pro Tips

### 1. Default Values Strategy
```python
# Good: Sensible defaults
page: int = Query(1, ge=1)
limit: int = Query(20, ge=1, le=100)

# Good: Explicitly optional
search: Optional[str] = Query(None)

# Bad: Required query params (usually)
required_query: str = Query(...)  # ❌ Use path or body instead
```

### 2. Validation Order
```python
# FastAPI validates in this order:
# 1. Path parameters (from URL)
# 2. Query parameters (from URL)
# 3. Body parameters (from request body)
# 4. Pydantic model validation
# 5. Custom validators
```

### 3. Error Responses
```python
# Invalid path: 404 Not Found
# Invalid query: 422 Unprocessable Entity
# Invalid body: 422 Unprocessable Entity
# Missing required: 422 Unprocessable Entity
```

### 4. Documentation
```python
# Always add descriptions for auto-generated docs
product_id: str = Path(..., description="Unique product identifier")

# Add examples in Pydantic models
model_config = {
    "json_schema_extra": {
        "example": {"name": "Product", "price": 99.99}
    }
}
```

---

## 🔄 Migration Cheatsheet

### From Query to Path
```python
# Before: GET /products?id=123
@router.get("/products")
async def get(id: str = Query(...)):
    ...

# After: GET /products/123
@router.get("/products/{product_id}")
async def get(product_id: str = Path(...)):
    ...
```

### From Body to Query (for filters)
```python
# Before: POST /products/search with body
@router.post("/products/search")
async def search(filters: FilterModel):
    ...

# After: GET /products?category=x&min_price=y
@router.get("/products")
async def list_products(
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None)
):
    ...
```

---

## 📚 Resources

- **Full Examples**: See `example.py` in this directory
- **Detailed Guide**: See `README.md` for in-depth explanations
- **FastAPI Docs**: https://fastapi.tiangolo.com/tutorial/query-params/
- **Pydantic Validation**: https://docs.pydantic.dev/latest/usage/validators/

---

**Quick Summary**: 
- **PATH** = Resource ID (required, in URL)
- **QUERY** = Filters/options (usually optional, after ?)
- **BODY** = Data payload (POST/PUT/PATCH)
