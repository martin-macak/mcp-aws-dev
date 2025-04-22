from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

from mcp_aws_dev.dynamodb_schema import DynamoDBSchemaAnalyzer


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
