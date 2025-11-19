# Pydantic Schema Quick Reference

Fast lookup for common Pydantic schema patterns in FastAPI.

## Table of Contents
- [Basic CRUD Schemas](#basic-crud-schemas)
- [Field Validation](#field-validation)
- [Model Validation](#model-validation)
- [Base Schemas](#base-schemas)
- [Response Schemas](#response-schemas)
- [Nested Schemas](#nested-schemas)
- [Computed Fields](#computed-fields)
- [Common Patterns](#common-patterns)

---

## Basic CRUD Schemas

### Create Schema (POST)
All fields required:
```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
```

### Update Schema (PATCH)
All fields optional:
```python
from typing import Optional

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
```

### Response Schema
Includes ID and timestamps:
```python
from datetime import datetime

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    created_at: datetime
    updated_at: datetime
```

---

## Field Validation

### String Constraints
```python
# Length constraints
name: str = Field(..., min_length=1, max_length=100)

# Regex pattern
phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")

# Email
from pydantic import EmailStr
email: EmailStr = Field(...)
```

### Numeric Constraints
```python
# Greater than
price: float = Field(..., gt=0)  # > 0

# Greater or equal
age: int = Field(..., ge=18)  # >= 18

# Less than
discount: float = Field(..., lt=100)  # < 100

# Less or equal
rating: int = Field(..., le=5)  # <= 5

# Range
percentage: float = Field(..., ge=0, le=100)
```

### List Constraints
```python
from typing import List

# Min/max items
tags: List[str] = Field(..., min_length=1, max_length=10)

# With default
tags: List[str] = Field(default_factory=list)
```

### Custom Field Validators
```python
from pydantic import field_validator

class UserCreate(BaseModel):
    username: str
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v
```

### Multiple Fields
```python
class ProductCreate(BaseModel):
    name: str
    category: str
    
    @field_validator("name", "category")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v
```

---

## Model Validation

### Cross-Field Validation
```python
from pydantic import model_validator

class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
```

### Password Confirmation
```python
class PasswordReset(BaseModel):
    new_password: str
    confirm_password: str
    
    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordReset":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
```

### Conditional Validation
```python
class Product(BaseModel):
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = None
    
    @model_validator(mode="after")
    def validate_discount(self) -> "Product":
        if self.discount_price is not None:
            if self.discount_price >= self.price:
                raise ValueError("Discount must be less than price")
        return self
```

---

## Base Schemas

### DRY Principle
```python
# Base schema with common fields
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str

# Inherit for Create
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Inherit for Update
class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

# Inherit for Response
class UserResponse(UserBase):
    id: str
    created_at: datetime
```

---

## Response Schemas

### Single Item
```python
class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    created_at: datetime
```

### Paginated Response
```python
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[T]

# Usage
@app.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products():
    pass
```

### Message Response
```python
class MessageResponse(BaseModel):
    message: str
    
# Usage
return MessageResponse(message="Product deleted successfully")
```

### Error Response
```python
class ErrorDetail(BaseModel):
    field: str
    message: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
```

---

## Nested Schemas

### One-to-One Relationship
```python
class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class UserProfile(BaseModel):
    id: str
    username: str
    address: Optional[Address] = None
```

### One-to-Many Relationship
```python
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem] = Field(..., min_length=1)
```

---

## Computed Fields

### Basic Computed Field
```python
from pydantic import computed_field

class Product(BaseModel):
    price: float
    stock: int
    
    @computed_field
    @property
    def in_stock(self) -> bool:
        return self.stock > 0
    
    @computed_field
    @property
    def formatted_price(self) -> str:
        return f"${self.price:.2f}"
```

### Computed from Multiple Fields
```python
class OrderItem(BaseModel):
    quantity: int
    unit_price: float
    
    @computed_field
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

class Order(BaseModel):
    items: List[OrderItem]
    
    @computed_field
    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)
```

---

## Common Patterns

### Enums
```python
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    moderator = "moderator"
    user = "user"

class User(BaseModel):
    role: UserRole = UserRole.user
```

### Default Values
```python
class Product(BaseModel):
    name: str
    is_active: bool = True  # Default value
    tags: List[str] = Field(default_factory=list)  # Empty list
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Alias Fields
```python
from pydantic import ConfigDict, Field

class Product(BaseModel):
    product_id: str = Field(..., alias="id")
    
    model_config = ConfigDict(populate_by_name=True)

# Can use either "product_id" or "id" in JSON
```

### Optional Fields
```python
from typing import Optional

class User(BaseModel):
    name: str  # Required
    bio: Optional[str] = None  # Optional, defaults to None
    age: Optional[int] = None
```

### File Upload Metadata
```python
class FileUpload(BaseModel):
    filename: str = Field(..., max_length=255)
    content_type: str
    size_bytes: int = Field(..., ge=0, le=10_485_760)  # Max 10MB
    
    @field_validator("content_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = ["image/jpeg", "image/png", "application/pdf"]
        if v not in allowed:
            raise ValueError(f"Allowed types: {allowed}")
        return v
```

### Sanitize HTML
```python
import re

class BlogPost(BaseModel):
    title: str
    content: str
    
    @field_validator("title", "content")
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        return v.strip()
```

### Normalize Email
```python
class UserCreate(BaseModel):
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()
```

### Clean Tags
```python
class Post(BaseModel):
    tags: List[str] = Field(default_factory=list)
    
    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: List[str]) -> List[str]:
        # Clean, lowercase, deduplicate
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        return list(dict.fromkeys(cleaned))  # Remove duplicates
```

### Password Strength
```python
class UserCreate(BaseModel):
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Must contain uppercase")
        if not any(c.islower() for c in v):
            raise ValueError("Must contain lowercase")
        if not any(c.isdigit() for c in v):
            raise ValueError("Must contain digit")
        return v
```

### Conditional Required Fields
```python
from enum import Enum

class PaymentMethod(str, Enum):
    card = "card"
    paypal = "paypal"

class Payment(BaseModel):
    method: PaymentMethod
    card_number: Optional[str] = None
    paypal_email: Optional[EmailStr] = None
    
    @model_validator(mode="after")
    def validate_method(self) -> "Payment":
        if self.method == PaymentMethod.card and not self.card_number:
            raise ValueError("Card number required for card payment")
        if self.method == PaymentMethod.paypal and not self.paypal_email:
            raise ValueError("PayPal email required for PayPal payment")
        return self
```

---

## Configuration

### Common ConfigDict Options
```python
from pydantic import ConfigDict

class Product(BaseModel):
    model_config = ConfigDict(
        # Allow field population by alias
        populate_by_name=True,
        
        # Validate on assignment (not just initialization)
        validate_assignment=True,
        
        # Allow arbitrary types
        arbitrary_types_allowed=True,
        
        # Strict type validation
        strict=True,
        
        # JSON schema examples
        json_schema_extra={
            "example": {
                "name": "Product",
                "price": 99.99
            }
        }
    )
```

### OpenAPI Examples
```python
class Product(BaseModel):
    name: str
    price: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Laptop", "price": 999.99},
                {"name": "Mouse", "price": 29.99}
            ]
        }
    )
```

---

## Route Usage

### Create with Validation
```python
@app.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    # product is automatically validated
    product_data = product.model_dump()
    # Save to database
    return ProductResponse(**product_data)
```

### Update (Partial)
```python
@app.patch("/products/{id}", response_model=ProductResponse)
async def update_product(id: str, product: ProductUpdate):
    # Get only provided fields
    update_data = product.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(400, "No fields to update")
    
    # Update database
    return ProductResponse(**updated_data)
```

### List with Pagination
```python
@app.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(page: int = 1, page_size: int = 20):
    # Query database
    products = get_products(page, page_size)
    
    return PaginatedResponse(
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=ceil(total_count / page_size),
        items=products
    )
```

---

## Security Checklist

✅ **DO**:
- Use EmailStr for email validation
- Set max_length on all strings (prevent DoS)
- Validate numeric ranges (gt, ge, lt, le)
- Use Enums for fixed values
- Sanitize user input (remove HTML)
- Normalize data (lowercase, strip whitespace)
- Exclude sensitive fields from responses

❌ **DON'T**:
- Expose password_hash in responses
- Allow unlimited string lengths
- Trust user input without validation
- Use strings for status/role (use Enums)
- Allow negative values where inappropriate

---

## Common Mistakes

### ❌ Mistake: Same schema for Create and Response
```python
# Don't do this
class Product(BaseModel):
    id: str  # ID shouldn't be in create!
    name: str
    password: str  # Password shouldn't be in response!
```

### ✅ Fix: Separate schemas
```python
class ProductCreate(BaseModel):
    name: str

class ProductResponse(BaseModel):
    id: str
    name: str
```

### ❌ Mistake: No field constraints
```python
class Product(BaseModel):
    name: str  # No max length!
    price: float  # Can be negative!
```

### ✅ Fix: Add constraints
```python
class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
```

### ❌ Mistake: Forgetting to validate cross-field
```python
class DateRange(BaseModel):
    start: datetime
    end: datetime
    # No validation that end > start!
```

### ✅ Fix: Use model_validator
```python
class DateRange(BaseModel):
    start: datetime
    end: datetime
    
    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self
```

---

## Tips

1. **Always add descriptions** - helps API documentation
2. **Provide examples** - makes your API easier to use
3. **Validate early** - catch errors at the schema level
4. **Use base schemas** - avoid repeating fields (DRY)
5. **Normalize data** - lowercase emails, strip whitespace
6. **Use computed fields** - for derived values
7. **Never expose secrets** - exclude password_hash, API keys
8. **Set max lengths** - prevent DoS attacks
9. **Use Enums** - for fixed values (status, role)
10. **Test your validators** - ensure they work as expected

---

For complete examples, see [example.py](example.py).

For detailed explanations, see [README.md](README.md).
