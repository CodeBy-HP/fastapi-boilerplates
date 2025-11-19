"""
Production-Ready Path, Query & Body Parameter Examples

This file demonstrates all common patterns for parameter handling in FastAPI.
Each example is production-ready and can be copied directly to your project.

USAGE:
1. Copy the pattern that matches your use case
2. Adapt to your specific models and business logic
3. Run with: uvicorn example:app --reload

Key Concepts:
- Path: Resource identifiers in URL (/users/{user_id})
- Query: Filters and options after ? (?page=1&limit=20)
- Body: JSON payload for POST/PUT/PATCH
"""

from fastapi import FastAPI, APIRouter, HTTPException, Path, Query, Body
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from enum import Enum
from datetime import datetime

app = FastAPI(
    title="Path, Query & Body Best Practices",
    description="Production-ready parameter handling examples",
    version="1.0.0"
)

router = APIRouter(prefix="/api", tags=["examples"])


# ============================================================================
# PYDANTIC MODELS (Data Structures)
# ============================================================================

class ProductStatus(str, Enum):
    """Enum for product status - validates input"""
    active = "active"
    inactive = "inactive"
    archived = "archived"

class SortOrder(str, Enum):
    """Sort direction"""
    asc = "asc"
    desc = "desc"

class SortBy(str, Enum):
    """Fields to sort by"""
    name = "name"
    price = "price"
    created_at = "created_at"

class ProductCreate(BaseModel):
    """Schema for creating a product"""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    stock: int = Field(..., ge=0, description="Stock quantity")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Gaming Laptop",
                "price": 1299.99,
                "description": "High-performance gaming laptop",
                "category": "Electronics",
                "stock": 50
            }
        }
    }

class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional for PATCH)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatus] = None

class ProductResponse(BaseModel):
    """Response model for products"""
    id: str
    name: str
    price: float
    description: Optional[str]
    category: str
    stock: int
    status: ProductStatus
    created_at: datetime
    
    # Computed field
    @property
    def in_stock(self) -> bool:
        return self.stock > 0

