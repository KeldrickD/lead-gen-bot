import os
import stripe
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('payment_api')

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Create router
router = APIRouter()

# Models
class PaymentOption(BaseModel):
    type: str
    link: str
    amount: float
    package: str
    remaining: Optional[float] = None

class PaymentOptionsRequest(BaseModel):
    lead_id: str
    package_type: str

class PaymentOptionsResponse(BaseModel):
    options: List[PaymentOption]

# Simple API key auth
def verify_api_key(x_api_key: str = Header(None)):
    api_key = os.environ.get("API_KEY")
    if not api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@router.post("/api/payment-options", response_model=PaymentOptionsResponse)
async def create_payment_options(
    request: PaymentOptionsRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Create payment options (deposit and full payment) for a lead.
    Returns links to payment pages for both options.
    """
    try:
        # Get package details
        package_details = {
            "basic": {"name": "Basic Business Website", "full_price": 497, "deposit": 500},
            "ecommerce": {"name": "E-commerce Store", "full_price": 997, "deposit": 500},
            "custom": {"name": "Custom Web Application", "full_price": 1997, "deposit": 500}
        }
        
        # Default to basic if package type isn't recognized
        if request.package_type.lower() not in package_details:
            request.package_type = "basic"
            
        package_info = package_details[request.package_type.lower()]
        package_name = package_info["name"]
        
        try:
            # Create deposit payment option
            deposit_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{package_name} - Deposit",
                            "description": f"$500 deposit for {package_name}"
                        },
                        "unit_amount": 50000,  # $500.00 in cents
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url="https://your-website.com/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://your-website.com/canceled",
                metadata={
                    "lead_id": request.lead_id,
                    "package_type": request.package_type,
                    "payment_type": "deposit"
                }
            )
            
            # Create full payment option
            full_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": package_name,
                            "description": f"Full payment for {package_name}"
                        },
                        "unit_amount": package_info["full_price"] * 100,  # Convert to cents
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url="https://your-website.com/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://your-website.com/canceled",
                metadata={
                    "lead_id": request.lead_id,
                    "package_type": request.package_type,
                    "payment_type": "full"
                }
            )
            
            # Return both payment options
            return PaymentOptionsResponse(
                options=[
                    PaymentOption(
                        type="deposit",
                        link=deposit_session.url,
                        amount=500,
                        remaining=package_info["full_price"] - 500,
                        package=package_name
                    ),
                    PaymentOption(
                        type="full",
                        link=full_session.url,
                        amount=package_info["full_price"],
                        package=package_name
                    )
                ]
            )
            
        except Exception as e:
            logger.error(f"Error creating Stripe payment options: {e}")
            
            # Fallback to mock URLs during development
            base_url = "https://buy.stripe.com/yourAccountLink/"
            
            return PaymentOptionsResponse(
                options=[
                    PaymentOption(
                        type="deposit",
                        link=f"{base_url}{request.package_type}_deposit_500",
                        amount=500,
                        remaining=package_info["full_price"] - 500,
                        package=package_name
                    ),
                    PaymentOption(
                        type="full",
                        link=f"{base_url}{request.package_type}_full_{package_info['full_price']}",
                        amount=package_info["full_price"],
                        package=package_name
                    )
                ]
            )
            
    except Exception as e:
        logger.error(f"Error generating payment options: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 