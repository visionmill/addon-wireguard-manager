import base64
import ipaddress
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

DATA = Path(os.environ.get('DATA_DIR', '/data'))
WG_DIR = DATA / 'wireguard'
CLIENT_DIR = DATA / 'clients'
STATE_FILE = DATA / 'state.json'
RESTART_LOG = DATA / 'last_restart.log'
WG_CONF = WG_DIR / 'wg0.conf'
ETC_WG_DIR = Path(os.environ.get('ETC_WG_DIR', '/etc/wireguard'))
ETC_WG_CONF = ETC_WG_DIR / 'wg0.conf'


def sh(cmd: List[str], input_text: Optional[str] = None, check: bool = True) -> str:
    p = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or 'Command failed').strip())
    return p.stdout.strip()


def ensure_dirs():
    WG_DIR.mkdir(parents=True, exist_ok=True)
    CLIENT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        ETC_WG_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        pass


def wg_keypair() -> Dict[str, str]:
    private = sh(['wg', 'genkey'])
    public = sh(['wg', 'pubkey'], input_text=private)
    return {'private_key': private, 'public_key': public}


def psk() -> str:
    return sh(['wg', 'genpsk'])


def load_state() -> Dict:
    ensure_dirs()
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'server': None, 'clients': []}


def save_state(state: Dict):
    ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_restart_log() -> str:
    ensure_dirs()
    if RESTART_LOG.exists():
        return RESTART_LOG.read_text()
    return ''


def clean_name(name: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9_.-]+', '-', name.strip()).strip('-')
    if not cleaned:
        raise ValueError('Client name is required')
    return cleaned[:40]


def clean_route_mode(route_mode: str) -> str:
    if route_mode not in {'home', 'lan', 'all'}:
        raise ValueError('Choose a valid routing mode')
    return route_mode


def next_client_ip(vpn_cidr: str, clients: List[Dict]) -> str:
    net = ipaddress.ip_network(vpn_cidr, strict=False)
    used = {c.get('address', '').split('/')[0] for c in clients}
    # server normally gets first host; clients begin after that
    for host in list(net.hosts())[1:]:
        if str(host) not in used:
            return str(host)
    raise RuntimeError('No free client IPs left in VPN subnet')


def server_address(vpn_cidr: str) -> str:
    net = ipaddress.ip_network(vpn_cidr, strict=False)
    return f'{next(net.hosts())}/{net.prefixlen}'


def detect_default_iface() -> str:
    try:
        out = sh(['sh', '-c', "ip route show default | awk '{print $5; exit}'"], check=False)
        return out or 'eth0'
    except Exception:
        return 'eth0'


def setup_server(public_host: str, port: int, vpn_cidr: str, lan_cidr: str, dns: str, default_route_mode: str) -> Dict:
    ensure_dirs()
    public_host = public_host.strip()
    if not public_host:
        raise ValueError('Public hostname or IP address is required')
    if not 1 <= int(port) <= 65535:
        raise ValueError('WireGuard UDP port must be between 1 and 65535')
    default_route_mode = clean_route_mode(default_route_mode)
    ipaddress.ip_network(vpn_cidr, strict=False)
    if lan_cidr:
        ipaddress.ip_network(lan_cidr, strict=False)
    keys = wg_keypair()
    state = load_state()
    state['server'] = {
        'public_host': public_host,
        'port': int(port),
        'vpn_cidr': vpn_cidr.strip(),
        'server_address': server_address(vpn_cidr),
        'lan_cidr': lan_cidr.strip(),
        'dns': dns.strip() or '1.1.1.1',
        'default_route_mode': default_route_mode,
        'private_key': keys['private_key'],
        'public_key': keys['public_key'],
        'interface': detect_default_iface(),
    }
    state['clients'] = []
    save_state(state)
    render_server_config(state)
    restart_wg()
    return state


def allowed_ips_for_client(server: Dict, route_mode: str) -> str:
    vpn_net = str(ipaddress.ip_network(server['vpn_cidr'], strict=False))
    lan = server.get('lan_cidr') or ''
    if route_mode == 'all':
        return '0.0.0.0/0, ::/0'
    if route_mode == 'lan':
        parts = [vpn_net]
        if lan:
            parts.append(lan)
        return ', '.join(parts)
    return vpn_net


