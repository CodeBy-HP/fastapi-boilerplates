# 🔍 Search & Pagination - Quick Reference

Fast lookup for search, filtering, sorting, and pagination patterns in FastAPI.

---

## 📋 Quick Decision Tree

```
Need to show list of items with pages? → Offset Pagination
    Use: page + page_size
    Good for: < 10,000 items

Need efficient pagination for large dataset? → Cursor Pagination
    Use: cursor + limit
    Good for: > 10,000 items, real-time data

Need "Load More" button? → Infinite Scroll
    Use: last_id + limit
    Good for: Mobile apps, social feeds

Need filter UI with counts? → Faceted Search
    Use: Aggregation pipeline
    Good for: E-commerce, catalogs
```

---

## 🔢 Pagination Templates

### Offset-Based (Most Common)
```python
@app.get("/items")
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    skip = (page - 1) * page_size
    total = await Item.count()
    items = await Item.find().skip(skip).limit(page_size).to_list()
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "items": items
    }
```

### Cursor-Based (Efficient)
```python
@app.get("/items/cursor")
async def list_items_cursor(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    from bson import ObjectId
    
    if cursor:
        query = Item.find(Item.id > ObjectId(cursor))
    else:
        query = Item.find()
    
    items = await query.sort("+_id").limit(limit + 1).to_list()
    
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]
    
    next_cursor = str(items[-1].id) if items and has_more else None
    
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more
    }
```

### Infinite Scroll
```python
@app.get("/items/infinite")
async def infinite_scroll(
    last_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    from bson import ObjectId
    
    if last_id:
        query = Item.find(Item.id > ObjectId(last_id))
    else:
        query = Item.find()
    
    items = await query.sort("+_id").limit(limit).to_list()
    
    return {
        "items": items,
        "last_id": str(items[-1].id) if items else None,
        "has_more": len(items) == limit
    }
```

---

## 🔍 Search & Filter Templates

### Text Search
```python
from beanie.operators import RegEx, Or

@app.get("/items/search")
async def search(
    q: str = Query(..., min_length=2, max_length=100)
):
    # Search across multiple fields
    items = await Item.find(
        Or(
            RegEx(Item.name, q, options="i"),
            RegEx(Item.description, q, options="i")
        )
    ).to_list()
    
    return {"results": items}
```

### Multiple Filters
```python
from beanie.operators import And, In

@app.get("/products")
async def filter_products(
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    tags: List[str] = Query([], max_items=10)
):
    conditions = []
    
    if category:
        conditions.append(Product.category == category)
    
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    
    if max_price is not None:
        conditions.append(Product.price <= max_price)
    
    if tags:
        conditions.append(In(Product.tags, tags))
    
    if conditions:
        query = Product.find(And(*conditions))
    else:
        query = Product.find()
    
    products = await query.to_list()
    return {"results": products}
```

### Complete Search Endpoint
```python
@app.get("/products/search")
async def search_products(
    # Search
    q: Optional[str] = Query(None, min_length=2, max_length=100),
    
    # Filters
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    
    # Sort
    sort_by: Literal["name", "price", "created_at"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    conditions = []
    
    # Search
    if q:
        conditions.append(Or(
            RegEx(Product.name, q, options="i"),
            RegEx(Product.description, q, options="i")
        ))
    
    # Filters
    if category:
        conditions.append(Product.category == category)
    if min_price:
        conditions.append(Product.price >= min_price)
    if max_price:
        conditions.append(Product.price <= max_price)
    
    # Query
    query = Product.find(And(*conditions)) if conditions else Product.find()
    
    # Count
    total = await query.count()
    
    # Sort
    sort_str = f"{'-' if order == 'desc' else '+'}{sort_by}"
    query = query.sort(sort_str)
    
    # Paginate
    skip = (page - 1) * page_size
    products = await query.skip(skip).limit(page_size).to_list()
    
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

---

## 📊 Sorting Templates

### Basic Sort
```python
from enum import Enum

class SortField(str, Enum):
    name = "name"
    price = "price"
    created_at = "created_at"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

