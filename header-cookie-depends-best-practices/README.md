# 🔐 Header, Cookie & Depends Best Practices

Complete guide to HTTP headers, cookies, and dependency injection in FastAPI with production-ready patterns.

## 📋 Quick Overview

| Feature | Purpose | Use When | Common Examples |
|---------|---------|----------|-----------------|
| **Header()** | Read HTTP headers | Authentication, API keys, tracking | `Authorization`, `X-API-Key`, `User-Agent` |
| **Cookie()** | Read browser cookies | Sessions, preferences, tracking | `session_id`, `theme`, `cart_id` |
| **Depends()** | Inject reusable logic | Auth, DB sessions, shared validation | `get_current_user`, `get_db`, `pagination` |

---

## 🎯 Header() - HTTP Headers

### What Are Headers?

HTTP headers are key-value pairs sent with every request/response:

```
GET /api/users HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
User-Agent: Mozilla/5.0
X-API-Key: sk_live_1234567890
Accept: application/json
Content-Type: application/json
```

### Basic Usage

```python
from fastapi import Header, HTTPException

@app.get("/info")
async def read_header(
    user_agent: str = Header(..., description="Client user agent")
):
    return {"user_agent": user_agent}
```

**How it works:**
- FastAPI reads the `User-Agent` header
- Converts snake_case (`user_agent`) → `User-Agent` (hyphen-case)
- Validates and injects the value

### Authentication with Headers

```python
@app.get("/protected")
async def protected_route(
    authorization: str = Header(..., description="Bearer token")
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    token = authorization.replace("Bearer ", "")
    # Verify token here
    
    return {"message": "Access granted"}
```

**Client sends:**
```bash
curl -H "Authorization: Bearer abc123" http://localhost:8000/protected
```

### API Key Authentication

```python
API_KEY = "sk_live_1234567890"

@app.get("/api/data")
async def get_data(
    x_api_key: str = Header(..., description="API key for authentication")
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return {"data": "sensitive information"}
```

**Client sends:**
```bash
curl -H "X-API-Key: sk_live_1234567890" http://localhost:8000/api/data
```

### Optional Headers

```python
@app.get("/analytics")
async def track_request(
    user_agent: Optional[str] = Header(None),
    x_request_id: Optional[str] = Header(None),
    referer: Optional[str] = Header(None)
):
    return {
        "user_agent": user_agent or "Unknown",
        "request_id": x_request_id,
        "referer": referer
    }
```

### Custom Header Names

```python
@app.get("/custom")
async def custom_header(
    # Override automatic conversion
    api_key: str = Header(..., alias="X-Custom-API-Key")
):
    return {"api_key": api_key}
```

### Common Header Patterns

```python
# Content negotiation
accept: str = Header("application/json")

# Rate limiting
x_ratelimit_limit: Optional[int] = Header(None)

# Correlation ID
x_correlation_id: str = Header(..., description="Request correlation ID")

# Client info
user_agent: str = Header(...)
x_forwarded_for: Optional[str] = Header(None)  # Client IP through proxy

# Cache control
if_none_match: Optional[str] = Header(None)  # ETag validation
```

---

## 🍪 Cookie() - Browser Cookies

### What Are Cookies?

Cookies are key-value pairs stored in the browser and sent automatically with requests:

```
GET /api/profile HTTP/1.1
Cookie: session_id=abc123; theme=dark; cart_id=xyz789
```

### Basic Usage

```python
from fastapi import Cookie

@app.get("/preferences")
async def read_preferences(
    theme: str = Cookie("light", description="User theme preference")
):
    return {"theme": theme}
```

**How it works:**
- Reads `theme` cookie from request
- Returns default value `"light"` if cookie doesn't exist
- No need for `Optional[]` when default is provided

### Session Management

```python
@app.get("/profile")
async def get_profile(
    session_id: str = Cookie(..., description="Session identifier")
):
    # Validate session
    if not is_valid_session(session_id):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    user = get_user_from_session(session_id)
    return {"user": user}
```

### Setting Cookies in Response

```python
from fastapi import Response

@app.post("/login")
async def login(credentials: LoginRequest, response: Response):
    # Verify credentials
    user = authenticate(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_id = create_session(user.id)
    
    # Set cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,      # Prevent JavaScript access (XSS protection)
        secure=True,        # HTTPS only
        samesite="lax",     # CSRF protection
        max_age=3600        # 1 hour expiration
    )
    
    return {"message": "Login successful"}
```

### Secure Cookie Configuration

```python
@app.post("/auth/login")
async def secure_login(credentials: LoginRequest, response: Response):
    user = authenticate(credentials)
    token = create_jwt_token(user)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,          # ✅ Prevent XSS
        secure=True,            # ✅ HTTPS only
        samesite="strict",      # ✅ Prevent CSRF
        max_age=1800,           # ✅ 30 minutes
        domain=".example.com",  # ✅ Subdomain access
        path="/api"             # ✅ Scope to API routes
    )
    
    return {"message": "Logged in"}
```

