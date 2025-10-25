from typing import List, Dict, Any, Optional
from enum import Enum
import requests
import json
from pathlib import Path
from pydantic import BaseModel
from ..privacy.privacy_manager import PrivacyManager

class Size(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"
    
class CrustType(str, Enum):
    THIN = "thin"
    REGULAR = "regular"
    THICK = "thick"
    STUFFED = "stuffed"
    
class Topping(BaseModel):
    name: str
    price: float
    
class Pizza(BaseModel):
    size: Size
    crust: CrustType
    toppings: List[str]
    quantity: int = 1
    
class DeliveryInfo(BaseModel):
    name: str
    phone: str
    address: str
    apt_number: Optional[str] = None
    city: str
    state: str
    zip_code: str
    delivery_instructions: Optional[str] = None
    
class PizzaOrderTool:
    """Tool for ordering pizzas from delivery services."""
    
    def __init__(self, api_key: str, privacy_manager: PrivacyManager):
        """Initialize pizza ordering tool."""
        self.api_key = api_key
        self.privacy_manager = privacy_manager
        self.base_url = "https://api.pizzadelivery.com/v1"  # Example API endpoint
        self.available_toppings = self._load_toppings()
        
    def _load_toppings(self) -> Dict[str, Topping]:
        """Load available toppings from configuration."""
        toppings_file = Path("config/toppings.json")
        if not toppings_file.exists():
            # Create default toppings file
            default_toppings = {
                "pepperoni": {"name": "Pepperoni", "price": 2.00},
                "mushrooms": {"name": "Mushrooms", "price": 1.50},
                "onions": {"name": "Onions", "price": 1.00},
                "sausage": {"name": "Sausage", "price": 2.00},
                "bacon": {"name": "Bacon", "price": 2.50},
                "extra_cheese": {"name": "Extra Cheese", "price": 1.50},
                "green_peppers": {"name": "Green Peppers", "price": 1.00},
                "olives": {"name": "Olives", "price": 1.00}
            }
            toppings_file.parent.mkdir(exist_ok=True)
            toppings_file.write_text(json.dumps(default_toppings, indent=4))
            return {k: Topping(**v) for k, v in default_toppings.items()}
            
        with toppings_file.open() as f:
            toppings = json.load(f)
            return {k: Topping(**v) for k, v in toppings.items()}
            
    def calculate_price(self, pizza: Pizza) -> float:
        """Calculate price for a pizza based on size, crust, and toppings."""
        # Base prices for different sizes
        base_prices = {
            Size.SMALL: 10.00,
            Size.MEDIUM: 12.00,
            Size.LARGE: 14.00,
            Size.XLARGE: 16.00
        }
        
        # Additional cost for premium crusts
        crust_prices = {
            CrustType.THIN: 0.00,
            CrustType.REGULAR: 0.00,
            CrustType.THICK: 1.00,
            CrustType.STUFFED: 2.50
        }
        
        # Calculate total price
        total = base_prices[pizza.size] + crust_prices[pizza.crust]
        
        # Add toppings
        for topping in pizza.toppings:
            if topping in self.available_toppings:
                total += self.available_toppings[topping].price
                
        return total * pizza.quantity
        
    def validate_delivery_info(self, info: DeliveryInfo) -> List[str]:
        """Validate delivery information."""
        errors = []
        
        # Phone number format (simple check)
        if not info.phone.replace("-", "").isdigit():
            errors.append("Invalid phone number format")
            
        # ZIP code format
        if not info.zip_code.isdigit() or len(info.zip_code) != 5:
            errors.append("Invalid ZIP code")
            
        # Required fields
        if not info.name or len(info.name.strip()) < 2:
            errors.append("Name is required")
            
        if not info.address or len(info.address.strip()) < 5:
            errors.append("Valid address is required")
            
        return errors
        
    def place_order(
        self,
        pizzas: List[Pizza],
        delivery_info: DeliveryInfo,
        payment_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Place a pizza delivery order.
        
        Args:
            pizzas: List of pizzas to order
            delivery_info: Delivery information
            payment_info: Payment information (card details, etc.)
            
        Returns:
            dict: Order confirmation details
        """
        if self.privacy_manager.is_sensitive_data("payment"):
            if not self.privacy_manager.ask_permission("process", "payment"):
                return {"error": "Payment not authorized"}
                
        # Validate delivery information
        errors = self.validate_delivery_info(delivery_info)
        if errors:
            return {"error": "Invalid delivery information", "details": errors}
            
        # Calculate total price
        total = sum(self.calculate_price(pizza) for pizza in pizzas)
        
        # Prepare order payload
        order = {
            "pizzas": [pizza.dict() for pizza in pizzas],
            "delivery_info": delivery_info.dict(),
            "payment_info": payment_info,  # In real implementation, encrypt sensitive data
            "total": total
        }
        
        try:
            # In a real implementation, this would call the actual pizza delivery API
            # For demonstration, we'll simulate a successful order
            order_id = "12345"  # Would be generated by the API
            
            return {
                "order_id": order_id,
                "status": "confirmed",
                "estimated_delivery": "30-45 minutes",
                "total": total,
                "delivery_info": delivery_info.dict()
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    def track_order(self, order_id: str) -> Dict[str, Any]:
        """
        Track the status of an order.
        
        Args:
            order_id: Order ID to track
            
        Returns:
            dict: Order status and tracking information
        """
        try:
            # In a real implementation, this would call the API to get status
            # For demonstration, return simulated status
            return {
                "order_id": order_id,
                "status": "in_progress",
                "current_step": "preparation",
                "estimated_delivery": "25 minutes",
                "driver_location": {
                    "latitude": 30.7233,
                    "longitude": -96.3202
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pizza order if it hasn't been prepared yet.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        try:
            # In a real implementation, this would call the API to cancel
            # For demonstration, always return success
            return True
            
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False