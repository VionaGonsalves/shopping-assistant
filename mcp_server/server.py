from dotenv import load_dotenv
load_dotenv()

import logging
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

# Log to stderr: stdout is reserved for MCP's own messages
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("shopping-mcp")

API_BASE_URL = os.getenv("SHOP_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("SHOP_API_TOKEN")  # the logged-in user's JWT

mcp = FastMCP("shopping-assistant")


async def call_api(method: str, path: str, **kwargs) -> dict | list:
    """Call the shopping API as the current user."""
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10) as client:
        response = await client.request(method, path, headers=headers, **kwargs)
    if response.status_code >= 400:
        logger.warning("API error %s on %s %s", response.status_code, method, path)
        return {"error": response.status_code, "detail": response.json().get("detail")}
    return response.json()


@mcp.tool()
async def search_products(query: str) -> list | dict:
    """Search the car catalogue by name. Returns matching cars with id, name, type and price in INR.
    Use this to find a car's id before getting its price or adding it to the cart."""
    logger.info("search_products called with query=%r", query)
    return await call_api("GET", "/products", params={"q": query})

@mcp.tool()
async def get_price(product_id: int) -> dict:
    """Get the current price of one car by its id. Returns name, type and price in INR.
    Always use this (not memory) when the user asks how much a car costs.
    If you only have the car's name, call search_products first to find its id."""
    logger.info("get_price called with product_id=%s", product_id)
    return await call_api("GET", f"/products/{product_id}")


@mcp.tool()
async def add_to_cart(product_id: int, quantity: int = 1) -> dict:
    """Add a car to the current user's cart. If it's already in the cart, the quantity increases.
    Only call this after the user has clearly confirmed they want to add this specific car."""
    logger.info("add_to_cart called with product_id=%s quantity=%s", product_id, quantity)
    if not API_TOKEN:
        return {"error": "not_authenticated", "detail": "No user is logged in."}
    return await call_api("POST", "/cart/items", json={"product_id": product_id, "quantity": quantity})


if __name__ == "__main__":
    mcp.run()