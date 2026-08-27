# Arch pro-audio setup

## Intro

Arch has some of the following projects we are installing, in its official repo which is convenient. However we are going to install them "the hard way" to ensure compatibility between them, stability between updates and avoid possible issues.

Open a terminal window (ctrl+alt+T)

## Prepare your environment

```
sudo nano /etc/pacman.conf
```

Uncomment:

```
[multilib]
Include = /etc/pacman.d/mirrorlist
```

update your system

```
sudo pacman -Syu
```

edit and add to '~/.profile' if not exist:

```
nano ~/.profile
```

Add installation paths for wine and yabridge in your home directory:

```
export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-9.21/bin"
export WINEFSYNC=1
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
sudo pacman -S --needed glibc lib32-glibc cabextract curl wget freetype2 lib32-freetype2 \
    fontconfig lib32-fontconfig libx11 lib32-libx11 libxext lib32-libxext \
    libxrender lib32-libxrender libxcursor lib32-libxcursor libxi lib32-libxi \
    libxinerama lib32-libxinerama libxrandr lib32-libxrandr \
    alsa-lib lib32-alsa-lib mesa lib32-mesa libpulse lib32-libpulse
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

to configure wine

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

check if it works

```
yabridgectl sync
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

## Install pipewire patchbay

```
sudo pacman -S --needed qpwgraph
```

## Enjoy

reboot

```
sudo shutdown -r now
```
