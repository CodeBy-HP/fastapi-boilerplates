# 🔐 Header, Cookie & Depends - Quick Reference

Fast lookup for HTTP headers, cookies, and dependency injection in FastAPI.

---

## 📋 Quick Decision Tree

```
Need to READ metadata from request? → Header()
    Examples: Authorization, API keys, User-Agent, X-Request-ID

Need to READ/SET browser state? → Cookie()
    Examples: session_id, theme, cart_id, preferences

Need to REUSE logic across routes? → Depends()
    Examples: Authentication, DB sessions, permissions, pagination
```

---

## 🎯 Header() Templates

### Basic Header
```python
from fastapi import Header
from typing import Optional

# Required header
user_agent: str = Header(..., description="Client user agent")

# Optional header
referer: Optional[str] = Header(None)

# Header with validation
x_api_key: str = Header(
    ...,
    min_length=20,
    max_length=100,
    description="API key"
)
```

### Common Headers
```python
# Authorization (Bearer token)
authorization: str = Header(
    ...,
    regex="^Bearer [A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$"
)

# API Key
x_api_key: str = Header(..., min_length=32, max_length=64)

# Tenant ID
x_tenant_id: str = Header(..., description="Tenant identifier")

# Request ID
x_request_id: Optional[str] = Header(None)

# User Agent
user_agent: str = Header(...)

# Client IP (through proxy)
x_forwarded_for: Optional[str] = Header(None)

# Content Type
content_type: str = Header("application/json")
```

### Custom Header Name
```python
# Use alias to override automatic conversion
tenant_id: str = Header(..., alias="X-Tenant-ID")
```

### Header Validation
```python
# String length
x_api_key: str = Header(..., min_length=10, max_length=100)

# Regex pattern
authorization: str = Header(..., regex="^Bearer .+")

# With description (for docs)
x_custom: str = Header(..., description="Custom header for tracking")
```

---

## 🍪 Cookie() Templates

### Basic Cookie
```python
from fastapi import Cookie
from typing import Optional

# With default value
theme: str = Cookie("light")

# Required cookie
session_id: str = Cookie(..., description="Session identifier")

# Optional cookie
cart_id: Optional[str] = Cookie(None)
```

### Reading Cookies
```python
@app.get("/profile")
async def get_profile(
    session_id: str = Cookie(...),
    theme: str = Cookie("light"),
    language: str = Cookie("en")
):
    return {"session": session_id, "theme": theme, "lang": language}
```

### Setting Cookies
```python
from fastapi import Response

@app.post("/login")
async def login(credentials: LoginRequest, response: Response):
    # Authenticate user
    session_id = create_session(user)
    
    # Set secure cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,      # ✅ Prevent XSS
        secure=True,        # ✅ HTTPS only
        samesite="strict",  # ✅ Prevent CSRF
        max_age=3600        # ✅ 1 hour
    )
    
    return {"message": "Logged in"}
```

### Cookie Security Flags
```python
# Production-ready cookie settings
response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,          # No JavaScript access (XSS protection)
    secure=True,            # HTTPS only (set False for local dev)
    samesite="strict",      # CSRF protection ("lax" or "none" alternatives)
    max_age=3600,           # Expiration in seconds
    domain=".example.com",  # Cookie domain (optional)
    path="/api"             # Cookie path (optional)
)
```

### Deleting Cookies
```python
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session_id")
    return {"message": "Logged out"}
```

---

## ⚡ Depends() Templates

### Basic Dependency
```python
from fastapi import Depends

def common_params(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    return {"q": q, "page": page, "limit": limit}

@app.get("/items")
async def list_items(commons: dict = Depends(common_params)):
    return commons
```

