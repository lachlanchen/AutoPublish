# File: load_env.py
import os
import shlex
import subprocess
import traceback

def load_env_from_bashrc():
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
        env_count = 0
        for line in output.decode().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                env_count += 1
                
        print(f"Successfully loaded {env_count} environment variables")
        
        # Verify specific environment variables we need
        critical_vars = ['TULING_USERNAME', 'TULING_PASSWORD', 'TULING_ID', 
                         'FROM_EMAIL', 'TO_EMAIL', 'SENDGRID_API_KEY']
        
        for var in critical_vars:
            if var in os.environ:
                # Mask passwords and API keys when printing
                if 'PASSWORD' in var or 'API_KEY' in var:
                    print(f"  ✓ {var}: {'*' * 8}")
                else:
                    print(f"  ✓ {var}: {os.environ[var]}")
            else:
                print(f"  ✗ {var}: Not found")
                
        return True
    except Exception as e:
        print(f"Error loading environment variables from .bashrc: {e}")
        traceback.print_exc()
        return False

# You can test the function by running this file directly
if __name__ == "__main__":
    load_env_from_bashrc()
