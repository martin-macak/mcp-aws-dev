from typing import Iterator

import boto3
from boto3.dynamodb.types import TypeDeserializer

from mcp_aws_dev.schema import SchemaInferenceAnalyzer


class DynamoDBSchemaAnalyzer:
    def __init__(
        self,
        session: boto3.Session,
        table_name: str,
    ):
        self.session = session
        self.table_name = table_name

    def analyze(self) -> dict:
        analyzer = SchemaInferenceAnalyzer()

        sample_iterator = self.open_sample_iterator(
            num_records=1000,
        )

        for record in sample_iterator:
            analyzer.add_data_sample(record)

        return analyzer.infer_schema(schema_type="JSONSchema-Draft-07")

    def open_sample_iterator(
        self,
        num_records: int,
        page_size: int = 100,
    ) -> Iterator[dict]:
        """Open an iterator to scan a DynamoDB table with pagination.

        This method scans a DynamoDB table and returns an iterator that yields
        deserialized records. It uses pagination to handle large tables efficiently.

        :param num_records: Maximum number of records to return
        :type num_records: int
        :param page_size: Number of records to fetch per page
        :type page_size: int
        :return: Iterator that yields deserialized records
        :rtype: Iterator[dict]
        """
        dynamodb_client = self.session.client("dynamodb")
        paginator = dynamodb_client.get_paginator("scan")
        deserializer = TypeDeserializer()

        records_processed = 0

        for page in paginator.paginate(
            TableName=self.table_name, PaginationConfig={"PageSize": page_size}
        ):
            for item in page.get("Items", []):
                if records_processed >= num_records:
                    return

                # Convert DynamoDB format to Python dict
                deserialized_item = {
                    k: deserializer.deserialize(v) for k, v in item.items()
                }
                yield deserialized_item
                records_processed += 1