class UserCreate(BaseModel):
    """User registration schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=13, le=150, description="Must be 13 or older")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com",
                "username": "johndoe",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "age": 25
            }
        }
    }

class Address(BaseModel):
    """Address schema"""
    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., pattern="^[0-9]{5}(-[0-9]{4})?$")


# ============================================================================
# PATTERN 1: Path Parameters Only
# ============================================================================

@router.get("/products/{product_id}")
async def get_product(
    product_id: str = Path(
        ...,
        min_length=3,
        max_length=50,
        description="Product ID",
        example="PROD-12345"
    )
):
    """
    Get a single product by ID.
    
    Example: GET /api/products/PROD-12345
    
    Path parameter:
    - Always required
    - Validated for length
    - Part of the URL itself
    """
    # Simulate database lookup
    # product = await Product.get(product_id)
    
    return {
        "product_id": product_id,
        "name": "Sample Product",
        "price": 99.99
    }


@router.get("/users/{user_id}/posts/{post_id}")
async def get_user_post(
    user_id: str = Path(..., description="User ID"),
    post_id: int = Path(..., ge=1, description="Post ID")
):
    """
    Multiple path parameters.
    
    Example: GET /api/users/USER123/posts/42
    
    Demonstrates hierarchical resource access.
    """
    return {
        "user_id": user_id,
        "post_id": post_id,
        "content": "Post content here"
    }


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str = Path(
        ...,
        regex="^ORD-[0-9]{6}$",
        description="Order ID (format: ORD-123456)"
    )
):
    """
    Path parameter with regex validation.
    
    Example: GET /api/orders/ORD-123456
    
    ❌ Invalid: /api/orders/123456 (missing prefix)
    ❌ Invalid: /api/orders/ORD-12 (wrong length)
    ✅ Valid: /api/orders/ORD-123456
    """
    return {"order_id": order_id}


# ============================================================================
# PATTERN 2: Query Parameters Only
# ============================================================================

@router.get("/products")
async def list_products(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, min_length=3, max_length=100, description="Search query")
):
    """
    List products with pagination and optional search.
    
    Examples:
    - GET /api/products
    - GET /api/products?page=2
    - GET /api/products?page=1&limit=50
    - GET /api/products?search=laptop&page=1
    
    Query parameters are optional (with defaults) or explicitly optional.
    """
    skip = (page - 1) * limit
    
    filters = {}
    if search:
        filters["search"] = search
    
    return {
        "page": page,
        "limit": limit,
        "skip": skip,
        "filters": filters,
        "items": []  # Your data here
    }


@router.get("/products/filter")
async def filter_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock status"),
    tags: List[str] = Query([], description="Filter by tags (can be multiple)"),
    sort_by: SortBy = Query(SortBy.created_at, description="Sort by field"),
    sort_order: SortOrder = Query(SortOrder.desc, description="Sort order")
):
    """
    Advanced filtering with multiple query parameters.
    
    Examples:
    - GET /api/products/filter?category=electronics
    - GET /api/products/filter?min_price=100&max_price=500
    - GET /api/products/filter?tags=sale&tags=new&tags=featured
    - GET /api/products/filter?in_stock=true&sort_by=price&sort_order=asc
    
    Demonstrates:
    - Optional filters
    - List parameters (tags)
    - Enum validation (sort_by, sort_order)
    - Boolean parameters
    """
    filters = {}
    
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if in_stock is not None:
        filters["in_stock"] = in_stock
    if tags:
        filters["tags"] = tags
    
    return {
        "filters": filters,
        "sort": {
            "by": sort_by.value,
            "order": sort_order.value
        }
    }


@router.get("/reports")
async def get_reports(
    start_date: str = Query(..., regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="End date (YYYY-MM-DD)")
):
    """
    Required query parameters.
    
    Example: GET /api/reports?start_date=2024-01-01&end_date=2024-12-31
    
    Both parameters are REQUIRED (using ... instead of default value).
    Validates date format with regex.
    """
    return {
        "start_date": start_date,
        "end_date": end_date,
        "report_type": "sales"
    }


# ============================================================================
# PATTERN 3: Body Parameters Only
# ============================================================================

@router.post("/products")
async def create_product(product: ProductCreate):
    """
    Create a new product using Pydantic model (RECOMMENDED).
    
    Request body:
    {
        "name": "Gaming Laptop",
        "price": 1299.99,
        "description": "High-performance gaming laptop",
        "category": "Electronics",
        "stock": 50
    }
    
    Pydantic automatically:
    - Validates all fields
    - Applies constraints (min_length, gt, etc.)
    - Converts types
    - Generates OpenAPI docs
    """
    # Simulate database insert
    product_id = "PROD-123456"
    
    return {
        "id": product_id,
        "message": "Product created successfully",
        **product.model_dump()
    }


@router.post("/users")
async def create_user(user: UserCreate):
    """
    Create a new user.
    
    Request body:
    {
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "full_name": "John Doe",
        "age": 25
    }
    
    Demonstrates:
    - Email validation (EmailStr)
    - Username pattern validation
    - Password length constraints
    - Optional age field with range validation
    """
    # In production: hash password, check for duplicates, etc.
    return {
        "message": "User created successfully",
        "username": user.username,
        "email": user.email
    }


@router.post("/login")
async def login(
    username: str = Body(..., min_length=3, max_length=50),
    password: str = Body(..., min_length=8),
    remember_me: bool = Body(False)
):
    """
    Login with explicit body parameters (alternative to Pydantic model).
    
    Request body:
    {
        "username": "johndoe",
        "password": "SecurePass123!",
        "remember_me": true
    }
    
    Use this pattern for simple cases or when you don't need a reusable model.
    """
    # In production: verify credentials, create session, etc.
    return {
        "message": "Login successful",
        "username": username,
        "remember_me": remember_me,
        "token": "fake-jwt-token"
    }


@router.post("/items/{item_id}/quantity")
async def update_quantity(
    item_id: str = Path(...),
    quantity: int = Body(..., embed=True, ge=1, description="New quantity")
):
    """
    Single body value with embed=True.
    
    Example: POST /api/items/ITEM123/quantity
    
    Request body (with embed=True):
    {
        "quantity": 10
    }
    
    Without embed=True, you'd send just: 10
    
    embed=True is useful for consistency when mixing with other body params.
    """
    return {
        "item_id": item_id,
        "new_quantity": quantity
    }


# ============================================================================
# PATTERN 4: Combining Path, Query & Body
# ============================================================================

@router.put("/products/{product_id}")
async def update_product(
    # PATH parameter - which resource to update
    product_id: str = Path(
        ...,
        regex="^PROD-[0-9]{6}$",
        description="Product ID (format: PROD-123456)"
    ),
    
    # BODY parameter - what to update
    product: ProductUpdate = Body(
        ...,
        description="Fields to update"
    ),
    
    # QUERY parameters - metadata/options
    notify_users: bool = Query(
        False,
        description="Send notification to subscribed users"
    ),
    audit_reason: Optional[str] = Query(
        None,
        max_length=200,
        description="Reason for update (for audit log)"
    )
):
    """
    Update a product - demonstrates all three parameter types.
    
    Example:
    PUT /api/products/PROD-123456?notify_users=true&audit_reason=Price%20correction
    
    Body:
    {
        "price": 999.99,
        "status": "active"
    }
    
    Parameters:
    - PATH: Product ID (which resource)
    - BODY: Fields to update (what to change)
    - QUERY: Options (how to process the update)
    """
    # Get update fields that were actually provided
    update_data = product.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided for update"
        )
    
    # Simulate database update
    # await Product.update(product_id, update_data)
    
    result = {
        "product_id": product_id,
        "updated_fields": list(update_data.keys()),
        "notify_users": notify_users
    }
    
    if audit_reason:
        result["audit_reason"] = audit_reason
    
    return result


@router.post("/users/{user_id}/addresses")
async def add_user_address(
    # PATH parameter
    user_id: str = Path(..., description="User ID"),
    
    # BODY parameter
    address: Address = Body(..., description="Address to add"),
    
    # QUERY parameter
    set_as_default: bool = Query(False, description="Set as default address")
):
    """
    Add address to user profile.
    
    Example:
    POST /api/users/USER123/addresses?set_as_default=true
    
    Body:
    {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001"
    }
    """
    return {
        "user_id": user_id,
        "address": address,
        "set_as_default": set_as_default,
        "message": "Address added successfully"
    }


@router.patch("/products/{product_id}")
async def partial_update_product(
    # PATH parameter
    product_id: str = Path(...),
    
    # BODY parameter - partial update (all optional)
    product: ProductUpdate = Body(...),
    
    # QUERY parameter
    validate_only: bool = Query(False, description="Only validate, don't save")
):
    """
    Partial update (PATCH) - only update provided fields.
    
    Example:
    PATCH /api/products/PROD-123456?validate_only=false
    
    Body (only update price):
    {
        "price": 899.99
    }
    
    All fields in ProductUpdate are optional, so you can update just one or more.
    """
    update_data = product.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided"
        )
    
    if validate_only:
        return {
            "valid": True,
            "would_update": list(update_data.keys())
        }
    
    # Simulate database update
    return {
        "product_id": product_id,
        "updated_fields": update_data,
        "message": "Product updated successfully"
    }


# ============================================================================
# PATTERN 5: Advanced - Dependency Injection for Common Params
# ============================================================================

class PaginationParams(BaseModel):
    """Reusable pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    
    def get_skip(self) -> int:
        return (self.page - 1) * self.limit

