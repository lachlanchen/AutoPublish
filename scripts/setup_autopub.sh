#!/bin/bash

# Create the run script
echo '#!/bin/bash
source /Users/lachlan/miniconda3/bin/activate
/Users/lachlan/miniconda3/bin/python /Users/lachlan/Documents/iProjects/auto-publish/autopub.py' > /Users/lachlan/Documents/iProjects/auto-publish/run_autopub.sh

# Make the run script executable
chmod +x /Users/lachlan/Documents/iProjects/auto-publish/run_autopub.sh

# Create the .plist file
echo '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lachlan.autopublish</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/lachlan/Documents/iProjects/auto-publish/run_autopub.sh</string>
    </array>

    <key>WatchPaths</key>
    <array>
        <string>/Users/lachlan/Nutstore Files/Vlog/AutoPublish</string>
    </array>

    <key>StandardErrorPath</key>
    <string>/tmp/autopub.err</string>

    <key>StandardOutPath</key>
    <string>/tmp/autopub.out</string>
</dict>
</plist>' > ~/Library/LaunchAgents/com.lachlan.autopublish.plist

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.lachlan.autopublish.plist

