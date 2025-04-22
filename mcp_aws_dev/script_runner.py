from dataclasses import dataclass
import functools
import subprocess
import os
import sys
import random
import string
import docker
from pathlib import Path
from typing import Dict, Optional, Tuple

from mcp_aws_dev.context import SessionCredentials

@functools.cache
def create_image() -> str:
    """
    Build a Docker image using the Dockerfile in the mcp_aws_dev package.
    
    :return: The name of the created Docker image
    """
    # Generate a random string for the image name
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    image_name = f"mcp_aws_{random_suffix}"
    
    # Get the path to the Dockerfile
    package_dir = Path(__file__).parent
    dockerfile_path = package_dir / "Dockerfile"
    
    # Build the Docker image
    client = docker.from_env()
    client.images.build(
        path=str(package_dir),
        dockerfile=str(dockerfile_path),
        tag=image_name
    )
    
    return image_name


def run_in_jail(
    work_dir: Path,
    script: str,
    aws_credentials: SessionCredentials,
    env: Optional[Dict[str, str]] = None
) -> Tuple[str, str, int]:
    """
    Run a Python script in an isolated environment (jail) where it can only
    read/write to the specified work directory.
    
    :param work_dir: Path to the directory where the script will run and have access
    :param script: Content of the Python script to execute
    :param aws_credentials: AWS credentials to use in the container
    :param env: Optional environment variables to set for the script
    :return: Tuple containing (stdout, stderr, return_code)
    """
    # Create a temporary script file in the work directory
    script_path = work_dir / "script.py"
    with open(script_path, "w") as f:
        f.write(script)
    
    # Get the Docker image name
    image_name = create_image()
    
    # Set up environment variables
    docker_env = {
        "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", "eu-west-1"),
        "AWS_REGION": os.environ.get("AWS_REGION", "eu-west-1"),
        "AWS_ACCESS_KEY_ID": aws_credentials.access_key,
        "AWS_SECRET_ACCESS_KEY": aws_credentials.secret_key,
        "AWS_SESSION_TOKEN": aws_credentials.session_token,
        **(env or {}),
    }
    
    # Add any additional environment variables
    if env:
        docker_env.update(env)
    
    # Set up volumes for mounting
    volumes = {
        str(work_dir): {
            "bind": "/workspace",
            "mode": "rw"
        }
    }
    
    # Check if MCP_ARTIFACT_DIR is set and add it to volumes and env
    artifact_dir = os.environ.get("MCP_ARTIFACT_DIR")
    if artifact_dir:
        artifact_path = Path(artifact_dir)
        if artifact_path.exists():
            # Mount the artifact directory with the same path as on the host
            volumes[str(artifact_path)] = {
                "bind": str(artifact_path),
                "mode": "rw"
            }
            # Pass the same path to the container
            docker_env["MCP_ARTIFACT_DIR"] = str(artifact_path)
    else:
        docker_env["MCP_ARTIFACT_DIR"] = str(work_dir)
    
    # Create and run the Docker container
    client = docker.from_env()
    container = client.containers.run(
        image=image_name,
        command=["python", "/workspace/script.py"],
        environment=docker_env,
        volumes=volumes,
        detach=True
    )
    
    # Wait for the container to finish
    result = container.wait()
    return_code = result["StatusCode"]
    
    # Get the logs
    logs = container.logs().decode("utf-8")
    
    # Remove the container
    container.remove()
    
    # Split logs into stdout and stderr
    # Docker combines stdout and stderr in the logs, so we'll just return the combined output
    # and the return code
    return logs, "", return_code