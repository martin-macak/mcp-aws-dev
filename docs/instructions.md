# MCP for AWS Developers

Provides usefool tools for developers that work on serverless applications on AWS.

## Coding Standards

- Use Python 3.11 or later
- Use [PEP 8](https://www.python.org/dev/peps/pep-0008/) - Python Style Guide
- Use [PEP 257](https://www.python.org/dev/peps/pep-0257/) - Docstring conventions
- Use [PEP 287](https://peps.python.org/pep-0287/) - reStructuredText for docstrings
- Use [Black](https://black.readthedocs.io/en/stable/) - Code formatter
- Use [Ruff](https://beta.ruff.rs/docs/) - Linter
- Use [isort](https://pycqa.github.io/isort/) - Import sorter
- Use [mypy](https://mypy.readthedocs.io/en/stable/) - Static type checker
- Use [Pydantic](https://docs.pydantic.dev/) - Use for models and data validation
- Always use type hints
- Always document your code
- Always use reStructuredText for docstrings
- For Pydantic models, always use Field to define the model fields. Always use `description` for the field.

### Docstrings

- Use reStructuredText for docstrings
- Use `:ivar` for instance variables
- Use `:type` for the type of the variable
- Use `:return` for the return type
- Use `:rtype` for the type of the return value
- Use `:raises` for the exceptions that the function raises
- Use `:param` for the parameters of the function
- Use `:type` for the type of the parameter
- Use `:raises` for the exceptions that the function raises

Good example:
```python
def create_session(profile_name: str) -> boto3.Session:
    """Creates a new boto3 session for the given profile name with caching.

    This function creates a boto3 session with caching to improve performance.
    The cache is invalidated every hour to ensure credentials are refreshed.

    :param profile_name: The name of the AWS profile to use.
    :type profile_name: str
    :return: A boto3 session configured with the given profile name.
    :rtype: boto3.Session
    :raises ValueError: If the profile name is not found.
    """
```

Bad example:
```python
def create_session(profile_name: str) -> boto3.Session:
    """Creates a new boto3 session for the given profile name with caching.

    Arguments:
        profile_name: The name of the AWS profile to use.

    Returns:
        A boto3 session configured with the given profile name.

    Raises:
        ValueError: If the profile name is not found.
    """
```


## Libraries

- [uv](https://github.com/astral-sh/uv) - Project manager
- [pytest](https://docs.pytest.org/en/latest/) - Testing framework
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - AWS SDK for Python
- [moto](https://github.com/getmoto/moto) - Mock AWS services for testing

- always use boto3 for AWS SDK
- always mock AWS services for testing using moto
- use `monkeypatch` fixture for mocking environment variables and other dependencies
- use `pytest.mock.MagicMock` for mocking classes and functions

## Project Structure

```text
├── docs # Documentation and work instructions
├── mcp_aws_dev # Source code
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py # Registry of mcp resources, tools and prompts
├── tests # Unit tests
│   ├── __init__.py
│   ├── conftest.py # Test configuration
├── Makefile # Makefile for building and testing
```

## Development rules

- Always follow coding standards
- Always run tests with `make test` before committing
- Always run linter with `make lint` before committing
- Always run formatter with `make format` before committing
