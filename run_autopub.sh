# #!/bin/zsh -l

# Load the user's bash or zsh profile to ensure all environment variables are set
source ~/.zprofile  # or source ~/.zshrc if you're using zsh
source ~/.zshrc  # or source ~/.zshrc if you're using zsh

# Activate Conda environment
source /Users/lachlan/miniconda3/bin/activate

# Define the lock file and log file
lock_file="/Users/lachlan/Documents/iProjects/auto-publish/autopub.lock"
log_dir="/Users/lachlan/Documents/iProjects/auto-publish/logs-autopub"
log_file="${log_dir}/autopub_$(date '+%Y-%m-%d_%H-%M-%S').log"

# Create log directory if it doesn't exist
mkdir -p "${log_dir}"

# Wait for lock file to be released
while [ -f "${lock_file}" ]; do
    echo "Another instance of the script is running. Waiting..."
    sleep 60  # Wait for 60 seconds before checking again
done

# Create a lock file
touch "${lock_file}"

# Ensure the lock file is removed when the script finishes
trap 'rm -f "${lock_file}"; exit' INT TERM EXIT

# Run your Python script and save its output to the log file
/Users/lachlan/miniconda3/bin/python /Users/lachlan/Documents/iProjects/auto-publish/autopub.py --use-cache > "${log_file}" 2>&1

# Remove the lock file and clear the trap
rm -f "${lock_file}"
trap - INT TERM EXIT
