"""
Example: Complete Error Handling Integration for FastAPI

This file demonstrates how to implement proper error handling patterns
in your FastAPI application with logging.

Copy these patterns to your own routes!
"""

from fastapi import FastAPI, APIRouter, HTTPException, status, Request
from contextlib import asynccontextmanager
from logger.logger import get_logger  # Assumes you have the logger boilerplate

# ============================================
# SETUP
# ============================================

# Get logger for main module
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with error logging"""
    try:
        logger.info("🚀 Application starting...")
        # Your startup logic here
        yield
    except Exception as e:
        logger.critical(f"Startup failed: {e}", exc_info=True)
        raise
    finally:
        logger.info("🛑 Application shutting down...")


app = FastAPI(title="Error Handling Example", lifespan=lifespan)


# ============================================
# PATTERN 1: CLIENT ERRORS (4xx)
# ============================================

router_users = APIRouter(prefix="/users", tags=["Users"])
users_logger = get_logger("routes.users")


@router_users.post("/")
async def create_user(email: str, password: str, age: int):
    """
    Pattern: Validation errors (400)
    - Log at WARNING level
    - Return specific error message
    - Status: 400 Bad Request
    """
    try:
        # Validation
        if "@" not in email:
            users_logger.warning(f"Invalid email format: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        if len(password) < 8:
            users_logger.warning(f"Weak password attempt for {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        if age < 18:
            users_logger.warning(f"Underage registration attempt: {age}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must be 18 or older to register"
            )
        
        # Simulate user creation
        user_id = 123  # Would come from database
        users_logger.info(f"User created successfully: {email}")
        
        return {
            "id": user_id,
            "email": email,
            "message": "User created successfully"
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
        
    except Exception as e:
        # Unexpected errors
        users_logger.error(f"Unexpected error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )


@router_users.get("/{user_id}")
async def get_user(user_id: int):
    """
    Pattern: Resource not found (404)
    - Log at INFO level (expected scenario)
    - Return specific message
    - Status: 404 Not Found
    """
    try:
        # Simulate database lookup
        user_exists = user_id != 999  # 999 doesn't exist
        
        if not user_exists:
            users_logger.info(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        users_logger.info(f"User retrieved: {user_id}")
        return {"id": user_id, "email": f"user{user_id}@example.com"}
        
    except HTTPException:
        raise
        
    except Exception as e:
        users_logger.error(f"Error retrieving user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


# ============================================
# PATTERN 2: SERVER ERRORS (5xx)
# ============================================

router_products = APIRouter(prefix="/products", tags=["Products"])
products_logger = get_logger("routes.products")


@router_products.get("/{product_id}")
async def get_product(product_id: int):
    """
    Pattern: Database/Infrastructure errors (500/503)
    - Log at ERROR level with full traceback
    - Return GENERIC message (don't expose internals!)
    - Status: 500 or 503
    """
    try:
        # Simulate database connection error
        if product_id == 500:
            raise ConnectionError("Database connection timeout")
        
        # Simulate successful retrieval
        products_logger.info(f"Product retrieved: {product_id}")
        return {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 99.99
        }
        
    except ConnectionError as e:
        # Infrastructure error - log FULL details
        products_logger.error(
            f"Database connection failed for product {product_id}: {e}",
            exc_info=True  # Includes full stack trace
        )
        
        # Return GENERIC message to client
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later."
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Catch-all for unexpected errors
        products_logger.error(
            f"Unexpected error for product {product_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the product"
        )


# ============================================
# PATTERN 3: EXTERNAL SERVICE FAILURES
# ============================================

router_payments = APIRouter(prefix="/payments", tags=["Payments"])
payments_logger = get_logger("routes.payments")


@router_payments.post("/")
async def process_payment(amount: float, card_last4: str):
    """
    Pattern: External API failures
    - Log error details (but NOT sensitive data!)
    - Return generic message
    - Status: 502 or 503
    """
    try:
        # Simulate payment gateway call
        if amount > 10000:
            raise ValueError("Payment gateway rejected: amount too large")
        
        if amount == 404:
            raise TimeoutError("Payment gateway timeout")
        
        # Success
        payments_logger.info(
            f"Payment processed: ${amount} (card ending {card_last4})"
        )
        return {
            "status": "success",
            "amount": amount,
            "transaction_id": "txn_123456"
        }
        
    except ValueError as e:
        # Gateway rejected - log why (internal)
        payments_logger.warning(f"Payment rejected: {e}")
        
        # Generic message to client
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment could not be processed. Please try a different card."
        )
        
    except TimeoutError as e:
        # Timeout - log details
        payments_logger.error(f"Payment gateway timeout: {e}", exc_info=True)
        
        # Generic message
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Payment processor is not responding. Please try again."
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Unexpected error
        payments_logger.error(f"Payment processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing failed"
        )


# ============================================
# PATTERN 4: BUSINESS LOGIC ERRORS
# ============================================

router_orders = APIRouter(prefix="/orders", tags=["Orders"])
orders_logger = get_logger("routes.orders")


@router_orders.post("/")
async def create_order(user_id: int, product_id: int, quantity: int):
    """
    Pattern: Complex business logic with multiple failure points
    - Different exceptions for different scenarios
    - Appropriate log levels for each
    - Clear error messages
    """
    try:
        # Check inventory
        stock = 10  # Would come from database
        if quantity > stock:
            orders_logger.warning(
                f"Insufficient stock: requested {quantity}, have {stock}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only {stock} items available"
            )
        
        # Check user exists
        user_exists = user_id != 999
        if not user_exists:
            orders_logger.info(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Process order
        order_id = 456  # Would come from database
        orders_logger.info(
            f"Order created: {order_id} (user: {user_id}, product: {product_id}, qty: {quantity})"
        )
        
        return {
            "order_id": order_id,
            "status": "confirmed",
            "total": quantity * 99.99
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        orders_logger.error(f"Order creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


# ============================================
# GLOBAL EXCEPTION HANDLER (OPTIONAL)
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unhandled exceptions
    Logs the error and returns a generic 500 response
    """
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path} - {exc}",
        exc_info=True
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred"
    )


# ============================================
# INCLUDE ROUTERS
# ============================================

app.include_router(router_users)
app.include_router(router_products)
app.include_router(router_payments)
app.include_router(router_orders)


# ============================================
# SIMPLE ENDPOINTS (NO ERROR HANDLING NEEDED)
# ============================================

@app.get("/")
async def root():
    """Simple endpoint that can't fail - no try/except needed"""
    logger.debug("Root endpoint accessed")
    return {"message": "API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check - no error handling needed"""
    return {"status": "healthy", "service": "api"}


# ============================================
# RUN THE APP
# ============================================

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(
        "example_integration:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )


"""
USAGE SUMMARY:

1. Import logger:
   from logger import get_logger

2. Create logger for your module:
   logger = get_logger("routes.MODULE_NAME")

3. Wrap logic in try/except:
   try:
       # Your code
   except ValueError as e:
       logger.warning(f"Validation: {e}")
       raise HTTPException(400, "Invalid data")
   except Exception as e:
       logger.error(f"Error: {e}", exc_info=True)
       raise HTTPException(500, "Server error")

4. Test your endpoints:
   - Check logs/ directory for error logs
   - Verify clients get safe messages
   - Ensure no sensitive data in responses

That's it! 🎉
"""
