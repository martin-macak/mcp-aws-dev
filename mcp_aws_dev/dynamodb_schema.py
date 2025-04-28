import json
import os
from typing import Iterator

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

from mcp_aws_dev.schema import SchemaInferenceAnalyzer


class DynamoDBSchemaAnalyzer:
    def __init__(
        self,
        session: boto3.Session,
        table_name: str,
    ):
        self.session = session
        self.table_name = table_name

    def get_table_schema(
        self,
        filter_expression: str | None = None,
        expression_attribute_values: dict | None = None,
        expression_attribute_names: dict | None = None,
    ) -> dict:
        """Get the schema for the DynamoDB table.

        This method checks if a schema exists in the EventBridge schema registry
        and returns it if found. Otherwise, it analyzes the table and creates
        a new schema.

        :param filter_expression: Optional filter expression to apply to the scan
        :type filter_expression: str | None
        :param expression_attribute_values: Values for the expression attributes in the filter expression
        :type expression_attribute_values: dict | None
        :param expression_attribute_names: Names for the expression attributes in the filter expression
        :type expression_attribute_names: dict | None
        :return: The schema for the DynamoDB table
        :rtype: dict
        """
        registry_name = os.environ.get("MCP_DATABASE_SCHEMA_REGISTRY")
        if not registry_name:
            return self.analyze(filter_expression=filter_expression)

        schemas_client = self.session.client("schemas")
        schema_name = f"aws.dynamodb@{self.table_name}"

        try:
            # Check if schema exists
            schemas_client.describe_schema(
                RegistryName=registry_name,
                SchemaName=schema_name,
            )
            # If we get here, schema exists, get its latest version
            response = schemas_client.describe_schema(
                RegistryName=registry_name,
                SchemaName=schema_name,
            )
            return json.loads(response["Content"])
        except ClientError as e:
            if (
                e.response["Error"]["Code"] == "ResourceNotFoundException"
                or e.response["Error"]["Code"] == "NotFoundException"
            ):
                # Schema doesn't exist, analyze and create it
                schema = self.analyze(
                    filter_expression=filter_expression,
                    expression_attribute_values=expression_attribute_values,
                    expression_attribute_names=expression_attribute_names,
                )

                try:
                    # Create new schema version
                    schemas_client.create_schema(
                        RegistryName=registry_name,
                        SchemaName=schema_name,
                        Type="JSONSchemaDraft4",
                        Content=json.dumps(schema),
                    )
                except ClientError as create_error:
                    if (
                        create_error.response["Error"]["Code"]
                        == "ResourceNotFoundException"
                    ):
                        # Registry doesn't exist, just return the schema
                        pass
                    else:
                        raise

                return schema
            else:
                raise

    def analyze(
        self,
        filter_expression: str | None = None,
    ) -> dict:
        """Analyze the DynamoDB table and infer its schema.

        :param filter_expression: Optional filter expression to apply to the scan
        :type filter_expression: str | None
        :return: The inferred schema for the DynamoDB table
        :rtype: dict
        """
        analyzer = SchemaInferenceAnalyzer()

        sample_iterator = self.open_sample_iterator(
            num_records=10000,
            page_size=100,
            filter_expression=filter_expression,
        )

        for record in sample_iterator:
            analyzer.add_data_sample(record)

        return analyzer.infer_schema(schema_type="JSONSchema-Draft-07")

    def open_sample_iterator(
        self,
        num_records: int,
        page_size: int = 100,
        filter_expression: str | None = None,
        expression_attribute_values: dict | None = None,
        expression_attribute_names: dict | None = None,
    ) -> Iterator[dict]:
        """Open an iterator to scan a DynamoDB table with pagination.

        This method scans a DynamoDB table and returns an iterator that yields
        deserialized records. It uses pagination to handle large tables efficiently.

        :param num_records: Maximum number of records to return
        :type num_records: int
        :param page_size: Number of records to fetch per page
        :type page_size: int
        :param filter_expression: Optional filter expression to apply to the scan
        :type filter_expression: str | None
        :param expression_attribute_values: Values for the expression attributes in the filter expression
        :type expression_attribute_values: dict | None
        :param expression_attribute_names: Names for the expression attributes in the filter expression
        :type expression_attribute_names: dict | None
        :return: Iterator that yields deserialized records
        :rtype: Iterator[dict]
        """
        dynamodb_client = self.session.client("dynamodb")
        paginator = dynamodb_client.get_paginator("scan")
        deserializer = TypeDeserializer()

        records_processed = 0
        scan_params = {
            "TableName": self.table_name,
            "PaginationConfig": {"PageSize": page_size},
        }
        if filter_expression:
            scan_params["FilterExpression"] = filter_expression
            if expression_attribute_values:
                scan_params["ExpressionAttributeValues"] = expression_attribute_values
            if expression_attribute_names:
                scan_params["ExpressionAttributeNames"] = expression_attribute_names

        for page in paginator.paginate(**scan_params):
            for item in page.get("Items", []):
                if records_processed >= num_records:
                    return

                # Convert DynamoDB format to Python dict
                deserialized_item = {
                    k: deserializer.deserialize(v) for k, v in item.items()
                }
                yield _sanitize_dynamodb_item(deserialized_item)
                records_processed += 1


def _sanitize_dynamodb_item(item: dict) -> dict:
    """Sanitize a DynamoDB item to remove any non-serializable values.

    Decimal is converted to int if it's a whole number, otherwise it's
    converted to float.

    :param item: The DynamoDB item to sanitize
    :type item: dict
    :return: The sanitized DynamoDB item
    :rtype: dict
    """
    from decimal import Decimal

    def _convert_value(value):
        if isinstance(value, Decimal):
            # Convert Decimal to int if it's a whole number, otherwise to float
            if value % 1 == 0:
                return int(value)
            return float(value)
        elif isinstance(value, dict):
            return {k: _convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_convert_value(v) for v in value]
        return value

    return _convert_value(item)
