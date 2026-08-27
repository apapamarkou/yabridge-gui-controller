# AntiX 26 pro-audio setup

Open a terminal window (ctrl+alt+T)

## Prepare your environment

update your system

```
sudo apt -y update && sudo apt -y upgrade
```

edit and add to '~/.profile' if not exist:

```
nano ~/.profile
```

Add installation paths for wine and yabridge:

```
export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-9.21/bin"
export WINEFSYNC=1
```

also add the above lines to icewm

```
nano ~/.icewm/env
```

Run the following to continue without having to logout and login to force system read the paths from `.profile`

```
export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-9.21/bin"
```

Some display managers like XFCEs LightDM wont call the `.profile` at startup. You need to call it from `.xsessionrc`

```
nano ~/.xsessionrc
```

add these lines

```
if [ -r "$HOME/.profile" ]; then
    . "$HOME/.profile"
fi
```

## Install wine-staging

```
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y libc6:amd64 libc6:i386 cabextract curl wget libfreetype6:amd64 libfreetype6:i386 \
    libfontconfig1:amd64 libfontconfig1:i386 libx11-6:amd64 libx11-6:i386 \
    libxext6:amd64 libxext6:i386 libxrender1:amd64 libxrender1:i386 \
    libxcursor1:amd64 libxcursor1:i386 libxi6:amd64 libxi6:i386 \
    libxinerama1:amd64 libxinerama1:i386 libxrandr2:amd64 libxrandr2:i386 \
    libasound2:amd64 libasound2:i386 libgl1:amd64 libgl1:i386
curl -L -o wine-9.21-staging-amd64.tar.xz \
  https://github.com/Kron4ek/Wine-Builds/releases/download/9.21/wine-9.21-staging-amd64.tar.xz
mkdir -p "$HOME/.local/share/wine-staging-9.21"
tar -xJf wine-9.21-staging-amd64.tar.xz \
  --strip-components=1 \
  -C "$HOME/.local/share/wine-staging-9.21"
```

check

```
wine --version
```

Make it default for the .exe file execution

```
mkdir -p "$HOME/.local/share/applications"

cat > "$HOME/.local/share/applications/wine921.desktop" <<EOF
[Desktop Entry]
Name=Wine 9.21
Comment=Run Windows applications with Wine 9.21
Exec=$HOME/.local/share/wine-staging-9.21/bin/wine %f
Terminal=false
Type=Application
MimeType=application/x-ms-dos-executable;application/x-msdownload;
NoDisplay=false
Categories=Utility;
EOF

update-desktop-database "$HOME/.local/share/applications"
```

## Install winetricks

```
wget  https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x winetricks
./winetricks vcrun6sp6
```

#### Configure wine

```
winecfg
```

## Install yabridge

```
mkdir -p "$HOME/.local/share/yabridge"
curl -L \
  -o /tmp/yabridge-5.1.1.tar.gz \
  "https://github.com/robbert-vdh/yabridge/releases/download/5.1.1/yabridge-5.1.1.tar.gz"
tar -xzf /tmp/yabridge-5.1.1.tar.gz \
  -C "$HOME/.local/share/yabridge" \
  --strip-components=1
```

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
yabridgectl set --path="$HOME/.local/share/yabridge"
```

## Allow audio group users to use

set to `/etc/security/limits.conf` if not set or set to other values before tthe line '# End of file'

```
sudo nano /etc/security/limits.conf
```

```
@audio           -      rtprio           95
@audio           -      memlock          unlimited
@audio           -      nice             10
```

## Add user to audio group

```
sudo usermod -a -G audio $USER
```

## Complete pipewire installation

Install missing packages

```
sudo apt install -y pipewire-jack pipewire-audio-client-libraries libspa-0.2-jack
```

initialize config

```
sudo mkdir -p /etc/pipewire/media-session.d
sudo touch /etc/pipewire/media-session.d/with-jack
sudo cp /usr/share/doc/pipewire/examples/ld.so.conf.d/pipewire-jack-*.conf /etc/ld.so.conf.d/
sudo ldconfig
```

## Install pipewire patchbay

```
sudo apt install -y qpwgraph
```

## Enjoy

reboot

```
sudo shutdown -r now
```