def pagination_params(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
) -> PaginationParams:
    """Dependency for pagination - can be reused across endpoints"""
    return PaginationParams(page=page, limit=limit)


@router.get("/items/paginated")
async def list_items_paginated(
    pagination: PaginationParams = Query(...)
):
    """
    Using query parameter dependency for reusable pagination.
    
    Example: GET /api/items/paginated?page=2&limit=50
    
    This pattern allows you to reuse pagination logic across endpoints.
    """
    return {
        "page": pagination.page,
        "limit": pagination.limit,
        "skip": pagination.get_skip(),
        "items": []
    }


# ============================================================================
# APP SETUP
# ============================================================================

app.include_router(router)


@app.get("/")
async def root():
    """API information and available endpoints"""
    return {
        "message": "Path, Query & Body Parameters Best Practices API",
        "docs": "/docs",
        "examples": {
            "path_only": "GET /api/products/{product_id}",
            "query_only": "GET /api/products?page=1&limit=20",
            "body_only": "POST /api/products",
            "combined": "PUT /api/products/{id}?notify=true",
            "filtering": "GET /api/products/filter?category=electronics&tags=sale",
            "multiple_path": "GET /api/users/{user_id}/posts/{post_id}",
            "partial_update": "PATCH /api/products/{id}"
        }
    }


# ============================================================================
# USAGE NOTES
# ============================================================================

"""
KEY TAKEAWAYS:

1. PATH PARAMETERS
   - Use for resource identifiers
   - Always required
   - Part of URL: /users/{user_id}
   - Validate with: min_length, max_length, regex, ge, le

2. QUERY PARAMETERS
   - Use for filters, pagination, sorting
   - Usually optional (can make required with ...)
   - After ?: /products?page=1&limit=20
   - Can be lists: ?tags=new&tags=sale

3. BODY PARAMETERS
   - Use for create/update operations
   - POST, PUT, PATCH methods
   - Prefer Pydantic models for structure
   - Validate complex data easily

4. BEST PRACTICES
   - Always add validation (ge, le, min_length, max_length, regex)
   - Always add descriptions for documentation
   - Use Enums for fixed choices
   - Use Pydantic models for complex body data
   - Think security - validate ranges and lengths
   - Make intentional choices about required vs optional

5. COMMON PATTERNS
   - GET /resource/{id} - Path only
   - GET /resources?filter=value - Query only
   - POST /resources - Body only
   - PUT /resources/{id}?option=true - All three combined

COPY THESE PATTERNS TO YOUR PROJECT AND ADAPT AS NEEDED!
"""
