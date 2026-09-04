# Windows VST support for Linux

## Disclaimer

The following information has been gathered from various sources online and is valid as of August 2026.
These instructions were tested on VMs with the current versions of the supported systems.
I'm sharing them only to save you time from endless Googling and from cluttering your system with trial-and-error fixes.
I take no responsibility for any issues that may arise. Many commands below require `sudo`. While I personally haven't encountered problems, I strongly recommend that before running anything you **make full backups**:

- Your system (e.g. with `timeshift`)
- Your home folder

## What these instructions cover

1. Prepare your system
2. Install Wine and yabridge for Windows VST support on Linux
3. Set up the required software for the Pro-Audio setup
4. Configure the user group and realtime limits

## Supported distributions

Click on the links to get the instructions:

- [Ubuntu 26.04](distros/Ubuntu26.04.md)
- [Debian 13](distros/Debian13.md)
- [Fedora 44](distros/Fedora44.md)
- [Arch Linux](distros/Arch.md)

---

## Other / Unsupported Distributions

Your distribution is not currently supported for automatic setup.
The following instructions describe the general process — adapt the package manager commands to your distribution.

### 1. Prepare your environment

Update your system using your distribution's package manager.

Add the following to `~/.profile`:

```
export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-9.21/bin"
export WINEFSYNC=1
```

If your display manager does not source `~/.profile` at login (e.g. LightDM), add to `~/.xsessionrc`:

```
if [ -r "$HOME/.profile" ]; then
    . "$HOME/.profile"
fi
```

### 2. Install Wine Staging 9.21

Install the required 32-bit and 64-bit libraries for Wine (freetype, fontconfig, libX11, libXext, libXrender, libXcursor, libXi, libXinerama, libXrandr, libasound/alsa, libGL, glibc, cabextract, curl, wget).

Then download and extract Wine Staging:

```bash
curl -L -o wine-9.21-staging-amd64.tar.xz \
  https://github.com/Kron4ek/Wine-Builds/releases/download/9.21/wine-9.21-staging-amd64.tar.xz
mkdir -p "$HOME/.local/share/wine-staging-9.21"
tar -xJf wine-9.21-staging-amd64.tar.xz \
  --strip-components=1 \
  -C "$HOME/.local/share/wine-staging-9.21"
```

Verify:

```bash
wine --version
```

### 3. Install winetricks

```bash
wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x winetricks
./winetricks vcrun6sp6
winecfg
```

### 4. Install yabridge 5.1.1

```bash
mkdir -p "$HOME/.local/share/yabridge"
curl -L \
  -o /tmp/yabridge-5.1.1.tar.gz \
  "https://github.com/robbert-vdh/yabridge/releases/download/5.1.1/yabridge-5.1.1.tar.gz"
tar -xzf /tmp/yabridge-5.1.1.tar.gz \
  -C "$HOME/.local/share/yabridge" \
  --strip-components=1
```

Create VST directories:

```bash
mkdir -p "$HOME/.wine/drive_c/Program Files/Steinberg/VstPlugins"
mkdir -p "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
mkdir -p "$HOME/.wine/drive_c/Program Files/VSTPlugins"
```

Configure yabridge:

```bash
yabridgectl add "$HOME/.wine/drive_c/Program Files/Steinberg/VstPlugins"
yabridgectl add "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
yabridgectl add "$HOME/.wine/drive_c/Program Files/VSTPlugins"
yabridgectl set --path="$HOME/.local/share/yabridge"
```

### 5. Audio group and realtime limits

Add your user to the `audio` group:

```bash
sudo usermod -a -G audio $USER
```

Add to `/etc/security/limits.conf` before `# End of file`:

```
@audio           -      rtprio           95
@audio           -      memlock          unlimited
@audio           -      nice             10
```

### 6. PipeWire JACK

Install PipeWire with JACK support using your distribution's package manager.
The package names vary by distribution. Common names include:

- `pipewire-jack`
- `pipewire-audio-client-libraries`
- `libspa-0.2-jack`

Enable WirePlumber:

```bash
systemctl --user --now enable wireplumber.service
```

### 7. Reboot

```bash
sudo shutdown -r now
```
