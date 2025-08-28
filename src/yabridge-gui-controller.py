#!/usr/bin/env python3

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
# GitHub direct uninstall script
#
# Created by Andrianos Papamarkou
#

import os
import subprocess
import re
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QListWidget, QVBoxLayout,
                             QLabel, QHBoxLayout, QPushButton, QWidget, QMessageBox,
                             QSpacerItem, QSizePolicy, QProgressBar, QDialog,
                             QDialogButtonBox)

class SyncThread(QThread):
    """Background thread for running yabridgectl sync command."""
    sync_completed = pyqtSignal(str)  # Signal to emit sync output when done

    def run(self):
        """Execute yabridgectl sync command and emit results."""
        # Run the yabridgectl sync and capture output
        result = subprocess.run(["yabridgectl", "sync"], check=True, text=True, stdout=subprocess.PIPE)
        # Emit the captured output
        self.sync_completed.emit(result.stdout)

class YabridgeController(QMainWindow):
    """Main application window for Yabridge GUI Controller."""
    
    def __init__(self):
        """Initialize the main window and set up the application."""
        super().__init__()
        self.setWindowTitle("Yabridge Controller")

        # Set up UI
        self.init_ui()

        # Environment checks
        self.check_environment()

        # Load plugin lists
        self.load_plugins()

    def init_ui(self):
        """Initialize and set up the user interface components."""
        self.vst2_list = QListWidget()
        self.vst3_list = QListWidget()

        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan_plugins)

        about_button = QPushButton("About")
        about_button.clicked.connect(self.show_about)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)

        # Align buttons to bottom-right
        button_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        button_layout.addItem(spacer)
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(about_button)
        button_layout.addWidget(quit_button)

        layout = QVBoxLayout()
        # Title, centered
        title = QLabel("<h2>Converted Plugins</h2><hr/>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Plugin lists
        vst2_layout = QVBoxLayout()
        vst2_layout.addWidget(QLabel("VST2 Plugins"))
        vst2_layout.addWidget(self.vst2_list)
        vst3_layout = QVBoxLayout()
        vst3_layout.addWidget(QLabel("VST3 Plugins"))
        vst3_layout.addWidget(self.vst3_list)

        list_layout = QHBoxLayout()
        list_layout.addLayout(vst2_layout)
        list_layout.addLayout(vst3_layout)

        layout.addLayout(list_layout)

        # Status labels for yabridge and wine checks
        self.yabridge_status = QLabel()
        self.wine_status = QLabel()
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.yabridge_status)
        status_layout.addWidget(self.wine_status)

        layout.addLayout(status_layout)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def check_environment(self):
        """Check if required tools (yabridge and wine) are installed."""
        # Check if yabridgectl is installed
        yabridge_installed = self.check_command("yabridgectl", "--version")
        if yabridge_installed:
            self.yabridge_status.setText("Yabridge: Installed")
            self.yabridge_status.setStyleSheet("color: green;")
        else:
            self.yabridge_status.setText("Yabridge: Not Installed")
            self.yabridge_status.setStyleSheet("color: red;")

        # Check if wine is installed
        wine_installed = self.check_command("wine", "--version")
        if wine_installed:
            self.wine_status.setText("Wine: Installed")
            self.wine_status.setStyleSheet("color: green;")
        else:
            self.wine_status.setText("Wine: Not Installed")
            self.wine_status.setStyleSheet("color: red;")
        
        # Disable scan button if either yabridge or wine is not installed
        self.scan_button.setEnabled(yabridge_installed and wine_installed)

    def check_command(self, command, version_flag):
        """Check if a command is available by running it with version flag.
        
        Args:
            command (str): Command to check
            version_flag (str): Version flag to use
            
        Returns:
            bool: True if command exists and runs successfully
        """
        try:
            subprocess.run([command, version_flag], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def load_plugins(self):
        """Load and display VST2 and VST3 plugins in the UI lists."""
        # Get VST2 plugins
        vst2_plugins = self.get_vst_plugins("VST2", "~/.vst/yabridge/")
        self.vst2_list.clear()
        self.vst2_list.addItems(vst2_plugins)

        # Get VST3 plugins
        vst3_plugins = self.get_vst_plugins("VST3", "~/.vst3/yabridge/")
        self.vst3_list.clear()
        self.vst3_list.addItems(vst3_plugins)

    def get_vst_plugins(self, plugin_type, plugin_dir):
        """Scan directory for VST plugins.
        
        Args:
            plugin_type (str): Type of plugin (VST2 or VST3)
            plugin_dir (str): Directory path to scan
            
        Returns:
            list: List of plugin names found
        """
        print ("Scan folder: {}",plugin_dir)
        # List plugins from the specified directory (files and folders)
        plugin_path = os.path.expanduser(plugin_dir)
        print ("Scan folder: {}",plugin_path)
        if not os.path.exists(plugin_path):
            return []

        # List all files and directories that contain the plugin_type
        plugins = []
        for entry in os.listdir(plugin_path):
            entry_path = os.path.join(plugin_path, entry)
            print ("Scan entry: {}", entry_path)
            # if entry_path has .vst or .vst3 in the name, add  the filename without the extention to the list
            if ".vst" in entry_path or ".vst3" in entry_path:
                plugins.append(os.path.splitext(entry)[0])

        print("Plugins found: {plugins}",plugins)
        return plugins

    def scan_plugins(self):
        """Start plugin scanning process with progress dialog."""
        # Show progress dialog with a 10-second progress bar
        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle("Scanning Plugins")

        progress_layout = QVBoxLayout(self.progress_dialog)
        self.progress_label = QLabel("Scanning... Please wait.")
        self.progress_bar = QProgressBar(self.progress_dialog)
        self.progress_bar.setRange(0, 100)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        # Timer to update the progress bar over 10 seconds
        self.progress_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)  # Update every 100ms

        # Run yabridgectl sync in the background using a separate thread
        self.sync_thread = SyncThread()
        self.sync_thread.sync_completed.connect(self.handle_sync_completed)  # Process output when done
        self.sync_thread.start()

        self.progress_dialog.exec()

    def update_progress(self):
        """Update progress bar during scanning process."""
        self.progress_value += 1
        self.progress_bar.setValue(self.progress_value)

        # Close the progress bar after 10 seconds (100 updates of 1%)
        if self.progress_value >= 100:
            self.timer.stop()

    def handle_sync_completed(self, sync_output):
        """Handle completion of sync operation and display results.
        
        Args:
            sync_output (str): Output from yabridgectl sync command
        """
        self.progress_value = 99

        # Parse sync output to extract values
        setting_up = re.search(r'setting up (\d+)', sync_output).group(1)
        new_plugins = re.search(r'(\d+) new', sync_output).group(1)
        skipped = re.search(r'skipped (\d+)', sync_output).group(1)

        # Update the progress dialog with scan results and add a "Close" button
        self.progress_label.setText(f"""<h2 style="text-align: center">Scan completed!</h2>
                                    <p>Scanned files: {setting_up}</p>
                                    <p>New plugins: {new_plugins}</p>
                                    <p>Skipped: {skipped}</p><hr/>"""
                                    )

        # Add Close button to the progress dialog
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.clicked.connect(self.progress_dialog.close)
        self.progress_dialog.layout().addWidget(button_box)

        # Reload plugins after sync
        self.load_plugins()

    def show_about(self):
        """Display the About dialog with application information."""
        QMessageBox.about(self, "About", """<h1>Yabridge GUI Controller</h1>
                          <h2>Version 1.0</h2>
                          <p>Facilitates the conversion of Windows VST2/VST3 plugins installed through wine-staging using yabridge. This application <strong>does not manage plugin installation</strong> or removal; those are handled by the plugin installers. It <strong>streamlines the conversion</strong> process to Linux-native VST2/VST3 formats for seamless use with your favorite DAW. Enjoy making music!</p>
                          <p>Created by: Andrianos Papamarkou</p>
                          <p><a href="https://github.com/apapamarkou/yabridge-gui-controller">Visit Yabridge GUI Controller on GitHub</a></p>
                          <p><a href="https://github.com/robbert-vdh/yabridge">Visit Yabridge on GitHub</a></p>
                          <p><a href="https://www.winehq.org/">Visit WineHQ on web</a></p>
                          """)

if __name__ == "__main__":
    """Main entry point for the application."""
    app = QApplication([])
    window = YabridgeController()
    window.show()
    app.exec()
