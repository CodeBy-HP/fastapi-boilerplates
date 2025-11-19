"""
Production-Ready Search & Pagination Examples

This file demonstrates all common patterns for search, filtering, sorting, and pagination.
Each example is production-ready and can be copied directly to your project.

USAGE:
1. Copy the pattern that matches your use case
2. Adapt to your specific models and database
3. Run with: uvicorn example:app --reload

Key Concepts:
- Offset Pagination: page + page_size (most common)
- Cursor Pagination: cursor + limit (efficient for large datasets)
- Filtering: category, price range, stock status, tags
- Sorting: by name, price, date, etc.
- Search: text search across multiple fields
"""

from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Generic, TypeVar
from datetime import datetime
from enum import Enum
import math
from beanie import Document, init_beanie
from beanie.operators import RegEx, And, Or, In
from motor.motor_asyncio import AsyncIOMotorClient
from functools import lru_cache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Search & Pagination Best Practices",
    description="Production-ready patterns for search, filtering, sorting, and pagination",
    version="1.0.0"
)

router = APIRouter(prefix="/api", tags=["products"])


# ============================================================================
# DATABASE MODELS (Beanie/MongoDB)
# ============================================================================

class Product(Document):
    """Product document in MongoDB"""
    name: str
    description: str
    category: str
    price: float
    stock: int
    tags: List[str] = []
    is_active: bool = True
    is_featured: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "products"
        # Add indexes for fields used in filtering/sorting
        indexes = [
            "category",
            "price",
            "stock",
            [("created_at", -1)],
            [("name", "text"), ("description", "text")],  # Text search
        ]


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class ProductResponse(BaseModel):
    """Product response schema"""
    id: str
    name: str
    description: str
    category: str
    price: float
    stock: int
    tags: List[str]
    is_active: bool
    created_at: datetime
    
    @classmethod
    def from_document(cls, product: Product):
        return cls(
            id=str(product.id),
            name=product.name,
            description=product.description,
            category=product.category,
            price=product.price,
            stock=product.stock,
            tags=product.tags,
            is_active=product.is_active,
            created_at=product.created_at
        )

class ProductListItem(BaseModel):
    """Minimal product info for lists (performance optimization)"""
    id: str
    name: str
    category: str
    price: float
    stock: int
    
    @classmethod
    def from_document(cls, product: Product):
        return cls(
            id=str(product.id),
            name=product.name,
            category=product.category,
            price=product.price,
            stock=product.stock
        )

# Generic paginated response
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=1, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    items: List[T] = Field(..., description="Items in current page")
    
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

class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based pagination response"""
    items: List[T]
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_more: bool = Field(..., description="Whether there are more items")
    count: int = Field(..., description="Number of items in this response")


# ============================================================================
# ENUMS FOR VALIDATION
# ============================================================================

class SortField(str, Enum):
    """Fields available for sorting"""
    name = "name"
    price = "price"
    created_at = "created_at"
    stock = "stock"

class SortOrder(str, Enum):
    """Sort order"""
    asc = "asc"
    desc = "desc"


# ============================================================================
# REUSABLE DEPENDENCIES
# ============================================================================

class PaginationParams:
    """Reusable pagination parameters"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (starts at 1)"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size

class ProductFilters:
    """Reusable product filter parameters"""
    def __init__(
        self,
        q: Optional[str] = Query(None, min_length=2, max_length=100, description="Search query"),
        category: Optional[str] = Query(None, max_length=100, description="Filter by category"),
        min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
        max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
        in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
        tags: List[str] = Query([], max_items=10, description="Filter by tags"),
        is_active: Optional[bool] = Query(None, description="Filter by active status")
    ):
        self.q = q
        self.category = category
        self.min_price = min_price
        self.max_price = max_price
        self.in_stock = in_stock
        self.tags = tags
        self.is_active = is_active
    
    def build_conditions(self) -> List:
        """Build MongoDB query conditions from filters"""
        conditions = []
        
        # Search query (across name and description)
        if self.q:
            conditions.append(
                Or(
                    RegEx(Product.name, self.q, options="i"),
                    RegEx(Product.description, self.q, options="i")
                )
            )
        
        # Category filter (case-insensitive partial match)
        if self.category:
            conditions.append(RegEx(Product.category, self.category, options="i"))
        
        # Price range
        if self.min_price is not None:
            conditions.append(Product.price >= self.min_price)
        
        if self.max_price is not None:
            conditions.append(Product.price <= self.max_price)
        
        # Stock availability
        if self.in_stock is not None:
            if self.in_stock:
                conditions.append(Product.stock > 0)
            else:
                conditions.append(Product.stock == 0)
        
        # Tags filter (product must have any of the specified tags)
        if self.tags:
            conditions.append(In(Product.tags, self.tags))
        
        # Active status
        if self.is_active is not None:
            conditions.append(Product.is_active == self.is_active)
        
        return conditions


