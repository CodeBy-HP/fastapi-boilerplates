"""
Production-Ready Pydantic Schema Examples

This file demonstrates all common patterns for Pydantic schemas in FastAPI.
Each example is production-ready and can be copied directly to your project.

USAGE:
1. Copy the pattern that matches your use case
2. Adapt field names and validation rules
3. Use in your FastAPI routes

Key Concepts:
- Create Schema: Input for POST (all fields required)
- Update Schema: Input for PUT/PATCH (all fields optional)
- Response Schema: Output (includes ID, timestamps, computed fields)
- Base Schema: Shared fields (DRY principle)
- Validators: Field and model-level validation
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import (
    BaseModel, 
    Field, 
    EmailStr, 
    field_validator, 
    model_validator,
    computed_field,
    ConfigDict
)
from typing import Optional, List, Generic, TypeVar, Literal
from datetime import datetime
from enum import Enum
import re

app = FastAPI(
    title="Pydantic Schema Best Practices",
    description="Production-ready schema patterns",
    version="1.0.0"
)


# ============================================================================
# PATTERN 1: Basic CRUD Schemas
# ============================================================================

class ProductCreate(BaseModel):
    """Schema for creating a product"""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product name"
    )
    
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Product description"
    )
    
    price: float = Field(
        ...,
        gt=0,
        description="Product price (must be positive)"
    )
    
    stock: int = Field(
        ...,
        ge=0,
        description="Stock quantity (non-negative)"
    )
    
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product category"
    )
    
    # Field validator - clean whitespace
    @field_validator("name", "category", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace"""
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or whitespace only")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Gaming Laptop",
                "description": "High-performance gaming laptop with RTX 4080",
                "price": 1299.99,
                "stock": 50,
                "category": "Electronics"
            }
        }
    )


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional for PATCH)"""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Product name"
    )
    
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Product description"
    )
    
    price: Optional[float] = Field(
        None,
        gt=0,
        description="Product price"
    )
    
    stock: Optional[int] = Field(
        None,
        ge=0,
        description="Stock quantity"
    )
    
    category: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Product category"
    )
    
    # Handle optional fields in validator
    @field_validator("name", "category", "description")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Remove whitespace if value provided"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or whitespace only")
            return v
        return None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price": 999.99,
                "stock": 45
            }
        }
    )


class ProductResponse(BaseModel):
    """Schema for product API response"""
    
    id: str = Field(..., description="Product ID")
    name: str
    description: str
    price: float
    stock: int
    category: str
    created_at: datetime
    updated_at: datetime
    
    # Computed fields - not stored in DB
    @computed_field
    @property
    def in_stock(self) -> bool:
        """Whether product is currently in stock"""
        return self.stock > 0
    
    @computed_field
    @property
    def formatted_price(self) -> str:
        """Formatted price with currency symbol"""
        return f"${self.price:,.2f}"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Gaming Laptop",
                "description": "High-performance gaming laptop with RTX 4080",
                "price": 1299.99,
                "stock": 50,
                "category": "Electronics",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "in_stock": True,
                "formatted_price": "$1,299.99"
            }
        }
    )


# ============================================================================
# PATTERN 2: Base Schema (DRY Principle)
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields"""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="Valid email address")
    full_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Username must be alphanumeric with underscores/hyphens"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower()


class UserCreate(UserBase):
    """Schema for user registration"""
    
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password must contain uppercase, lowercase, and digit"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "SecurePass123"
            }
        }
    )


class UserUpdate(UserBase):
    """Schema for updating user (all fields optional)"""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)


class UserRole(str, Enum):
    """User roles enum"""
    admin = "admin"
    moderator = "moderator"
    user = "user"


class UserResponse(UserBase):
    """Schema for user response (no password!)"""
    
    id: str
    role: UserRole = UserRole.user
    is_active: bool = True
    created_at: datetime
    
    # ✅ Never include password_hash or sensitive data in response!
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


# ============================================================================
# PATTERN 3: Nested Schemas
# ============================================================================

class Address(BaseModel):
    """Address schema"""
    
    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    country: str = Field(..., min_length=2, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "USA"
            }
        }
    )


class UserProfileResponse(UserResponse):
    """User profile with address"""
    
    address: Optional[Address] = None
    bio: Optional[str] = Field(None, max_length=500)


class OrderItem(BaseModel):
    """Single order item"""
    
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit_price: float = Field(..., gt=0, description="Price per unit")
    
    @computed_field
    @property
    def total_price(self) -> float:
        """Total price for this item"""
        return self.quantity * self.unit_price
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "prod-123",
                "product_name": "Gaming Laptop",
                "quantity": 2,
                "unit_price": 1299.99,
                "total_price": 2599.98
            }
        }
    )


