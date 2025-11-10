#!/bin/bash

# Create a folder in ~/AppImage if it doesn't exist
mkdir -p ~/AppImage/turing-monitor

# Copy current code to that folder
rsync -av --exclude='.git' --exclude='logs' --exclude='log.log' --exclude='config/' --exclude='res/themes' ~/Git/turing-smart-screen-python4buntu/ ~/AppImage/turing-monitor/

#make it autostart
mkdir -p ~/.config/autostart
cp ~/AppImage/turing-monitor/cicd/turing-monitor.desktop ~/.config/autostart/

#that's it!
echo "Local release prepared in ~/AppImage/turing-monitor"