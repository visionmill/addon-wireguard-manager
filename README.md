# WireGuard Wizard for Home Assistant OS

A PiVPN-style Home Assistant add-on for creating and managing a simple WireGuard VPN server.

Features:

- Ingress web UI inside Home Assistant
- Guided server setup wizard
- Add/revoke clients
- QR code generation
- iPhone-friendly config copy/save controls
- Friendly service status with optional technical diagnostics
- Per-client routing mode:
  - VPN subnet only
  - Home network / LAN
  - Route all traffic through VPN

This add-on is intended for Home Assistant OS installations where the add-on can manage a WireGuard interface with `NET_ADMIN`, `host_network`, `iptables`, and `wg-quick`.

## Install from GitHub

1. In Home Assistant, go to **Settings -> Add-ons -> Add-on Store**.
2. Open the three-dot menu and choose **Repositories**.
3. Add this repository:

```text
https://github.com/visionmill/addon-wireguard-manager
```

4. Install **WireGuard Wizard**.
5. Start it and open the Web UI.
6. Forward UDP `51820` on your router to your Home Assistant Pi.

## Using Client Profiles

For phones, scanning the QR code is usually the easiest setup path.

The device card also includes:

- **Save .conf**: saves a WireGuard profile file in the browser.
- **Show config text**: shows the raw config and a copy button.

If you manually save the config text, the filename must end in `.conf`. A `.txt` file will not import into the WireGuard app.

## Important

This add-on uses `NET_ADMIN`, `host_network`, `iptables`, and `wg-quick`. It is intentionally powerful because VPN routing/NAT needs network control.

WireGuard is a trademark of Jason A. Donenfeld. This project is not affiliated with or endorsed by the WireGuard project.