### Reading Multiple Cookies

```python
@app.get("/cart")
async def get_cart(
    session_id: str = Cookie(...),
    cart_id: Optional[str] = Cookie(None),
    user_id: Optional[str] = Cookie(None)
):
    return {
        "session": session_id,
        "cart": cart_id or "new",
        "user": user_id
    }
```

### Deleting Cookies

```python
@app.post("/logout")
async def logout(response: Response):
    # Delete cookie by setting max_age=0
    response.delete_cookie(
        key="session_id",
        path="/",
        domain=".example.com"
    )
    
    return {"message": "Logged out successfully"}
```

---

## ⚡ Depends() - Dependency Injection

### What is Dependency Injection?

Dependency injection allows you to write reusable logic once and inject it into multiple routes.

**Benefits:**
- ✅ Code reusability
- ✅ Separation of concerns
- ✅ Easier testing
- ✅ Automatic execution before route handler
- ✅ Type safety and validation

### Basic Dependency

```python
from fastapi import Depends

def common_parameters(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    return {"q": q, "page": page, "limit": limit}

@app.get("/items")
async def list_items(commons: dict = Depends(common_parameters)):
    return {
        "query": commons["q"],
        "page": commons["page"],
        "limit": commons["limit"],
        "items": []
    }

@app.get("/products")
async def list_products(commons: dict = Depends(common_parameters)):
    # Same parameters, zero duplication!
    return commons
```

### Authentication Dependency

```python
async def get_current_user(
    authorization: str = Header(..., description="Bearer token")
) -> dict:
    """Verify JWT token and return user"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = verify_jwt_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Fetch user from database
        user = await get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Use in routes
@app.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@app.post("/posts")
async def create_post(
    post: PostCreate,
    current_user: dict = Depends(get_current_user)
):
    return {"author": current_user["username"], "post": post}
```

### Database Session Dependency

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with automatic cleanup"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@app.post("/users")
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Use db session
    new_user = User(**user.dict())
    db.add(new_user)
    # Automatically committed/rolled back
    return new_user
```

### Nested Dependencies

```python
def verify_api_key(x_api_key: str = Header(...)) -> str:
    """First level: verify API key"""
    if x_api_key != "valid-key":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

def get_current_user(
    api_key: str = Depends(verify_api_key),
    user_id: str = Header(...)
) -> dict:
    """Second level: depends on verify_api_key"""
    # API key already verified by dependency
    return {"user_id": user_id, "api_key": api_key}

@app.get("/admin")
async def admin_route(
    current_user: dict = Depends(get_current_user)
):
    """Route depends on get_current_user, which depends on verify_api_key"""
    return current_user
```

### Class-Based Dependencies

```python
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.limit = limit
        self.skip = (page - 1) * limit

@app.get("/items")
async def list_items(pagination: PaginationParams = Depends()):
    return {
        "page": pagination.page,
        "limit": pagination.limit,
        "skip": pagination.skip
    }
```

### Permission Checking

```python
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return current_user

# Create checker instances
require_admin = RoleChecker(["admin"])
require_moderator = RoleChecker(["admin", "moderator"])

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    return {"message": f"User {user_id} deleted by admin {current_user['username']}"}

@app.post("/posts/{post_id}/approve")
async def approve_post(
    post_id: str,
    current_user: dict = Depends(require_moderator)
):
    return {"message": "Post approved"}
```

### Caching Dependencies

```python
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    """Load settings once and cache"""
    return Settings()

@app.get("/config")
async def get_config(settings: Settings = Depends(get_settings)):
    # Settings loaded only once per application lifecycle
    return {"app_name": settings.app_name}
```

---

## 🔗 Combining Header, Cookie & Depends

### Complete Authentication System

```python
from typing import Optional
from datetime import datetime, timedelta
import jwt

# Settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Models
class User(BaseModel):
    id: str
    username: str
    email: str
    role: str

# Helper functions
def create_access_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Dependencies
async def get_token(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> str:
    """Get token from header or cookie"""
    token = None
    
    # Try header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    # Fallback to cookie
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return token

async def get_current_user(token: str = Depends(get_token)) -> User:
    """Verify token and return user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        # Fetch user from database
        user = await db.users.find_one({"id": user_id})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Protected routes
@app.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
```

### API Key + User Session

```python
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key"""
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

async def get_user_from_session(
    session_id: str = Cookie(...),
    api_key: str = Depends(verify_api_key)
) -> User:
    """Get user from session (API key already verified)"""
    session = await get_session(session_id)
    
    if not session or session.expired:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return await get_user(session.user_id)

@app.get("/dashboard")
async def dashboard(user: User = Depends(get_user_from_session)):
    return {"user": user, "dashboard_data": "..."}
```

---

## 🛡️ Security Best Practices

### ✅ Headers

```python
# Good: Validate header format
authorization: str = Header(..., regex="^Bearer [A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$")

# Good: Set max length
x_api_key: str = Header(..., min_length=32, max_length=64)

# Good: Optional sensitive headers
x_real_ip: Optional[str] = Header(None)

# Bad: Required sensitive headers without validation
api_key: str = Header(...)  # ❌ No validation
```

### ✅ Cookies

```python
# Good: Secure cookie settings
response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,      # ✅ Prevent XSS
    secure=True,        # ✅ HTTPS only
    samesite="strict",  # ✅ Prevent CSRF
    max_age=3600        # ✅ Expiration
)

