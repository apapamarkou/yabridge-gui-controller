#!/bin/bash

#
# A yabridge GUI controller
#
# Created by Andrianos Papamarkou
#

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
LOCAL_APPLICATION_DIR="$HOME/.local/share/applications"
LOCAL_BIN_DIR="$HOME/.local/bin"
APP_NAME="yabridge-gui-controller"
ICON_DIR="$HOME/.local/share/icons"

echo "Installing Yabridge GUI Controller..."
mkdir -p "$LOCAL_APPLICATION_DIR"
mkdir -p "$LOCAL_BIN_DIR"
mkdir -p "$ICON_DIR"

chmod +x "$SCRIPT_DIR/src/$APP_NAME.py"

echo "Copying files..."

echo "Copying icon..."
cp "$SCRIPT_DIR/src/$APP_NAME.png" "$ICON_DIR"

echo "Copying script..."
cp "$SCRIPT_DIR/src/$APP_NAME.py" "$LOCAL_BIN_DIR"

echo "Creating desktop entry..."
echo "[Desktop Entry]
Type=Application
Name=Pipewire Audio Controller
Comment=Control your audio
Exec=$LOCAL_BIN_DIR/$APP_NAME.py $1
Icon=$ICON_DIR/$APP_NAME.png
Terminal=false
Categories=AudioVideo;Audio;Settings;
StartupNotify=true
" > "$LOCAL_APPLICATION_DIR/$APP_NAME.desktop"

echo "Yabridge GUI Controller has installed."
echo "Enjoy your Windows VST/VST3 plugins!"