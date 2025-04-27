"""Knowledge base related functionality.

This module provides functionality for working with AWS knowledge bases.
"""

import os
import re
from typing import List

from pydantic import BaseModel, Field


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
    :raises ValueError: If AWS_KNOWLEDGE_BASES environment variable is not set
    """
    knowledge_bases_str = os.environ.get("AWS_KNOWLEDGE_BASES")
    if not knowledge_bases_str:
        raise ValueError("AWS_KNOWLEDGE_BASES environment variable is not set")

    knowledge_bases = []
    for kb_str in knowledge_bases_str.split(","):
        # Match pattern: profile/${awsProfile}:${knowledgeBaseId}/${knowledgeBaseName}
        match = re.match(
            r"profile/([^:]+):([^/]+)/(.+)$",
            kb_str.strip(),
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