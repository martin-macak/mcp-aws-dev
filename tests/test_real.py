from unittest.mock import MagicMock

import pytest


@pytest.mark.skip(reason="This test is real and requires a real AWS profile.")
def test_aws_dev_get_dynamodb_schema(monkeypatch):
    from mcp_aws_dev.server import aws_dev_get_dynamodb_schema

    monkeypatch.setenv("MCP_DATABASE_SCHEMA_REGISTRY", "database")

    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.aws_context.profile_name = (
        "vertice-saas-rnd-v1/AdministratorAccess"
    )

    result = aws_dev_get_dynamodb_schema(
        table_name="vertice-doc-proc-queues",
        ctx=mock_ctx,
    )
    assert result is not None
