# Windows VST support for Linux

## **Disclaimer**  

The following information has been gathered from various sources online and is valid as of June 2025.  
These instructions work on my own computers.
I’m sharing them only to save you time from endless Googling and from cluttering your system with trial-and-error fixes.
I take no responsibility for any issues that may arise. Many commands below require `sudo`. While I personally haven’t encountered problems, I strongly recommend that before running anything you **make full backups**:

- Your system (e.g. with `timeshift`)
- Your home folder

## 1. wine-staging installation instructions

### 1.a Arch

```sh
sudo pacman -S --needed wine-staging
```

### 1.b OpenSUSE

```sh
sudo zypper install wine-staging wine-staging32bit
```

### 1.c Fedora

```sh
sudo dnf -y config-manager --add-repo https://dl.winehq.org/wine-builds/fedora/$(rpm -E %fedora)/winehq.repo
```

```sh
sudo dnf -y install winehq-staging
```

### 1.d Ubuntu

```sh
sudo apt -y install wget cabextract
```

```sh
sudo dpkg --add-architecture i386
```

```sh
wget -O- https://dl.winehq.org/wine-builds/winehq.key | sudo gpg --dearmor | sudo tee /usr/share/keyrings/winehq.gpg
```

```sh
echo deb [signed-by=/usr/share/keyrings/winehq.gpg] http://dl.winehq.org/wine-builds/ubuntu/ $(lsb_release -cs) main | sudo tee /etc/apt/sources.list.d/winehq.list
```

```sh
sudo apt -y update && sudo apt -y install --install-recommends winehq-staging
```

Edit .profile

```sh
nano .profile
```

Add the following lines and then execute them to continue

```txt
export WINEFSYNC=1
```

- Close the terminal

## 2. Configure using `winetricks`

- Download latest `winetricks` script:

```sh
wget  https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
```

- Make it executable:

```sh
chmod +x winetricks
```

- Install service pack 6:

```sh
./winetricks vcrun6sp6
```

- configure wine:

```sh
winecfg
```

## 3. Install yabridge

### 3.a Arch

```sh
sudo pacman -S --needed yabridge yabridgectl
```

### 3.b Other distributions

- [Download the latest release of `yabridge`](https://github.com/robbert-vdh/yabridge/releases)
- Extract the archive
- Copy the 'yabridge' folder to `$HOME/.local/share/`
- Edit .profile

```sh
sudo nano .profile
```

- Add the following line

```sh
export PATH="$PATH:$HOME/.local/share/yabridge"
```

- Close terminal, reopen it and run.

```sh
yabridgectl set --path="$HOME/.local/share/yabridge"
```

### 4. Install Yabridge GUI

#### Debian/Ubuntu and directives (Mint,MX Linux)

```sh
sudo apt install python3-pyqt6 git wget && wget -qO- https://raw.githubusercontent.com/apapamarkou/yabridge-gui-controller/main/src/yabridge-gui-controller-git-install | bash

```

#### Arch (Manjaro,Garuda,CatchyOS)

```sh
sudo pacman -S --needed python-pyqt6 git wget && wget -qO- https://raw.githubusercontent.com/apapamarkou/yabridge-gui-controller/main/src/yabridge-gui-controller-git-install | bash
```

## 4. Prepare VST Plugin Folders

```sh
mkdir -p "$HOME/.wine/drive_c/Program Files/Steinberg"
mkdir -p "$HOME/.wine/drive_c/Program Files/Steinberg/VstPlugins"
mkdir -p "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
mkdir -p "$HOME/.wine/drive_c/Program Files/VSTPlugins"
yabridgectl add "$HOME/.wine/drive_c/Program Files/Steinberg/VstPlugins"
yabridgectl add "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
yabridgectl add "$HOME/.wine/drive_c/Program Files/VSTPlugins"
```

## 5. Optimize for audio

- Add your self to `audio` group

```sh
sudo usermod -a -G audio $USER
```

- Editing the `limits.conf` file

```sh
sudo nano /etc/security/limits.conf
```

- Add the lines:

```txt
@audio           -      rtprio           95
@audio           -      memlock          unlimited
@audio           -      nice             10
```

- Restart the system
