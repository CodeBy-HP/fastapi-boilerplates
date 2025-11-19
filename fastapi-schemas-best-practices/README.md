# 📐 Pydantic Schemas Best Practices

Complete guide to building production-ready Pydantic schemas (models) for FastAPI applications.

## 📋 Quick Overview

| Schema Type | Purpose | When to Use |
|-------------|---------|-------------|
| **Create Schema** | Input for creating resources | POST endpoints |
| **Update Schema** | Input for updating resources | PUT/PATCH endpoints |
| **Response Schema** | Output returned to clients | All endpoints |
| **List Response** | Paginated list responses | List/search endpoints |
| **Base Schema** | Shared fields across schemas | DRY principle |

---

## 🎯 Why This Matters

### Common Challenges
- ❌ Exposing internal database fields to clients
- ❌ Duplicate validation logic across schemas
- ❌ No separation between input and output
- ❌ Inconsistent validation across endpoints
- ❌ Missing API documentation examples

### Solutions in This Guide
- ✅ Separate schemas for Create/Update/Response
- ✅ Reusable base schemas (DRY)
- ✅ Field validators for data cleaning
- ✅ Model validators for cross-field validation
- ✅ Proper alias handling for database fields
- ✅ OpenAPI examples for better docs
- ✅ Security best practices

---

## 📖 Table of Contents