class OrderStatus(str, Enum):
    """Order status enum"""
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderResponse(BaseModel):
    """Order with multiple items"""
    
    id: str
    user_id: str
    items: List[OrderItem] = Field(..., min_length=1, description="Order items")
    status: OrderStatus = OrderStatus.pending
    created_at: datetime
    
    @computed_field
    @property
    def total_amount(self) -> float:
        """Total order amount"""
        return sum(item.total_price for item in self.items)
    
    @computed_field
    @property
    def item_count(self) -> int:
        """Total number of items"""
        return sum(item.quantity for item in self.items)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "order-123",
                "user_id": "user-456",
                "items": [
                    {
                        "product_id": "prod-1",
                        "product_name": "Laptop",
                        "quantity": 1,
                        "unit_price": 999.99
                    }
                ],
                "status": "pending",
                "created_at": "2024-01-15T10:30:00Z",
                "total_amount": 999.99,
                "item_count": 1
            }
        }
    )


# ============================================================================
# PATTERN 4: Model Validators (Cross-Field Validation)
# ============================================================================

class DateRangeFilter(BaseModel):
    """Date range filter with validation"""
    
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    
    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRangeFilter":
        """Ensure end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        
        # Optional: Limit range to prevent abuse
        delta = self.end_date - self.start_date
        if delta.days > 365:
            raise ValueError("Date range cannot exceed 1 year")
        
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            }
        }
    )


class PasswordReset(BaseModel):
    """Password reset with confirmation"""
    
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordReset":
        """Ensure passwords match"""
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password strength validation"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class DiscountProduct(BaseModel):
    """Product with optional discount"""
    
    name: str
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = Field(None, gt=0)
    
    @model_validator(mode="after")
    def validate_discount(self) -> "DiscountProduct":
        """Ensure discount price is less than regular price"""
        if self.discount_price is not None:
            if self.discount_price >= self.price:
                raise ValueError("Discount price must be less than regular price")
        return self


# ============================================================================
# PATTERN 5: Generic Responses
# ============================================================================

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=1, description="Total number of pages")
    items: List[T] = Field(..., description="Items in current page")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "items": []
            }
        }
    )


class MessageResponse(BaseModel):
    """Generic message response"""
    
    message: str = Field(..., description="Response message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class ErrorDetail(BaseModel):
    """Validation error detail"""
    
    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """Detailed error response"""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Validation errors")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": [
                    {"field": "email", "message": "Invalid email format"},
                    {"field": "age", "message": "Must be at least 18"}
                ]
            }
        }
    )


# ============================================================================
# PATTERN 6: Conditional Fields & Complex Validation
# ============================================================================

class PaymentMethod(str, Enum):
    """Payment method options"""
    credit_card = "credit_card"
    paypal = "paypal"
    bank_transfer = "bank_transfer"


class PaymentCreate(BaseModel):
    """Payment with conditional required fields"""
    
    amount: float = Field(..., gt=0, description="Payment amount")
    method: PaymentMethod = Field(..., description="Payment method")
    
    # Credit card fields (optional, required if method is credit_card)
    card_number: Optional[str] = Field(None, pattern=r"^\d{16}$")
    card_expiry: Optional[str] = Field(None, pattern=r"^\d{2}/\d{2}$")
    card_cvv: Optional[str] = Field(None, pattern=r"^\d{3,4}$")
    
    # PayPal fields
    paypal_email: Optional[EmailStr] = None
    
    # Bank transfer fields
    account_number: Optional[str] = None
    routing_number: Optional[str] = Field(None, pattern=r"^\d{9}$")
    
    @model_validator(mode="after")
    def validate_payment_method(self) -> "PaymentCreate":
        """Ensure required fields for selected payment method"""
        
        if self.method == PaymentMethod.credit_card:
            if not all([self.card_number, self.card_expiry, self.card_cvv]):
                raise ValueError("Credit card details required for credit card payment")
        
        elif self.method == PaymentMethod.paypal:
            if not self.paypal_email:
                raise ValueError("PayPal email required for PayPal payment")
        
        elif self.method == PaymentMethod.bank_transfer:
            if not all([self.account_number, self.routing_number]):
                raise ValueError("Bank account details required for bank transfer")
        
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "amount": 99.99,
                    "method": "credit_card",
                    "card_number": "4532015112830366",
                    "card_expiry": "12/25",
                    "card_cvv": "123"
                },
                {
                    "amount": 99.99,
                    "method": "paypal",
                    "paypal_email": "user@example.com"
                }
            ]
        }
    )


# ============================================================================
# PATTERN 7: File Upload Metadata
# ============================================================================

class FileUpload(BaseModel):
    """File upload metadata with validation"""
    
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., ge=0, le=10_485_760, description="File size (max 10MB)")
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Sanitize filename - remove unsafe characters"""
        # Remove path separators and dangerous characters
        v = re.sub(r'[/\\:*?"<>|]', '', v)
        # Remove leading/trailing spaces and dots
        v = v.strip('. ')
        
        if not v:
            raise ValueError("Invalid filename")
        
        return v
    
    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Only allow specific file types"""
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/pdf",
            "application/zip"
        ]
        
        if v not in allowed_types:
            raise ValueError(f"File type not allowed. Allowed: {', '.join(allowed_types)}")
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "document.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1048576
            }
        }
    )


# ============================================================================
# PATTERN 8: Tags and Lists
# ============================================================================

class BlogPostCreate(BaseModel):
    """Blog post with tags"""
    
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    tags: List[str] = Field(default_factory=list, max_length=10)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Clean and deduplicate tags"""
        # Clean each tag
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in cleaned:
            if tag not in seen and len(tag) <= 50:  # Max tag length
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags
    
    @field_validator("title", "content")
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        """Remove HTML tags from text"""
        v = re.sub(r'<[^>]+>', '', v)
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Introduction to FastAPI",
                "content": "FastAPI is a modern web framework...",
                "tags": ["python", "fastapi", "tutorial"]
            }
        }
    )


