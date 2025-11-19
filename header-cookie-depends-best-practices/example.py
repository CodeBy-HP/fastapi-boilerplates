"""
Production-Ready Header, Cookie & Depends Examples

This file demonstrates all common patterns for Headers, Cookies, and Dependency Injection.
Each example is production-ready and can be copied directly to your project.

USAGE:
1. Copy the pattern that matches your use case
2. Adapt to your specific authentication/business logic
3. Run with: uvicorn example:app --reload

Key Concepts:
- Header: Read HTTP headers (Authorization, API keys, tracking)
- Cookie: Read/set browser cookies (sessions, preferences)
- Depends: Inject reusable logic (auth, DB, validation)
"""

from fastapi import FastAPI, APIRouter, HTTPException, Header, Cookie, Depends, Response, Query, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import jwt
from functools import lru_cache

app = FastAPI(
    title="Header, Cookie & Depends Best Practices",
    description="Production-ready patterns for headers, cookies, and dependency injection",
    version="1.0.0"
)

router = APIRouter(prefix="/api", tags=["examples"])


# ============================================================================
# CONFIGURATION & MODELS
# ============================================================================

# Settings
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VALID_API_KEYS = {"sk_live_1234567890", "sk_test_0987654321"}

class UserRole(str, Enum):
    """User roles for permission checking"""
    admin = "admin"
    moderator = "moderator"
    user = "user"

class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool = True

