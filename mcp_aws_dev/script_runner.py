from dataclasses import dataclass
import subprocess
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


def run_in_jail(
    work_dir: Path,
    script: str,
    env: Optional[Dict[str, str]] = None
) -> Tuple[str, str, int]:
    """
    Run a Python script in an isolated environment (jail) where it can only
    read/write to the specified work directory.
    
    :param work_dir: Path to the directory where the script will run and have access
    :param script: Content of the Python script to execute
    :param env: Optional environment variables to set for the script
    :return: Tuple containing (stdout, stderr, return_code)
    """
    # Ensure work_dir exists
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the script to work_dir/script.py
    script_path = work_dir / "script.py"
    script_path.write_text(script)
    
    # Create a wrapper script that will set up the jail
    wrapper_path = work_dir / "jail_wrapper.py"
    
    # Get Python installation paths that should be readable
    python_path = sys.executable
    
    # Handle the case where sys.__file__ is not available (Python 3.13+)
    try:
        python_lib_path = Path(sys.__file__).parent
    except AttributeError:
        # For Python 3.13+, we need to use a different approach
        # We'll use sys.prefix which is always available
        python_lib_path = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    
    site_packages_paths = []
    
    for path in sys.path:
        if path and Path(path).exists() and "site-packages" in path:
            site_packages_paths.append(path)
    
    # Create the wrapper script
    wrapper_code = f"""
import os
import sys
import builtins
from pathlib import Path

# The allowed directory for read/write access
ALLOWED_DIR = "{work_dir}"

# Original built-in open function
original_open = builtins.open

# Override the built-in open() function to restrict file access
def restricted_open(file, mode='r', *args, **kwargs):
    file_path = Path(file).resolve()
    
    # Allow read access to Python installation directories
    if any(str(file_path).startswith(str(p)) for p in [
        "{python_lib_path}",  # Python standard library
        {", ".join(f'"{p}"' for p in site_packages_paths)}  # Site packages
    ]):
        if 'w' not in mode and 'a' not in mode and '+' not in mode:
            return original_open(file, mode, *args, **kwargs)
        else:
            raise PermissionError(f"Write access denied to {{file_path}}")
    
    # Check if the file is within the allowed directory
    if str(file_path).startswith(str(Path("{work_dir}").resolve())):
        return original_open(file, mode, *args, **kwargs)
    
    # Deny access to all other files
    raise PermissionError(f"Access to {{file_path}} is not allowed")

# Apply the restriction
builtins.open = restricted_open

# Execute the target script
with original_open("{script_path}", 'r') as f:
    code = compile(f.read(), "{script_path}", 'exec')
    # Set up a clean globals dictionary
    globals_dict = {{
        '__name__': '__main__',
        '__file__': "{script_path}",
        '__builtins__': __builtins__
    }}
    exec(code, globals_dict)
"""
    
    wrapper_path.write_text(wrapper_code)
    
    # Prepare environment variables
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)
    
    # Run the wrapper script which will execute the target script in the jail
    process = subprocess.run(
        [sys.executable, str(wrapper_path)],
        cwd=str(work_dir),
        env=exec_env,
        capture_output=True,
        text=True
    )
    
    return process.stdout, process.stderr, process.returncode