# ============================================================================
# PATTERN 1: Basic Pagination (Offset-Based)
# ============================================================================

@router.get("/products/basic", response_model=PaginatedResponse[ProductListItem])
async def list_products_basic(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Basic pagination with page and page_size.
    
    Example: GET /api/products/basic?page=2&page_size=20
    
    Returns:
    - Total count
    - Current page
    - Total pages
    - Navigation flags (has_next, has_prev)
    - Items in current page
    """
    try:
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Get total count
        total = await Product.find(Product.is_active == True).count()
        
        # Get paginated products
        products = await Product.find(
            Product.is_active == True
        ).sort("-created_at").skip(skip).limit(page_size).to_list()
        
        # Calculate total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            items=[ProductListItem.from_document(p) for p in products]
        )
    
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


# ============================================================================
# PATTERN 2: Filtering & Search
# ============================================================================

@router.get("/products/filter", response_model=PaginatedResponse[ProductResponse])
async def filter_products(
    filters: ProductFilters = Depends(),
    pagination: PaginationParams = Depends(),
    sort_by: SortField = Query(SortField.created_at, description="Sort by field"),
    order: SortOrder = Query(SortOrder.desc, description="Sort order")
):
    """
    Advanced filtering with multiple parameters.
    
    Example:
    GET /api/products/filter?q=laptop&category=electronics&min_price=500&max_price=2000&in_stock=true&sort_by=price&order=asc&page=1&page_size=20
    
    Supports:
    - Text search (q)
    - Category filter
    - Price range (min_price, max_price)
    - Stock availability
    - Tags
    - Sorting
    - Pagination
    """
    try:
        # Build query conditions
        conditions = filters.build_conditions()
        
        # Create query
        if conditions:
            query = Product.find(And(*conditions))
        else:
            query = Product.find()
        
        # Get total count (before pagination)
        total = await query.count()
        
        # Apply sorting
        sort_string = f"{'-' if order == SortOrder.desc else '+'}{sort_by.value}"
        query = query.sort(sort_string)
        
        # Apply pagination
        products = await query.skip(pagination.skip).limit(pagination.page_size).to_list()
        
        # Calculate total pages
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
    
    except Exception as e:
        logger.error(f"Failed to filter products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter products"
        )


# ============================================================================
# PATTERN 3: Complete Search Endpoint (Most Common)
# ============================================================================

@router.get("/products/search", response_model=PaginatedResponse[ProductResponse])
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
    sort_by: Literal["name", "price", "created_at", "stock"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Complete search endpoint with all features.
    
    This is the most commonly used pattern in production.
    
    Example:
    GET /api/products/search?q=gaming&category=electronics&min_price=100&max_price=1000&in_stock=true&tags=sale&tags=featured&sort_by=price&order=asc&page=1&page_size=20
    
    Features:
    - Full-text search across name and description
    - Multiple filters (category, price range, stock, tags)
    - Flexible sorting
    - Offset-based pagination with metadata
    """
    try:
        conditions = []
        
        # Search query
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
        
        # Stock filter
        if in_stock is not None:
            if in_stock:
                conditions.append(Product.stock > 0)
            else:
                conditions.append(Product.stock == 0)
        
        # Tags filter
        if tags:
            conditions.append(In(Product.tags, tags))
        
        # Only active products
        conditions.append(Product.is_active == True)
        
        # Build query
        if conditions:
            query = Product.find(And(*conditions))
        else:
            query = Product.find(Product.is_active == True)
        
        # Get total count
        total = await query.count()
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        # Apply sorting
        sort_string = f"{'-' if order == 'desc' else '+'}{sort_by}"
        query = query.sort(sort_string)
        
        # Get results
        products = await query.skip(skip).limit(page_size).to_list()
        
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            items=[ProductResponse.from_document(p) for p in products]
        )
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


# ============================================================================
# PATTERN 4: Cursor-Based Pagination (Efficient for Large Datasets)
# ============================================================================