class LoginRequest(BaseModel):
    """Login credentials"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Mock database
MOCK_USERS = {
    "john_doe": {
        "id": "user-123",
        "username": "john_doe",
        "email": "john@example.com",
        "password": "hashed_password_here",  # In production: use bcrypt
        "role": UserRole.admin,
        "is_active": True
    },
    "jane_smith": {
        "id": "user-456",
        "username": "jane_smith",
        "email": "jane@example.com",
        "password": "hashed_password_here",
        "role": UserRole.user,
        "is_active": True
    }
}

MOCK_SESSIONS = {}  # session_id -> user_id


# ============================================================================
# PATTERN 1: Header() - HTTP Headers
# ============================================================================

@router.get("/headers/user-agent")
async def read_user_agent(
    user_agent: str = Header(..., description="Client user agent")
):
    """
    Read User-Agent header.
    
    Example request:
    GET /api/headers/user-agent
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
    
    FastAPI converts user_agent -> User-Agent automatically.
    """
    return {
        "user_agent": user_agent,
        "is_mobile": "Mobile" in user_agent,
        "is_bot": "bot" in user_agent.lower()
    }


@router.get("/headers/optional")
async def read_optional_headers(
    user_agent: Optional[str] = Header(None, description="Client user agent"),
    referer: Optional[str] = Header(None, description="Referrer URL"),
    x_request_id: Optional[str] = Header(None, description="Request correlation ID")
):
    """
    Read optional headers with defaults.
    
    Example:
    GET /api/headers/optional
    User-Agent: Chrome
    X-Request-ID: req-12345
    """
    return {
        "user_agent": user_agent or "Unknown",
        "referer": referer,
        "request_id": x_request_id
    }


@router.get("/headers/api-key")
async def verify_api_key(
    x_api_key: str = Header(
        ...,
        description="API key for authentication",
        min_length=10,
        max_length=100
    )
):
    """
    API key authentication via header.
    
    Example:
    GET /api/headers/api-key
    X-API-Key: sk_live_1234567890
    
    Security: Validate API key format and value.
    """
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return {
        "message": "API key valid",
        "key": x_api_key[:10] + "..."  # Don't expose full key
    }


@router.get("/headers/custom-name")
async def custom_header_name(
    # Use alias to specify exact header name
    tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier")
):
    """
    Custom header name using alias.
    
    Example:
    GET /api/headers/custom-name
    X-Tenant-ID: tenant-abc-123
    """
    return {"tenant_id": tenant_id}


# ============================================================================
# PATTERN 2: Cookie() - Browser Cookies
# ============================================================================

@router.get("/cookies/theme")
async def get_theme(
    theme: str = Cookie("light", description="User theme preference")
):
    """
    Read cookie with default value.
    
    Example request:
    GET /api/cookies/theme
    Cookie: theme=dark
    
    Returns "light" if cookie not set.
    """
    return {
        "theme": theme,
        "is_dark_mode": theme == "dark"
    }


@router.post("/cookies/set-theme")
async def set_theme(
    theme: str = Query(..., regex="^(light|dark)$"),
    response: Response = None
):
    """
    Set theme cookie.
    
    Example:
    POST /api/cookies/set-theme?theme=dark
    
    Response includes Set-Cookie header.
    """
    response.set_cookie(
        key="theme",
        value=theme,
        max_age=31536000,  # 1 year
        httponly=False,    # Allow JavaScript access for theme switching
        samesite="lax"
    )
    
    return {"message": f"Theme set to {theme}"}


@router.get("/cookies/preferences")
async def get_preferences(
    theme: str = Cookie("light"),
    language: str = Cookie("en"),
    timezone: str = Cookie("UTC")
):
    """
    Read multiple cookies.
    
    Example request:
    GET /api/cookies/preferences
    Cookie: theme=dark; language=es; timezone=America/New_York
    """
    return {
        "theme": theme,
        "language": language,
        "timezone": timezone
    }


@router.get("/cookies/cart")
async def get_cart(
    cart_id: Optional[str] = Cookie(None, description="Shopping cart ID")
):
    """
    Optional cookie for cart tracking.
    
    Creates new cart if cookie not present.
    """
    if not cart_id:
        cart_id = f"cart-{datetime.utcnow().timestamp()}"
        # In production, save to database
    
    return {
        "cart_id": cart_id,
        "items": []  # Fetch from database
    }


# ============================================================================
# PATTERN 3: Authentication with Headers & Cookies
# ============================================================================

def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, response: Response):
    """
    Login with username/password.
    Sets JWT token in cookie and returns it.
    
    Example:
    POST /api/auth/login
    Body: {"username": "john_doe", "password": "password123"}
    
    Response includes Set-Cookie header with access_token.
    """
    # Verify credentials
    user_data = MOCK_USERS.get(credentials.username)
    
    if not user_data or user_data["password"] != credentials.password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    if not user_data["is_active"]:
        raise HTTPException(status_code=403, detail="Account is inactive")
    
    # Create JWT token
    access_token = create_access_token(user_data["id"])
    
    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,          # Prevent XSS
        secure=True,            # HTTPS only (set to False for local dev)
        samesite="lax",         # CSRF protection
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/auth/logout")
async def logout(response: Response):
    """
    Logout by deleting access token cookie.
    
    Example:
    POST /api/auth/logout
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


# ============================================================================
# PATTERN 4: Depends() - Dependency Injection
# ============================================================================

# Dependency 1: Extract token from header or cookie
async def get_token(
    authorization: Optional[str] = Header(None, description="Bearer token"),
    access_token: Optional[str] = Cookie(None, description="JWT token from cookie")
) -> str:
    """
    Get JWT token from Authorization header or cookie.
    
    Tries header first (for API clients), then cookie (for browsers).
    """
    token = None
    
    # Try Authorization header
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format. Use: Bearer <token>"
            )
        token = authorization.replace("Bearer ", "")
    
    # Fallback to cookie
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Provide token in header or cookie."
        )
    
    return token


