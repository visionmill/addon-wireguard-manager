from pathlib import Path
from flask import Flask, abort, redirect, render_template, request, send_file, url_for
import wireguard as wg

app = Flask(__name__)


@app.route('/')
def index():
    state = wg.load_state()
    status = wg.wg_status() if state.get('server') else 'Not configured yet.'
    return render_template('index.html', state=state, status=status)


@app.post('/setup')
def setup():
    wg.setup_server(
        public_host=request.form['public_host'],
        port=int(request.form.get('port', 51820)),
        vpn_cidr=request.form.get('vpn_cidr', '10.6.0.0/24'),
        lan_cidr=request.form.get('lan_cidr', ''),
        dns=request.form.get('dns', '1.1.1.1'),
        default_route_mode=request.form.get('default_route_mode', 'lan'),
    )
    return redirect(url_for('index'))


@app.post('/clients')
def clients():
    wg.add_client(request.form['name'], request.form.get('route_mode', 'lan'))
    return redirect(url_for('index'))


@app.post('/clients/<name>/delete')
def delete_client(name):
    wg.remove_client(name)
    return redirect(url_for('index'))


@app.post('/restart')
def restart():
    wg.restart_wg()
    return redirect(url_for('index'))


@app.get('/clients/<name>.conf')
def download_conf(name):
    state = wg.load_state()
    client = next((c for c in state.get('clients', []) if c['name'] == name), None)
    if not client:
        abort(404)
    path = wg.write_client_config(state['server'], client)
    return send_file(path, as_attachment=True, download_name=f'{name}.conf', mimetype='text/plain')


@app.get('/clients/<name>.png')
def qr(name):
    if not any(c['name'] == name for c in wg.load_state().get('clients', [])):
        abort(404)
    return send_file(wg.client_qr_png(name), mimetype='image/png')
