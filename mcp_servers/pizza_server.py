#!/usr/bin/env python3
"""
MCP Server for Pizza Ordering
Handles pizza orders (simulated - would integrate with real API)
"""
from typing import Optional
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PizzaServer")


class PizzaOrder(BaseModel):
    size: str
    toppings: list[str]
    quantity: int
    delivery_address: str


@mcp.tool()
def order_pizza(
    size: str,
    toppings: str,
    quantity: int = 1,
    delivery_address: Optional[str] = None
) -> str:
    """
    Order pizza for delivery.
    
    Args:
        size: Pizza size (small/medium/large/xlarge)
        toppings: Comma-separated list of toppings
        quantity: Number of pizzas (default: 1)
        delivery_address: Delivery address (required)
    
    Returns:
        Order confirmation with estimated delivery time
    """
    try:
        if not delivery_address:
            return "Error: Delivery address is required to place an order."
        
        valid_sizes = ['small', 'medium', 'large', 'xlarge']
        size = size.lower()
        
        if size not in valid_sizes:
            return f"Error: Invalid size '{size}'. Please choose from: {', '.join(valid_sizes)}"
        
        topping_list = [t.strip() for t in toppings.split(',')]
        
        price_map = {'small': 8.99, 'medium': 12.99, 'large': 15.99, 'xlarge': 18.99}
        base_price = price_map[size] * quantity
        topping_price = len(topping_list) * 1.50 * quantity
        total_price = base_price + topping_price
        
        order_summary = f"""
🍕 Pizza Order Confirmed! 🍕

Order Details:
- Size: {size.title()}
- Toppings: {', '.join(topping_list)}
- Quantity: {quantity}
- Delivery Address: {delivery_address}

Pricing:
- Pizza(s): ${base_price:.2f}
- Toppings: ${topping_price:.2f}
- Total: ${total_price:.2f}

Estimated delivery time: 30-45 minutes

NOTE: This is a simulated order. To place a real order, integrate with Domino's API, 
Pizza Hut API, or other pizza delivery service APIs.

Order ID: PIZZA-{hash(delivery_address) % 10000}
"""
        return order_summary
    
    except Exception as e:
        return f"Error placing order: {str(e)}"


@mcp.tool()
def ask_pizza_preferences() -> str:
    """
    Ask user for their pizza preferences before ordering.
    
    Returns:
        Questions to gather order details
    """
    return """To order pizza for you, I need to know:
1. What size pizza would you like? (small/medium/large/xlarge)
2. What toppings do you want? (e.g., pepperoni, mushrooms, olives)
3. How many pizzas?
4. What's your delivery address?

Please provide these details so I can place your order."""


@mcp.tool()
def get_menu() -> str:
    """
    Get the pizza menu with available sizes and toppings.
    
    Returns:
        Menu information
    """
    return """
🍕 Pizza Menu 🍕

Sizes & Prices:
- Small (10"): $8.99
- Medium (12"): $12.99
- Large (14"): $15.99
- XLarge (16"): $18.99

Available Toppings ($1.50 each):
- Pepperoni
- Italian Sausage
- Ham
- Bacon
- Mushrooms
- Onions
- Green Peppers
- Black Olives
- Pineapple
- Jalapenos
- Extra Cheese

Special Combos:
- Meat Lovers: Pepperoni, Sausage, Ham, Bacon
- Veggie Delight: Mushrooms, Onions, Green Peppers, Black Olives
- Hawaiian: Ham, Pineapple
- Supreme: Pepperoni, Sausage, Mushrooms, Onions, Green Peppers

Delivery: Free for orders over $20
Estimated delivery time: 30-45 minutes
"""


if __name__ == "__main__":
    mcp.run(transport="stdio")
