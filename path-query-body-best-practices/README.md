# 🎯 Path, Query & Body Parameters Best Practices

Production-ready patterns for handling URL parameters, query strings, and request bodies in FastAPI.

## 🚀 What This Module Provides

A complete reference for using FastAPI's parameter handling:

- ✅ When to use Path, Query, and Body
- ✅ Validation and constraints
- ✅ Production-ready patterns
- ✅ Common mistakes and solutions
- ✅ Security best practices

## ⚡ Quick Overview

| Parameter Type | Location | Example | Use Case |
|---------------|----------|---------|----------|
| **Path** | URL path | `/users/{user_id}` | Resource identifiers |
| **Query** | After `?` | `/users?page=1&limit=20` | Filters, pagination, sorting |
| **Body** | Request body | JSON payload | Create/update data |

---

## 🎯 Path Parameters

**Location:** Inside the URL path  
**Use for:** Resource identifiers, required values  
**Always required:** Yes

### Basic Usage

```python
from fastapi import Path

@app.get("/users/{user_id}")
async def get_user(
    user_id: str = Path(..., description="User ID")
):
    """Path parameter - part of the URL itself"""
    return {"user_id": user_id}
```

### With Validation

```python
@app.get("/products/{product_id}")
async def get_product(
    product_id: str = Path(
        ...,
        min_length=3,
        max_length=50,
        description="Product ID",
        example="PROD-12345"
    )
):
    return {"product_id": product_id}
```

### Numeric Constraints

```python
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(
        ...,
        ge=1,  # Greater than or equal to 1
        le=1000000,  # Less than or equal to 1M
        description="Item ID must be between 1 and 1,000,000"
    )
):
    return {"item_id": item_id}
```

### Regex Pattern Validation

```python
@app.get("/orders/{order_id}")
async def get_order(
    order_id: str = Path(
        ...,
        regex="^ORD-[0-9]{6}$",  # Format: ORD-123456
        description="Order ID format: ORD-XXXXXX"
    )
):
    return {"order_id": order_id}
```

### Multiple Path Parameters

```python
@app.get("/users/{user_id}/posts/{post_id}")
async def get_user_post(
    user_id: str = Path(..., description="User ID"),
    post_id: int = Path(..., ge=1, description="Post ID")
):
    return {
        "user_id": user_id,
        "post_id": post_id
    }
```

---

## 🔍 Query Parameters

**Location:** After `?` in URL  
**Use for:** Filtering, pagination, sorting, optional parameters  
**Always optional:** Usually (can make required)

### Basic Usage

```python
from fastapi import Query
from typing import Optional

@app.get("/products")
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Example: /products?page=2&limit=50
    """
    return {
        "page": page,
        "limit": limit,
        "items": []  # Your data here
    }
```

### Optional Query Parameters

```python
@app.get("/search")
async def search_items(
    q: Optional[str] = Query(
        None,  # Default is None (optional)
        min_length=3,
        max_length=50,
        description="Search query"
    ),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Example: /search?q=laptop&category=electronics
    Or: /search?q=laptop (category is optional)
    """
    filters = {}
    if q:
        filters["search"] = q
    if category:
        filters["category"] = category
    
    return {"filters": filters}
```

### Required Query Parameters

```python
@app.get("/reports")
async def get_reports(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Both parameters are required!
    Example: /reports?start_date=2024-01-01&end_date=2024-12-31
    """
    return {
        "start_date": start_date,
        "end_date": end_date
    }
```

### List Query Parameters

```python
@app.get("/products/filter")
async def filter_products(
    tags: list[str] = Query(
        [],  # Default empty list
        description="Filter by tags",
        example=["electronics", "sale"]
    )
):
    """
    Example: /products/filter?tags=electronics&tags=sale&tags=new
    Returns: tags = ["electronics", "sale", "new"]
    """
    return {"tags": tags}
```

### Enum Query Parameters

```python
from enum import Enum

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class SortBy(str, Enum):
    name = "name"
    price = "price"
    created_at = "created_at"

@app.get("/products")
async def list_products(
    sort_by: SortBy = Query(SortBy.created_at, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.desc, description="Sort order")
):
    """
    Example: /products?sort_by=price&sort_order=asc
    Validates that sort_by and sort_order are valid enum values!
    """
    return {
        "sort_by": sort_by.value,
        "sort_order": sort_order.value
    }
```

### Boolean Query Parameters

```python
@app.get("/products")
async def list_products(
    in_stock: Optional[bool] = Query(None, description="Filter by stock status"),
    on_sale: bool = Query(False, description="Show only sale items")
):
    """
    Example: /products?in_stock=true&on_sale=false
    Accepts: true, false, 1, 0, yes, no
    """
    filters = {"on_sale": on_sale}
    if in_stock is not None:
        filters["in_stock"] = in_stock
    
    return {"filters": filters}
```

---

## 📦 Body Parameters

**Location:** Request body (JSON)  
**Use for:** Create/update operations, complex data structures  
**Methods:** POST, PUT, PATCH

### Using Pydantic Models (Recommended)

