from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

if __name__ == "server_module":
    # get parent folder of this module
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))


from mcp_aws_dev.context import AppContext, AWSContext


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    try:
        yield AppContext(
            aws_context=AWSContext(
                profile_name="default",
            ),
        )

    finally:
        # Cleanup on shutdown
        pass


mcp = FastMCP("AWS Developer", lifespan=app_lifespan)


@mcp.tool("aws_dev_kokot")
def kokot() -> str:
    """
    Returns kokot and does nothing else.

    Returns:
        str: kokot
    """
    return "kokot"
