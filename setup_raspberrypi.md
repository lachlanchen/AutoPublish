# Raspberry Pi setup

This guide provisions a fresh Raspberry Pi for AutoPublish. Run everything from a terminal on the Pi.

## 1. Create a user and log in

Create a sudo user (replace placeholders):

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

Log in with the new user:

```bash
su - <USERNAME>
```

If you connect remotely:

```bash
ssh <USERNAME>@<PI_HOST>
```

## 2. Desktop autologin (lachlan)

To boot straight into the desktop as `lachlan`:

```bash
sudo raspi-config
```

Then:

- System Options -> Boot / Auto Login -> Desktop Autologin
- Select user `lachlan`
- Reboot

## 3. Decide about Docker

Docker works on Raspberry Pi, but Selenium + Chromium + Xvfb is easier to keep stable on the host. Start without Docker, then containerize once the scripts are reliable.

## 4. Clone or update the repo

```bash
mkdir -p /home/<USERNAME>/Projects
cd /home/<USERNAME>/Projects
git clone git@github.com:lachlanchen/AutoPublish.git autopub
# Or use HTTPS if SSH keys are not configured:
# git clone https://github.com/lachlanchen/AutoPublish.git autopub
cd /home/<USERNAME>/Projects/autopub
```

## 5. One-command setup (recommended)

Runs all setup scripts in order (packages, virtual desktop, driver aliases, service):

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Optional VNC password and port:

```bash
export AUTOPUB_VNC_PASSWORD=<VNC_PASSWORD>
export AUTOPUB_VNC_PORT=5901
```

## 6. Install OS packages and Python env

This creates the `autopub` virtual environment and installs dependencies.

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo ./scripts/setup_envs.sh
```

By default, `scripts/setup_envs.sh` installs a minimal set from `requirements.autopub.txt`.
To force the full `requirements.txt` install, run:

```bash
export AUTOPUB_REQUIREMENTS=full
sudo -E ./scripts/setup_envs.sh
```

## 7. Set up the virtual desktop service

This creates `virtual-desktop.service` and starts it on `DISPLAY=:1`.

```bash
export AUTOPUB_USER=<USERNAME>
sudo ./scripts/setup_virtual_desktop_service.sh
```

Check status:

```bash
systemctl status virtual-desktop.service
```

## 8. Set up Chromium driver aliases

```bash
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo ./scripts/download_and_setup_driver.sh
```

## 9. Set up the AutoPublish service

This creates `autopub.service` which starts a tmux session running `app.py`.

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo ./scripts/setup_autopub_service.sh
```

Check status:

```bash
systemctl status autopub.service
```

Attach to tmux:

```bash
tmux attach -t autopub
```

## 10. Notes

- The service uses `DISPLAY=:1`. If you change it, update `AUTOPUB_DISPLAY` when running the setup scripts.
- The app listens on port `8081` by default. Adjust `scripts/start_autopub_tmux.sh` if you want a different port.
- The virtual desktop exposes VNC on port `5901` when `x11vnc` is installed.
- `scripts/setup_envs.sh` installs a minimal `requirements.autopub.txt` by default. Use `AUTOPUB_REQUIREMENTS=full` for the full file.
- When running full mode, the script skips `arandr==0.1.11`, `av==10.0.0`, `cupshelpers==1.0`, `dbus-python==1.3.2`, and `gpg==1.18.0` by default on Pi. Override with `AUTOPUB_PIP_EXCLUDE=""` if you want to try installing them.

## 11. Check VNC + services

Service status:

```bash
systemctl status virtual-desktop.service
systemctl status autopub.service
```

Logs:

```bash
journalctl -u virtual-desktop.service --no-pager -n 200
```

Confirm VNC is listening:

```bash
ss -ltnp | grep 5901
```

Connect from RealVNC Viewer:

- Host: `lazyingart:5901` (or `lazyingart::5901`)
- If you set a password, add it to `/etc/default/autopub` as `AUTOPUB_VNC_PASSWORD=...`, then restart:

```bash
sudo systemctl restart virtual-desktop.service
```