# Dependency 2: Verify token and get current user
async def get_current_user(token: str = Depends(get_token)) -> User:
    """
    Verify JWT token and return current user.
    
    This dependency requires get_token dependency (nested).
    """
    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Find user in database
        user_data = None
        for username, data in MOCK_USERS.items():
            if data["id"] == user_id:
                user_data = data
                break
        
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user_data["is_active"]:
            raise HTTPException(status_code=403, detail="Account is inactive")
        
        return User(**user_data)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Dependency 3: Verify API key
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify X-API-Key header"""
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


# Protected routes using dependencies
@router.get("/protected/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Protected route - requires valid JWT token.
    
    Example with header:
    GET /api/protected/profile
    Authorization: Bearer <token>
    
    Example with cookie:
    GET /api/protected/profile
    Cookie: access_token=<token>
    """
    return {
        "user": current_user,
        "message": "This is your protected profile"
    }


@router.get("/protected/admin-only")
async def admin_only(current_user: User = Depends(get_current_user)):
    """
    Admin-only route.
    
    Requires authentication + admin role check.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return {
        "message": "Welcome, admin!",
        "admin": current_user.username
    }


@router.get("/protected/api-key")
async def api_key_route(api_key: str = Depends(verify_api_key)):
    """
    Route protected by API key.
    
    Example:
    GET /api/protected/api-key
    X-API-Key: sk_live_1234567890
    """
    return {
        "message": "API key verified",
        "key_prefix": api_key[:10]
    }


# ============================================================================
# PATTERN 5: Advanced Dependencies
# ============================================================================

# Class-based dependency for pagination
class PaginationParams:
    """Reusable pagination parameters"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.limit = limit
        self.skip = (page - 1) * limit
    
    def to_dict(self):
        return {
            "page": self.page,
            "limit": self.limit,
            "skip": self.skip
        }


@router.get("/items")
async def list_items(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    List items with pagination.
    
    Example:
    GET /api/items?page=2&limit=50
    Authorization: Bearer <token>
    
    Uses two dependencies:
    - PaginationParams for query params
    - get_current_user for authentication
    """
    return {
        "user": current_user.username,
        "pagination": pagination.to_dict(),
        "items": []  # Your data here
    }


# Permission checker dependency (callable class)
class RoleChecker:
    """Check if user has required role"""
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Create permission checker instances
require_admin = RoleChecker([UserRole.admin])
require_moderator = RoleChecker([UserRole.admin, UserRole.moderator])


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(require_admin)
):
    """
    Delete post - admin only.
    
    Uses RoleChecker dependency to enforce permissions.
    """
    return {
        "message": f"Post {post_id} deleted",
        "deleted_by": current_user.username
    }


@router.post("/posts/{post_id}/approve")
async def approve_post(
    post_id: str,
    current_user: User = Depends(require_moderator)
):
    """
    Approve post - admin or moderator.
    
    Uses RoleChecker with multiple allowed roles.
    """
    return {
        "message": f"Post {post_id} approved",
        "approved_by": current_user.username,
        "role": current_user.role
    }


# ============================================================================
# PATTERN 6: Database Session Dependency
# ============================================================================

class FakeDatabase:
    """Simulated database connection"""
    def __init__(self):
        self.connected = True
    
    async def query(self, sql: str):
        return f"Executing: {sql}"
    
    async def close(self):
        self.connected = False


async def get_db() -> AsyncGenerator[FakeDatabase, None]:
    """
    Database session dependency with automatic cleanup.
    
    Uses yield to provide session and ensure cleanup.
    """
    db = FakeDatabase()
    try:
        yield db
    finally:
        await db.close()


@router.get("/database/query")
async def query_database(
    db: FakeDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query database with automatic connection cleanup.
    
    Database session is automatically closed after request.
    """
    result = await db.query(f"SELECT * FROM users WHERE id = '{current_user.id}'")
    return {"result": result}


# ============================================================================
# PATTERN 7: Settings Dependency (Cached)
# ============================================================================

class Settings(BaseModel):
    """Application settings"""
    app_name: str = "FastAPI Boilerplate"
    environment: str = "production"
    debug: bool = False
    api_version: str = "1.0.0"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).
    
    Settings are loaded once and cached for application lifetime.
    """
    return Settings()


@router.get("/config")
async def get_config(settings: Settings = Depends(get_settings)):
    """
    Get application configuration.
    
    Settings dependency is cached - only created once.
    """
    return settings


# ============================================================================
# PATTERN 8: Combining Multiple Dependencies
# ============================================================================

async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract and validate tenant ID"""
    # Validate tenant exists
    if not x_tenant_id.startswith("tenant-"):
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    return x_tenant_id


