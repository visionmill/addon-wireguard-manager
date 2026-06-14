# WireGuard Wizard for Home Assistant OS

A PiVPN-style Home Assistant add-on MVP for WireGuard.

Features:

- Ingress web UI inside Home Assistant
- One-page server setup wizard
- Add/revoke clients
- QR code generation
- Downloadable `.conf` files
- Per-client routing mode:
  - VPN subnet only
  - Home network / LAN
  - Route all traffic through VPN

This is an MVP for personal testing on HAOS, especially Raspberry Pi 4 / `aarch64`.

## Install as a local add-on

1. Copy the `ha-wireguard-wizard` folder to your Home Assistant add-ons folder.
2. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
3. Open the three-dot menu and choose **Repositories** if using a git repo, or reload local add-ons if copied locally.
4. Install **WireGuard Wizard**.
5. Start it and open the Web UI.
6. Forward UDP `51820` on your router to your Home Assistant Pi.

## Important

This add-on uses `NET_ADMIN`, `host_network`, `iptables`, and `wg-quick`. It is intentionally powerful because VPN routing/NAT needs network control.

