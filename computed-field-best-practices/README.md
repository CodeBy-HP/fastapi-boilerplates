# 🧮 Computed Fields Best Practices

Production-ready patterns for using computed fields in FastAPI + Beanie/Pydantic. Never forget the best practices again!

## 🎯 What This Module Provides

A complete reference implementation showing **the right way** to handle computed/derived fields in your FastAPI SaaS application:

- ✅ When to compute vs. when to store
- ✅ How to keep data consistent and accurate
- ✅ Production-ready code patterns you can copy
- ✅ Common pitfalls and how to avoid them

## ⚡ The Golden Rule

**NEVER store derived values in the database if they can be calculated from other fields.**

**Why?** Data inconsistency! If you update `quantity` but forget to update `in_stock`, your data becomes incorrect.

---

## 🚀 Quick Start

### Installation
```bash
pip install fastapi beanie pydantic motor
```

### Basic Example
```python
from beanie import Document
from pydantic import computed_field

class Product(Document):
    name: str
    price: float
    quantity: int
    
    # ✅ Compute this - DON'T store it!
    @computed_field
    @property
    def in_stock(self) -> bool:
        """Always accurate, no sync issues"""
        return self.quantity > 0
    
    # ✅ This appears in API responses automatically
    @computed_field
    @property
    def total_value(self) -> float:
        return self.price * self.quantity
```

### In Your API
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ProductCreate(BaseModel):
    name: str
    price: float
    quantity: int
    # Notice: NO in_stock or total_value - they're computed!

@app.post("/products")
async def create_product(data: ProductCreate):
    product = Product(**data.model_dump())
    await product.insert()
    # Response includes in_stock and total_value automatically!
    return product
```

That's it! Your computed fields are always up-to-date.

---

## 📚 What's Included

### 📄 Files in This Module

1. **`example.py`** - Complete working example with Product model, schemas, and routes
   - Copy this file and adapt it to your needs
   - Includes all common patterns in one place

2. **`QUICK_REFERENCE.md`** - Fast lookup cheat sheet
   - Use when you need a quick reminder
   - Decision trees and templates

3. **`README.md`** (this file) - Full documentation
   - Comprehensive guide with examples
   - Best practices and anti-patterns
   - Read this once, then bookmark for reference

---

## 🎯 When to Use What

| Pattern | Use For | Store in DB? | In API Response? |
|---------|---------|--------------|------------------|
| `@computed_field` | `in_stock`, `total_price`, `full_name` | ❌ No | ✅ Yes |
| `@field_validator` | Normalize email, validate format | N/A | N/A |
| `@model_validator` | Cross-field validation, auto-timestamps | N/A | N/A |
| Regular field | User input, **historical snapshots** | ✅ Yes | ✅ Yes |

---

## 📖 Core Concepts

### 1️⃣ Computed Fields - Calculate on Demand

**Use when:** Value is derived from other fields and should always be current.

```python
@computed_field
@property
def in_stock(self) -> bool:
    return self.quantity > 0

@computed_field
@property
def discount_price(self) -> float:
    if self.quantity > 100:
        return self.price * 0.9  # Bulk discount
    return self.price
```

**Benefits:**
- ✅ Always accurate
- ✅ Automatically in API responses
- ✅ Appears in OpenAPI schema
- ✅ No storage waste

---

### 2️⃣ Field Validators - Clean Data Before Saving

**Use when:** You need to normalize or validate data before it hits the database.

```python
@field_validator('email')
@classmethod
def normalize_email(cls, v: str) -> str:
    """Always store emails lowercase"""
    return v.lower().strip()

@field_validator('name')
@classmethod
def normalize_name(cls, v: str) -> str:
    """Clean and capitalize names"""
    return v.strip().title()
```

---

### 3️⃣ Model Validators - Cross-Field Logic

**Use when:** Validation depends on multiple fields.

```python
@model_validator(mode='after')
def validate_date_range(self):
    """Ensure end_date > start_date"""
    if self.end_date and self.end_date < self.start_date:
        raise ValueError('end_date must be after start_date')
    return self

@model_validator(mode='after')
def update_timestamp(self):
    """Auto-update modification time"""
    self.updated_at = datetime.utcnow()
    return self
```

---

### 4️⃣ When DO You Store Computed Values?

**Historical Snapshots** - When values should NOT change with source data:

```python
class Order(Document):
    # ✅ Store these - they're snapshots in time
    product_price_at_purchase: float
    tax_rate_at_purchase: float
    quantity: int
    
    # ✅ Compute from historical values
    @computed_field
    @property
    def order_total(self) -> float:
        subtotal = self.product_price_at_purchase * self.quantity
        tax = subtotal * self.tax_rate_at_purchase
        return subtotal + tax
```

**Why?** Even if the product price changes later, the order total should remain what the customer paid.

---

## 🚨 Common Mistakes & How to Avoid Them

### ❌ MISTAKE 1: Storing Computed Values

```python
# ❌ WRONG - in_stock will get out of sync
class Product(Document):
    quantity: int
    in_stock: bool  # Gets stale when quantity changes!
```

```python
# ✅ RIGHT - Always accurate
class Product(Document):
    quantity: int
    
    @computed_field
    @property
    def in_stock(self) -> bool:
        return self.quantity > 0
