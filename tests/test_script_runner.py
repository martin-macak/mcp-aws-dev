import re
import docker
import os
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any
from unittest.mock import patch, MagicMock

import pytest

from mcp_aws_dev.script_runner import create_image, run_in_jail
from mcp_aws_dev.context import SessionCredentials


def test_create_image():
    """Test that create_image builds a Docker image and returns a valid image name.

    This test verifies that:
    1. The Docker client is properly initialized
    2. The image is built with correct parameters
    3. The returned image name follows the expected format
    """
    # Mock the docker client
    with patch('docker.from_env') as mock_from_env:
        # Set up the mock
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        
        # Mock the images.build method
        mock_client.images.build.return_value = (MagicMock(), [])
        
        # Call the function
        image_name = create_image()
        
        # Verify the image name format
        assert re.match(r'^mcp_aws_[a-z0-9]{8}$', image_name)
        
        # Verify that the docker client was used correctly
        mock_from_env.assert_called_once()
        mock_client.images.build.assert_called_once()
        
        # Get the arguments passed to build
        build_args = mock_client.images.build.call_args[1]
        
        # Verify the path argument points to the package directory
        package_dir = Path(__file__).parent.parent / "mcp_aws_dev"
        assert build_args['path'] == str(package_dir)
        
        # Verify the dockerfile argument points to the Dockerfile
        assert build_args['dockerfile'] == str(package_dir / "Dockerfile")
        
        # Verify the tag argument matches the returned image name
        assert build_args['tag'] == image_name


def test_run_in_jail():
    """Test that run_in_jail correctly sets up the Docker container with the right environment variables and mounts.

    This test verifies that:
    1. The Docker container is created with the correct image
    2. The environment variables are properly set
    3. The volumes are correctly mounted
    4. The script is executed and its output is captured
    """
    # Create a temporary directory for the work directory
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        
        # Create a simple test script
        script = "print('Hello, world!')"
        
        # Create mock AWS credentials
        aws_credentials = SessionCredentials(
            access_key="test_access_key",
            secret_key="test_secret_key",
            session_token="test_session_token",
        )
        
        # Set up environment variables for testing
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
        os.environ["AWS_REGION"] = "us-east-1"
        
        # Mock the docker client and create_image function
        with patch('docker.from_env') as mock_from_env, \
             patch('mcp_aws_dev.script_runner.create_image') as mock_create_image:
            
            # Set up the mocks
            mock_client = MagicMock()
            mock_from_env.return_value = mock_client
            
            mock_container = MagicMock()
            mock_client.containers.run.return_value = mock_container
            
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.return_value = b"Hello, world!\n"
            
            mock_create_image.return_value = "mcp_aws_test_image"
            
            # Call the function
            stdout, stderr, return_code = run_in_jail(work_dir, script, aws_credentials)
            
            # Verify the script file was created
            assert (work_dir / "script.py").exists()
            with open(work_dir / "script.py", "r") as f:
                assert f.read() == script
            
            # Verify create_image was called
            mock_create_image.assert_called_once()
            
            # Verify the Docker container was run with the correct parameters
            mock_client.containers.run.assert_called_once()
            
            # Get the arguments passed to run
            run_args = mock_client.containers.run.call_args[1]
            
            # Verify the image argument
            assert run_args['image'] == "mcp_aws_test_image"
            
            # Verify the command argument
            assert run_args['command'] == ["python", "/workspace/script.py"]
            
            # Verify the environment variables
            env = run_args['environment']
            assert env["AWS_DEFAULT_REGION"] == "us-east-1"
            assert env["AWS_REGION"] == "us-east-1"
            assert env["AWS_ACCESS_KEY_ID"] == "test_access_key"
            assert env["AWS_SECRET_ACCESS_KEY"] == "test_secret_key"
            assert env["AWS_SESSION_TOKEN"] == "test_session_token"
            
            # Verify the volumes
            volumes = run_args['volumes']
            assert volumes[str(work_dir)]["bind"] == "/workspace"
            assert volumes[str(work_dir)]["mode"] == "rw"
            
            # Verify the detach argument
            assert run_args['detach']
            
            # Verify the container was waited for and removed
            mock_container.wait.assert_called_once()
            mock_container.remove.assert_called_once()
            
            # Verify the return values
            assert stdout == "Hello, world!\n"
            assert stderr == ""
            assert return_code == 0


