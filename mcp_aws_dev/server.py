from contextlib import asynccontextmanager
from typing import AsyncIterator
import anyio
import click
import httpx
import mcp.types as types
from mcp.server.fastmcp import Context, FastMCP

if __name__ == "server_module":
    # get parent folder of this module
    import sys
    from pathlib import Path
    from os.path import dirname
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