# ============================================================================
# APP ROUTES (Examples of using schemas)
# ============================================================================

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    """Create a new product"""
    # Simulate database creation
    product_data = product.model_dump()
    product_data["id"] = "507f1f77bcf86cd799439011"
    product_data["created_at"] = datetime.utcnow()
    product_data["updated_at"] = datetime.utcnow()
    
    return ProductResponse(**product_data)


@app.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductUpdate):
    """Update a product (partial update)"""
    # Get fields that were actually provided
    update_data = product.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    # Simulate database update
    existing_product = {
        "id": product_id,
        "name": "Gaming Laptop",
        "description": "High-performance laptop",
        "price": 1299.99,
        "stock": 50,
        "category": "Electronics",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    existing_product.update(update_data)
    existing_product["updated_at"] = datetime.utcnow()
    
    return ProductResponse(**existing_product)


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Register a new user"""
    # In production: hash password, check for duplicates
    user_data = user.model_dump(exclude={"password"})
    user_data["id"] = "user-123"
    user_data["role"] = UserRole.user
    user_data["is_active"] = True
    user_data["created_at"] = datetime.utcnow()
    
    return UserResponse(**user_data)


@app.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(page: int = 1, page_size: int = 20):
    """List products with pagination"""
    # Simulate database query
    products = []  # Your products here
    
    return PaginatedResponse(
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
        items=products
    )


@app.get("/")
async def root():
    """API information"""
    return {
        "message": "Pydantic Schema Best Practices API",
        "docs": "/docs",
        "patterns": [
            "Basic CRUD schemas (Create/Update/Response)",
            "Base schemas for DRY code",
            "Nested schemas (relationships)",
            "Model validators (cross-field validation)",
            "Generic responses (paginated, message, error)",
            "Conditional fields (payment methods)",
            "File upload metadata",
            "Tags and lists with validation"
        ]
    }


# ============================================================================
# USAGE NOTES
# ============================================================================

"""
KEY TAKEAWAYS:

1. SCHEMA SEPARATION
   - Create: All fields required, for POST
   - Update: All fields optional, for PATCH
   - Response: Includes ID, timestamps, computed fields
   - Base: Shared fields across schemas (DRY)

2. FIELD VALIDATION
   - Use Field() for constraints (min_length, max_length, gt, ge, lt, le)
   - @field_validator for custom validation (cleaning, normalization)
   - Apply to multiple fields: @field_validator("name", "email")

3. MODEL VALIDATION
   - @model_validator for cross-field validation
   - mode="after" to validate after field validation
   - Returns self to allow chaining

4. COMPUTED FIELDS
   - @computed_field for derived values
   - Not stored in database
   - Calculated on-the-fly
   - Use @property for read-only

5. CONFIGURATION
   - model_config with ConfigDict
   - json_schema_extra for OpenAPI examples
   - populate_by_name for alias support
   - validate_assignment for runtime validation

6. SECURITY
   - Never expose password_hash in responses
   - Validate string lengths (prevent DoS)
   - Validate numeric ranges
   - Sanitize user input (HTML tags)
   - Use Enums for fixed values

7. BEST PRACTICES
   - Always add descriptions
   - Provide examples for documentation
   - Use EmailStr for emails
   - Use Enums for status/role fields
   - Normalize data (lowercase emails, strip whitespace)
   - Validate cross-field constraints

8. COMMON PATTERNS
   - Paginated responses with Generic[T]
   - Nested schemas for relationships
   - Conditional required fields
   - File upload metadata
   - Date range validation
   - Password confirmation

COPY THESE PATTERNS TO YOUR PROJECT AND ADAPT AS NEEDED!
"""
