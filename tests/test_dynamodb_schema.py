import json
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws


@pytest.fixture
def dynamodb_table():
    """Create a DynamoDB table for testing."""
    with mock_aws():
        # Create a DynamoDB client
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create a table
        table = dynamodb.create_table(
            TableName="test-table",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Wait for the table to be created
        table.meta.client.get_waiter("table_exists").wait(TableName="test-table")

        # Add some test data
        table.put_item(Item={"id": "1", "name": "Item 1", "value": 100})
        table.put_item(
            Item={"id": "2", "name": "Item 2", "value": 200, "tags": ["tag1", "tag2"]}
        )
        table.put_item(
            Item={
                "id": "3",
                "name": "Item 3",
                "value": 300,
                "metadata": {"key": "value"},
            }
        )

        yield table


def test_open_sample_iterator(dynamodb_table):
    """
    Test that open_sample_iterator correctly scans a DynamoDB table
    and deserializes the results.
    """
    from mcp_aws_dev.dynamodb_schema import DynamoDBSchemaAnalyzer

    # Create a boto3 session
    session = boto3.Session(region_name="us-east-1")

    # Create a DynamoDBSchemaAnalyzer
    analyzer = DynamoDBSchemaAnalyzer(session=session, table_name="test-table")

    # Call open_sample_iterator
    iterator = analyzer.open_sample_iterator(num_records=10)

    # Convert iterator to list
    items = list(iterator)

    # Verify the results
    assert len(items) == 3

    # Check the first item
    assert items[0]["id"] == "1"
    assert items[0]["name"] == "Item 1"
    assert items[0]["value"] == 100

    # Check the second item
    assert items[1]["id"] == "2"
    assert items[1]["name"] == "Item 2"
    assert items[1]["value"] == 200
    assert items[1]["tags"] == ["tag1", "tag2"]

    # Check the third item
    assert items[2]["id"] == "3"
    assert items[2]["name"] == "Item 3"
    assert items[2]["value"] == 300
    assert items[2]["metadata"] == {"key": "value"}


def test_open_sample_iterator_with_limit(dynamodb_table):
    """Test that open_sample_iterator respects the num_records limit."""
    # Create a boto3 session
    from mcp_aws_dev.dynamodb_schema import DynamoDBSchemaAnalyzer

    session = boto3.Session(region_name="us-east-1")

    # Create a DynamoDBSchemaAnalyzer
    analyzer = DynamoDBSchemaAnalyzer(session=session, table_name="test-table")

    # Call open_sample_iterator with a limit
    iterator = analyzer.open_sample_iterator(num_records=2)

    # Convert iterator to list
    items = list(iterator)

    # Verify the results
    assert len(items) == 2


def test_open_sample_iterator_with_page_size(dynamodb_table):
    """Test that open_sample_iterator respects the page_size parameter."""
    # Create a boto3 session
    from mcp_aws_dev.dynamodb_schema import DynamoDBSchemaAnalyzer

    session = boto3.Session(region_name="us-east-1")

    # Create a DynamoDBSchemaAnalyzer
    analyzer = DynamoDBSchemaAnalyzer(session=session, table_name="test-table")

    # Mock the paginator to verify page_size is used
    with patch("boto3.Session.client") as mock_client:
        # Set up the mock
        mock_dynamodb = MagicMock()
        mock_client.return_value = mock_dynamodb

        mock_paginator = MagicMock()
        mock_dynamodb.get_paginator.return_value = mock_paginator

        # Create a mock page iterator
        mock_page_iterator = MagicMock()
        mock_paginator.paginate.return_value = mock_page_iterator

        # Set up the mock page iterator to yield one page
        mock_page_iterator.__iter__.return_value = [
            {
                "Items": [
                    {"id": {"S": "1"}, "name": {"S": "Item 1"}, "value": {"N": "100"}}
                ]
            }
        ]

        # Call open_sample_iterator
        iterator = analyzer.open_sample_iterator(num_records=10, page_size=5)

        # Convert iterator to list to trigger the pagination
        list(iterator)

        # Verify that paginate was called with the correct page size
        mock_paginator.paginate.assert_called_once()
        call_args = mock_paginator.paginate.call_args[1]
        assert call_args["PaginationConfig"]["PageSize"] == 5


@pytest.fixture
def mock_session():
    """Create a mock boto3 session.

    :return: A mock boto3 session
    :rtype: MagicMock
    """
    return MagicMock(spec=boto3.Session)


@pytest.fixture
def analyzer(mock_session):
    """Create a DynamoDBSchemaAnalyzer instance.

    :param mock_session: A mock boto3 session
    :type mock_session: MagicMock
    :return: A DynamoDBSchemaAnalyzer instance
    :rtype: DynamoDBSchemaAnalyzer
    """
    from mcp_aws_dev.dynamodb_schema import DynamoDBSchemaAnalyzer

    return DynamoDBSchemaAnalyzer(mock_session, "test-table")


def test_get_table_schema_no_registry(analyzer, monkeypatch):
    """Test get_table_schema when MCP_DATABASE_SCHEMA_REGISTRY is not set.

    :param analyzer: A DynamoDBSchemaAnalyzer instance
    :type analyzer: DynamoDBSchemaAnalyzer
    :param monkeypatch: pytest monkeypatch fixture
    :type monkeypatch: pytest.MonkeyPatch
    """
    monkeypatch.delenv("MCP_DATABASE_SCHEMA_REGISTRY", raising=False)

    mock_schema = {"type": "object", "properties": {}}
    analyzer.analyze = MagicMock(return_value=mock_schema)

    result = analyzer.get_table_schema()

    assert result == mock_schema
    analyzer.analyze.assert_called_once()


def test_get_table_schema_existing_schema(analyzer, monkeypatch):
    """Test get_table_schema when schema exists in registry.

    :param analyzer: A DynamoDBSchemaAnalyzer instance
    :type analyzer: DynamoDBSchemaAnalyzer
    :param monkeypatch: pytest monkeypatch fixture
    :type monkeypatch: pytest.MonkeyPatch
    """
    monkeypatch.setenv("MCP_DATABASE_SCHEMA_REGISTRY", "test-registry")

    mock_schemas_client = MagicMock()
    mock_schemas_client.describe_schema.return_value = {
        "Content": '{"type": "object", "properties": {}}'
    }

    analyzer.session.client.return_value = mock_schemas_client

    result = analyzer.get_table_schema()

    assert result == '{"type": "object", "properties": {}}'
    assert mock_schemas_client.describe_schema.call_count == 2
    mock_schemas_client.describe_schema.assert_has_calls(
        [
            call(RegistryName="test-registry", SchemaName="aws.dynamodb@test-table"),
            call(RegistryName="test-registry", SchemaName="aws.dynamodb@test-table"),
        ]
    )


def test_get_table_schema_create_new(analyzer, monkeypatch):
    """Test get_table_schema when schema needs to be created.

    :param analyzer: A DynamoDBSchemaAnalyzer instance
    :type analyzer: DynamoDBSchemaAnalyzer
    :param monkeypatch: pytest monkeypatch fixture
    :type monkeypatch: pytest.MonkeyPatch
    """
    monkeypatch.setenv("MCP_DATABASE_SCHEMA_REGISTRY", "test-registry")

    mock_schemas_client = MagicMock()
    mock_schemas_client.describe_schema.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException"}},
        "DescribeSchema",
    )

    mock_schema = {"type": "object", "properties": {}}
    analyzer.analyze = MagicMock(return_value=mock_schema)

    analyzer.session.client.return_value = mock_schemas_client

    result = analyzer.get_table_schema()

    assert result == mock_schema
    mock_schemas_client.create_schema.assert_called_once_with(
        RegistryName="test-registry",
        SchemaName="aws.dynamodb@test-table",
        Type="JSONSchemaDraft4",
        Content=json.dumps(mock_schema),
    )


