import os
from flask import Flask, abort, flash, make_response, render_template, request, send_file, url_for
import wireguard as wg

app = Flask(__name__)
app.secret_key = os.environ.get('WIZARD_SECRET_KEY', 'wireguard-wizard-local')


def app_url(endpoint, **values):
    path = url_for(endpoint, **values)
    ingress_path = (
        request.headers.get('X-Ingress-Path')
        or request.headers.get('X-Forwarded-Prefix')
        or ''
    ).rstrip('/')
    if ingress_path and path.startswith('/'):
        return f'{ingress_path}{path}'
    return path


@app.context_processor
def template_helpers():
    return {'app_url': app_url}


def render_index():
    state = wg.load_state()
    status = wg.wg_status() if state.get('server') else 'Not configured yet.'
    client_configs = {}
    if state.get('server'):
        client_configs = {
            client['name']: wg.client_config_text(state['server'], client)
            for client in state.get('clients', [])
        }
    return render_template(
        'index.html',
        state=state,
        status=status,
        client_configs=client_configs,
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action', '')
        try:
            if action == 'setup':
                wg.setup_server(
                    public_host=request.form['public_host'],
                    port=int(request.form.get('port', 51820)),
                    vpn_cidr=request.form.get('vpn_cidr', '10.6.0.0/24'),
                    lan_cidr=request.form.get('lan_cidr', ''),
                    dns=request.form.get('dns', '1.1.1.1'),
                    default_route_mode=request.form.get('default_route_mode', 'lan'),
                )
                flash('WireGuard server configuration created.', 'success')
            elif action == 'add_client':
                client = wg.add_client(request.form['name'], request.form.get('route_mode', 'lan'))
                flash(f"Added {client['name']}. Scan the QR code or download the config below.", 'success')
            elif action == 'restart':
                result = wg.restart_wg()
                flash(result or 'WireGuard restart requested.', 'success')
            elif action == 'delete_client':
                name = request.form.get('name', '')
                wg.remove_client(name)
                flash(f'Revoked {name}.', 'success')
            else:
                flash('Unknown action.', 'error')
        except Exception as exc:
            flash(str(exc), 'error')
    return render_index()


@app.post('/setup')
def setup():
    try:
        wg.setup_server(
            public_host=request.form['public_host'],
            port=int(request.form.get('port', 51820)),
            vpn_cidr=request.form.get('vpn_cidr', '10.6.0.0/24'),
            lan_cidr=request.form.get('lan_cidr', ''),
            dns=request.form.get('dns', '1.1.1.1'),
            default_route_mode=request.form.get('default_route_mode', 'lan'),
        )
        flash('WireGuard server configuration created.', 'success')
        return render_index()
    except Exception as exc:
        flash(str(exc), 'error')
        return render_index()


@app.post('/clients')
def clients():
    try:
        client = wg.add_client(request.form['name'], request.form.get('route_mode', 'lan'))
        flash(f"Added {client['name']}. Scan the QR code or download the config below.", 'success')
        return render_index()
    except Exception as exc:
        flash(str(exc), 'error')
        return render_index()


@app.post('/clients/<name>/delete')
def delete_client(name):
    try:
        wg.remove_client(name)
        flash(f'Revoked {name}.', 'success')
        return render_index()
    except Exception as exc:
        flash(str(exc), 'error')
        return render_index()


@app.post('/restart')
def restart():
    result = wg.restart_wg()
    flash(result or 'WireGuard restart requested.', 'success')
    return render_index()


@app.get('/clients/<name>.conf')
def download_conf(name):
    state = wg.load_state()
    client = next((c for c in state.get('clients', []) if c['name'] == name), None)
    if not client:
        abort(404)
    path = wg.write_client_config(state['server'], client)
    response = make_response(send_file(
        path,
        as_attachment=True,
        download_name=f'{name}.conf',
        mimetype='application/octet-stream',
    ))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.get('/clients/<name>.png')
def qr(name):
    if not any(c['name'] == name for c in wg.load_state().get('clients', [])):
        abort(404)
    return send_file(wg.client_qr_png(name), mimetype='image/png')