# Bad: Insecure cookies
response.set_cookie("token", token)  # ❌ No security flags

# Good: Validate cookie format
session_id: str = Cookie(..., regex="^[a-f0-9]{32}$")
```

### ✅ Dependencies

```python
# Good: Raise specific errors
async def get_current_user(token: str = Depends(get_token)):
    try:
        # ...
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Bad: Generic error handling
async def get_current_user(token: str = Depends(get_token)):
    try:
        # ...
    except Exception:
        raise HTTPException(status_code=500)  # ❌ Too generic
```

---

## 🎨 Common Patterns

### Pattern 1: Multi-Tenant API

```python
async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Verify tenant ID from header"""
    if not is_valid_tenant(x_tenant_id):
        raise HTTPException(status_code=403, detail="Invalid tenant")
    return x_tenant_id

@app.get("/data")
async def get_data(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    # Data scoped to tenant
    return await db.data.find({"tenant_id": tenant_id})
```

### Pattern 2: Rate Limiting

```python
from datetime import datetime
from collections import defaultdict

rate_limit_store = defaultdict(list)

async def rate_limiter(
    x_api_key: str = Header(...),
    request: Request
):
    """Simple rate limiter (use Redis in production)"""
    now = datetime.utcnow()
    minute_ago = now - timedelta(minutes=1)
    
    # Clean old requests
    rate_limit_store[x_api_key] = [
        ts for ts in rate_limit_store[x_api_key]
        if ts > minute_ago
    ]
    
    # Check limit
    if len(rate_limit_store[x_api_key]) >= 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Record request
    rate_limit_store[x_api_key].append(now)
    
    return x_api_key

@app.get("/limited")
async def limited_route(api_key: str = Depends(rate_limiter)):
    return {"message": "Success"}
```

### Pattern 3: Feature Flags

```python
async def check_feature_flag(
    feature: str,
    current_user: User = Depends(get_current_user)
):
    """Check if feature is enabled for user"""
    if not is_feature_enabled(feature, current_user):
        raise HTTPException(status_code=403, detail="Feature not available")
    return True

@app.get("/beta-feature")
async def beta_feature(
    _: bool = Depends(lambda: check_feature_flag("beta_feature"))
):
    return {"message": "Beta feature"}
```

---

## ❌ Common Mistakes

### Mistake 1: Not Handling Missing Headers

```python
# ❌ Bad: Assumes header always exists
@app.get("/bad")
async def bad_route(user_agent: str = Header(...)):
    # Fails if User-Agent is missing
    return {"agent": user_agent}

# ✅ Good: Make optional or provide default
@app.get("/good")
async def good_route(user_agent: Optional[str] = Header(None)):
    return {"agent": user_agent or "Unknown"}
```

### Mistake 2: Insecure Cookie Configuration

```python
# ❌ Bad: No security flags
response.set_cookie("session", session_id)

# ✅ Good: Secure configuration
response.set_cookie(
    "session",
    session_id,
    httponly=True,
    secure=True,
    samesite="strict"
)
```

### Mistake 3: Not Reusing Dependencies

```python
# ❌ Bad: Duplicate validation logic
@app.get("/route1")
async def route1(token: str = Header(...)):
    user = verify_token(token)  # Duplicate
    return user

@app.get("/route2")
async def route2(token: str = Header(...)):
    user = verify_token(token)  # Duplicate
    return user

# ✅ Good: Reusable dependency
async def get_user(token: str = Header(...)):
    return verify_token(token)

@app.get("/route1")
async def route1(user = Depends(get_user)):
    return user

@app.get("/route2")
async def route2(user = Depends(get_user)):
    return user
```

---

## 📚 Quick Reference

See **QUICK_REFERENCE.md** for fast lookup templates and code snippets.

## 💡 Next Steps

1. Copy patterns from **example.py** to your project
2. Adapt authentication logic to your needs
3. Add proper JWT/session management
4. Implement rate limiting and security measures
5. Use dependencies to keep your code DRY

---

## 🔗 Related Modules

- **Path/Query/Body Parameters** - Request parameter handling
- **Error Handling** - Secure error responses
- **Logger** - Request/response logging

---

**Remember:** 
- Headers for authentication/metadata
- Cookies for session management
- Dependencies for reusable logic
- Always validate and secure your inputs!
