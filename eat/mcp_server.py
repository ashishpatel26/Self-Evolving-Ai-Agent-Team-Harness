"""Custom MCP server (component 7): order tools the agents call over stdio.

Run standalone: uv run python -m eat.mcp_server
"""
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("support-tools")

# ponytail: in-memory orders, swap for the real order API.
ORDERS = {"1042": "in transit, arrives tomorrow", "1043": "delayed at the carrier", "1044": "delivered"}


@mcp.tool()
def lookup_order(order_id: str) -> str:
    """Return the shipping status of an order id such as 1042."""
    return f"Order {order_id}: {ORDERS.get(order_id, 'not found')}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
