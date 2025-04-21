# File: load_env.py
import os
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
        
        # Execute the .bashrc using a shell command and capture the environment
        command = f"bash -c 'source {bashrc_path} && env'"
        
        # Run the command and capture the output
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, _ = proc.communicate()
        
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