@router.get("/products/cursor", response_model=CursorPaginatedResponse[ProductResponse])
async def list_products_cursor(
    cursor: Optional[str] = Query(None, description="Cursor for next page (ID of last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Cursor-based pagination for efficient large dataset traversal.
    
    Example:
    First request: GET /api/products/cursor?limit=20
    Next request: GET /api/products/cursor?cursor=<next_cursor>&limit=20
    
    Advantages:
    - Consistent results even if data changes
    - More efficient than offset for large datasets
    - No skip queries (faster)
    
    Disadvantages:
    - Can't jump to specific page
    - No total count
    - Only forward navigation
    """
    try:
        from bson import ObjectId
        
        # Build base query
        conditions = [Product.is_active == True]
        
        if category:
            conditions.append(Product.category == category)
        
        query = Product.find(And(*conditions))
        
        # If cursor provided, get items after cursor
        if cursor:
            try:
                cursor_id = ObjectId(cursor)
                query = Product.find(And(*conditions, Product.id > cursor_id))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        
        # Sort by ID for consistent ordering
        query = query.sort("+_id")
        
        # Fetch limit + 1 to check if there are more items
        products = await query.limit(limit + 1).to_list()
        
        # Check if there are more items
        has_more = len(products) > limit
        
        # Remove extra item
        if has_more:
            products = products[:limit]
        
        # Get next cursor (ID of last item)
        next_cursor = str(products[-1].id) if products and has_more else None
        
        return CursorPaginatedResponse(
            items=[ProductResponse.from_document(p) for p in products],
            next_cursor=next_cursor,
            has_more=has_more,
            count=len(products)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cursor pagination failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


# ============================================================================
# PATTERN 5: Autocomplete/Suggestions
# ============================================================================

class AutocompleteResponse(BaseModel):
    suggestions: List[str]

@router.get("/products/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_products(
    q: str = Query(..., min_length=2, max_length=50, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions")
):
    """
    Fast autocomplete for product names.
    
    Example: GET /api/products/autocomplete?q=lap&limit=5
    
    Returns only product names that start with the query.
    Optimized for speed - returns only names, not full objects.
    """
    try:
        # Find products where name starts with query (case-insensitive)
        products = await Product.find(
            And(
                RegEx(Product.name, f"^{q}", options="i"),
                Product.is_active == True
            )
        ).limit(limit).to_list()
        
        # Extract unique names
        suggestions = list(set([p.name for p in products]))[:limit]
        
        return AutocompleteResponse(suggestions=suggestions)
    
    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Autocomplete failed"
        )


# ============================================================================
# PATTERN 6: Infinite Scroll
# ============================================================================

class InfiniteScrollResponse(BaseModel):
    items: List[ProductResponse]
    last_id: Optional[str]
    has_more: bool

@router.get("/products/infinite", response_model=InfiniteScrollResponse)
async def infinite_scroll(
    last_id: Optional[str] = Query(None, description="ID of last item from previous request"),
    limit: int = Query(20, ge=1, le=50, description="Number of items")
):
    """
    Infinite scroll pagination.
    
    Example:
    First load: GET /api/products/infinite?limit=20
    Load more: GET /api/products/infinite?last_id=<last_id>&limit=20
    
    Client keeps track of last_id and requests more items as user scrolls.
    """
    try:
        from bson import ObjectId
        
        if last_id:
            try:
                last_obj_id = ObjectId(last_id)
                query = Product.find(
                    And(
                        Product.id > last_obj_id,
                        Product.is_active == True
                    )
                )
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid last_id")
        else:
            query = Product.find(Product.is_active == True)
        
        # Sort by ID (creation order)
        products = await query.sort("+_id").limit(limit).to_list()
        
        return InfiniteScrollResponse(
            items=[ProductResponse.from_document(p) for p in products],
            last_id=str(products[-1].id) if products else None,
            has_more=len(products) == limit
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Infinite scroll failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load more items"
        )


# ============================================================================
# PATTERN 7: Faceted Search (with Counts)
# ============================================================================

class FacetCount(BaseModel):
    value: str
    count: int

class FacetsResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    facets: dict

@router.get("/products/facets", response_model=FacetsResponse)
async def faceted_search(
    q: Optional[str] = Query(None, min_length=2, max_length=100),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Faceted search with filter counts.
    
    Example: GET /api/products/facets?q=laptop
    
    Returns:
    - Matching products
    - Total count
    - Facets (category counts, price ranges, etc.)
    
    Useful for building filter UI with counts.
    """
    try:
        conditions = [Product.is_active == True]
        
        # Search query
        if q:
            conditions.append(
                Or(
                    RegEx(Product.name, q, options="i"),
                    RegEx(Product.description, q, options="i")
                )
            )
        
        if category:
            conditions.append(Product.category == category)
        
        query_filter = And(*conditions) if len(conditions) > 1 else conditions[0]
        
        # Get products
        skip = (page - 1) * page_size
        products = await Product.find(query_filter).skip(skip).limit(page_size).to_list()
        total = await Product.find(query_filter).count()
        
        # Get category facets (aggregation)
        pipeline = [
            {"$match": query_filter.to_dict()},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_facets = await Product.aggregate(pipeline).to_list()
        
        # Format facets
        facets = {
            "categories": [
                {"value": f["_id"], "count": f["count"]}
                for f in category_facets
            ]
        }
        
        return FacetsResponse(
            products=[ProductResponse.from_document(p) for p in products],
            total=total,
            facets=facets
        )
    
    except Exception as e:
        logger.error(f"Faceted search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Faceted search failed"
        )


# ============================================================================
# APP SETUP
# ============================================================================

app.include_router(router)


@app.get("/")
async def root():
    """API information and available endpoints"""
    return {
        "message": "Search & Pagination Best Practices API",
        "docs": "/docs",
        "patterns": {
            "basic_pagination": "GET /api/products/basic?page=1&page_size=20",
            "filtering": "GET /api/products/filter?category=electronics&min_price=100",
            "complete_search": "GET /api/products/search?q=laptop&category=electronics&sort_by=price&order=asc",
            "cursor_pagination": "GET /api/products/cursor?limit=20",
            "autocomplete": "GET /api/products/autocomplete?q=lap",
            "infinite_scroll": "GET /api/products/infinite?limit=20",
            "faceted_search": "GET /api/products/facets?q=laptop"
        },
        "features": [
            "Offset-based pagination (page + page_size)",
            "Cursor-based pagination (efficient for large datasets)",
            "Full-text search",
            "Multiple filters (category, price, stock, tags)",
            "Flexible sorting",
            "Autocomplete suggestions",
            "Infinite scroll",
            "Faceted search with counts"
        ]
    }


# Database initialization (call this on startup)
async def init_db():
    """Initialize database connection and Beanie"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.products_db,
        document_models=[Product]
    )


@app.on_event("startup")
async def startup_event():
    """Startup event to initialize database"""
    # Uncomment to enable database
    # await init_db()
    logger.info("Application started")


# ============================================================================
# USAGE NOTES
# ============================================================================

"""
KEY TAKEAWAYS:

1. PAGINATION TYPES
   - Offset-based (page + page_size): Most common, good for < 10k items
   - Cursor-based (cursor + limit): Efficient for large datasets, consistent results
   - Infinite scroll: UX pattern, uses cursor or last_id

2. FILTERING
   - Use Query parameters for all filters
   - Validate: min_length, max_length, ge, le
   - Limit array sizes: max_items
   - Build conditions list and use And(*conditions)

3. SORTING
   - Use Enums for allowed sort fields
   - Prefix with + (asc) or - (desc)
   - Default sort for consistency
   - Index sorted fields in database

4. SEARCH
   - RegEx for text search (case-insensitive with options="i")
   - Use Or() to search multiple fields
   - Escape user input to prevent regex DoS
   - Consider MongoDB text indexes for better performance

5. PERFORMANCE
   - Add database indexes for filtered/sorted fields
   - Use projection to fetch only needed fields
   - Cache expensive queries (facets, counts)
   - Consider skipping total count if not needed

6. SECURITY
   - Limit max page_size (le=100)
   - Validate search query length
   - Limit filter array sizes
   - Rate limit search endpoints
   - Sanitize regex inputs

7. RESPONSE STRUCTURE
   - Include metadata: total, page, total_pages, has_next, has_prev
   - Use generic PaginatedResponse[T] for consistency
   - Provide navigation info for better UX

8. BEST PRACTICES
   - Always use dependencies for reusable logic
   - Consistent error handling with try/except
   - Log errors for debugging
   - Validate all inputs
   - Default sorting for consistent results
   - Return appropriate HTTP status codes

COPY THESE PATTERNS TO YOUR PROJECT AND ADAPT AS NEEDED!
"""
