import pytest

from mcp_aws_dev.schema import SchemaInferenceAnalyzer


def test_schema_inference_analyzer_initialization():
    """Test that the SchemaInferenceAnalyzer initializes correctly."""
    analyzer = SchemaInferenceAnalyzer()
    assert analyzer is not None


def test_add_data_sample():
    """Test adding a data sample to the analyzer."""
    analyzer = SchemaInferenceAnalyzer()
    sample_data = {"name": "John", "age": 30}
    analyzer.add_data_sample(sample_data)

    # We can't directly test the internal state, but we can infer the schema
    # and check if it contains the expected properties
    schema = analyzer.infer_schema("JSONSchema-Draft-07")
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"


def test_infer_schema_with_multiple_samples():
    """Test schema inference with multiple data samples."""
    analyzer = SchemaInferenceAnalyzer()

    # Add multiple samples with different structures
    analyzer.add_data_sample({"name": "John", "age": 30})
    analyzer.add_data_sample({"name": "Jane", "age": 25, "email": "jane@example.com"})

    schema = analyzer.infer_schema("JSONSchema-Draft-07")

    # Check that all properties are included
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "email" in schema["properties"]

    # Check property types
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"
    assert schema["properties"]["email"]["type"] == "string"


def test_infer_schema_with_nested_objects():
    """Test schema inference with nested objects."""
    analyzer = SchemaInferenceAnalyzer()

    sample_data = {
        "person": {
            "name": "John",
            "address": {"street": "123 Main St", "city": "Anytown"},
        }
    }

    analyzer.add_data_sample(sample_data)
    schema = analyzer.infer_schema("JSONSchema-Draft-07")

    # Check nested structure
    assert "properties" in schema
    assert "person" in schema["properties"]
    assert "properties" in schema["properties"]["person"]
    assert "name" in schema["properties"]["person"]["properties"]
    assert "address" in schema["properties"]["person"]["properties"]
    assert "properties" in schema["properties"]["person"]["properties"]["address"]
    assert (
        "street"
        in schema["properties"]["person"]["properties"]["address"]["properties"]
    )
    assert (
        "city" in schema["properties"]["person"]["properties"]["address"]["properties"]
    )


def test_infer_schema_with_arrays():
    """Test schema inference with arrays."""
    analyzer = SchemaInferenceAnalyzer()

    sample_data = {"tags": ["python", "testing"], "scores": [95, 87, 92]}

    analyzer.add_data_sample(sample_data)
    schema = analyzer.infer_schema("JSONSchema-Draft-07")

    # Check array properties
    assert "properties" in schema
    assert "tags" in schema["properties"]
    assert "scores" in schema["properties"]
    assert schema["properties"]["tags"]["type"] == "array"
    assert schema["properties"]["scores"]["type"] == "array"
    assert "items" in schema["properties"]["tags"]
    assert "items" in schema["properties"]["scores"]
    assert schema["properties"]["tags"]["items"]["type"] == "string"
    assert schema["properties"]["scores"]["items"]["type"] == "integer"


def test_infer_schema_with_unsupported_type():
    """Test that infer_schema raises ValueError for unsupported schema types."""
    analyzer = SchemaInferenceAnalyzer()

    # Use a type that's not in the SchemaType Literal
    with pytest.raises(ValueError, match="Unsupported schema type"):
        analyzer.infer_schema("JSONSchema-Draft-04")  # type: ignore


def test_infer_schema_with_empty_samples():
    """Test schema inference with no data samples."""
    analyzer = SchemaInferenceAnalyzer()

    schema = analyzer.infer_schema("JSONSchema-Draft-07")
    assert schema == {"$schema": "http://json-schema.org/schema#", "type": "object"}
