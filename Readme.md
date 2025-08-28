# Yabridge GUI Controller

## Overview

Yabridge is a command-line tool that converts Windows VST/VST3 plugins into Linux-native plugins, enabling you to run them via Wine. This PyQt-based GUI application simplifies managing and converting VST2 and VST3 plugins installed through Wine. With this application, you can:

- Scan and synchronize your VST plugins.
- Display lists of converted plugins.
- Check the status of converted plugins.

This tool streamlines the process of using Windows plugins seamlessly on a Linux system.

If you dont know how to install wine-staging and yabridge on your system, you can [follow my tutorial](https://github.com/apapamarkou/yabridge-gui-controller/blob/main/LinuxProAudio.md).

## Features

- **Environment Checks**: Verifys if `Yabridge` and `Wine` are installed.
- **Plugin Lists**: Display lists of integrated VST2 and VST3 plugins.
- **Scan Plugins**: Sync plugins using `yabridgectl sync` and update the plugin lists.

## Installation

### Dependencies

Ensure you have the necessary packages installed.

- puthon3-pyqt6
- python3-pyqt6.qtsvg
- git
- wget

#### Install the dependencies

To install and operate you need `pyqt6`, `git` and `wget`:

- **Arch** based distros

```sh
sudo pacman -S --needed python-pyqt6 wget git
```

- **Debian/Ubuntu** based distros

```sh
sudo apt install python3-pyqt6 wget git
```

### Installation/Update

Copy the following command, paste it in a terminal and hit [ENTER]. Thats it!

```sh
wget -qO- https://raw.githubusercontent.com/apapamarkou/yabridge-gui-controller/main/src/yabridge-gui-controller-git-install | bash
```

### Uninstallation

Copy the following command, paste it in a terminal and hit [ENTER]. Thats it!

```sh
wget -qO- https://raw.githubusercontent.com/apapamarkou/yabridge-gui-controller/main/src/yabridge-gui-controller-git-uninstall | bash
```

## Usage

- **Scan Button**: Starts the scan operation to sync plugins and update the lists. A progress dialog with a progress bar will be displayed. This action is nesessary to integrate any windows VST/VST3 plugins installed in your DAW as native Linux plugins.
- **About Button**: Opens a dialog box with information about the application.
- **Quit Button**: Closes the application.

## Development

Feel free to contribute to the project by submitting issues, feature requests, or pull requests. Make sure to follow the coding style.

## License

This project is licensed under the GNU License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **PyQt**: For providing the graphical interface framework.
- **Yabridge**: For managing VST plugins in Wine.
- **Wine**: For providing the Windows execution environment.
