# Fedora 44 pro-audio setup

Open a terminal window (ctrl+alt+T)

## Prepare your environment

update your system

```
sudo dnf -y update
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

Some display managers like XFCEs LightDM wont read the `.profile` at startup. You need to point it into `.xsessionrc`

```
nano ~/.xsessionrc
```

add these lines

```
if [ -r "$HOME/.profile" ]; then
    . "$HOME/.profile"
fi
```

## Install proper wine-staging version

```
sudo dnf -y install glibc.i686 cabextract curl wget freetype freetype.i686 fontconfig fontconfig.i686 \
    libX11 libX11.i686 libXext libXext.i686 libXrender libXrender.i686 \
    libXcursor libXcursor.i686 libXi libXi.i686 libXinerama libXinerama.i686 \
    libXrandr libXrandr.i686
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
sudo dnf install -y qpwgraph
```

## Enjoy

reboot

```
sudo shutdown -r now
```
