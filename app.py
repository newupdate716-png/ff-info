import os
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "SB_SAKIB_PREMIUM_FINAL_v4"
app.permanent_session_lifetime = timedelta(days=30)

# --- এডমিন পাসওয়ার্ড ---
ADMIN_PASS = "sakib123" 

# ডাটাবেস (Vercel ইন্সট্যান্স চালু থাকা পর্যন্ত থাকবে)
DATABASE = {
    "apis": {}, # {id: {type, url, custom_params: {key: val}}}
    "keys": {}  # {key: {limit, expiry, used}}
}

# --- প্রিমিয়াম ডার্ক থিম UI ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | API MANAGER PRO</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --accent: #00ffcc; --bg: #0a0a0f; --card: #16161d; --danger: #ff4d4d; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #e0e0e0; margin: 0; padding-bottom: 50px; }
        .nav { background: #1a1a24; padding: 20px; text-align: center; border-bottom: 2px solid var(--accent); color: var(--accent); font-size: 22px; font-weight: bold; }
        .container { max-width: 800px; margin: auto; padding: 20px; }
        .card { background: var(--card); border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #252530; }
        h3 { color: var(--accent); border-bottom: 1px solid #333; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #0d0d12; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: var(--accent); border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: #000; transition: 0.3s; }
        button:hover { opacity: 0.8; }
        .api-item, .key-item { background: #1f1f29; padding: 15px; border-radius: 10px; margin-top: 15px; position: relative; }
        .btn-sm { width: auto; padding: 5px 15px; font-size: 12px; margin-left: 5px; }
        .btn-del { background: var(--danger); color: white; }
        .btn-edit { background: #ffcc00; color: black; }
        code { color: #ffcc00; word-break: break-all; background: #000; padding: 2px 5px; border-radius: 4px; }
        .status-active { color: #00ffcc; font-size: 12px; font-weight: bold; }
        .status-expired { color: var(--danger); font-size: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="nav"><i class="fas fa-shield-halved"></i> SB SAKIB PREMIUM API PANEL</div>
    <div class="container">
        {% if page == 'login' %}
            <div class="card" style="max-width: 400px; margin: 100px auto;">
                <h2 style="text-align: center;">ADMIN LOGIN</h2>
                <form method="POST" action="/admin">
                    <input type="password" name="password" placeholder="Admin Password" required>
                    <button type="submit">UNLOCK PANEL</button>
                </form>
            </div>
        {% else %}
            <div class="card">
                <h3><i class="fas fa-plus-circle"></i> ADD NEW API</h3>
                <form action="/add" method="POST">
                    <input type="text" name="type" placeholder="API Type (e.g. Vehicle Info)" required>
                    <input type="text" name="url" placeholder="Main API URL (https://site.com/api?id=)" required>
                    <button type="submit">SAVE & DEPLOY</button>
                </form>
            </div>

            <div class="card">
                <h3><i class="fas fa-key"></i> CREATE PREMIUM KEY</h3>
                <form action="/key" method="POST">
                    <input type="text" name="custom_key" placeholder="Custom Key Name (Optional)">
                    <input type="number" name="limit" placeholder="Usage Limit (Total Requests)" required>
                    <input type="date" name="expiry" required>
                    <button type="submit" style="background: #ffcc00;">GENERATE KEY</button>
                </form>
            </div>

            <h3><i class="fas fa-server"></i> MANAGED APIS & SETTINGS</h3>
            {% for id, api in data.apis.items() %}
                <div class="api-item">
                    <b>Type:</b> {{ api.type }} 
                    <a href="/settings/{{ id }}" class="btn-sm btn-edit" style="float: right; text-decoration: none;"><i class="fas fa-edit"></i> Edit Params</a>
                    <br><br>
                    <code>{{ root }}api/{{ id }}?key=YOUR_KEY&term=VALUE</code>
                </div>
            {% endfor %}

            <h3><i class="fas fa-users-cog"></i> ACTIVE KEYS</h3>
            {% for key, info in data.keys.items() %}
                <div class="key-item">
                    <b>Key:</b> <code>{{ key }}</code> 
                    <a href="/del-key/{{ key }}" class="btn-sm btn-del" style="float: right; text-decoration: none;"><i class="fas fa-trash"></i></a>
                    <br>
                    <small>Usage: {{ info.used }}/{{ info.limit }} | Expiry: {{ info.expiry }}</small>
                    <br>
                    {% if info.used < info.limit %}
                        <span class="status-active">● ACTIVE</span>
                    {% else %}
                        <span class="status-expired">● LIMIT REACHED</span>
                    {% endif %}
                </div>
            {% endfor %}

            <a href="/logout" style="display: block; text-align: center; color: var(--danger); margin-top: 30px; text-decoration: none;">LOGOUT SYSTEM</a>
        {% endif %}
    </div>
</body>
</html>
"""

SETTINGS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit API Params</title>
    <style>
        body { background: #0a0a0f; color: white; font-family: sans-serif; padding: 50px; }
        .card { background: #16161d; padding: 30px; border-radius: 12px; max-width: 500px; margin: auto; border: 1px solid #333; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #000; border: 1px solid #00ffcc; color: #fff; }
        button { width: 100%; padding: 12px; background: #00ffcc; border: none; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h3>Edit Parameters for: {{ api_type }}</h3>
        <form method="POST">
            <label>JSON Parameter Name (e.g. owner):</label>
            <input type="text" name="param_key" value="{{ params.key or '' }}" placeholder="Parameter Key" required>
            <label>New Text/Value:</label>
            <input type="text" name="param_val" value="{{ params.val or '' }}" placeholder="Parameter Value" required>
            <button type="submit">UPDATE API</button>
        </form>
        <br>
        <a href="/admin" style="color: #666; text-decoration: none;">← Back to Dashboard</a>
    </div>
</body>
</html>
"""

# --- Routes ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASS:
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
    
    if session.get('logged_in'):
        return render_template_string(HTML_LAYOUT, page='dash', data=DATABASE, root=request.url_root)
    return render_template_string(HTML_LAYOUT, page='login')

@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    uid = str(uuid.uuid4())[:6]
    DATABASE['apis'][uid] = {
        "type": request.form.get('type'),
        "url": request.form.get('url'),
        "params": {"key": "owner", "val": "SB-SAKIB @sakib01994"}
    }
    return redirect(url_for('admin'))

@app.route('/settings/<api_id>', methods=['GET', 'POST'])
def settings(api_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    api = DATABASE['apis'].get(api_id)
    if request.method == 'POST':
        api['params']['key'] = request.form.get('param_key')
        api['params']['val'] = request.form.get('param_val')
        return redirect(url_for('admin'))
    return render_template_string(SETTINGS_HTML, api_type=api['type'], params=api['params'])

@app.route('/key', methods=['POST'])
def key_gen():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    custom_name = request.form.get('custom_key')
    key = custom_name if custom_name else "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATABASE['keys'][key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'),
        "used": 0
    }
    return redirect(url_for('admin'))

@app.route('/del-key/<key>')
def del_key(key):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    DATABASE['keys'].pop(key, None)
    return redirect(url_for('admin'))

@app.route('/api/<api_id>')
def gateway(api_id):
    api = DATABASE['apis'].get(api_id)
    key = request.args.get('key')
    term = request.args.get('term', '')

    if not api or not key: return jsonify({"error": "Unauthorized"}), 401
    
    k_info = DATABASE['keys'].get(key)
    if not k_info: return jsonify({"error": "Invalid Key"}), 403
    
    if k_info['used'] >= k_info['limit'] or k_info['expiry'] < time.strftime("%Y-%m-%d"):
        return jsonify({"error": "Key Expired/Limit Reached"}), 403

    try:
        # Dynamic Request
        r = requests.get(api['url'], params={"term": term}).json()
        
        # Apply Custom Params (Settings থেকে যা সেট করবেন)
        p_key = api['params']['key']
        p_val = api['params']['val']
        r[p_key] = p_val
        
        k_info['used'] += 1
        return jsonify(r)
    except:
        return jsonify({"error": "Main API Response Error"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

@app.route('/')
def home():
    return redirect(url_for('admin'))
