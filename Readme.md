# Yabridge GUI Controller

## Overview

Yabridge is a command-line tool that converts Windows VST/VST3 plugins into Linux-native plugins, enabling you to run them via Wine. This PyQt5-based GUI application simplifies managing and converting VST2 and VST3 plugins installed through Wine. With this application, you can:

- Scan and synchronize your VST plugins.
- Display lists of converted plugins.
- Check the status of converted plugins.

This tool streamlines the process of using Windows plugins seamlessly on a Linux system.

## Features

- **Environment Checks**: Verifys if `Yabridge` and `Wine` are installed.
- **Plugin Lists**: Display lists of integrated VST2 and VST3 plugins.
- **Scan Plugins**: Sync plugins using `yabridgectl sync` and update the plugin lists.

## Installation

### Dependencies

Ensure you have the necessary packages installed. For most Linux distributions, you can install the required dependencies using the following commands.

- puthon3-pyqt6
- python3-pyqt6.qtsvg
- wine-staging
- yabridge

#### Arch-based distros (Arch,Manjaro, Garuda etc)

If you are in an Arch based distro copy the following, paste it into a terminal and hit [Enter].

```sh
sudo pacman -S python-pyqt5 wine-staging yabridge yabridgectl
```

### Installation

## Usage

- **Scan Button**: Starts the scan operation to sync plugins and update the lists. A progress dialog with a progress bar will be displayed. This action is nesessary to integrate any windows VST/VST3 plugins installed in your DAW as native Linux plugins.
- **About Button**: Opens a dialog box with information about the application.
- **Quit Button**: Closes the application.

## Development

Feel free to contribute to the project by submitting issues, feature requests, or pull requests. Make sure to follow the coding style.

## License

This project is licensed under the GNU License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **PyQt5**: For providing the graphical interface framework.
- **Yabridge**: For managing VST plugins in Wine.
- **Wine**: For providing the Windows execution environment.


