# Changelog

## 0.2.3

- Client configs and server state now persist across add-on uninstalls.
- Re-running server setup after reinstall no longer wipes existing clients.

## 0.2.2

- Moved data storage to `/config/wireguard_wizard` so it survives uninstall.

## 0.2.1

- Added FORWARD iptables rules required for VPN traffic to flow through the server.

## 0.2.0

- Fixed iptables interface detection — hardcoded `eth0` which is what the container always sees regardless of host interface name.

## 0.1.9

- Attempted dynamic interface detection via `/sys/class/net` excluding docker/bridge interfaces.

## 0.1.8

- Attempted dynamic interface detection to fix NAT on systems where host interface is not `end0`.

## 0.1.7

- Fixed iptables MASQUERADE rule using wrong interface name (`end0`) inside container.

## 0.1.6

- Refined add-on artwork with a clean WireGuard symbol.
- Added a Web UI shortcut back to the Home Assistant add-on settings page.

## 0.1.5

- Added add-on artwork and release-ready documentation.
- Added `.gitignore` entries for macOS and Python cache files.

## 0.1.4

- Replaced raw restart command output with friendly status messages.
- Moved technical WireGuard output into a diagnostics section.

## 0.1.3

- Removed unsupported `sysctl` startup command from generated WireGuard configs.
- Set generated server and client config permissions to `0600`.
- Replaced external config download links with an in-page save button.

## 0.1.2

- Added mobile-friendly config text and copy controls.
- Improved `.conf` download response headers.

## 0.1.1

- Fixed Home Assistant ingress form handling.
- Refreshed the Web UI.

## 0.1.0

- Initial MVP.