@app.get("/items")
async def list_items(
    sort_by: SortField = Query(SortField.created_at),
    order: SortOrder = Query(SortOrder.desc)
):
    sort_str = f"{'-' if order == SortOrder.desc else '+'}{sort_by.value}"
    items = await Item.find().sort(sort_str).to_list()
    return {"items": items}
```

### Multiple Sort Fields
```python
@app.get("/items")
async def list_items(
    sort_by: List[str] = Query(["created_at", "name"])
):
    # Sort by multiple fields
    items = await Item.find().sort(
        "-created_at", "+name"  # Desc by date, then asc by name
    ).to_list()
    return {"items": items}
```

---

## ♻️ Reusable Dependencies

### Pagination Dependency
```python
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size

@app.get("/items")
async def list_items(pagination: PaginationParams = Depends()):
    items = await Item.find().skip(pagination.skip).limit(pagination.page_size).to_list()
    return {"page": pagination.page, "items": items}
```

### Filter Dependency
```python
class ProductFilters:
    def __init__(
        self,
        q: Optional[str] = Query(None, min_length=2, max_length=100),
        category: Optional[str] = Query(None),
        min_price: Optional[float] = Query(None, ge=0),
        max_price: Optional[float] = Query(None, ge=0)
    ):
        self.q = q
        self.category = category
        self.min_price = min_price
        self.max_price = max_price
    
    def build_conditions(self):
        conditions = []
        
        if self.q:
            conditions.append(Or(
                RegEx(Product.name, self.q, options="i"),
                RegEx(Product.description, self.q, options="i")
            ))
        
        if self.category:
            conditions.append(Product.category == self.category)
        
        if self.min_price:
            conditions.append(Product.price >= self.min_price)
        
        if self.max_price:
            conditions.append(Product.price <= self.max_price)
        
        return conditions

@app.get("/products")
async def search(filters: ProductFilters = Depends()):
    conditions = filters.build_conditions()
    query = Product.find(And(*conditions)) if conditions else Product.find()
    products = await query.to_list()
    return {"results": products}
```

---

## 📦 Response Models

### Generic Paginated Response
```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    items: List[T]

# Usage
@app.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(...):
    return PaginatedResponse(
        total=100,
        page=1,
        page_size=20,
        total_pages=5,
        has_next=True,
        has_prev=False,
        items=[...]
    )
```

### Cursor Response
```python
class CursorResponse(BaseModel, Generic[T]):
    items: List[T]
    next_cursor: Optional[str]
    has_more: bool
    count: int
```

---

## 🎯 Common Patterns

### Autocomplete
```python
@app.get("/products/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=50),
    limit: int = Query(10, ge=1, le=20)
):
    products = await Product.find(
        RegEx(Product.name, f"^{q}", options="i")  # Starts with
    ).limit(limit).to_list()
    
    return {"suggestions": [p.name for p in products]}
