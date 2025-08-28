#!/bin/bash

# __     __   _          _     _               _____ _    _ _____ 
# \ \   / /  | |        (_)   | |             / ____| |  | |_   _|
#  \ \_/ /_ _| |__  _ __ _  __| | __ _  ___  | |  __| |  | | | |  
#   \   / _` | '_ \| '__| |/ _` |/ _` |/ _ \ | | |_ | |  | | | |  
#    | | (_| | |_) | |  | | (_| | (_| |  __/ | |__| | |__| |_| |_ 
#    |_|\__,_|_.__/|_|  |_|\__,_|\__, |\___|  \_____|\____/|_____|
#                                 __/ |                           
#                                |___/  
#
# A yabridge GUI controller
#
# Uninstall script
#
# Created by Andrianos Papamarkou
#

LOCAL_APPLICATION_DIR="$HOME/.local/share/applications"
LOCAL_BIN_DIR="$HOME/.local/bin"
APP_NAME="yabridge-gui-controller"
ICON_DIR="$HOME/.local/share/icons"

echo "Removing $APP_NAME..."
echo "Removing $LOCAL_APPLICATION_DIR/$APP_NAME.desktop"
rm f $LOCAL_APPLICATION_DIR/$APP_NAME.desktop
echo "Removing $LOCAL_BIN_DIR/$APP_NAME.py"
rm f $LOCAL_BIN_DIR/$APP_NAME.py
echo "Removing $ICON_DIR/$APP_NAME.png"
rm f $ICON_DIR/$APP_NAME.png

echo "Done!"