def test_run_in_jail_with_additional_env():
    """Test that run_in_jail correctly adds additional environment variables.

    This test verifies that:
    1. Additional environment variables are properly passed to the Docker container
    2. The container is created with the combined environment variables
    """
    # Create a temporary directory for the work directory
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        
        # Create a simple test script
        script = "print('Hello, world!')"
        
        # Create mock AWS credentials
        aws_credentials = SessionCredentials(
            access_key="test_access_key",
            secret_key="test_secret_key",
            session_token="test_session_token",
        )
        
        # Set up additional environment variables
        additional_env = {
            "CUSTOM_VAR": "custom_value",
            "ANOTHER_VAR": "another_value"
        }
        
        # Mock the docker client and create_image function
        with patch('docker.from_env') as mock_from_env, \
             patch('mcp_aws_dev.script_runner.create_image') as mock_create_image:
            
            # Set up the mocks
            mock_client = MagicMock()
            mock_from_env.return_value = mock_client
            
            mock_container = MagicMock()
            mock_client.containers.run.return_value = mock_container
            
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.return_value = b"Hello, world!\n"
            
            mock_create_image.return_value = "mcp_aws_test_image"
            
            # Call the function with additional environment variables
            run_in_jail(work_dir, script, aws_credentials, env=additional_env)
            
            # Get the arguments passed to run
            run_args = mock_client.containers.run.call_args[1]
            
            # Verify the environment variables
            env = run_args['environment']
            assert env["CUSTOM_VAR"] == "custom_value"
            assert env["ANOTHER_VAR"] == "another_value"


@pytest.mark.docker
def test_run_in_jail_with_real_docker():
    """Test that run_in_jail works with a real Docker instance.

    This test verifies that:
    1. The Docker image can be built successfully
    2. The script can be executed in a real Docker container
    3. The output is captured correctly

    This test requires Docker to be running on the system.
    """
    # Create a temporary directory for the work directory
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        
        # Create a test script that prints a message and returns a value
        script = """
import os
import sys

print("Hello from Docker!")
print(f"AWS_REGION: {os.environ.get('AWS_REGION', 'not set')}")
print(f"CUSTOM_VAR: {os.environ.get('CUSTOM_VAR', 'not set')}")

# Return a specific exit code to verify it's captured
sys.exit(42)
"""
        
        # Create AWS credentials
        aws_credentials = SessionCredentials(
            access_key="test_access_key",
            secret_key="test_secret_key",
            session_token="test_session_token",
        )
        
        # Set up additional environment variables
        additional_env = {
            "CUSTOM_VAR": "custom_value",
            "AWS_REGION": "us-west-2"
        }
        
        # First, build the Docker image
        # Clear the cache to ensure we get a fresh image
        create_image.cache_clear()
        image_name = create_image()
        
        # Call the function with real Docker
        stdout, stderr, return_code = run_in_jail(
            work_dir, 
            script, 
            aws_credentials, 
            env=additional_env
        )
        
        # Verify the script file was created
        assert (work_dir / "script.py").exists()
        with open(work_dir / "script.py", "r") as f:
            assert f.read() == script
        
        # Verify the output contains expected strings
        assert "Hello from Docker!" in stdout
        assert "AWS_REGION: us-west-2" in stdout
        assert "CUSTOM_VAR: custom_value" in stdout
        
        # Verify the return code
        assert return_code == 42