```

### Faceted Search
```python
@app.get("/products/facets")
async def faceted_search(q: Optional[str] = None):
    # Get products
    query = Product.find(RegEx(Product.name, q, options="i")) if q else Product.find()
    products = await query.limit(20).to_list()
    
    # Get category counts
    pipeline = [
        {"$match": RegEx(Product.name, q, options="i").to_dict() if q else {}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    facets = await Product.aggregate(pipeline).to_list()
    
    return {
        "products": products,
        "facets": {"categories": facets}
    }
```

### Search Highlighting
```python
def highlight_match(text: str, query: str) -> str:
    """Highlight search query in text"""
    import re
    pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
    return pattern.sub(r"<mark>\1</mark>", text)

@app.get("/search")
async def search_with_highlight(q: str = Query(...)):
    products = await Product.find(RegEx(Product.name, q, options="i")).to_list()
    
    results = [
        {
            "id": str(p.id),
            "name": highlight_match(p.name, q),
            "description": highlight_match(p.description, q)
        }
        for p in products
    ]
    
    return {"results": results}
```

---

## 🛡️ Security Checklist

```python
✅ Limit page size
page_size: int = Query(20, ge=1, le=100)  # Max 100

✅ Validate search query
q: str = Query(..., min_length=2, max_length=100)

✅ Limit filter arrays
tags: List[str] = Query([], max_items=10)

✅ Use Enums for sort fields
sort_by: SortField = Query(SortField.created_at)  # Only allowed values

✅ Escape regex input (prevent ReDoS)
import re
safe_query = re.escape(user_query)

✅ Rate limit search endpoints
from slowapi import Limiter
@limiter.limit("30/minute")
async def search(...): ...

✅ Add database indexes
class Product(Document):
    class Settings:
        indexes = ["category", "price", [("created_at", -1)]]
```

---

## ⚡ Performance Tips

### 1. Use Indexes
```python
class Product(Document):
    class Settings:
        indexes = [
            "category",           # Single field
            "price",
            [("created_at", -1)], # Descending
            [("name", "text")],   # Text search
        ]
```

### 2. Project Only Needed Fields
```python
# Instead of all fields
products = await Product.find().to_list()

# Project only needed
class ProductListItem(BaseModel):
    id: str
    name: str
    price: float

products = await Product.find(
    projection_model=ProductListItem
).to_list()
```

### 3. Skip Count When Not Needed
```python
# With count (slower)
total = await query.count()

# Without count (faster) - for cursor pagination
# Just return items, no total
```

### 4. Cache Expensive Queries
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_categories():
    """Cache category list"""
    return await Product.distinct("category")
```

---

## 📊 Beanie Operators Quick Reference

```python
from beanie.operators import (
    And, Or, In, RegEx, Eq, Ne, Gt, Gte, Lt, Lte
)

# Equals
Product.category == "electronics"
Eq(Product.category, "electronics")

# Not equals
Product.status != "inactive"
Ne(Product.status, "inactive")

# Greater than
Product.price > 100
Gt(Product.price, 100)

# Greater than or equal
Product.price >= 100
Gte(Product.price, 100)

# Less than
Product.price < 1000
Lt(Product.price, 1000)

# Less than or equal
Product.price <= 1000
Lte(Product.price, 1000)

# In list
In(Product.tags, ["sale", "new"])

# Regex (case-insensitive)
RegEx(Product.name, "laptop", options="i")

# And
And(Product.price > 100, Product.stock > 0)

# Or
Or(Product.category == "electronics", Product.category == "computers")
```

---

## 🔄 Complete Flow Example

```python
# 1. Define dependencies
class PaginationParams:
    def __init__(self, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size

class ProductFilters:
    def __init__(
        self,
        q: Optional[str] = Query(None, min_length=2, max_length=100),
        category: Optional[str] = Query(None)
    ):
        self.q = q
        self.category = category
    
    def build_conditions(self):
        conditions = []
        if self.q:
            conditions.append(RegEx(Product.name, self.q, options="i"))
        if self.category:
            conditions.append(Product.category == self.category)
        return conditions

# 2. Create endpoint
@app.get("/products", response_model=PaginatedResponse[ProductResponse])
async def search_products(
    filters: ProductFilters = Depends(),
    pagination: PaginationParams = Depends(),
    sort_by: SortField = Query(SortField.created_at),
    order: SortOrder = Query(SortOrder.desc)
):
    # Build query
    conditions = filters.build_conditions()
    query = Product.find(And(*conditions)) if conditions else Product.find()
    
    # Count
    total = await query.count()
    
    # Sort
    sort_str = f"{'-' if order == SortOrder.desc else '+'}{sort_by.value}"
    query = query.sort(sort_str)
    
    # Paginate
    products = await query.skip(pagination.skip).limit(pagination.page_size).to_list()
    
    # Response
    total_pages = math.ceil(total / pagination.page_size) if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[ProductResponse.from_document(p) for p in products]
    )
```

---

## 📚 Resources

- **Full Examples**: See `example.py` in this directory
- **Detailed Guide**: See `README.md` for comprehensive explanations
- **Beanie Docs**: https://beanie-odm.dev/
- **MongoDB Operators**: https://www.mongodb.com/docs/manual/reference/operator/

---

**Quick Summary**:
- **Offset Pagination** = page + page_size (most common)
- **Cursor Pagination** = cursor + limit (large datasets)
- **Filters** = Build conditions with And/Or
- **Search** = RegEx with options="i" (case-insensitive)
- **Sort** = Prefix with +/- for asc/desc
