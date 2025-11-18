"""
Production-Ready Example: Computed Fields in FastAPI + Beanie

This file contains everything you need:
- Model with computed fields
- Input/Output schemas
- API routes with best practices

USAGE:
1. Copy this file to your project
2. Adapt the Product model to your domain (User, Order, Subscription, etc.)
3. Follow the same patterns for your other models

Run with:
    uvicorn example:app --reload
"""

from fastapi import FastAPI, APIRouter, HTTPException, Query
from beanie import Document, init_beanie
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator, ConfigDict
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager


# ============================================================================
# 1. DATABASE MODEL (What goes in MongoDB)
# ============================================================================

class Product(Document):
    """
    Production-ready Product model demonstrating computed fields best practices.
    
    Key Principles:
    1. DON'T store derived values (in_stock) - calculate on-the-fly
    2. DO store raw data (quantity, price) that may change independently
    3. Use @computed_field for automatic API serialization
    4. Use validators for data normalization BEFORE saving
    """
    
    # === STORED FIELDS (Persisted in Database) ===
    name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=150)
    price: float = Field(..., gt=0, description="Must be positive")
    quantity: int = Field(..., ge=0, description="Current stock")
    cost: float = Field(..., gt=0, description="Wholesale cost")
    
    # Optional fields with defaults
    low_stock_threshold: int = Field(default=5, ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # === FIELD VALIDATORS (Run BEFORE saving to DB) ===
    @field_validator('name', 'category')
    @classmethod
    def normalize_text(cls, v: str) -> str:
        """Ensure consistent text formatting"""
        return v.strip().title()
    
    @field_validator('price', 'cost')
    @classmethod
    def round_money(cls, v: float) -> float:
        """Always store money with 2 decimal places"""
        return round(v, 2)
    
    # === MODEL VALIDATORS (Run AFTER field validation) ===
    @model_validator(mode='after')
    def update_timestamp(self):
        """Auto-update timestamp on any change"""
        self.last_updated = datetime.utcnow()
        return self
    
    @model_validator(mode='after')
    def validate_profit_margin(self):
        """Ensure we're not selling at a loss"""
        if self.price < self.cost:
            raise ValueError(f"Price ({self.price}) cannot be less than cost ({self.cost})")
        return self
    
    # === COMPUTED FIELDS (NOT stored in DB, calculated on-the-fly) ===
    @computed_field
    @property
    def in_stock(self) -> bool:
        """
        ✅ Perfect use of computed field
        - Simple calculation from existing field
        - Always accurate, no sync issues
        - Automatically appears in API responses
        """
        return self.quantity > 0
    
    @computed_field
    @property
    def stock_status(self) -> str:
        """More detailed status for UI"""
        if self.quantity == 0:
            return "out_of_stock"
        elif self.quantity <= self.low_stock_threshold:
            return "low_stock"
        else:
            return "in_stock"
    
    @computed_field
    @property
    def total_value(self) -> float:
        """Total inventory value (for financial reports)"""
        return round(self.cost * self.quantity, 2)
    
    @computed_field
    @property
    def profit_margin(self) -> float:
        """Profit margin percentage"""
        if self.price == 0:
            return 0.0
        return round(((self.price - self.cost) / self.price) * 100, 2)
    
    # === INTERNAL HELPERS (Not in API responses) ===
    @property
    def needs_restock(self) -> bool:
        """Internal business logic - not exposed in API"""
        return self.quantity < self.low_stock_threshold
    
    # === BEANIE CONFIGURATION ===
    class Settings:
        name = "products"
        indexes = [
            "category",
            "quantity",  # For fast in_stock queries
        ]


# ============================================================================
# 2. API SCHEMAS (What goes in/out of API)
# ============================================================================

# --- INPUT SCHEMAS (What users send) ---

class ProductCreate(BaseModel):
    """
    Schema for creating products.
    
    NOTICE: No computed fields (in_stock, stock_status, etc.)
    Users can't set these - they're calculated automatically!
    """
    name: str = Field(..., min_length=1, max_length=150, examples=["Gaming Laptop"])
    category: str = Field(..., min_length=1, max_length=150, examples=["Electronics"])
    price: float = Field(..., gt=0, examples=[1299.99])
    quantity: int = Field(..., ge=0, examples=[15])
    cost: float = Field(..., gt=0, examples=[800.00])
    low_stock_threshold: int = Field(default=5, ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Gaming Laptop",
                "category": "Electronics",
                "price": 1299.99,
                "quantity": 15,
                "cost": 800.00,
                "low_stock_threshold": 5
            }
        }
    )


