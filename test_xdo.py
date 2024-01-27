import subprocess

def get_current_window_name():
    try:
        # Get the ID of the active window
        active_window_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode().strip()

        # Get the name of the active window using its ID
        window_name = subprocess.check_output(["xdotool", "getwindowname", active_window_id]).decode().strip()

        return window_name
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode()}")
        return None

if __name__ == "__main__":
    window_name = get_current_window_name()
    if window_name:
        print(f"The name of the current active window is: '{window_name}'")
    else:
        print("Failed to retrieve the active window name.")

