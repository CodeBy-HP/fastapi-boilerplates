"""
Production-Ready Try-Except Patterns for FastAPI

This file contains working examples of exception handling patterns.
Each example demonstrates a different scenario with best practices.

USAGE:
1. Copy the pattern that matches your use case
2. Adapt to your specific needs
3. Always follow the golden rules

Run with:
    uvicorn example:app --reload
"""

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from datetime import datetime
import logging
import httpx
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM EXCEPTIONS (Reusable across application)
# ============================================================================

class ProductNotFoundError(Exception):
    """Raised when product doesn't exist"""
    pass

class InsufficientStockError(Exception):
    """Raised when product is out of stock"""
    pass

class InvalidProductIDError(Exception):
    """Raised when product ID format is invalid"""
    pass


# ============================================================================
# MOCK MODELS (Replace with your actual models)
# ============================================================================

class Product(BaseModel):
    id: str
    name: str
    price: float
    stock: int

class User(BaseModel):
    id: str
    email: str
    name: str

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    in_stock: bool

class OrderCreate(BaseModel):
    user_id: str
    product_id: str
    quantity: int


# ============================================================================
# PATTERN 1: Standard Try-Except Structure
# ============================================================================

router = APIRouter(prefix="/api", tags=["examples"])

@router.get("/products/{product_id}")
async def get_product_by_id(product_id: str) -> ProductResponse:
    """
    Standard pattern for most endpoints.
    
    Key points:
    - Validate input and raise HTTPException for user errors
    - Re-raise HTTPException immediately
    - Log and mask unexpected errors
    """
    try:
        # 1. Input validation
        if not product_id or len(product_id) < 3:
            raise HTTPException(
                status_code=400,
                detail="Invalid product ID format"
            )
        
        # 2. Database query (simulated)
        # In real code: product = await Product.get(product_id)
        product = None  # Simulate not found
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )
        
        # 3. Return success response
        return ProductResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            in_stock=product.stock > 0
        )
    
    except HTTPException:
        # ✅ ALWAYS re-raise HTTPException - don't wrap them!
        raise
    
    except Exception as e:
        # ✅ Log unexpected errors with full context
        logger.error(
            f"Unexpected error getting product {product_id}: {e}",
            exc_info=True  # Include full traceback
        )
        # ✅ Return generic message (security!)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ============================================================================
# PATTERN 2: Nested Try-Except for Complex Operations
# ============================================================================

@router.post("/orders")
async def create_order(order_data: OrderCreate):
    """
    Nested try-except for operations with multiple failure points.
    Each operation has specific error handling.
    """
    try:
        # Validate user
        try:
            # user = await User.get(order_data.user_id)
            user = None  # Simulate
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User lookup failed for {order_data.user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="User validation failed"
            )
        
        # Validate product and stock
        try:
            # product = await Product.get(order_data.product_id)
            product = Product(id="1", name="Test", price=10.0, stock=5)
            
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail="Product not found"
                )
            
            if product.stock < order_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Available: {product.stock}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Product validation failed for {order_data.product_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Product validation failed"
            )
        
        # Create order
        try:
            # order = Order(**order_data.model_dump())
            # await order.insert()
            order_id = "ORDER123"
            logger.info(f"Order created: {order_id}")
            
            return {
                "order_id": order_id,
                "status": "created",
                "message": "Order created successfully"
            }
        except Exception as e:
            logger.error(f"Order creation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to create order"
            )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in create_order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# PATTERN 3: Custom Exceptions for Business Logic
# ============================================================================

async def get_product_or_fail(product_id: str) -> Product:
    """
    Reusable business logic with custom exceptions.
    Can be called from multiple endpoints.
    """
    if not product_id or len(product_id) < 3:
        raise InvalidProductIDError(f"Invalid product ID: {product_id}")
    
    # Simulate database query
    product = None
    
    if not product:
        raise ProductNotFoundError(f"Product {product_id} not found")
    
    return product


@router.get("/products/{product_id}/details")
async def get_product_details(product_id: str):
    """
    Using custom exceptions for clean separation of concerns.
    """
    try:
        product = await get_product_or_fail(product_id)
        return product
    
    except InvalidProductIDError as e:
        # ✅ Specific exception -> specific status code
        raise HTTPException(status_code=400, detail=str(e))
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# PATTERN 4: External API Calls
# ============================================================================

