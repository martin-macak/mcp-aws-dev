from contextlib import asynccontextmanager
from typing import AsyncIterator, Tuple

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
    return app_ctx.aws_context.profile_name


@mcp.tool("aws_dev_run_script")
def aws_dev_run_script(
    script: str,
    ctx: Context,
) -> Tuple[str, str, int]:
    """
    Runs a python 3.11+ script with current AWS profile.
    This script is run in a jail environment with the current AWS profile.
    This script has following packages available:
    - boto3
    - botocore
    - jq
    - yaml
    - tomli

    AWS credentials environment variables are set automatically, so initialize
    boto3 sessions in the script with default credentials chain.

    Jailed script MUST NOT use subprocess module.
    Jailed script MUST NOT execute system commands.
    Whenever you are asked to store a file, use the MCP_ARTIFACT_DIR environment
    variable to get the directory.

    This tool returns a tuple with stdout, stderr and return code of the script.
    """

    import tempfile
    from pathlib import Path

    from mcp_aws_dev.script_runner import run_in_jail

    app_ctx: AppContext = ctx.request_context.lifespan_context
    credentials = app_ctx.aws_context.get_session_credentials()

    work_dir = Path(tempfile.mkdtemp())
    stdout, stderr, return_code = run_in_jail(
        work_dir=work_dir,
        script=script,
        aws_credentials=credentials,
        env={},
    )

    if return_code != 0:
        raise Exception(f"Script failed with return code {return_code}")

    return stdout, stderr, return_code


def main():
    mcp.run()


if __name__ == "__main__":
    main()