```python
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    age: Optional[int] = Field(None, ge=0, le=150)

@app.post("/users")
async def create_user(user: UserCreate):
    """
    Request body example:
    {
        "email": "user@example.com",
        "username": "johndoe",
        "password": "securepass123",
        "age": 25
    }
    """
    return {
        "message": "User created",
        "user": user
    }
```

### Explicit Body Parameters

```python
from fastapi import Body

@app.post("/items")
async def create_item(
    name: str = Body(..., min_length=1, max_length=100),
    price: float = Body(..., gt=0),
    description: Optional[str] = Body(None, max_length=500)
):
    """
    Request body:
    {
        "name": "Product Name",
        "price": 29.99,
        "description": "Optional description"
    }
    """
    return {
        "name": name,
        "price": price,
        "description": description
    }
```

### Multiple Body Parameters

```python
class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

@app.put("/users/{user_id}")
async def update_user(
    user_id: str = Path(...),
    user: UserUpdate = Body(...),
    address: Optional[Address] = Body(None)
):
    """
    Request body:
    {
        "user": {
            "name": "John Doe",
            "email": "john@example.com"
        },
        "address": {
            "street": "123 Main St",
            "city": "NYC",
            "zip_code": "10001"
        }
    }
    """
    return {
        "user_id": user_id,
        "user": user,
        "address": address
    }
```

### Embedded Body Parameter

```python
@app.post("/login")
async def login(
    username: str = Body(...),
    password: str = Body(...),
    remember_me: bool = Body(False)
):
    """
    Request body:
    {
        "username": "john",
        "password": "secret",
        "remember_me": true
    }
    """
    return {"username": username}
```

### Single Value in Body

```python
@app.post("/items/{item_id}")
async def update_item(
    item_id: str = Path(...),
    quantity: int = Body(..., embed=True, ge=1)
):
    """
    embed=True forces the value to be wrapped:
    {
        "quantity": 5
    }
    
    Without embed=True, you'd send just: 5
    """
    return {"item_id": item_id, "quantity": quantity}
```

---

## 🎨 Combining All Three

### Production-Ready Endpoint Example

```python
from typing import Optional
from enum import Enum

class ProductStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProductStatus] = None

@app.put("/products/{product_id}")
async def update_product(
    # PATH parameter - resource identifier
    product_id: str = Path(
        ...,
        regex="^PROD-[0-9]{6}$",
        description="Product ID (format: PROD-123456)"
    ),
    
    # BODY parameter - data to update
    product: ProductUpdate = Body(
        ...,
        description="Product fields to update"
    ),
    
    # QUERY parameters - metadata/options
    notify_users: bool = Query(
        False,
        description="Send notification to subscribed users"
    ),
    reason: Optional[str] = Query(
        None,
        max_length=200,
        description="Reason for update (for audit log)"
    )
):
    """
    Complete example:
    PUT /products/PROD-123456?notify_users=true&reason=Price%20adjustment
    
    Body:
    {
        "price": 29.99,
        "status": "active"
    }
    """
    return {
        "product_id": product_id,
        "updates": product.model_dump(exclude_none=True),
        "notify_users": notify_users,
        "reason": reason
    }
```

---

## 🔒 Security Best Practices

### 1. Input Validation

```python
@app.get("/files/{file_path:path}")
async def get_file(
    file_path: str = Path(
        ...,
        regex="^[a-zA-Z0-9/_-]+\.(txt|pdf|jpg)$",  # Only specific file types
        description="File path"
    )
):
    """
    ✅ Prevents directory traversal attacks
    ✅ Limits to specific file extensions
    """
    return {"file_path": file_path}
```

### 2. Limit String Lengths

```python
@app.get("/search")
async def search(
    q: str = Query(
        ...,
        min_length=1,
        max_length=100,  # ✅ Prevent huge inputs
        description="Search query"
    )
):
    return {"query": q}
```

### 3. Limit List Sizes

```python
@app.get("/bulk")
async def bulk_operation(
    ids: list[str] = Query(
        ...,
        max_items=50,  # ✅ Prevent DOS attacks
        description="IDs to process"
    )
):
    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="Too many IDs")
    return {"count": len(ids)}
```

### 4. Validate Numeric Ranges

```python
@app.get("/products")
async def list_products(
    page: int = Query(1, ge=1, le=1000),  # ✅ Reasonable page limit
    limit: int = Query(20, ge=1, le=100)  # ✅ Limit items per page
):
    return {"page": page, "limit": limit}
```

---

## 🚨 Common Mistakes & Solutions

### ❌ MISTAKE 1: Not Using Constraints

```python
# ❌ WRONG - No validation
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    # What if item_id is negative or 0?
    pass
```

```python
# ✅ RIGHT - With validation
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(..., ge=1, description="Item ID")
):
    pass
```

### ❌ MISTAKE 2: Making Everything Optional

```python
# ❌ WRONG - Too permissive
@app.get("/search")
async def search(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None
):
    # What if all are None? No search criteria!
    pass
```

