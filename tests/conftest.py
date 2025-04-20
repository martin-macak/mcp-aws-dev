import logging

import pytest


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """
    Configure logging for tests and the mcp_aws_dev package.
    This fixture runs automatically before any tests.
    """
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Create console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Specifically configure the package logger
    package_logger = logging.getLogger("mcp_aws_dev")
    package_logger.setLevel(logging.DEBUG)

    # Log that testing has started
    root_logger.info("Logging has been configured for tests")
    package_logger.debug("mcp_aws_dev package logger initialized at DEBUG level")