1. [Schema Types](#schema-types)
2. [Field Validation](#field-validation)
3. [Model Validation](#model-validation)
4. [Base Schemas (DRY)](#base-schemas-dry)
5. [Response Schemas](#response-schemas)
6. [Nested Schemas](#nested-schemas)
7. [Common Patterns](#common-patterns)
8. [Security Best Practices](#security-best-practices)
9. [Configuration](#configuration)
10. [Advanced Patterns](#advanced-patterns)

---

## 📋 Schema Types

### 1. Create Schema (POST)

Used for creating new resources. All required fields.

```python
from pydantic import BaseModel, Field, field_validator

class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    
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
        description="Stock quantity"
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
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or whitespace")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Gaming Laptop",
                "description": "High-performance gaming laptop",
                "price": 1299.99,
                "stock": 50,
                "category": "Electronics"
            }
        }
    }
```

### 2. Update Schema (PUT/PATCH)

Used for updating resources. All fields optional for partial updates.

```python
from typing import Optional

class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)"""
    
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
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or whitespace")
            return v
        return None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "price": 999.99,
                "stock": 45
            }
        }
    }
```

### 3. Response Schema

Used for API responses. Includes computed/derived fields.

```python
from datetime import datetime
from pydantic import computed_field

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
    
    # Computed field - not stored in DB
    @computed_field
    @property
    def in_stock(self) -> bool:
        """Whether product is in stock"""
        return self.stock > 0
    
    @computed_field
    @property
    def formatted_price(self) -> str:
        """Formatted price with currency"""
        return f"${self.price:,.2f}"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Gaming Laptop",
                "description": "High-performance gaming laptop",
                "price": 1299.99,
                "stock": 50,
                "category": "Electronics",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "in_stock": True,
                "formatted_price": "$1,299.99"
            }
        }
    }
```

---

## ✅ Field Validation

### String Validators

```python
from pydantic import field_validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    password: str = Field(..., min_length=8)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Username must be alphanumeric with underscores"""
        import re
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v.lower()  # Normalize to lowercase
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email"""
        v = v.lower().strip()
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password must contain uppercase, lowercase, and digit"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v
```

### Numeric Validators

```python
class OrderCreate(BaseModel):
    quantity: int = Field(..., ge=1, le=1000)
    discount_percent: float = Field(0, ge=0, le=100)
    
    @field_validator("discount_percent")
    @classmethod
    def round_discount(cls, v: float) -> float:
        """Round discount to 2 decimal places"""
        return round(v, 2)
```

### List/Array Validators

```python
class ProductCreate(BaseModel):
    tags: List[str] = Field(default_factory=list, max_length=10)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Clean and deduplicate tags"""
        # Remove empty strings
        v = [tag.strip().lower() for tag in v if tag.strip()]
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in v:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        return unique_tags
```

---

## 🔗 Model Validation

Model validators work across multiple fields.

```python
from pydantic import model_validator

class DateRangeFilter(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRangeFilter":
        """Ensure end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class ProductCreate(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = Field(None, gt=0)
    
    @model_validator(mode="after")
    def validate_discount(self) -> "ProductCreate":
        """Ensure discount price is less than regular price"""
        if self.discount_price is not None:
            if self.discount_price >= self.price:
                raise ValueError("Discount price must be less than regular price")
        return self

class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordReset":
        """Ensure passwords match"""
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
```

---

## 🔄 Base Schemas (DRY)

Avoid duplication by using base schemas.

```python
class ProductBase(BaseModel):
    """Base schema with common product fields"""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    
    @field_validator("name", "category", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or whitespace")
        return v

# Create inherits all fields from base
class ProductCreate(ProductBase):
    """Schema for creating products"""
    pass

# Update makes all fields optional
class ProductUpdate(ProductBase):
    """Schema for updating products (all fields optional)"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    
    @field_validator("name", "category", "description")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or whitespace")
        return v

# Response adds ID and timestamps
class ProductResponse(ProductBase):
    """Schema for product responses"""
    
    id: str
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def in_stock(self) -> bool:
        return self.stock > 0
```

---

## 📤 Response Schemas

### Single Resource Response

```python
class ProductResponse(BaseModel):
    """Single product response"""
    id: str
    name: str
    price: float
    stock: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123",
                "name": "Laptop",
                "price": 999.99,
                "stock": 10
            }
        }
    }
```

### List Response with Pagination

```python
from typing import List, Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=1, description="Total pages")
    items: List[T] = Field(..., description="Items in current page")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "items": []
            }
        }
    }

# Usage
class ProductListResponse(PaginatedResponse[ProductResponse]):
    """Paginated product list response"""
    pass
```

### Message Response

```python
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="Response message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Product deleted successfully"
            }
        }
    }
```

### Error Response

```python
class ErrorDetail(BaseModel):
    """Error detail"""
    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")

class ErrorResponse(BaseModel):
    """Error response with details"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Validation errors")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": [
                    {"field": "email", "message": "Invalid email format"},
                    {"field": "age", "message": "Must be at least 18"}
                ]
            }
        }
    }
```

---

## 🔗 Nested Schemas

### One-to-One Relationship

```python
class Address(BaseModel):
    """Address schema"""
    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    country: str = Field(..., min_length=2, max_length=100)

class UserResponse(BaseModel):
    """User with embedded address"""
    id: str
    username: str
    email: str
    address: Optional[Address] = None
```

### One-to-Many Relationship

```python
class OrderItem(BaseModel):
    """Single order item"""
    product_id: str
    product_name: str
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., gt=0)
    
    @computed_field
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

class OrderResponse(BaseModel):
    """Order with multiple items"""
    id: str
    user_id: str
    items: List[OrderItem] = Field(..., min_length=1)
    created_at: datetime
    
    @computed_field
    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)
```

---

## 🎨 Common Patterns

### Pattern 1: Enum Fields

```python
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    moderator = "moderator"
    user = "user"

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class UserCreate(BaseModel):
    username: str
    role: UserRole = Field(UserRole.user, description="User role")

class OrderResponse(BaseModel):
    id: str
    status: OrderStatus
```

### Pattern 2: Conditional Fields

```python
class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    method: Literal["credit_card", "paypal", "bank_transfer"]
    
    # Only required for credit card
    card_number: Optional[str] = Field(None, pattern=r"^\d{16}$")
    card_expiry: Optional[str] = Field(None, pattern=r"^\d{2}/\d{2}$")
    card_cvv: Optional[str] = Field(None, pattern=r"^\d{3,4}$")
    
    # Only required for PayPal
    paypal_email: Optional[str] = None
    
    # Only required for bank transfer
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    
    @model_validator(mode="after")
    def validate_payment_details(self) -> "PaymentCreate":
        """Ensure required fields for payment method"""
        if self.method == "credit_card":
            if not all([self.card_number, self.card_expiry, self.card_cvv]):
                raise ValueError("Credit card details required")
        
        elif self.method == "paypal":
            if not self.paypal_email:
                raise ValueError("PayPal email required")
        
        elif self.method == "bank_transfer":
            if not all([self.account_number, self.routing_number]):
                raise ValueError("Bank account details required")
        
        return self
```

### Pattern 3: File Metadata

```python
class FileUpload(BaseModel):
    """File upload metadata"""
    filename: str = Field(..., max_length=255)
    content_type: str
    size_bytes: int = Field(..., ge=0, le=10_485_760)  # Max 10MB
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Ensure safe filename"""
        import re
        # Remove unsafe characters
        v = re.sub(r'[^\w\s.-]', '', v)
        if not v:
            raise ValueError("Invalid filename")
        return v
    
    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Only allow specific file types"""
        allowed = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
        if v not in allowed:
            raise ValueError(f"File type not allowed. Allowed: {', '.join(allowed)}")
        return v
```

---

## 🛡️ Security Best Practices

### 1. Never Expose Sensitive Fields

```python
class UserResponse(BaseModel):
    """Public user response - NO sensitive data"""
    id: str
    username: str
    email: str
    # ❌ DON'T include: password_hash, api_key, secret_token
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123",
                "username": "john_doe",
                "email": "john@example.com"
            }
        }
    }
```

### 2. Validate String Lengths

```python
class CommentCreate(BaseModel):
    """Prevent DoS with length limits"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,  # ✅ Limit max length
        description="Comment content"
    )
```

### 3. Validate Numeric Ranges

```python
class ProductCreate(BaseModel):
    """Prevent unrealistic values"""
    price: float = Field(..., gt=0, le=1_000_000)  # ✅ Max price
    quantity: int = Field(..., ge=0, le=10_000)    # ✅ Max quantity
```

### 4. Sanitize User Input

```python
class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    
    @field_validator("title", "content")
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        """Remove HTML tags"""
        import re
        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        # Trim whitespace
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v
```

### 5. Use Enums for Fixed Values

```python
# ❌ Bad: Accept any string
status: str

# ✅ Good: Only allow specific values
class Status(str, Enum):
    active = "active"
    inactive = "inactive"

status: Status
```

---

## ⚙️ Configuration

### Model Config Options

```python
from pydantic import ConfigDict

class Product(BaseModel):
    id: str = Field(..., alias="_id")  # MongoDB _id
    name: str
    
    model_config = ConfigDict(
        # Allow population by field name and alias
        populate_by_name=True,
        
        # Validate assignment after creation
        validate_assignment=True,
        
        # Strict mode (no type coercion)
        strict=False,
        
        # Allow extra fields (keep them)
        extra="allow",  # or "forbid" or "ignore"
        
        # JSON schema example
        json_schema_extra={
            "example": {
                "id": "123",
                "name": "Product"
            }
        }
    )
```

---

## 🚀 Advanced Patterns

### Generic Base Schema

```python
from typing import TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

class TimestampedSchema(BaseModel, Generic[T]):
    """Add timestamps to any schema"""
    created_at: datetime
    updated_at: datetime
    data: T

# Usage
class ProductWithTimestamps(TimestampedSchema[ProductResponse]):
    pass
```

### Schema Factory

```python
def create_update_schema(base_schema: type[BaseModel]) -> type[BaseModel]:
    """Create update schema from base schema (all fields optional)"""
    from typing import get_type_hints
    
    fields = {}
    for field_name, field_info in base_schema.model_fields.items():
        fields[field_name] = (Optional[field_info.annotation], None)
    
    return type(f"{base_schema.__name__}Update", (BaseModel,), fields)

# Usage
ProductUpdate = create_update_schema(ProductCreate)
```

---

## ❌ Common Mistakes

### Mistake 1: Same Schema for Create and Response

```python
# ❌ Bad: Exposes internal fields, missing computed fields
class Product(BaseModel):
    id: str  # Client shouldn't send this!
    name: str
    price: float

# ✅ Good: Separate schemas
class ProductCreate(BaseModel):
    name: str
    price: float

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    created_at: datetime
```

### Mistake 2: No Validation

```python
# ❌ Bad: No validation
class User(BaseModel):
    email: str
    age: int

# ✅ Good: With validation
class User(BaseModel):
    email: EmailStr  # Validates email format
    age: int = Field(..., ge=18, le=120)
```

### Mistake 3: Not Using Examples

```python
# ❌ Bad: No examples in OpenAPI docs
class Product(BaseModel):
    name: str
    price: float

# ✅ Good: With examples
class Product(BaseModel):
    name: str
    price: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Laptop",
                "price": 999.99
            }
        }
    }
```

---

## 📚 Quick Reference

See **QUICK_REFERENCE.md** for fast lookup templates and code snippets.

## 💡 Next Steps

1. Copy patterns from **example.py** to your project
2. Create base schemas for common fields
3. Add field validators for data cleaning
4. Add model validators for cross-field validation
5. Include examples for OpenAPI documentation
6. Never expose sensitive data in response schemas

---

## 🔗 Related Modules

- **Path/Query/Body Parameters** - Request validation
- **Error Handling** - Validation error responses
- **Computed Fields** - Derived fields in schemas

---

**Remember:**
- Separate Create/Update/Response schemas
- Always validate user input
- Use base schemas to stay DRY
- Add examples for documentation
- Never expose sensitive data!