```python
# ✅ RIGHT - Require at least one parameter
@app.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query")
):
    pass
```

### ❌ MISTAKE 3: Not Documenting Parameters

```python
# ❌ WRONG - No descriptions
@app.get("/products")
async def list_products(
    page: int = 1,
    limit: int = 20
):
    pass
```

```python
# ✅ RIGHT - Well documented
@app.get("/products")
async def list_products(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    pass
```

### ❌ MISTAKE 4: Ignoring Type Hints

```python
# ❌ WRONG - No type hints
@app.get("/items/{item_id}")
async def get_item(item_id):  # What type?
    pass
```

```python
# ✅ RIGHT - Clear types
@app.get("/items/{item_id}")
async def get_item(item_id: int = Path(...)):
    pass
```

### ❌ MISTAKE 5: Using Query for Resource IDs

```python
# ❌ WRONG - ID in query parameter
@app.get("/products")
async def get_product(product_id: str = Query(...)):
    # Should be in path!
    pass
```

```python
# ✅ RIGHT - ID in path
@app.get("/products/{product_id}")
async def get_product(product_id: str = Path(...)):
    pass
```

---

## 📊 Decision Guide

### When to Use Path Parameters?

✅ **Use Path when:**
- Identifying a specific resource (user ID, product ID)
- The parameter is **always required**
- It's part of the resource hierarchy (`/users/{user_id}/posts/{post_id}`)

Examples:
- `/users/{user_id}`
- `/products/{product_id}`
- `/orders/{order_id}/items/{item_id}`

### When to Use Query Parameters?

✅ **Use Query when:**
- Filtering results (`?category=electronics`)
- Pagination (`?page=1&limit=20`)
- Sorting (`?sort_by=price&order=asc`)
- Search (`?q=laptop`)
- Optional parameters
- Multiple values (`?tags=new&tags=sale`)

Examples:
- `/products?category=electronics&price_min=100`
- `/users?active=true&page=2`
- `/search?q=laptop&brand=dell`

### When to Use Body Parameters?

✅ **Use Body when:**
- Creating resources (POST)
- Updating resources (PUT/PATCH)
- Sending complex data structures
- Sending sensitive data (passwords, tokens)
- Multiple related fields

Examples:
- `POST /users` with user data in body
- `PUT /products/{id}` with updated fields in body
- `PATCH /settings` with settings in body

---

## 🎯 Production Patterns

### Pattern 1: Pagination

```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")

@app.get("/items")
async def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    skip = (page - 1) * limit
    
    # Query database with skip and limit
    # items = await Item.find().skip(skip).limit(limit).to_list()
    
    return {
        "page": page,
        "limit": limit,
        "total": 100,  # Total count from DB
        "items": []
    }
```

### Pattern 2: Filtering & Sorting

```python
from enum import Enum

class SortBy(str, Enum):
    name = "name"
    price = "price"
    created_at = "created_at"

@app.get("/products")
async def list_products(
    # Filters
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    
    # Sorting
    sort_by: SortBy = Query(SortBy.created_at),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    # Pagination
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["price_min"] = min_price
    if max_price is not None:
        filters["price_max"] = max_price
    if in_stock is not None:
        filters["in_stock"] = in_stock
    
    return {
        "filters": filters,
        "sort": {"by": sort_by, "order": sort_order},
        "pagination": {"page": page, "limit": limit}
    }
```

### Pattern 3: Partial Updates

```python
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    
    class Config:
        # Only include fields that were explicitly set
        exclude_none = True

@app.patch("/products/{product_id}")
async def partial_update_product(
    product_id: str = Path(...),
    product: ProductUpdate = Body(...)
):
    # Only update fields that are present
    update_data = product.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided"
        )
    
    # await Product.update(product_id, update_data)
    
    return {"updated_fields": list(update_data.keys())}
```

---

## 📚 Quick Reference Card

```python
# PATH - Resource identifier (always required)
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(..., ge=1, description="Item ID")
):
    pass

# QUERY - Filters, pagination (usually optional)
@app.get("/items")
async def list_items(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None, max_length=100)
):
    pass

# BODY - Create/update data (complex structures)
@app.post("/items")
async def create_item(
    item: ItemCreate = Body(..., description="Item data")
):
    pass

# COMBINED - All three together
@app.put("/items/{item_id}")
async def update_item(
    item_id: int = Path(..., ge=1),           # PATH
    item: ItemUpdate = Body(...),              # BODY
    notify: bool = Query(False)                # QUERY
):
    pass
```

---

## 🎓 Summary

**Key Principles:**

1. **Path** = Resource identifiers (required)
2. **Query** = Filters & options (usually optional)
3. **Body** = Complex data (POST/PUT/PATCH)

4. **Always validate** - Use constraints (ge, le, min_length, max_length, regex)
5. **Always document** - Add descriptions and examples
6. **Think security** - Validate ranges, lengths, patterns
7. **Use Pydantic models** - For complex body data
8. **Use Enums** - For limited choice fields

**Remember:** Good parameter handling makes your API robust, secure, and self-documenting!
