import os
import sys
from pathlib import Path
import pytest
from mcp_aws_dev.script_runner import run_in_jail


@pytest.fixture
def temp_work_dir(tmp_path):
    """
    Create a temporary working directory for script execution.
    
    :return: Path to the temporary directory
    :rtype: Path
    """
    work_dir = tmp_path / "script_work"
    work_dir.mkdir(exist_ok=True)
    return work_dir


def test_run_in_jail_basic_script(temp_work_dir):
    """
    Test running a basic script in the jail environment.
    
    This test verifies that a simple script can be executed in the jail
    and produces the expected output.
    """
    script = """
print("Hello, World!")
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code == 0
    assert stdout.strip() == "Hello, World!"
    assert stderr == ""


def test_run_in_jail_with_environment_variables(temp_work_dir):
    """
    Test running a script with environment variables.
    
    This test verifies that environment variables are properly passed
    to the script running in the jail.
    """
    script = """
import os
print(os.environ.get('TEST_VAR', 'Not set'))
"""
    env = {"TEST_VAR": "Test Value"}
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script, env)
    
    assert return_code == 0
    assert stdout.strip() == "Test Value"
    assert stderr == ""


def test_run_in_jail_file_access_allowed(temp_work_dir):
    """
    Test that file access is allowed within the work directory.
    
    This test verifies that the script can read and write files
    within the allowed work directory.
    """
    script = """
import os
from pathlib import Path

# Write a file
with open('test_file.txt', 'w') as f:
    f.write('Test content')

# Read the file back
with open('test_file.txt', 'r') as f:
    content = f.read()
    print(content)
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code == 0
    assert stdout.strip() == "Test content"
    assert stderr == ""
    
    # Verify the file was created in the work directory
    test_file = temp_work_dir / "test_file.txt"
    assert test_file.exists()
    assert test_file.read_text() == "Test content"


def test_run_in_jail_file_access_denied(temp_work_dir):
    """
    Test that file access is denied outside the work directory.
    
    This test verifies that the script cannot access files
    outside the allowed work directory.
    """
    script = """
import os
from pathlib import Path

# Try to access a file outside the work directory
try:
    with open('/etc/passwd', 'r') as f:
        content = f.read()
        print("Access granted (should not happen)")
except PermissionError as e:
    print(f"Access denied: {e}")
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code == 0
    assert "Access denied" in stdout
    assert "is not allowed" in stdout  # Check for the actual error message format


def test_run_in_jail_with_imports(temp_work_dir):
    """
    Test that standard library imports work in the jail.
    
    This test verifies that the script can import and use
    standard library modules.
    """
    script = """
import json
import datetime

data = {"key": "value"}
json_str = json.dumps(data)
print(json_str)

now = datetime.datetime.now()
print(f"Current year: {now.year}")
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code == 0
    assert '{"key": "value"}' in stdout
    assert "Current year:" in stdout
    assert stderr == ""


def test_run_in_jail_with_error(temp_work_dir):
    """
    Test that script errors are properly captured.
    
    This test verifies that errors in the script are properly
    captured and reported.
    """
    script = """
# This will raise a NameError
print(undefined_variable)
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code != 0
    assert "NameError" in stderr
    assert "undefined_variable" in stderr


def test_run_in_jail_with_sys_modules(temp_work_dir):
    """
    Test that sys module functions work in the jail.
    
    This test verifies that the script can use sys module
    functions like sys.path.
    """
    script = """
import sys
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Number of sys.path entries: {len(sys.path)}")
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code == 0
    assert f"Python version: {sys.version_info.major}.{sys.version_info.minor}" in stdout
    assert "Number of sys.path entries:" in stdout
    assert stderr == ""


def test_run_in_jail_with_multiple_environment_variables(temp_work_dir):
    """
    Test running a script with multiple environment variables.
    
    This test verifies that multiple environment variables are properly passed
    to the script running in the jail and their values are correctly accessible.
    """
    script = """
import os

# Test multiple environment variables
env_vars = {
    'TEST_VAR1': os.environ.get('TEST_VAR1', 'Not set'),
    'TEST_VAR2': os.environ.get('TEST_VAR2', 'Not set'),
    'TEST_VAR3': os.environ.get('TEST_VAR3', 'Not set')
}

# Print each variable and its value
for var_name, value in env_vars.items():
    print(f"{var_name}={value}")
"""
    env = {
        "TEST_VAR1": "Value 1",
        "TEST_VAR2": "Value 2",
        "TEST_VAR3": "Value 3"
    }
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script, env)
    
    assert return_code == 0
    assert "TEST_VAR1=Value 1" in stdout
    assert "TEST_VAR2=Value 2" in stdout
    assert "TEST_VAR3=Value 3" in stdout
    assert stderr == ""


@pytest.mark.parametrize("package_name,should_be_available", [
    ("boto3", True),
    ("yaml", True),
    ("tomli", True),
    ("jq", True),
    ("foobar", False),
])
def test_run_in_jail_package_availability(temp_work_dir, package_name, should_be_available):
    """
    Test that specified packages are available or not available in the jail environment.
    
    This test verifies that packages installed with this project are accessible
    to scripts running in the jail, and that non-existent packages are properly
    reported as unavailable.
    
    :param package_name: Name of the package to check
    :param should_be_available: Whether the package should be available
    """
    script = f"""
try:
    import {package_name}
    print("{package_name} is available")
    print(f"{package_name} version: {{getattr({package_name}, '__version__', 'unknown')}}")
except ImportError as e:
    print(f"{package_name} is not available: {{e}}")
"""
    stdout, stderr, return_code = run_in_jail(temp_work_dir, script)
    
    assert return_code == 0
    if should_be_available:
        assert f"{package_name} is available" in stdout
        assert f"{package_name} version:" in stdout
    else:
        assert f"{package_name} is not available" in stdout
    assert stderr == "" 