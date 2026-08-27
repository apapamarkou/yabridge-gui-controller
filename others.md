# Pro-Audio Setup — Other / Unsupported Distributions

Your distribution is not currently supported for automatic setup.

The following instructions describe the general process. Adapt the package manager
commands to your distribution.

---

## 1. Prepare your environment

Update your system using your distribution's package manager.

Add the following to `~/.profile`:

```
export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-9.21/bin"
export WINEFSYNC=1
```

If your display manager does not source `~/.profile` at login (e.g. LightDM), add
to `~/.xsessionrc`:

```
if [ -r "$HOME/.profile" ]; then
    . "$HOME/.profile"
fi
```

---

## 2. Install Wine Staging 9.21

Install the required 32-bit and 64-bit libraries for Wine (freetype, fontconfig,
libX11, libXext, libXrender, libXcursor, libXi, libXinerama, libXrandr, libasound/alsa,
libGL, glibc, cabextract, curl, wget).

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

---

## 3. Install winetricks

```bash
wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x winetricks
./winetricks vcrun6sp6
winecfg
```

---

## 4. Install yabridge 5.1.1

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

---

## 5. Audio group and realtime limits

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

---

## 6. PipeWire JACK

Install PipeWire with JACK support using your distribution's package manager.
The package names vary by distribution. Common names include:

- `pipewire-jack`
- `pipewire-audio-client-libraries`
- `libspa-0.2-jack`

Enable WirePlumber:

```bash
systemctl --user --now enable wireplumber.service
```

---

## 7. Reboot

```bash
sudo shutdown -r now
```
