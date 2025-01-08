import subprocess
import shlex
import os
import re
import asyncio
from pathlib import Path
from functools import partial

def get_current_directory_contents():
    current_directory = os.getcwd()
    contents = os.listdir(current_directory)
    return contents

def execute_command_factory(uuid: str) -> dict["stdout": str, "stderr": str]:
    return partial(execute_command, uuid)


def execute_command(uuid: str, command: str) -> dict["stdout": str, "stderr": str]:
    """Executes a command in the shell and returns the output.

    Args:
    - command: str - The command to execute in the shell.

    Returns:
    - output: str - The output of the command.
    """

    # Change the current working directory to the specified directory

    try:
        cleaned_command = process_command(command=command)
    except ValueError as e:
        return f"""Error with command syntax. There was an error while processing the command before it was executed:
        {str(e)}"""

    cwd = os.getcwd()
    print(cwd)
    Path(f"/working_dir/{uuid}").mkdir(parents=True, exist_ok=True)
    os.chdir(f"/working_dir/{uuid}")

     
    result = subprocess.run(
        cleaned_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Capture stderr as well
        text=True,  # Decode the output to strings
        shell=True
    )

    print("Command execution completed.")
    print("Return Code:", result.returncode)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)

    print("RESULT: ", result)

    stdout = None
    if (result.stdout):
        stdout = result.stdout

    stderr = None
    if (result.stderr):
        stderr = result.stderr

    output = f"""Command: {command}

stdout:
{stdout}

stderr:
{stderr}

{"It appears there was an error running the command, try searching the tool documentation again with improved parameters"
 if stderr != None and len(stderr) > 0 else ""}

Return Code: {result.returncode}

Current Directory Contents:
{get_current_directory_contents()}
"""


    os.chdir(cwd)
    print(output)
    return output



def normalize_path(path):
    # Normalize the path to eliminate '..' or '../'
    norm_path = os.path.normpath(path)
    return norm_path

def validate_and_sanitize_paths(paths):
    sanitized_paths = []
    for path in paths:
        # Check for absolute paths and reject them
        if os.path.isabs(path):
            return False, path

        # Normalize the path
        normalized_path = normalize_path(path)

        # Check if the normalized path goes outside the current directory
        if '..' in normalized_path.split(os.sep):
            return False, path
        
        sanitized_paths.append(normalized_path)
    
    return True, sanitized_paths

def process_command(command):
    # Handle wrapping quotes
    command = command.strip()
    while command[0] in ["'", "`", '"'] and command[len(command)-1] == command[0]:
        command = command[1:len(command)-1]

    # Split command using shlex to handle quotes correctly
    args = shlex.split(command)
    
    # Extract paths (simplified assumption: paths are arguments that look like files or directories)
    paths = [arg for arg in args if not arg.startswith('-') and (os.path.isabs(arg) or not arg.startswith('--'))]

    # Validate and sanitize paths
    valid, result = validate_and_sanitize_paths(paths)
    if not valid:
        return f"Error: Invalid path detected: '{result}'"

    sanitized_paths = result

    # Replace original paths with sanitized paths in the command
    path_index = 0
    sanitized_command = []
    for arg in args:
        if arg in paths:
            sanitized_command.append(sanitized_paths[path_index])
            path_index += 1
        else:
            sanitized_command.append(arg)

    return ' '.join(sanitized_command)