"""
Exception Handling Best Practices - Logging vs HTTPException

This file demonstrates the correct way to handle exceptions in FastAPI:
1. Log detailed errors for developers
2. Return safe, user-friendly messages to clients
"""

from fastapi import APIRouter, HTTPException, status
from logger.logger import get_logger

logger = get_logger("routes.error_handling_examples")
router = APIRouter(prefix="/examples", tags=["Error Handling Examples"])


# ============================================================================
# PATTERN 1: Client Error (4xx) - User made a mistake
# ============================================================================

@router.post("/users")
async def create_user(email: str, password: str):
    """
    Pattern for handling client errors (validation, bad input, etc.)
    """
    try:
        # Validate email
        if "@" not in email:
            # Log the issue (INFO or WARNING level)
            logger.warning(f"Invalid email format attempted: {email}")
            
            # Return clear error to client
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password
        if len(password) < 8:
            logger.warning(f"Weak password attempted for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Success
        logger.info(f"User created successfully: {email}")
        return {"email": email, "status": "created"}
        
    except HTTPException:
        # Re-raise HTTPExceptions (they're already handled)
        raise
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error creating user {email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )


# ============================================================================
# PATTERN 2: Server Error (5xx) - Something broke on our side
# ============================================================================

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """
    Pattern for handling server errors (database, external APIs, etc.)
    """
    try:
        # Simulate database query
        if product_id == 999:
            # Simulate database error
            raise ConnectionError("Database connection timeout")
        
        logger.info(f"Product {product_id} retrieved successfully")
        return {"id": product_id, "name": f"Product {product_id}"}
        
    except ConnectionError as e:
        # Log FULL error details with stack trace for debugging
        logger.error(
            f"Database connection failed for product {product_id}: {e}",
            exc_info=True  # This logs the full stack trace
        )
        
        # Return GENERIC error to client (don't expose DB details!)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later."
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(
            f"Unexpected error retrieving product {product_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the product"
        )


# ============================================================================
# PATTERN 3: Resource Not Found (404)
# ============================================================================

@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    """
    Pattern for handling resource not found scenarios
    """
    try:
        # Simulate checking if order exists
        order_exists = order_id != 404  # Simplified check
        
        if not order_exists:
            # Log at INFO or WARNING level (this is expected behavior)
            logger.info(f"Order not found: {order_id}")
            
            # Return 404 to client
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        
        logger.info(f"Order {order_id} retrieved successfully")
        return {"id": order_id, "status": "delivered"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the order"
        )


# ============================================================================
# PATTERN 4: External API Failure
# ============================================================================

@router.post("/payments")
async def process_payment(amount: float, card_number: str):
    """
    Pattern for handling external service failures
    """
    try:
        # Simulate calling external payment API
        if amount > 10000:
            raise ValueError("Payment gateway rejected transaction")
        
        logger.info(f"Payment processed successfully: ${amount}")
        return {"status": "success", "amount": amount}
        
    except ValueError as e:
        # Log the specific error (but NOT sensitive card data!)
        logger.warning(f"Payment rejected for amount ${amount}: {e}")
        
        # Return user-friendly message
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment could not be processed. Please try a different card."
        )
        
    except Exception as e:
        # Log with full context
        logger.error(
            f"Payment processing failed for amount ${amount}: {e}",
            exc_info=True
        )
        
        # Generic error to client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing failed. Please try again later."
        )


# ============================================================================
# ANTI-PATTERN: What NOT to do
# ============================================================================

@router.post("/bad-example")
async def bad_error_handling(data: dict):
    """
    ❌ BAD - This exposes internal errors to clients!
    """
    try:
        # Some operation
        result = 1 / 0  # This will raise ZeroDivisionError
        return result
        
    except Exception as e:
        # ❌ BAD: Exposing internal error details to client
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"  # Shows "division by zero" to client!
        )
        # Also BAD: No logging! You won't know what happened.


# ============================================================================
# BEST PRACTICE: Complete error handling
# ============================================================================

@router.post("/best-practice")
async def good_error_handling(data: dict):
    """
    ✅ GOOD - Proper logging + safe error messages
    """
    try:
        # Your business logic here
        result = {"status": "success"}
        logger.info("Operation completed successfully")
        return result
        
    except ValueError as e:
        # Expected errors (validation, business logic)
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
        
    except ConnectionError as e:
        # Infrastructure errors
        logger.error(f"Connection error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
        
    except Exception as e:
        # Unexpected errors - log everything for debugging
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"
        )


# ============================================================================
# BONUS: When you DON'T need HTTPException
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Simple endpoints that always succeed don't need try/except
    """
    logger.debug("Health check called")
    return {"status": "healthy"}
