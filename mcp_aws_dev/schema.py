from typing import Literal

from genson import SchemaBuilder

SchemaType = Literal["JSONSchema-Draft-07",]


class SchemaInferenceAnalyzer:
    """A class for inferring JSON Schema from data samples.

    This class uses the genson library to analyze data samples and infer a JSON Schema.
    It supports JSON Schema Draft-07 format.

    :ivar _builder: The SchemaBuilder instance used for schema inference
    :type _builder: SchemaBuilder
    """

    def __init__(
        self,
    ):
        """Initialize the SchemaInferenceAnalyzer.

        Creates a new SchemaBuilder instance for schema inference.
        """
        self._builder = SchemaBuilder()

    def add_data_sample(self, record: dict):
        """Add a record to the data sample for schema inference.

        :param record: A dictionary representing a data record
        :type record: dict
        """
        self._builder.add_object(record)

    def infer_schema(
        self,
        schema_type: SchemaType,
    ) -> dict:
        """Infer a JSON Schema from the collected data samples.

        :param schema_type: The type of JSON Schema to generate (currently only
            supports JSONSchema-Draft-07)
        :type schema_type: SchemaType
        :return: The inferred JSON Schema as a dictionary
        :rtype: dict
        :raises ValueError: If an unsupported schema type is provided
        """
        if schema_type != "JSONSchema-Draft-07":
            raise ValueError(f"Unsupported schema type: {schema_type}")

        schema = self._builder.to_schema()

        # Ensure the schema always has a type field
        if "type" not in schema:
            schema["type"] = "object"

        return schema
