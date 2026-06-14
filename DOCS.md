# WireGuard Wizard docs

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

## Reset

Stop the add-on and delete `/data/state.json`, `/data/wireguard/wg0.conf`, and `/data/clients/*` from the add-on data folder.
