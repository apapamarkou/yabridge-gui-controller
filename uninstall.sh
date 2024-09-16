#!/bin/bash

#
# A yabridge GUI controller
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

