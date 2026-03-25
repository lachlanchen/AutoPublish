# File: load_env.py
import os
import shlex
import subprocess
import traceback
from pathlib import Path

CRITICAL_VARS = [
    "TULING_USERNAME",
    "TULING_PASSWORD",
    "TULING_ID",
    "FROM_EMAIL",
    "TO_EMAIL",
    "SENDGRID_API_KEY",
]


def _log_critical_vars():
    for var in CRITICAL_VARS:
        if var in os.environ:
            if "PASSWORD" in var or "API_KEY" in var:
                print(f"  ✓ {var}: {'*' * 8}")
            else:
                print(f"  ✓ {var}: {os.environ[var]}")
        else:
            print(f"  ✗ {var}: Not found")


def _candidate_env_paths(dotenv_path=None):
    if dotenv_path:
        return [Path(dotenv_path).expanduser()]

    module_dir = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()
    home = Path.home()

    candidates = []
    for candidate in (module_dir / ".env", cwd / ".env", home / ".env"):
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _parse_dotenv(dotenv_path):
    env_map = {}
    for raw_line in Path(dotenv_path).read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        env_map[key] = value
    return env_map


def _apply_env_map(env_map, source, overwrite=True):
    applied = 0
    for key, value in env_map.items():
        if not overwrite and key in os.environ:
            continue
        os.environ[key] = value
        applied += 1
    print(f"Successfully loaded {applied} environment variables from {source}")
    return applied


def load_env_from_dotenv(dotenv_path=None, overwrite=True):
    for candidate in _candidate_env_paths(dotenv_path=dotenv_path):
        if not candidate.exists():
            continue
        print(f"Attempting to load environment variables from {candidate}")
        env_map = _parse_dotenv(candidate)
        _apply_env_map(env_map, candidate, overwrite=overwrite)
        _log_critical_vars()
        return True

    print("No .env file found in candidate paths:")
    for candidate in _candidate_env_paths(dotenv_path=dotenv_path):
        print(f"  - {candidate}")
    return False


def load_env_from_bashrc(overwrite=True):
    """
    Source the .bashrc file to load environment variables
    and make them available to the current Python process.
    """
    try:
        # Get the path to the user's .bashrc file
        home_dir = os.path.expanduser("~")
        bashrc_path = os.path.join(home_dir, ".bashrc")
        
        print(f"Attempting to load environment variables from {bashrc_path}")
        
        # .bashrc on this host exits early for non-interactive shells, so
        # force an interactive bash and silence shell-control noise.
        quoted_bashrc = shlex.quote(bashrc_path)
        command = f"bash -ic 'source {quoted_bashrc} >/dev/null 2>&1; env' 2>/dev/null"

        # Run the command and capture the output
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        output, stderr = proc.communicate()
        if proc.returncode != 0:
            stderr_text = (stderr or b"").decode().strip()
            raise RuntimeError(
                f"Failed to source {bashrc_path} (exit {proc.returncode}): {stderr_text}"
            )
        
        # Parse the environment variables and set them in the current process
        env_map = {}
        for line in output.decode().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                env_map[key] = value

        _apply_env_map(env_map, bashrc_path, overwrite=overwrite)
        _log_critical_vars()
                
        return True
    except Exception as e:
        print(f"Error loading environment variables from .bashrc: {e}")
        traceback.print_exc()
        return False


def load_env(dotenv_path=None):
    """
    Prefer the repo-local .env file, then fall back to ~/.bashrc only for any
    missing values. This keeps .env as the source of truth for automation.
    """
    loaded_from_dotenv = load_env_from_dotenv(dotenv_path=dotenv_path, overwrite=True)
    missing = [var for var in CRITICAL_VARS if not os.environ.get(var)]

    if missing:
        print(
            "Missing critical variables after .env load. "
            "Falling back to ~/.bashrc for any remaining values."
        )
        load_env_from_bashrc(overwrite=False)
        missing = [var for var in CRITICAL_VARS if not os.environ.get(var)]

    if missing:
        print("Environment load incomplete. Missing critical variables:")
        for var in missing:
            print(f"  - {var}")
        return False

    if loaded_from_dotenv:
        print("Environment load completed using .env as the primary source.")
    else:
        print("Environment load completed using ~/.bashrc fallback.")
    return True

# You can test the function by running this file directly
if __name__ == "__main__":
    load_env()
