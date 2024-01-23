from selenium.common.exceptions import NoAlertPresentException

import os
import subprocess

def dismiss_alert(driver, dismiss=False):
    try:
        alert = driver.switch_to.alert
        if dismiss:
            alert.dismiss()
        else:
            alert.accept()  # Use alert.accept() if you want to accept the alert.
        print("Alert was present and dismissed.")
    except NoAlertPresentException:
        print("No alert present.")

def crop_and_resize_cover_image(path_cover):
    # Define the base name and create a name for the resized cover
    base_name = os.path.basename(path_cover)
    name, ext = os.path.splitext(base_name)
    resized_name = f"{name}_resized{ext}"
    path_cover_resized = os.path.join(os.path.dirname(path_cover), resized_name)
    
    # FFmpeg command to crop and resize the image
    ffmpeg_command = [
        '/usr/local/bin/ffmpeg',
        '-y',
        '-i', path_cover,  # Input file
        '-vf', 'crop=in_w:in_h*3/4,scale=1200:900',  # Crop and scale filter
        path_cover_resized  # Output file
    ]

    # Execute the FFmpeg command
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Resized image saved to {path_cover_resized}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the resizing process: {e}")
        return None
    
    return path_cover_resized
