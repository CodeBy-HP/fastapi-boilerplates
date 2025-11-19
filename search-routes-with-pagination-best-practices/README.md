# 🔍 Search & Pagination Best Practices

Complete guide to building production-ready search endpoints with filtering, sorting, and pagination in FastAPI.

## 📋 Quick Overview

| Feature | Purpose | Example |
|---------|---------|---------|
| **Search/Filter** | Find specific records | `?name=laptop&category=electronics` |
| **Sorting** | Order results | `?sort_by=price&order=desc` |
| **Pagination** | Limit results per page | `?page=2&page_size=20` |
| **Cursor Pagination** | Efficient large datasets | `?cursor=abc123&limit=50` |

---

## 🎯 Why This Matters

### Common Challenges
- ❌ Returning thousands of records at once (performance killer)
- ❌ Inefficient database queries (N+1 problems)
- ❌ No filtering options (users can't find what they need)
- ❌ Inconsistent pagination across endpoints
- ❌ Missing total count information

### Solutions in This Guide
- ✅ Efficient pagination with total counts
- ✅ Flexible filtering and search
- ✅ Multi-field sorting
- ✅ Reusable pagination dependencies
- ✅ Cursor-based pagination for large datasets
- ✅ Production-ready error handling

---

## 📖 Table of Contents

1. [Basic Pagination](#basic-pagination)
2. [Filtering & Search](#filtering--search)
3. [Sorting](#sorting)
4. [Complete Search Endpoint](#complete-search-endpoint)
5. [Cursor Pagination](#cursor-pagination)
6. [Reusable Dependencies](#reusable-dependencies)
7. [Response Models](#response-models)
8. [Performance Tips](#performance-tips)
9. [Common Patterns](#common-patterns)
10. [Security Best Practices](#security-best-practices)

---

## 🔢 Basic Pagination

### Offset-Based Pagination

Most common pagination type - uses `page` and `page_size`.

```python
from fastapi import Query

@app.get("/products")
async def list_products(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Query database
    total = await Product.count()
    products = await Product.find().skip(skip).limit(page_size).to_list()
    
    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "items": products
    }
```

### Response Structure

```json
{
  "total": 150,
  "page": 2,
  "page_size": 20,
  "total_pages": 8,
  "has_next": true,
  "has_prev": true,
  "items": [...]
}
```

**Pros:**
- ✅ Easy to implement
- ✅ Users can jump to any page
- ✅ Shows total count

**Cons:**
- ❌ Inefficient for large datasets (high skip values are slow)
- ❌ Can miss items if data changes during pagination

---

## 🔍 Filtering & Search

### Text Search

```python
from beanie.operators import RegEx

@app.get("/products/search")
async def search_products(
    q: Optional[str] = Query(None, min_length=2, max_length=100, description="Search query")
):
    if not q:
        products = await Product.find().to_list()
    else:
        # Case-insensitive regex search
        products = await Product.find(
            RegEx(Product.name, q, options="i")
        ).to_list()
    
    return {"results": products}
```

### Multiple Field Search

```python
from beanie.operators import Or

@app.get("/products/search")
async def search_products(
    q: Optional[str] = Query(None, min_length=2, max_length=100)
):
    if not q:
        return {"results": []}
    
    # Search across multiple fields
    products = await Product.find(
        Or(
            RegEx(Product.name, q, options="i"),
            RegEx(Product.description, q, options="i"),
            RegEx(Product.category, q, options="i")
        )
    ).to_list()
    
    return {"results": products}
```

### Field-Specific Filters

```python
@app.get("/products")
async def filter_products(
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    tags: List[str] = Query([], description="Filter by tags")
):
    conditions = []
    
    # Category filter (exact match)
    if category:
        conditions.append(Product.category == category)
    
    # Price range
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    if max_price is not None:
        conditions.append(Product.price <= max_price)
    
    # Stock status
    if in_stock is not None:
        conditions.append(Product.stock > 0 if in_stock else Product.stock == 0)
    
    # Tags (contains any)
    if tags:
        conditions.append(In(Product.tags, tags))
    
    # Build query
    if conditions:
        query = Product.find(And(*conditions))
    else:
        query = Product.find()
    
    products = await query.to_list()
    return {"results": products}
```

---

## 📊 Sorting

### Basic Sorting

```python
from enum import Enum

class SortField(str, Enum):
    name = "name"
    price = "price"
    created_at = "created_at"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

@app.get("/products")
async def list_products(
    sort_by: SortField = Query(SortField.created_at),
    order: SortOrder = Query(SortOrder.desc)
):
    # Build sort string: + for asc, - for desc
    sort_string = f"{'-' if order == SortOrder.desc else '+'}{sort_by.value}"
    
    products = await Product.find().sort(sort_string).to_list()
    
    return {"results": products}
```

### Multiple Sort Fields

```python
@app.get("/products")
async def list_products(
    sort_by: List[SortField] = Query([SortField.created_at]),
    order: SortOrder = Query(SortOrder.desc)
):
    # Sort by multiple fields
    sort_strings = [
        f"{'-' if order == SortOrder.desc else '+'}{field.value}"
        for field in sort_by
    ]
    
    products = await Product.find().sort(*sort_strings).to_list()
    
    return {"results": products}
```

---

## 🎯 Complete Search Endpoint

Combining filtering, sorting, and pagination:

```python
import math
from typing import Optional, List, Literal
from fastapi import Query, HTTPException, status
from beanie.operators import RegEx, And, Or, In

class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    items: List[ProductResponse]

@app.get("/products/search", response_model=ProductListResponse)
async def search_products(
    # Search
    q: Optional[str] = Query(None, min_length=2, max_length=100, description="Search query"),
    
    # Filters
    category: Optional[str] = Query(None, max_length=100),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    tags: List[str] = Query([], max_items=10),
    
    # Sorting
    sort_by: Literal["name", "price", "created_at"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Search products with filters, sorting, and pagination.
    
    Example:
    GET /products/search?q=laptop&category=electronics&min_price=500&sort_by=price&order=asc&page=1&page_size=20
    """
    try:
        conditions = []
        
        # Search query (across multiple fields)
        if q:
            conditions.append(
                Or(
                    RegEx(Product.name, q, options="i"),
                    RegEx(Product.description, q, options="i"),
                    RegEx(Product.category, q, options="i")
                )
            )
        
        # Category filter
        if category:
            conditions.append(RegEx(Product.category, category, options="i"))
        
        # Price range
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        
        # Stock status
        if in_stock is not None:
            if in_stock:
                conditions.append(Product.stock > 0)
            else:
                conditions.append(Product.stock == 0)
        
        # Tags filter
        if tags:
            conditions.append(In(Product.tags, tags))
        
        # Build query
        if conditions:
            query = Product.find(And(*conditions))
        else:
            query = Product.find()
        
        # Get total count (before pagination)
        total = await query.count()
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        # Apply sorting
        sort_string = f"{'-' if order == 'desc' else '+'}{sort_by}"
        query = query.sort(sort_string)
        
        # Apply pagination
        products = await query.skip(skip).limit(page_size).to_list()
        
        # Build response
        return ProductListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            items=[ProductResponse.from_orm(p) for p in products]
        )
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )
```

---

## 🚀 Cursor Pagination

For large datasets, cursor-based pagination is more efficient than offset-based.

### How It Works

Instead of `page` and `skip`, use a `cursor` (ID of last item) and `limit`.

```python
from typing import Optional

class CursorPaginatedResponse(BaseModel):
    items: List[ProductResponse]
    next_cursor: Optional[str]
    has_more: bool
    count: int

@app.get("/products/cursor", response_model=CursorPaginatedResponse)
async def list_products_cursor(
    cursor: Optional[str] = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Cursor-based pagination for efficient large dataset traversal.
    
    First request: GET /products/cursor?limit=20
    Next request: GET /products/cursor?cursor=<next_cursor>&limit=20
    """
    query = Product.find()
    
    # If cursor provided, filter to items after cursor
    if cursor:
        try:
            from bson import ObjectId
            cursor_id = ObjectId(cursor)
            query = query.find(Product.id > cursor_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")
    
    # Sort by ID for consistent ordering
    query = query.sort("+_id")
    
    # Fetch limit + 1 to check if there are more items
    products = await query.limit(limit + 1).to_list()
    
    # Check if there are more items
    has_more = len(products) > limit
    
    # Remove extra item if present
    if has_more:
        products = products[:limit]
    
    # Get next cursor (ID of last item)
    next_cursor = str(products[-1].id) if products and has_more else None
    
    return CursorPaginatedResponse(
        items=[ProductResponse.from_orm(p) for p in products],
        next_cursor=next_cursor,
        has_more=has_more,
        count=len(products)
    )
```

**Pros:**
- ✅ Consistent results even if data changes
- ✅ Efficient for large datasets (no skip)
- ✅ Fast queries

**Cons:**
- ❌ Can't jump to specific page
- ❌ No total count
- ❌ Only forward navigation

---

## ♻️ Reusable Dependencies

Create reusable pagination dependencies to avoid code duplication.

### Pagination Dependency

```python
from dataclasses import dataclass
from fastapi import Query

@dataclass
class PaginationParams:
    page: int
    page_size: int
    skip: int
    
    @classmethod
    def create(
        cls,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        skip = (page - 1) * page_size
        return cls(page=page, page_size=page_size, skip=skip)

# Use in routes
@app.get("/products")
async def list_products(pagination: PaginationParams = Depends(PaginationParams.create)):
    products = await Product.find().skip(pagination.skip).limit(pagination.page_size).to_list()
    return {"page": pagination.page, "items": products}
```

### Search & Filter Dependency

```python
@dataclass
class ProductFilters:
    q: Optional[str]
    category: Optional[str]
    min_price: Optional[float]
    max_price: Optional[float]
    in_stock: Optional[bool]
    
    @classmethod
    def create(
        cls,
        q: Optional[str] = Query(None, min_length=2, max_length=100),
        category: Optional[str] = Query(None),
        min_price: Optional[float] = Query(None, ge=0),
        max_price: Optional[float] = Query(None, ge=0),
        in_stock: Optional[bool] = Query(None)
    ):
        return cls(
            q=q,
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
    
    def build_conditions(self) -> List:
        """Build MongoDB query conditions"""
        conditions = []
        
        if self.q:
            conditions.append(
                Or(
                    RegEx(Product.name, self.q, options="i"),
                    RegEx(Product.description, self.q, options="i")
                )
            )
        
        if self.category:
            conditions.append(Product.category == self.category)
        
        if self.min_price is not None:
            conditions.append(Product.price >= self.min_price)
        
        if self.max_price is not None:
            conditions.append(Product.price <= self.max_price)
        
        if self.in_stock is not None:
            conditions.append(Product.stock > 0 if self.in_stock else Product.stock == 0)
        
        return conditions

# Use in routes
@app.get("/products")
async def search_products(
    filters: ProductFilters = Depends(ProductFilters.create),
    pagination: PaginationParams = Depends(PaginationParams.create)
):
    conditions = filters.build_conditions()
    
    if conditions:
        query = Product.find(And(*conditions))
    else:
        query = Product.find()
    
    total = await query.count()
    products = await query.skip(pagination.skip).limit(pagination.page_size).to_list()
    
    return {
        "total": total,
        "page": pagination.page,
        "items": products
    }
```

---

## 📦 Response Models

### Paginated Response Model

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    items: List[T]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 150,
                "page": 2,
                "page_size": 20,
                "total_pages": 8,
                "has_next": True,
                "has_prev": True,
                "items": []
            }
        }
    }

# Usage
class ProductResponse(BaseModel):
    id: str
    name: str
    price: float

@app.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(pagination: PaginationParams = Depends(PaginationParams.create)):
    total = await Product.count()
    products = await Product.find().skip(pagination.skip).limit(pagination.page_size).to_list()
    
    total_pages = math.ceil(total / pagination.page_size) if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[ProductResponse.from_orm(p) for p in products]
    )
```

---

## ⚡ Performance Tips

### 1. Use Database Indexes

```python
# In your Beanie model
class Product(Document):
    name: str
    category: str
    price: float
    created_at: datetime
    
    class Settings:
        # Add indexes for fields used in filtering/sorting
        indexes = [
            "category",
            "price",
            [("created_at", -1)],  # Descending index
            [("name", "text")],     # Text search index
        ]
```

### 2. Project Only Needed Fields

```python
# Instead of fetching all fields
products = await Product.find().to_list()

# Fetch only needed fields
products = await Product.find(
    projection_model=ProductListItem  # Smaller model
).to_list()
```

### 3. Count Only When Needed

```python
# If you don't need total count, skip it
@app.get("/products/simple")
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    skip = (page - 1) * page_size
    products = await Product.find().skip(skip).limit(page_size).to_list()
    
    return {
        "page": page,
        "items": products
        # No total count = faster query
    }
```

### 4. Cache Common Queries

```python
from functools import lru_cache
from datetime import datetime, timedelta

cache = {}

async def get_popular_products(page: int = 1, page_size: int = 20):
    """Cache popular products for 5 minutes"""
    cache_key = f"popular:{page}:{page_size}"
    
    if cache_key in cache:
        cached_data, cached_time = cache[cache_key]
        if datetime.utcnow() - cached_time < timedelta(minutes=5):
            return cached_data
    
    # Fetch from database
    skip = (page - 1) * page_size
    products = await Product.find(
        Product.is_popular == True
    ).skip(skip).limit(page_size).to_list()
    
    # Cache result
    cache[cache_key] = (products, datetime.utcnow())
    
    return products
```

---

## 🎨 Common Patterns

### Pattern 1: Search with Autocomplete

```python
@app.get("/products/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=50),
    limit: int = Query(10, ge=1, le=20)
):
    """
    Fast autocomplete for product names.
    
    Returns only names, not full objects.
    """
    products = await Product.find(
        RegEx(Product.name, f"^{q}", options="i")  # Starts with query
    ).limit(limit).project(ProductNameOnly).to_list()
    
    return {"suggestions": [p.name for p in products]}
```

### Pattern 2: Faceted Search

```python
@app.get("/products/facets")
async def faceted_search(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    """
    Search with facet counts (for filters UI).
    
    Returns:
    - Matching products
    - Category facets (count per category)
    - Price range facets
    """
    conditions = []
    
    if q:
        conditions.append(RegEx(Product.name, q, options="i"))
    
    if category:
        conditions.append(Product.category == category)
    
    query = Product.find(And(*conditions)) if conditions else Product.find()
    
    # Get products
    products = await query.limit(20).to_list()
    
    # Get facets (aggregation)
    category_facets = await Product.aggregate([
        {"$match": And(*conditions).to_dict() if conditions else {}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list()
    
    return {
        "products": products,
        "facets": {
            "categories": category_facets,
        }
    }
```

### Pattern 3: Infinite Scroll

```python
@app.get("/products/infinite")
async def infinite_scroll(
    last_id: Optional[str] = Query(None, description="ID of last item from previous request"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Infinite scroll pagination.
    
    Client keeps track of last_id and requests more items.
    """
    if last_id:
        from bson import ObjectId
        query = Product.find(Product.id > ObjectId(last_id))
    else:
        query = Product.find()
    
    products = await query.sort("+_id").limit(limit).to_list()
    
    return {
        "items": products,
        "last_id": str(products[-1].id) if products else None,
        "has_more": len(products) == limit
    }
```

---

## 🛡️ Security Best Practices

### 1. Limit Maximum Page Size

```python
# ✅ Good: Enforce maximum
page_size: int = Query(20, ge=1, le=100)

# ❌ Bad: No upper limit
page_size: int = Query(20, ge=1)  # User could request 1000000!
```

### 2. Validate Search Query Length

```python
# ✅ Good: Limit query length
q: str = Query(..., min_length=2, max_length=100)

# ❌ Bad: No length limit
q: str = Query(...)  # Could be megabytes!
```

### 3. Limit Filter Arrays

```python
# ✅ Good: Limit array size
tags: List[str] = Query([], max_items=10)

# ❌ Bad: Unlimited array
tags: List[str] = Query([])  # Could send 10000 tags!
```

### 4. Prevent Regex DoS

```python
# ✅ Good: Simple contains search
RegEx(Product.name, re.escape(q), options="i")

# ⚠️ Careful: User controls regex
# If user sends: ".*.*.*.*.*" it can cause ReDoS
```

### 5. Rate Limit Search Endpoints

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/products/search")
@limiter.limit("30/minute")  # Max 30 searches per minute
async def search_products(...):
    ...
```

---

## ❌ Common Mistakes

### Mistake 1: Not Using Indexes

```python
# ❌ Bad: Slow query on unindexed field
products = await Product.find(Product.email == "test@example.com").to_list()

# ✅ Good: Add index
class Product(Document):
    email: str
    
    class Settings:
        indexes = ["email"]
```

### Mistake 2: Counting on Every Request

```python
# ❌ Bad: Count is expensive
total = await Product.count()  # Scans entire collection

# ✅ Good: Cache counts or skip if not needed
# Use cursor pagination which doesn't need total
```

### Mistake 3: No Default Sort

```python
# ❌ Bad: Random order on each request
products = await Product.find().to_list()

# ✅ Good: Consistent ordering
products = await Product.find().sort("-created_at").to_list()
```

### Mistake 4: Fetching All Fields

```python
# ❌ Bad: Fetching large fields unnecessarily
products = await Product.find().to_list()  # Includes description, images, etc.

# ✅ Good: Project only needed fields
products = await Product.find(projection_model=ProductListItem).to_list()
```

---

## 📚 Quick Reference

See **QUICK_REFERENCE.md** for fast lookup templates and code snippets.

## 💡 Next Steps

1. Copy patterns from **example.py** to your project
2. Add database indexes for filtered/sorted fields
3. Implement caching for common queries
4. Add rate limiting to search endpoints
5. Choose pagination strategy based on your use case

---

## 🔗 Related Modules

- **Path/Query/Body Parameters** - Parameter validation
- **Header/Cookie/Depends** - Authentication for search endpoints
- **Error Handling** - Proper error responses

---

**Remember:**
- Always limit page_size maximum
- Add indexes for filtered/sorted fields
- Use cursor pagination for large datasets
- Cache expensive queries
- Validate all user inputs!
