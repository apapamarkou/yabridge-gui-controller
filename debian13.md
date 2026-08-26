# Debian 13 pro-audio setup

Not so hard...
Open a terminal window

## Install wine-staging

```
sudo apt -y install wget cabextract
sudo dpkg --add-architecture i386
sudo mkdir -pm755 /etc/apt/keyrings
yes | sudo wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
CODENAME=$(grep -oP 'VERSION="[0-9]+\s+\(\K[^")]+' /etc/os-release)
yes | sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/$CODENAME/winehq-$CODENAME.sources
sudo apt update
sudo apt -y install --install-recommends wine-staging
```

edit and add to '$HOME/.profile' if not exist:

```
export PATH="/opt/wine-staging/bin:$PATH"
export WINEFSYNC=1
```

## Install winetricks

```
wget  https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x winetricks
./winetricks vcrun6sp6
winecfg
```

## Install yabridge to '$HOME/.local'

prepare VST folders

```
mkdir -p "$HOME/.wine/drive_c/Program Files/Steinberg/VstPlugins"
mkdir -p "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
mkdir -p "$HOME/.wine/drive_c/Program Files/VSTPlugins"
```

show them to yabridge

```
yabridgectl add "$HOME/.wine/drive_c/Program Files/Steinberg/VstPlugins"
yabridgectl add "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
yabridgectl add "$HOME/.wine/drive_c/Program Files/VSTPlugins"
yabridgectl set --path="~/Applications/yabridge"
```

## Allow audio group users to use

set to `/etc/security/limits.conf` if not set or set to other values before tthe line '# End of file'

```
@audio           -      rtprio           95
@audio           -      memlock          unlimited
@audio           -      nice             10
```

## Add user to audio group

```
sudo usermod -a -G audio $USER
```

## Install pipewire patchbay

```
sudo apt install qpwgraph
```

## Enjoy

reboot
'''
sudo shutdown -r now

```