def test_get_table_schema_registry_not_found(analyzer, monkeypatch):
    """Test get_table_schema when registry doesn't exist.

    :param analyzer: A DynamoDBSchemaAnalyzer instance
    :type analyzer: DynamoDBSchemaAnalyzer
    :param monkeypatch: pytest monkeypatch fixture
    :type monkeypatch: pytest.MonkeyPatch
    """
    monkeypatch.setenv("MCP_DATABASE_SCHEMA_REGISTRY", "test-registry")

    mock_schemas_client = MagicMock()
    mock_schemas_client.describe_schema.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException"}},
        "DescribeSchema",
    )
    mock_schemas_client.create_schema.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException"}},
        "CreateSchema",
    )

    mock_schema = {"type": "object", "properties": {}}
    analyzer.analyze = MagicMock(return_value=mock_schema)

    analyzer.session.client.return_value = mock_schemas_client

    result = analyzer.get_table_schema()

    assert result == mock_schema


@pytest.mark.parametrize(
    "input_item,expected_output",
    [
        # Test with Decimal values
        (
            {"id": Decimal("1"), "value": Decimal("100.5")},
            {"id": 1, "value": 100.5},
        ),
        # Test with nested dictionaries
        (
            {
                "id": "1",
                "metadata": {"count": Decimal("42"), "price": Decimal("99.99")},
            },
            {"id": "1", "metadata": {"count": 42, "price": 99.99}},
        ),
        # Test with lists containing Decimal values
        (
            {"id": "1", "values": [Decimal("1"), Decimal("2.5"), Decimal("3")]},
            {"id": "1", "values": [1, 2.5, 3]},
        ),
        # Test with nested lists and dictionaries
        (
            {
                "id": "1",
                "items": [
                    {"count": Decimal("10"), "price": Decimal("5.5")},
                    {"count": Decimal("20"), "price": Decimal("10.0")},
                ],
            },
            {
                "id": "1",
                "items": [
                    {"count": 10, "price": 5.5},
                    {"count": 20, "price": 10.0},
                ],
            },
        ),
        # Test with non-Decimal values (should remain unchanged)
        (
            {"id": "1", "name": "Test", "active": True, "count": 42},
            {"id": "1", "name": "Test", "active": True, "count": 42},
        ),
    ],
)
def test_sanitize_dynamodb_item(input_item, expected_output):
    """Test the _sanitize_dynamodb_item function with various input types.

    :param input_item: The input item to sanitize
    :type input_item: dict
    :param expected_output: The expected output after sanitization
    :type expected_output: dict
    """
    from mcp_aws_dev.dynamodb_schema import _sanitize_dynamodb_item

    result = _sanitize_dynamodb_item(input_item)
    assert result == expected_output