### Authentication Dependency
```python
async def get_current_user(
    authorization: str = Header(..., description="Bearer token")
) -> User:
    """Verify token and return user"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")
    
    token = authorization.replace("Bearer ", "")
    user = verify_jwt_token(token)
    
    if not user:
        raise HTTPException(401, "Invalid token")
    
    return user

# Use in routes
@app.get("/me")
async def get_profile(user: User = Depends(get_current_user)):
    return user
```

### Token from Header or Cookie
```python
async def get_token(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> str:
    """Get token from header (API) or cookie (browser)"""
    token = None
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    return token

async def get_current_user(token: str = Depends(get_token)) -> User:
    """Nested dependency - requires get_token"""
    return verify_token(token)
```

### Database Session
```python
async def get_db() -> AsyncGenerator[Session, None]:
    """Provide DB session with automatic cleanup"""
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
    db: Session = Depends(get_db)
):
    # Use db, automatically committed/closed
    new_user = User(**user.dict())
    db.add(new_user)
    return new_user
```

### Class-Based Dependency
```python
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100)
    ):
        self.page = page
        self.limit = limit
        self.skip = (page - 1) * limit

@app.get("/items")
async def list_items(pagination: PaginationParams = Depends()):
    return {"page": pagination.page, "skip": pagination.skip}
```

### Permission Checker (Callable Class)
```python
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return user

# Create instances
require_admin = RoleChecker(["admin"])
require_moderator = RoleChecker(["admin", "moderator"])

@app.delete("/users/{id}")
async def delete_user(
    id: str,
    user: User = Depends(require_admin)
):
    return {"message": "User deleted"}
```

### Cached Settings
```python
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    """Load settings once and cache"""
    return Settings()

@app.get("/config")
async def config(settings: Settings = Depends(get_settings)):
    # Settings loaded only once
    return settings
```

---

## 🔗 Common Combinations

### JWT Auth (Header or Cookie)
```python
async def get_token(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    elif access_token:
        return access_token
    raise HTTPException(401, "Not authenticated")

async def get_user(token: str = Depends(get_token)) -> User:
    return verify_jwt(token)

@app.get("/protected")
async def protected(user: User = Depends(get_user)):
    return user
```

### API Key + User Auth
```python
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    if x_api_key not in VALID_KEYS:
        raise HTTPException(403, "Invalid API key")
    return x_api_key

async def get_user(
    api_key: str = Depends(verify_api_key),
    session_id: str = Cookie(...)
) -> User:
    # API key verified, now check session
    return get_user_from_session(session_id)

@app.get("/data")
async def get_data(user: User = Depends(get_user)):
    return {"user": user}
```

### Multi-Tenant
```python
async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    if not is_valid_tenant(x_tenant_id):
        raise HTTPException(403, "Invalid tenant")
    return x_tenant_id

@app.get("/data")
async def get_data(
    tenant_id: str = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends()
):
    return {"tenant": tenant_id, "user": user.id}
```

---

## 🛡️ Security Cheatsheet

### Header Security
```python
✅ Validate format and length
x_api_key: str = Header(..., min_length=32, max_length=64)

✅ Use regex for patterns
authorization: str = Header(..., regex="^Bearer .+")

✅ Make optional when appropriate
x_request_id: Optional[str] = Header(None)

❌ Don't expose sensitive data in responses
return {"api_key": api_key[:10] + "..."}  # Truncate
```

### Cookie Security
```python
✅ Always use httponly for auth cookies
httponly=True  # Prevent XSS

✅ Use secure in production
secure=True  # HTTPS only

✅ Set samesite
samesite="strict"  # or "lax"

✅ Set expiration
max_age=3600  # 1 hour

❌ Don't store sensitive data in plain cookies
# Use encrypted sessions or JWT
```

### Dependency Security
```python
✅ Validate all inputs
async def get_user(token: str = Depends(get_token)):
    if not token:
        raise HTTPException(401)
    # ...

✅ Use specific error codes
raise HTTPException(401, "Token expired")  # Not generic 500

✅ Clean up resources
async def get_db():
    db = Database()
    try:
        yield db
    finally:
        await db.close()  # Always cleanup
```