def add_client(name: str, route_mode: str) -> Dict:
    state = load_state()
    if not state.get('server'):
        raise RuntimeError('Run server setup first')
    name = clean_name(name)
    route_mode = clean_route_mode(route_mode)
    if any(c['name'] == name for c in state['clients']):
        raise ValueError('A client with that name already exists')
    keys = wg_keypair()
    address = next_client_ip(state['server']['vpn_cidr'], state['clients'])
    client = {
        'name': name,
        'address': f'{address}/32',
        'private_key': keys['private_key'],
        'public_key': keys['public_key'],
        'preshared_key': psk(),
        'route_mode': route_mode,
        'enabled': True,
    }
    state['clients'].append(client)
    save_state(state)
    render_server_config(state)
    write_client_config(state['server'], client)
    restart_wg()
    return client


def remove_client(name: str):
    state = load_state()
    state['clients'] = [c for c in state.get('clients', []) if c['name'] != name]
    save_state(state)
    render_server_config(state)
    for suffix in ('.conf', '.png'):
        p = CLIENT_DIR / f'{clean_name(name)}{suffix}'
        if p.exists():
            p.unlink()
    restart_wg()


def render_server_config(state: Dict):
    server = state['server']
    # Always detect the live default interface at render time.
    # The container's interface name (eth0) differs from the host name
    # (end0) that was stored during setup, so we don't trust the stored value.
    iface = detect_default_iface()
    vpn_net = str(ipaddress.ip_network(server['vpn_cidr'], strict=False))
    lines = [
        '[Interface]',
        f"Address = {server['server_address']}",
        f"ListenPort = {server['port']}",
        f"PrivateKey = {server['private_key']}",
        'SaveConfig = false',
        '# NAT/forwarding for clients using route-all mode. Safe for LAN-only clients too.',
        f'PostUp = iptables -t nat -A POSTROUTING -s {vpn_net} -o {iface} -j MASQUERADE',
        f'PostDown = iptables -t nat -D POSTROUTING -s {vpn_net} -o {iface} -j MASQUERADE',
        '',
    ]
    for c in state.get('clients', []):
        if not c.get('enabled', True):
            continue
        lines += [
            f"# {c['name']}",
            '[Peer]',
            f"PublicKey = {c['public_key']}",
            f"PresharedKey = {c['preshared_key']}",
            f"AllowedIPs = {c['address']}",
            '',
        ]
    ensure_dirs()
    WG_CONF.write_text('\n'.join(lines))
    WG_CONF.chmod(0o600)
    try:
        if ETC_WG_CONF.exists() or ETC_WG_CONF.is_symlink():
            ETC_WG_CONF.unlink()
        ETC_WG_CONF.symlink_to(WG_CONF)
    except Exception:
        pass


def client_config_text(server: Dict, client: Dict) -> str:
    endpoint = f"{server['public_host']}:{server['port']}"
    address = client['address']
    dns = server.get('dns') or '1.1.1.1'
    allowed = allowed_ips_for_client(server, client.get('route_mode', 'lan'))
    return '\n'.join([
        '[Interface]',
        f'PrivateKey = {client["private_key"]}',
        f'Address = {address}',
        f'DNS = {dns}',
        '',
        '[Peer]',
        f'PublicKey = {server["public_key"]}',
        f'PresharedKey = {client["preshared_key"]}',
        f'Endpoint = {endpoint}',
        f'AllowedIPs = {allowed}',
        'PersistentKeepalive = 25',
        '',
    ])


def write_client_config(server: Dict, client: Dict) -> Path:
    path = CLIENT_DIR / f"{client['name']}.conf"
    path.write_text(client_config_text(server, client))
    path.chmod(0o600)
    return path


def client_qr_png(client_name: str) -> Path:
    import qrcode
    state = load_state()
    client = next(c for c in state['clients'] if c['name'] == client_name)
    txt = client_config_text(state['server'], client)
    img = qrcode.make(txt)
    path = CLIENT_DIR / f'{client_name}.png'
    img.save(path)
    return path


def restart_wg() -> Dict:
    if not WG_CONF.exists():
        log = 'No wg0.conf yet'
        RESTART_LOG.write_text(log)
        return {'ok': False, 'message': 'No WireGuard configuration exists yet.', 'log': log}
    out = []
    ok = True
    for cmd in (['wg-quick', 'down', 'wg0'], ['wg-quick', 'up', 'wg0']):
        p = subprocess.run(cmd, capture_output=True, text=True)
        out.append(f"$ {' '.join(cmd)}\n{p.stdout}{p.stderr}")
        if cmd[1] == 'up' and p.returncode != 0:
            ok = False
            break
    log = '\n'.join(out)
    RESTART_LOG.write_text(log)
    if ok:
        message = 'WireGuard is running.'
    else:
        message = 'WireGuard could not start. Open diagnostics below for details.'
    return {'ok': ok, 'message': message, 'log': log}


def wg_status() -> str:
    return sh(['wg', 'show', 'wg0'], check=False) or 'WireGuard is not running yet.'