@router.get("/multi-tenant/data")
async def get_tenant_data(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(),
    api_key: str = Depends(verify_api_key)
):
    """
    Multi-tenant data access with multiple dependencies.
    
    Example:
    GET /api/multi-tenant/data?page=1&limit=20
    X-Tenant-ID: tenant-abc-123
    X-API-Key: sk_live_1234567890
    Authorization: Bearer <token>
    
    Combines:
    - Tenant validation (header)
    - API key verification (header)
    - User authentication (token)
    - Pagination (query params)
    """
    return {
        "tenant_id": tenant_id,
        "user": current_user.username,
        "pagination": pagination.to_dict(),
        "api_key_valid": True,
        "data": []
    }


# ============================================================================
# APP SETUP
# ============================================================================

app.include_router(router)


@app.get("/")
async def root():
    """API information"""
    return {
        "message": "Header, Cookie & Depends Best Practices API",
        "docs": "/docs",
        "examples": {
            "headers": {
                "user_agent": "GET /api/headers/user-agent",
                "api_key": "GET /api/headers/api-key (X-API-Key header)"
            },
            "cookies": {
                "theme": "GET /api/cookies/theme",
                "set_theme": "POST /api/cookies/set-theme?theme=dark"
            },
            "auth": {
                "login": "POST /api/auth/login",
                "profile": "GET /api/protected/profile (requires token)",
                "admin": "GET /api/protected/admin-only (requires admin role)"
            },
            "dependencies": {
                "pagination": "GET /api/items?page=1&limit=20",
                "permissions": "DELETE /api/posts/{id} (admin only)",
                "multi_tenant": "GET /api/multi-tenant/data"
            }
        },
        "test_credentials": {
            "admin": {"username": "john_doe", "password": "hashed_password_here"},
            "user": {"username": "jane_smith", "password": "hashed_password_here"}
        }
    }


# ============================================================================
# USAGE NOTES
# ============================================================================

"""
KEY TAKEAWAYS:

1. HEADER()
   - Read HTTP headers from requests
   - Use for: API keys, tokens, tracking, metadata
   - FastAPI converts snake_case to Hyphen-Case
   - Always validate (min_length, max_length, regex)
   - Use Optional[] for optional headers

2. COOKIE()
   - Read browser cookies from requests
   - Use for: sessions, preferences, tracking
   - Set cookies with response.set_cookie()
   - Security flags: httponly, secure, samesite
   - Provide defaults: Cookie("default_value")

3. DEPENDS()
   - Inject reusable logic into routes
   - Use for: auth, DB sessions, validation, permissions
   - Can be nested (dependencies can have dependencies)
   - Supports async/sync, classes, generators
   - Use @lru_cache() for cached dependencies

4. AUTHENTICATION PATTERNS
   - JWT tokens in Authorization header or cookie
   - API keys in custom headers (X-API-Key)
   - Session IDs in cookies
   - Multi-factor: API key + user token

5. SECURITY BEST PRACTICES
   - Validate all header/cookie inputs
   - Use httponly=True for sensitive cookies
   - Set secure=True in production (HTTPS)
   - Use samesite="strict" or "lax"
   - Never expose full tokens in responses
   - Implement proper error messages

6. COMMON DEPENDENCY PATTERNS
   - get_current_user: Authentication
   - get_db: Database session
   - pagination: Reusable query params
   - RoleChecker: Permission verification
   - get_settings: Cached configuration

COPY THESE PATTERNS TO YOUR PROJECT AND ADAPT AS NEEDED!
"""