```

---

### ❌ MISTAKE 2: Using Validators for Computed Fields

```python
# ❌ WRONG - Only runs at creation
@field_validator('in_stock')
@classmethod
def set_in_stock(cls, v, info):
    return info.data.get('quantity', 0) > 0
```

```python
# ✅ RIGHT - Recalculates every time
@computed_field
@property
def in_stock(self) -> bool:
    return self.quantity > 0
```

---

### ❌ MISTAKE 3: Querying Computed Fields Directly

```python
# ❌ WRONG - in_stock doesn't exist in DB
products = await Product.find({"in_stock": True}).to_list()
```

```python
# ✅ RIGHT - Query the source field
products = await Product.find({"quantity": {"$gt": 0}}).to_list()

# ✅ Index the source field for performance
class Settings:
    indexes = ["quantity"]
```

---

## 🏭 Production Patterns

### Pattern 1: Separate Input/Output Schemas

```python
# Input: Only what users can set
class ProductCreate(BaseModel):
    name: str
    price: float
    quantity: int
    # NO computed fields!

# Output: Include computed fields
class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    quantity: int
    in_stock: bool  # ← Computed
    total_value: float  # ← Computed

# Route
@app.post("/products", response_model=ProductResponse)
async def create_product(data: ProductCreate):
    product = Product(**data.model_dump())
    await product.insert()
    return product  # Computed fields auto-included!
```

---

### Pattern 2: Auto-Generate Fields Once

```python
@field_validator('slug', mode='before')
@classmethod
def generate_slug(cls, v: Optional[str], info) -> str:
    """Generate slug at creation if not provided"""
    if v:
        return v  # User provided one
    name = info.data.get('name', '')
    return name.lower().replace(' ', '-')
```

**Use for:** Slugs, SKUs, reference numbers that should be stable.

---

### Pattern 3: Complex Business Logic

```python
@computed_field
@property
def effective_price(self) -> float:
    """Calculate with all applicable discounts"""
    base_price = self.price
    
    # Bulk discount
    if self.quantity > 100:
        base_price *= 0.9
    elif self.quantity > 50:
        base_price *= 0.95
    
    # Category discount
    if self.category == "Clearance":
        base_price *= 0.8
    
    return round(base_price, 2)

@computed_field
@property
def savings(self) -> float:
    return round(self.price - self.effective_price, 2)
```

---

## 🔍 Real-World Examples

### Example 1: User Profile

```python
class User(Document):
    first_name: str
    last_name: str
    birth_date: date
    
    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @computed_field
    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < 
            (self.birth_date.month, self.birth_date.day)
        )
```

---

### Example 2: Subscription Tiers

```python
class Subscription(Document):
    plan: str  # "free", "pro", "enterprise"
    custom_limit: Optional[int] = None
    
    @computed_field
    @property
    def api_rate_limit(self) -> int:
        """Calculate rate limit based on plan"""
        if self.custom_limit:
            return self.custom_limit
        
        return {
            "free": 100,
            "pro": 1000,
            "enterprise": 10000
        }.get(self.plan, 100)
```

---

## 📊 Performance Tips

### Tip 1: Index Source Fields

```python
class Product(Document):
    quantity: int
    
    class Settings:
        indexes = ["quantity"]  # ✅ Fast queries for in_stock

# Fast query
in_stock = await Product.find({"quantity": {"$gt": 0}}).to_list()
```

### Tip 2: Project Only Needed Fields

```python
# ❌ Fetch everything
products = await Product.find({}).to_list()

# ✅ Project only what you need
products = await Product.find({}).project(ProductMinimal).to_list()
```

### Tip 3: Cache Expensive Calculations

```python
from functools import cached_property

@cached_property
def expensive_score(self) -> float:
    """Cache until object is recreated"""
    return complex_ml_calculation()
```

---

## ✅ Decision Checklist

When you're unsure what to do with a field, ask:

1. **Can it be calculated from other fields?**
   - Yes → Use `@computed_field`
   - No → Store it

2. **Should it change when source data changes?**
   - Yes → Use `@computed_field` (e.g., `in_stock`)
   - No → Store it (e.g., `order_total_at_purchase`)

3. **Is it fast to calculate (< 1ms)?**
   - Yes → Use `@computed_field`
   - No → Consider caching

4. **Do you need it in API responses?**
   - Yes → Use `@computed_field` + `@property`
   - No (internal only) → Use `@property` only

---

## 📖 Further Reading

- **`QUICK_REFERENCE.md`** - Fast lookup cheat sheet with templates
- **`example.py`** - Complete working code example
- [Pydantic Computed Fields Docs](https://docs.pydantic.dev/latest/concepts/computed_fields/)
- [Beanie Documentation](https://beanie-odm.dev/)

---

## 🎓 Summary

**Default to computed fields** for derived data. They're always accurate and prevent data inconsistency.

**Key Principles:**
1. Compute values from source fields (quantity → in_stock)
2. Use validators for data normalization
3. Store historical snapshots that shouldn't change
4. Index source fields you'll query frequently
5. Separate input/output schemas

**Copy `example.py` and adapt it to your SaaS needs!**
