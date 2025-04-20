# MCP for AWS Developers

Provides usefool tools for developers that work on serverless applications on AWS.

## Coding Standards

- Use Python 3.11 or later
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) - Python Style Guide
- [PEP 257](https://www.python.org/dev/peps/pep-0257/) - Docstring conventions
- [Black](https://black.readthedocs.io/en/stable/) - Code formatter
- [Ruff](https://beta.ruff.rs/docs/) - Linter
- [isort](https://pycqa.github.io/isort/) - Import sorter
- [mypy](https://mypy.readthedocs.io/en/stable/) - Static type checker
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) - Google Python Style Guide
- Always use type hints
- Always document your code
- Use reStructuredText for docstrings

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