@router.get("/weather/{city}")
async def get_weather(city: str):
    """
    Exception handling for third-party API calls.
    Handles timeouts, API errors, and network issues.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"https://api.weather.example.com/v1/weather",
                    params={"city": city}
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.TimeoutException:
                logger.warning(f"Weather API timeout for city: {city}")
                raise HTTPException(
                    status_code=504,  # Gateway timeout
                    detail="Weather service is taking too long to respond"
                )
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Weather data not found for {city}"
                    )
                logger.error(f"Weather API error: {e}")
                raise HTTPException(
                    status_code=502,  # Bad gateway
                    detail="Weather service error"
                )
            
            except httpx.NetworkError as e:
                logger.error(f"Network error calling weather API: {e}")
                raise HTTPException(
                    status_code=503,  # Service unavailable
                    detail="Weather service temporarily unavailable"
                )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error fetching weather: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# PATTERN 5: File Upload with Error Handling
# ============================================================================

@router.post("/upload")
async def upload_file(file: UploadFile):
    """
    File operation error handling.
    Handles validation, permission, and storage errors.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided"
            )
        
        # Check file size
        max_size = 10_000_000  # 10MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size} bytes"
            )
        
        # Save file
        file_path = Path(f"uploads/{file.filename}")
        file_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
        except PermissionError:
            logger.error(f"Permission denied writing to {file_path}")
            raise HTTPException(
                status_code=500,
                detail="File save failed - insufficient permissions"
            )
        except OSError as e:
            logger.error(f"OS error saving file: {e}")
            raise HTTPException(
                status_code=500,
                detail="File save failed"
            )
        
        return {
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path)
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# PATTERN 6: Pydantic Validation Error Handling
# ============================================================================

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

@router.post("/products")
async def create_product(data: dict):
    """
    Explicit Pydantic validation with custom error messages.
    """
    try:
        # Parse and validate
        try:
            product_data = ProductCreate(**data)
        except ValidationError as e:
            # ✅ Validation errors are user errors - return 400
            logger.info(f"Validation error: {e.errors()}")
            raise HTTPException(
                status_code=400,
                detail=e.errors()  # Return detailed validation errors
            )
        
        # Additional business validation
        if product_data.price < 0.01:
            raise HTTPException(
                status_code=400,
                detail="Price must be at least $0.01"
            )
        
        # Create product (simulated)
        logger.info(f"Creating product: {product_data.name}")
        
        return {
            "id": "PROD123",
            **product_data.model_dump()
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error creating product: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# APP SETUP
# ============================================================================

app = FastAPI(
    title="Try-Except Best Practices",
    description="Production-ready exception handling patterns for FastAPI",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
async def root():
    """API info"""
    return {
        "message": "Try-Except Best Practices Examples",
        "docs": "/docs",
        "patterns": {
            "standard": "GET /api/products/{id}",
            "nested": "POST /api/orders",
            "custom_exceptions": "GET /api/products/{id}/details",
            "external_api": "GET /api/weather/{city}",
            "file_upload": "POST /api/upload",
            "validation": "POST /api/products"
        }
    }


# ============================================================================
# USAGE NOTES
# ============================================================================

"""
KEY TAKEAWAYS:

1. ALWAYS RE-RAISE HTTPException
   - Don't wrap them in generic Exception handlers
   - They represent intentional, specific errors

2. LOG INTERNAL ERRORS
   - Use exc_info=True for full traceback
   - Include context (user_id, product_id, etc.)
   - Never expose in client responses

3. USE SPECIFIC EXCEPTIONS
   - Catch specific types when possible
   - Create custom exceptions for business logic
   - Avoid bare except clauses

4. RETURN APPROPRIATE STATUS CODES
   - 400: Bad request (user error)
   - 404: Not found
   - 500: Internal server error
   - 502: Bad gateway (external API error)
   - 504: Gateway timeout

5. SECURITY FIRST
   - Never expose internal error details
   - Sanitize user input in logs
   - Use generic error messages for clients

COPY THESE PATTERNS AND ADAPT TO YOUR USE CASE!
"""
