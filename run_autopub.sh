#!/bin/bash -l
# Load the user's bash profile or zsh profile to ensure all environment variables are set
source ~/.bash_profile  # or source ~/.zshrc if you're using zsh

# Activate Conda environment
source /Users/lachlan/miniconda3/bin/activate


touch /Users/lachlan/Documents/iProjects/auto-publish/automator.txt

# Run your Python script
# /Users/lachlan/miniconda3/bin/python /Users/lachlan/Documents/iProjects/auto-publish/autopub.py
/Users/lachlan/miniconda3/bin/python /Users/lachlan/Documents/iProjects/auto-publish/autopub.py > /Users/lachlan/Documents/iProjects/auto-publish/autopub.log 2>&1