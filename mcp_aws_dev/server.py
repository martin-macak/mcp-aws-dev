import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Tuple

import boto3
from mcp.server.fastmcp import Context, FastMCP

from mcp_aws_dev.context import AppContext, AWSContext
from mcp_aws_dev.dynamodb_schema import DynamoDBSchemaAnalyzer
from mcp_aws_dev.knowledge_base import (KnowledgeBase,
                                        KnowledgeBaseQueryResponse,
                                        list_knowledge_bases,
                                        query_knowledge_base)


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


@mcp.tool("aws_dev_get_dynamodb_schema")
def aws_dev_get_dynamodb_schema(
    table_name: str,
    artifact_name: str,
    ctx: Context,
) -> str:
    """
    Get the schema for a DynamoDB table and save it to an artifact file with given name.
    Schema is in JSONSchema-Draft-04 format.
    The artifact is saved in the MCP_ARTIFACT_DIR environment variable.
    Returns the path to the artifact file.
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context
    profile_name = app_ctx.aws_context.profile_name
    session = boto3.Session(
        profile_name=profile_name,
    )

    analyzer = DynamoDBSchemaAnalyzer(
        session=session,
        table_name=table_name,
    )
    schema = analyzer.get_table_schema()
    schema_str = json.dumps(schema)

    artifact_dir = Path(os.environ["MCP_ARTIFACT_DIR"])
    artifact_path = artifact_dir / artifact_name
    artifact_path.write_text(schema_str)
    return str(artifact_path)


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


@mcp.tool("aws_list_knowledge_bases")
def aws_list_knowledge_bases(ctx: Context) -> list[KnowledgeBase]:
    """List knowledge bases from AWS_KNOWLEDGE_BASES environment variable.

    This function checks the AWS_KNOWLEDGE_BASES environment variable for knowledge base
    configurations. Each knowledge base should be in the format:
    profile/${awsProfile}:${knowledgeBaseId}/${knowledgeBaseName}

    :return: JSON string containing knowledge bases
    :rtype: str
    :raises ValueError: If AWS_KNOWLEDGE_BASES environment variable is not set
    """
    return list_knowledge_bases()


def aws_dev_query_knowledge_base(
    knowledge_base: str,
    query: str,
    ctx: Context,
) -> KnowledgeBaseQueryResponse:
    """Query a knowledge base using Amazon Bedrock.

    This function queries a knowledge base using Amazon Bedrock's knowledge base API.
    It first finds the matching knowledge base by ID or name, then uses the associated
    AWS profile to create a session and query the knowledge base.

    :param knowledge_base: The ID or name of the knowledge base to query.
    :type knowledge_base: str
    :param query: The query to send to the knowledge base.
    :type query: str
    :param ctx: The context object containing the application context.
    :type ctx: Context
    :return: The response from the knowledge base query.
    :rtype: KnowledgeBaseQueryResponse
    :raises ValueError: If no matching knowledge base is found.
    """
    # Get all knowledge bases
    knowledge_bases = list_knowledge_bases()

    # Find matching knowledge base by ID or name
    matching_kb = None
    for kb in knowledge_bases:
        if (
            kb.knowledge_base_id == knowledge_base
            or kb.knowledge_base_name == knowledge_base
        ):
            matching_kb = kb
            break

    if not matching_kb:
        raise ValueError(f"No knowledge base found with ID or name: {knowledge_base}")

    # Create AWS session with the profile from the knowledge base
    session = boto3.Session(profile_name=matching_kb.aws_profile)

    # Query the knowledge base
    return query_knowledge_base(
        session=session,
        knowledge_base_id=matching_kb.knowledge_base_id,
        query=query,
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
