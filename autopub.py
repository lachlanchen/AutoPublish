import os
from datetime import datetime

# Define the path for the logs folder
logs_folder_path = '/Users/lachlan/Documents/iProjects/auto-publish/logs'

# Create the logs folder if it does not exist
if not os.path.exists(logs_folder_path):
    os.makedirs(logs_folder_path)

# Get the current date and time
current_datetime = datetime.now()

# Define the filename for the log file
log_filename = f"{current_datetime.strftime('%Y-%m-%d %H-%M-%S')}.txt"

# Define the path for the log file
log_file_path = os.path.join(logs_folder_path, log_filename)

# Write a log to the file
with open(log_file_path, 'a') as log_file:
    log_file.write(f"Log entry at {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

log_file_path

print("Success")