---

## 📝 Common Patterns

### Pattern 1: Login & Set Cookie
```python
@app.post("/login")
async def login(creds: LoginRequest, response: Response):
    user = authenticate(creds)
    token = create_jwt(user)
    
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600
    )
    
    return {"access_token": token}
```

### Pattern 2: Protected Route
```python
@app.get("/protected")
async def protected(user: User = Depends(get_current_user)):
    return {"message": f"Hello, {user.username}"}
```

### Pattern 3: Admin Only
```python
require_admin = RoleChecker(["admin"])

@app.delete("/users/{id}")
async def delete_user(
    id: str,
    user: User = Depends(require_admin)
):
    return {"deleted": id}
```

### Pattern 4: Pagination
```python
class Pagination:
    def __init__(self, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
        self.page = page
        self.limit = limit
        self.skip = (page - 1) * limit

@app.get("/items")
async def list_items(p: Pagination = Depends()):
    return {"page": p.page, "skip": p.skip}
```

### Pattern 5: Logout
```python
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
```

---

## 🎯 Quick Comparison

| Feature | When to Use | Example |
|---------|-------------|---------|
| **Header()** | API keys, tokens, metadata | `x_api_key: str = Header(...)` |
| **Cookie()** | Sessions, preferences | `session_id: str = Cookie(...)` |
| **Depends()** | Reusable logic | `user = Depends(get_current_user)` |

---

## 💡 Pro Tips

### Tip 1: Header Name Conversion
```python
# FastAPI converts snake_case to Hyphen-Case
user_agent: str = Header(...)  # Reads: User-Agent
x_api_key: str = Header(...)   # Reads: X-Api-Key

# Override with alias
api_key: str = Header(..., alias="X-API-Key")  # Reads: X-API-Key
```

### Tip 2: Token Priority
```python
# Try header first (API clients), then cookie (browsers)
async def get_token(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> str:
    return extract_from_header(authorization) or access_token or raise_401()
```

### Tip 3: Nested Dependencies
```python
# Dependencies can depend on other dependencies
async def get_token(...) -> str:
    ...

async def get_user(token: str = Depends(get_token)) -> User:
    ...

@app.get("/route")
async def route(user: User = Depends(get_user)):
    # get_user called → get_token called → route called
    ...
```

### Tip 4: Dependency Caching
```python
# Same dependency called multiple times in one request?
# FastAPI caches the result automatically!

@app.get("/route")
async def route(
    user1: User = Depends(get_current_user),
    user2: User = Depends(get_current_user)
):
    # get_current_user only called ONCE
    # user1 and user2 are the same object
    ...
```

---

## 🔄 Complete Auth Flow

```python
# 1. Login endpoint
@app.post("/auth/login")
async def login(creds: LoginRequest, response: Response):
    user = authenticate(creds)
    token = create_jwt(user.id)
    
    response.set_cookie("access_token", token, httponly=True, secure=True)
    return {"access_token": token}

# 2. Token extraction
async def get_token(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    elif access_token:
        return access_token
    raise HTTPException(401, "Not authenticated")

# 3. User verification
async def get_current_user(token: str = Depends(get_token)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]})
        if not user:
            raise HTTPException(401, "User not found")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")

# 4. Protected routes
@app.get("/me")
async def me(user: User = Depends(get_current_user)):
    return user

# 5. Logout
@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
```

---

## 📚 Resources

- **Full Examples**: See `example.py` in this directory
- **Detailed Guide**: See `README.md` for comprehensive explanations
- **FastAPI Docs**: https://fastapi.tiangolo.com/tutorial/dependencies/
- **Security**: https://fastapi.tiangolo.com/tutorial/security/

---

**Quick Summary**:
- **Header()** = Read request metadata
- **Cookie()** = Read/set browser state
- **Depends()** = Inject reusable logic
