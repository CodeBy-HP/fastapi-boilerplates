# 🎯 Quick Reference: Computed Fields Cheat Sheet

> **Fast lookup guide** - Bookmark this page for quick reminders!

## ⚡ The Golden Rules

1. **DON'T store values that can be calculated** from other fields
2. **DO store historical snapshots** that shouldn't change with source data
3. **USE @computed_field** for values in API responses
4. **USE validators** for data normalization before saving

---

## 📋 When to Use What

| Pattern | Use Case | Store in DB? | In API Response? |
|---------|----------|--------------|------------------|
| `@computed_field` + `@property` | `in_stock`, `total_price`, `full_name` | ❌ No | ✅ Yes |
| `@property` only | Internal helpers, `needs_restock` | ❌ No | ❌ No |
| `@field_validator` | Normalize text, validate email | N/A | N/A |
| `@model_validator` | Cross-field validation, auto-timestamps | N/A | N/A |
| Regular field | User input, **historical snapshots** | ✅ Yes | ✅ Yes |

---

## 📝 Code Templates

### Template 1: Simple Computed Field
```python
@computed_field
@property
def in_stock(self) -> bool:
    """Always reflects current quantity"""
    return self.quantity > 0
```

### Template 2: Field Validator (Normalize)
```python
@field_validator('email')
@classmethod
def normalize_email(cls, v: str) -> str:
    """Clean data before saving"""
    return v.lower().strip()
```

### Template 3: Model Validator (Cross-field)
```python
@model_validator(mode='after')
def validate_dates(self):
    """Ensure end_date > start_date"""
    if self.end_date < self.start_date:
        raise ValueError('Invalid range')
    return self
```

### Template 4: Auto-generate Field (Once)
```python
@field_validator('slug', mode='before')
@classmethod
def generate_slug(cls, v: Optional[str], info) -> str:
    """Generate slug at creation if not provided"""
    if v:
        return v
    name = info.data.get('name', '')
    return name.lower().replace(' ', '-')
```

### Template 5: Internal Helper (Not in API)
```python
@property
def needs_attention(self) -> bool:
    """Internal business logic only"""
    return self.quantity < 10
```

---

## 💡 Common Scenarios

### Stock Status
```python
# ❌ WRONG - Gets out of sync
in_stock: bool

# ✅ RIGHT - Always accurate
@computed_field
@property
def in_stock(self) -> bool:
    return self.quantity > 0
```

### Full Name
```python
# ❌ WRONG - Redundant storage
full_name: str

# ✅ RIGHT - Compute on demand
@computed_field
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"
```

### Order Total (Historical Snapshot!)
```python
# ✅ RIGHT - Store historical values
class Order(Document):
    price_at_purchase: float  # Store snapshot
    quantity: int
    
    @computed_field
    @property
    def total(self) -> float:
        return self.price_at_purchase * self.quantity
```

### Age from Birthdate
```python
# ❌ WRONG - Gets outdated
age: int

# ✅ RIGHT - Calculate dynamically
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

## 🔌 API Schema Pattern

```python
# INPUT SCHEMA: Only fields users can set
class ProductCreate(BaseModel):
    name: str
    price: float
    quantity: int
    # NO computed fields here!

# OUTPUT SCHEMA: Includes computed fields
class ProductResponse(BaseModel):
    name: str
    price: float
    quantity: int
    in_stock: bool  # ← Computed
    total_value: float  # ← Computed

# ROUTE USAGE
@app.post("/products", response_model=ProductResponse)
async def create_product(data: ProductCreate):
    product = Product(**data.model_dump())
    await product.insert()
    return product  # Computed fields auto-included!
```

---

## 🔍 Querying Computed Fields

```python
# ✅ Query the SOURCE field, not the computed field

# Find in_stock products
products = await Product.find({"quantity": {"$gt": 0}}).to_list()

# Find out_of_stock products
products = await Product.find({"quantity": 0}).to_list()

# ⚡ Index source fields for performance
class Settings:
    indexes = ["quantity"]  # Fast queries
```

---

## ⚡ Performance Tips

```python
# ✅ Fast: Simple calculation
@computed_field
@property
def total(self) -> float:
    return self.price * self.quantity

# ⚠️ Expensive: Cache it!
from functools import cached_property

@cached_property
def expensive_score(self) -> float:
    return complex_ml_calculation()

# ✅ Fetch less data: Use projections
products = await Product.find({}).project(ProductMinimal).to_list()
```

---

## ⚙️ Validation Order

Pydantic/Beanie processes in this order:
1. `@field_validator`
2. `@model_validator(mode='before')`
3. Create model instance
4. `@model_validator(mode='after')`
5. `@computed_field` (when accessed)

---

## 🚨 Common Mistakes

```python
# ❌ MISTAKE 1: Storing computed values
in_stock: bool  # Will get stale!

# ❌ MISTAKE 2: Validator for computed field
@field_validator('total')
def calc_total(cls, v, info):
    return info.data['price'] * info.data['qty']
# Problem: Only runs at creation!

# ❌ MISTAKE 3: Querying computed field
Product.find({"in_stock": True})  # ❌ Not in DB!

# ✅ CORRECT VERSIONS
@computed_field
@property
def in_stock(self) -> bool:
    return self.quantity > 0

Product.find({"quantity": {"$gt": 0}})  # ✅
```

---

## 🧪 Testing Computed Fields

```python
async def test_in_stock():
    # Test logic
    product = Product(name="Test", price=10, quantity=5)
    assert product.in_stock == True
    
    product.quantity = 0
    assert product.in_stock == False  # ✅ Auto-updates!
    
    # Test in API
    response = await client.post("/products", json={
        "name": "Test", "price": 10, "quantity": 5
    })
    assert response.json()["in_stock"] == True
```

---

## 🌳 Decision Tree

```
Is the value derived from other fields?
├─ YES: Can it be calculated quickly (< 1ms)?
│  ├─ YES: Use @computed_field ✅
│  └─ NO: Cache or store
└─ NO: Should it change when source changes?
   ├─ YES: Store it normally
   └─ NO: Historical snapshot - store it
```

---

## 📚 See Also

- **`README.md`** - Full guide with detailed examples
- **`example.py`** - Complete working code to copy
- [Pydantic Docs](https://docs.pydantic.dev/latest/concepts/computed_fields/)

---

**Remember:** Compute `in_stock` from `quantity`, never store it!
