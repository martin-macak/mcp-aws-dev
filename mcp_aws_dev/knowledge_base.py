"""Knowledge base related functionality.

This module provides functionality for working with AWS knowledge bases.
"""

import functools
import os
import re
from typing import List

import boto3
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError


class KnowledgeBase(BaseModel):
    """Represents a knowledge base configuration.

    :ivar knowledgeBaseId: The ID of the knowledge base.
    :type knowledgeBaseId: str
    :ivar knowledgeBaseName: The name of the knowledge base.
    :type knowledgeBaseName: str
    """

    knowledgeBaseId: str = Field(description="The ID of the knowledge base.")
    knowledgeBaseName: str = Field(description="The name of the knowledge base.")


class KnowledgeBasesResponse(BaseModel):
    """Represents the response containing knowledge bases.

    :ivar knowledgeBases: List of knowledge bases.
    :type knowledgeBases: List[KnowledgeBase]
    """

    knowledgeBases: List[KnowledgeBase] = Field(description="List of knowledge bases.")


class KnowledgeBaseQueryResponse(BaseModel):
    """Represents the response containing knowledge base query.

    :ivar answer: The answer to the query.
    :type answer: str
    :ivar citations: List of citations used to generate the answer.
    :type citations: List[dict]
    """

    answer: str = Field(description="The answer to the query.")
    citations: List[dict] = Field(description="List of citations used to generate the answer.")


@functools.cache
def list_knowledge_bases() -> str:
    """List knowledge bases from AWS_KNOWLEDGE_BASES environment variable.

    This function checks the AWS_KNOWLEDGE_BASES environment variable for knowledge base
    configurations. Each knowledge base should be in the format:
    profile/${awsProfile}:${knowledgeBaseId}/${knowledgeBaseName}

    For example:
    profile/my-org-ai-tools/MyOrgAiToolsAdmin:R0QO4WPOIJ/my-org-sw-engineer-kb
    is
    awsProfile = my-org-ai-tools/MyOrgAiToolsAdmin
    knowledgeBaseId = R0QO4WPOIJ
    knowledgeBaseName = my-org-sw-engineer-kb

    :return: JSON string containing knowledge bases
    :rtype: str
    :raises ValueError: If AWS_KNOWLEDGE_BASES environment variable is not set or empty
    """
    try:
        knowledge_bases_str = os.environ["AWS_KNOWLEDGE_BASES"].strip()
        if not knowledge_bases_str:
            raise ValueError("AWS_KNOWLEDGE_BASES environment variable is not set")
    except KeyError:
        raise ValueError("AWS_KNOWLEDGE_BASES environment variable is not set")

    knowledge_bases = []
    for kb_str in knowledge_bases_str.split(","):
        kb_str = kb_str.strip()
        if not kb_str:
            continue

        # Match pattern: profile/${awsProfile}:${knowledgeBaseId}/${knowledgeBaseName}
        match = re.match(
            r"profile/([^:]+):([^/]+)/(.+)$",
            kb_str,
        )
        if not match:
            continue

        knowledge_bases.append(
            KnowledgeBase(
                knowledgeBaseId=match.group(2),
                knowledgeBaseName=match.group(3),
            )
        )

    response = KnowledgeBasesResponse(knowledgeBases=knowledge_bases)
    return response.model_dump_json(indent=2)


def query_knowledge_base(
    session: boto3.Session,
    knowledge_base_id: str,
    query: str,
) -> KnowledgeBaseQueryResponse:
    """Query a knowledge base using Amazon Bedrock.

    This function queries a knowledge base using Amazon Bedrock's knowledge base API.
    It returns a response containing the answer, citations, confidence score, and source attributions.

    :param session: The boto3 session to use for the query.
    :type session: boto3.Session
    :param knowledge_base_id: The ID of the knowledge base to query.
    :type knowledge_base_id: str
    :param query: The query to send to the knowledge base.
    :type query: str
    :return: The response from the knowledge base query.
    :rtype: KnowledgeBaseQueryResponse
    :raises ValueError: If the knowledge base ID is not found.
    :raises ClientError: If there is an error querying the knowledge base.
    """
    aws_region = session.region_name
    bedrock_client = session.client("bedrock-agent-runtime")

    try:
        response = bedrock_client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": knowledge_base_id,
                    "modelArn": f"arn:aws:bedrock:{aws_region}::foundation-model/eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
                },
            },
        )

        return KnowledgeBaseQueryResponse(
            answer=response["output"]["text"],
            citations=response.get("citations", []),
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise ValueError(f"Knowledge base with ID {knowledge_base_id} not found")
        raise
