import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError

from mcp_aws_dev.knowledge_base import list_knowledge_bases, query_knowledge_base


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the list_knowledge_bases cache before each test."""
    list_knowledge_bases.cache_clear()


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
        "profile/my-org-ai-tools/MyOrgAiToolsAdmin:R0QO4WPOIJ/my-org-sw-engineer-kb,profile/my-org-ai-tools/MyOrgAiToolsAdmin:ABC123/another-kb",
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
        "profile/my-org-ai-tools/MyOrgAiToolsAdmin:R0QO4WPOIJ/my-org-sw-engineer-kb,invalid-format",
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


def test_aws_list_knowledge_bases_missing_env_var(monkeypatch):
    """Test listing knowledge bases when environment variable is not set."""
    # Setup
    monkeypatch.delenv("AWS_KNOWLEDGE_BASES", raising=False)

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


def test_query_knowledge_base_success():
    """Test successful knowledge base query."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = "What is the capital of France?"

    mock_response = {
        "output": {"text": "The capital of France is Paris."},
        "citations": [
            {
                "generatedResponsePart": {"textResponsePart": {"text": "Paris"}},
                "retrievedReferences": [
                    {
                        "content": {"text": "Paris is the capital of France."},
                        "location": {"type": "S3", "uri": "s3://bucket/key"},
                    }
                ],
            }
        ],
    }

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.return_value = mock_response

        # Execute
        result = query_knowledge_base(session, knowledge_base_id, query)

        # Verify
        assert result.answer == "The capital of France is Paris."
        assert len(result.citations) == 1
        mock_bedrock.retrieve_and_generate.assert_called_once_with(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": knowledge_base_id,
                    "modelArn": f"arn:aws:bedrock:{session.region_name}::foundation-model/eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
                },
            },
        )


def test_query_knowledge_base_not_found():
    """Test knowledge base query when knowledge base is not found."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "non-existent-kb"
    query = "What is the capital of France?"

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}},
            "RetrieveAndGenerate",
        )

        # Execute and verify
        with pytest.raises(ValueError, match=f"Knowledge base with ID {knowledge_base_id} not found"):
            query_knowledge_base(session, knowledge_base_id, query)


def test_query_knowledge_base_error():
    """Test knowledge base query when an error occurs."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = "What is the capital of France?"

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError"}},
            "RetrieveAndGenerate",
        )

        # Execute and verify
        with pytest.raises(ClientError):
            query_knowledge_base(session, knowledge_base_id, query)


def test_query_knowledge_base_empty_query():
    """Test knowledge base query with empty query string."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = ""

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.return_value = {
            "output": {"text": ""},
            "citations": [],
        }

        # Execute
        result = query_knowledge_base(session, knowledge_base_id, query)

        # Verify
        assert result.answer == ""
        assert len(result.citations) == 0


def test_query_knowledge_base_missing_fields():
    """Test knowledge base query with missing response fields."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = "What is the capital of France?"

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.return_value = {
            "output": {"text": "The capital of France is Paris."},
            # Missing citations
        }

        # Execute
        result = query_knowledge_base(session, knowledge_base_id, query)

        # Verify
        assert result.answer == "The capital of France is Paris."
        assert len(result.citations) == 0


def test_query_knowledge_base_different_model():
    """Test knowledge base query with different model ARN."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = "What is the capital of France?"

    mock_response = {
        "output": {"text": "The capital of France is Paris."},
        "citations": [],
    }

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.return_value = mock_response

        # Execute
        result = query_knowledge_base(session, knowledge_base_id, query)

        # Verify
        assert result.answer == "The capital of France is Paris."
        mock_bedrock.retrieve_and_generate.assert_called_once_with(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": knowledge_base_id,
                    "modelArn": f"arn:aws:bedrock:{session.region_name}::foundation-model/eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
                },
            },
        )


def test_query_knowledge_base_access_denied():
    """Test knowledge base query when access is denied."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = "What is the capital of France?"

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException"}},
            "RetrieveAndGenerate",
        )

        # Execute and verify
        with pytest.raises(ClientError) as exc_info:
            query_knowledge_base(session, knowledge_base_id, query)
        assert exc_info.value.response["Error"]["Code"] == "AccessDeniedException"


def test_query_knowledge_base_throttling():
    """Test knowledge base query when throttled."""
    # Setup
    session = boto3.Session()
    knowledge_base_id = "test-kb-id"
    query = "What is the capital of France?"

    with patch("boto3.Session.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.retrieve_and_generate.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException"}},
            "RetrieveAndGenerate",
        )

        # Execute and verify
        with pytest.raises(ClientError) as exc_info:
            query_knowledge_base(session, knowledge_base_id, query)
        assert exc_info.value.response["Error"]["Code"] == "ThrottlingException" 