class ProductUpdate(BaseModel):
    """
    Schema for updating products.
    All fields optional for partial updates.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, min_length=1, max_length=150)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    cost: Optional[float] = Field(None, gt=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)


# --- OUTPUT SCHEMAS (What API returns) ---

class ProductResponse(BaseModel):
    """
    Schema for product responses.
    INCLUDES all computed fields automatically!
    """
    id: str = Field(..., alias="_id")
    name: str
    category: str
    price: float
    quantity: int
    cost: float
    low_stock_threshold: int
    
    # Computed fields (from @computed_field in model)
    in_stock: bool
    stock_status: str
    total_value: float
    profit_margin: float
    
    # Timestamps
    last_updated: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Gaming Laptop",
                "category": "Electronics",
                "price": 1299.99,
                "quantity": 15,
                "cost": 800.00,
                "low_stock_threshold": 5,
                "in_stock": True,
                "stock_status": "in_stock",
                "total_value": 12000.00,
                "profit_margin": 38.46,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
    )


class ProductListResponse(BaseModel):
    """Response for paginated lists"""
    total: int
    page: int
    page_size: int
    products: list[ProductResponse]


# --- SPECIALIZED SCHEMAS ---

class StockAdjustment(BaseModel):
    """Dedicated schema for stock operations"""
    adjustment: int = Field(..., description="Positive to add, negative to remove")
    reason: Optional[str] = Field(None, max_length=200)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "adjustment": 50,
                "reason": "New shipment received"
            }
        }
    )


# ============================================================================
# 3. API ROUTES (How to use the model)
# ============================================================================

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(product_data: ProductCreate):
    """
    Create a new product.
    
    The response automatically includes computed fields!
    """
    product = Product(**product_data.model_dump())
    await product.insert()
    return product


@router.get("/", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List products with filtering.
    
    IMPORTANT: Filter by 'in_stock' using the source field 'quantity'
    since in_stock is computed and not stored in DB.
    """
    query = {}
    
    if category:
        query["category"] = category
    
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    # Query source field 'quantity' to filter by computed 'in_stock'
    if in_stock_only is True:
        query["quantity"] = {"$gt": 0}
    elif in_stock_only is False:
        query["quantity"] = 0
    
    total = await Product.find(query).count()
    skip = (page - 1) * page_size
    products = await Product.find(query).skip(skip).limit(page_size).to_list()
    
    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        products=products
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a single product by ID"""
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, update_data: ProductUpdate):
    """
    Update a product.
    
    Computed fields recalculate automatically after update!
    """
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(product, field, value)
    
    await product.save()
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str):
    """Delete a product"""
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await product.delete()


@router.post("/{product_id}/adjust-stock", response_model=ProductResponse)
async def adjust_stock(product_id: str, adjustment: StockAdjustment):
    """
    Adjust product stock (add or remove).
    
    Production pattern: Dedicated endpoint for specific operations.
    Response includes updated in_stock and stock_status automatically!
    """
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_quantity = product.quantity + adjustment.adjustment
    
    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove {abs(adjustment.adjustment)} items. Only {product.quantity} in stock."
        )
    
    product.quantity = new_quantity
    await product.save()
    
    return product


@router.get("/reports/low-stock", response_model=list[ProductResponse])
async def get_low_stock_products():
    """
    Get products with low stock.
    
    Query by source fields, response includes computed stock_status.
    """
    products = await Product.find({
        "quantity": {"$gt": 0},
        "$expr": {"$lte": ["$quantity", "$low_stock_threshold"]}
    }).to_list()
    
    return products


@router.get("/reports/out-of-stock", response_model=list[ProductResponse])
async def get_out_of_stock_products():
    """Get products that are out of stock"""
    products = await Product.find({"quantity": 0}).to_list()
    return products


# ============================================================================
# 4. APP SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database connection"""
    # Startup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.products_db, document_models=[Product])
    yield
    # Shutdown
    client.close()


app = FastAPI(
    title="Computed Fields Example",
    description="Production-ready patterns for computed fields in FastAPI + Beanie",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/")
async def root():
    """API info"""
    return {
        "message": "Computed Fields Example API",
        "docs": "/docs",
        "examples": {
            "create": "POST /products",
            "list": "GET /products",
            "filter_in_stock": "GET /products?in_stock_only=true",
            "adjust_stock": "POST /products/{id}/adjust-stock"
        }
    }


# ============================================================================
# 5. USAGE NOTES
# ============================================================================

"""
KEY TAKEAWAYS:

1. COMPUTED FIELDS
   - Use @computed_field for values derived from stored fields
   - They appear in API responses automatically
   - Always accurate, no sync issues

2. VALIDATORS
   - @field_validator: Normalize/validate BEFORE saving
   - @model_validator: Cross-field validation

3. QUERYING
   - Query by SOURCE fields (quantity), not computed (in_stock)
   - Index source fields for performance

4. SCHEMAS
   - Input: Only fields users can set
   - Output: Includes computed fields
   - Separate them for clean API contracts

5. WHEN TO STORE
   - Historical snapshots (order_total_at_purchase)
   - Values that shouldn't change with source
   - Everything else: compute it!

COPY THIS FILE AND ADAPT TO YOUR DOMAIN:
- Change Product to User, Order, Subscription, etc.
- Add your own computed fields
- Follow the same patterns
"""
