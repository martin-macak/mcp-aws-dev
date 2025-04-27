import json

import pytest

from mcp_aws_dev.knowledge_base import list_knowledge_bases


def test_aws_list_knowledge_bases_single_entry(monkeypatch):
    """Test listing knowledge bases with a single valid entry."""
    # Setup
    monkeypatch.setenv(
        "AWS_KNOWLEDGE_BASES",
        "profile/my-org-ai-tools/MyOrgAiToolsAdmin:R0QO4WPOIJ/my-org-sw-engineer-kb",
    )

    # Execute
    result = list_knowledge_bases()

    # Verify
    expected = {
        "knowledgeBases": [
            {
                "knowledgeBaseId": "R0QO4WPOIJ",
                "knowledgeBaseName": "my-org-sw-engineer-kb",
            }
        ]
    }
    assert json.loads(result) == expected


def test_aws_list_knowledge_bases_multiple_entries(monkeypatch):
    """Test listing knowledge bases with multiple valid entries."""
    # Setup
    monkeypatch.setenv(
        "AWS_KNOWLEDGE_BASES",
        "profile/my-org-ai-tools/MyOrgAiToolsAdmin:R0QO4WPOIJ/my-org-sw-engineer-kb,"
        "profile/my-org-ai-tools/MyOrgAiToolsAdmin:ABC123/another-kb",
    )

    # Execute
    result = list_knowledge_bases()

    # Verify
    expected = {
        "knowledgeBases": [
            {
                "knowledgeBaseId": "R0QO4WPOIJ",
                "knowledgeBaseName": "my-org-sw-engineer-kb",
            },
            {
                "knowledgeBaseId": "ABC123",
                "knowledgeBaseName": "another-kb",
            },
        ]
    }
    assert json.loads(result) == expected


def test_aws_list_knowledge_bases_invalid_entry(monkeypatch):
    """Test listing knowledge bases with an invalid entry."""
    # Setup
    monkeypatch.setenv(
        "AWS_KNOWLEDGE_BASES",
        "profile/my-org-ai-tools/MyOrgAiToolsAdmin:R0QO4WPOIJ/my-org-sw-engineer-kb,"
        "invalid-format",
    )

    # Execute
    result = list_knowledge_bases()

    # Verify
    expected = {
        "knowledgeBases": [
            {
                "knowledgeBaseId": "R0QO4WPOIJ",
                "knowledgeBaseName": "my-org-sw-engineer-kb",
            }
        ]
    }
    assert json.loads(result) == expected


def test_aws_list_knowledge_bases_missing_env_var():
    """Test listing knowledge bases when environment variable is not set."""
    # Execute and verify
    with pytest.raises(ValueError, match="AWS_KNOWLEDGE_BASES environment variable is not set"):
        list_knowledge_bases()


def test_aws_list_knowledge_bases_empty_env_var(monkeypatch):
    """Test listing knowledge bases when environment variable is empty."""
    # Setup
    monkeypatch.setenv("AWS_KNOWLEDGE_BASES", "")

    # Execute and verify
    with pytest.raises(ValueError, match="AWS_KNOWLEDGE_BASES environment variable is not set"):
        list_knowledge_bases() 