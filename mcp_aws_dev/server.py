from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import Context, FastMCP

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


@mcp.tool("aws_dev_get_profile")
def aws_dev_get_profile(ctx: Context) -> str:
    """
    Returns then name of the current AWS profile.
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context
    return app_ctx.aws_context.profile_name


@mcp.tool("aws_dev_change_profile")
def aws_dev_change_profile(
    profile_name: str,
    ctx: Context,
) -> str:
    """
    Change the AWS profile.
    This will change the profile for the current session.
    """

    app_ctx: AppContext = ctx.request_context.lifespan_context
    app_ctx.aws_context.profile_name = profile_name


def main():
    mcp.run()


if __name__ == "__main__":
    main()
