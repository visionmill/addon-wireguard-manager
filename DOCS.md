# WireGuard Wizard docs

## Setup

The setup wizard creates a WireGuard server profile, generates server keys, and writes the server configuration to:

```text
/data/wireguard/wg0.conf
```

Client profiles and QR codes are stored under:

```text
/data/clients/
```

## Routing modes

### VPN subnet only

Client `AllowedIPs` is limited to the WireGuard subnet.

### Home network / LAN

Client `AllowedIPs` includes the WireGuard subnet and your LAN subnet, for example:

```ini
AllowedIPs = 10.6.0.0/24, 192.168.1.0/24
```

### Route all internet traffic through VPN

Client `AllowedIPs` becomes:

```ini
AllowedIPs = 0.0.0.0/0, ::/0
```

The server adds an iptables masquerade rule so clients can reach the internet through Home Assistant's network connection.

## Router setup

Forward UDP `51820` to the Home Assistant Pi.

If you use a different WireGuard port in the wizard, forward that UDP port instead.

## Starting and restarting WireGuard

The Web UI shows a friendly running/not-running status. Technical command output from `wg-quick` and `wg show` is available under **Show technical details**.

Successful output can still contain command lines such as `ip link add`, `wg setconf`, and `iptables`. Those lines are informational unless the status message says WireGuard could not start.

## iPhone and mobile setup

The QR code is the recommended setup method for iPhone.

If you use the config text instead, save it as a `.conf` file. A `.txt` file will not import into the WireGuard app.

## Reset

Stop the add-on and delete `/data/state.json`, `/data/wireguard/wg0.conf`, and `/data/clients/*` from the add-on data folder.
