# osmate_runner.py
import shlex
import subprocess
from typing import Tuple

# Strict allowlist for read-only commands
ALLOWLIST = {
    "uname": ["-a", ""],
    "df": ["-h", ""],
    "whoami": [""],
    "uptime": [""],
    "ls": ["-la", ""],
    "sw_vers": [""],
    "diskutil": ["list"],
    "top": ["-l", "1"],
    "ps": ["aux"],
}

def is_allowed(command: str, args: list) -> bool:
    if command not in ALLOWLIST:
        return False
    allowed_args = ALLOWLIST[command]
    # If user supplied no args that's okay
    if not args:
        return True
    # Accept only args that are explicitly listed, one-by-one
    for a in args:
        if a not in allowed_args:
            return False
    return True

def run_command_safe(command_line: str, timeout: int = 8) -> Tuple[bool, str]:
    """
    Validate the command_line against the allowlist, run it, return (success, output_or_error).
    """
    try:
        parts = shlex.split(command_line)
        if not parts:
            return False, "No command provided."
        cmd = parts[0]
        args = parts[1:]
        if not is_allowed(cmd, args):
            return False, f"Command not allowed or arguments not permitted: {cmd} {' '.join(args)}"
        proc = subprocess.run(parts, capture_output=True, text=True, timeout=timeout)
        output = proc.stdout.strip() or proc.stderr.strip()
        return True, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out."
    except Exception as e:
        return False, f"Error running command: {e}"
