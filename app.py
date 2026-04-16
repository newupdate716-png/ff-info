import os
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "SB_SAKIB_FINAL_PRO_99"
app.permanent_session_lifetime = timedelta(days=30)

# --- এডমিন পাসওয়ার্ড ---
ADMIN_PASS = "sakib123" 

# গ্লোবাল ডাটাবেস
DATABASE = {
    "apis": {}, 
    "keys": {}  
}

# --- প্রিমিয়াম UI লেআউট ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | API PRO</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --accent: #00ffcc; --bg: #0d0d12; --card: #16161d; --danger: #ff4d4d; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #e0e0e0; margin: 0; padding-bottom: 50px; }
        .nav { background: #1a1a24; padding: 20px; text-align: center; border-bottom: 2px solid var(--accent); color: var(--accent); font-size: 22px; font-weight: bold; }
        .container { max-width: 800px; margin: auto; padding: 20px; }
        .card { background: var(--card); border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #252530; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h3 { color: var(--accent); margin-top: 0; display: flex; justify-content: space-between; align-items: center; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #0d0d12; color: #fff; box-sizing: border-box; outline: none; }
        input:focus { border-color: var(--accent); }
        button { width: 100%; padding: 12px; background: var(--accent); border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: #000; transition: 0.3s; }
        button:hover { opacity: 0.8; }
        .item { background: #1f1f29; padding: 15px; border-radius: 10px; margin-top: 15px; border-left: 4px solid var(--accent); position: relative; }
        .btn-sm { padding: 5px 10px; font-size: 12px; border-radius: 4px; text-decoration: none; font-weight: bold; }
        .btn-edit { background: #ffcc00; color: #000; float: right; }
        .btn-del { background: var(--danger); color: #fff; float: right; margin-left: 10px; }
        code { color: #ffcc00; background: #000; padding: 2px 5px; border-radius: 4px; word-break: break-all; }
        .status { font-size: 11px; font-weight: bold; margin-top: 5px; display: block; }
    </style>
</head>
<body>
    <div class="nav"><i class="fas fa-bolt"></i> SB SAKIB PREMIUM API PANEL</div>
    <div class="container">
        {% if page == 'login' %}
            <div class="card" style="max-width: 380px; margin: 100px auto;">
                <h2 style="text-align: center; color: var(--accent);">ADMIN LOGIN</h2>
                <form method="POST" action="/admin">
                    <input type="password" name="password" placeholder="Enter Password" required>
                    <button type="submit">LOGIN</button>
                </form>
            </div>
        {% elif page == 'dash' %}
            <div class="card">
                <h3><i class="fas fa-plus-circle"></i> ADD MAIN API</h3>
                <form action="/add" method="POST">
                    <input type="text" name="type" placeholder="API Type (e.g. Number Info)" required>
                    <input type="text" name="url" placeholder="Main API URL (https://site.com/api?id=)" required>
                    <button type="submit">DEPLOY SUB-API</button>
                </form>
            </div>

            <div class="card">
                <h3><i class="fas fa-key"></i> GENERATE KEY</h3>
                <form action="/key" method="POST">
                    <input type="text" name="custom_key" placeholder="Custom Key Name (Optional)">
                    <input type="number" name="limit" placeholder="Limit" required>
                    <input type="date" name="expiry" required>
                    <button type="submit" style="background: #ffcc00;">CREATE KEY</button>
                </form>
            </div>

            <h3><i class="fas fa-server"></i> ACTIVE APIS</h3>
            {% for id, api in data.apis.items() %}
                <div class="item">
                    <a href="/settings/{{ id }}" class="btn-sm btn-edit"><i class="fas fa-cog"></i> SETTINGS</a>
                    <b>Type:</b> {{ api.type }}<br><br>
                    <code>{{ root }}api/{{ id }}?key=KEY&term=VALUE</code>
                </div>
            {% endfor %}

            <h3><i class="fas fa-id-card"></i> ACTIVE KEYS</h3>
            {% for key, info in data.keys.items() %}
                <div class="item" style="border-left-color: #ffcc00;">
                    <a href="/del-key/{{ key }}" class="btn-sm btn-del"><i class="fas fa-trash"></i></a>
                    <b>Key:</b> <code>{{ key }}</code><br>
                    <small>Usage: {{ info.used }}/{{ info.limit }} | Expiry: {{ info.expiry }}</small>
                </div>
            {% endfor %}

            <p style="text-align: center;"><a href="/logout" style="color: var(--danger); text-decoration: none;">Logout System</a></p>
        {% elif page == 'edit' %}
            <div class="card" style="max-width: 500px; margin: 50px auto;">
                <h3>EDIT PARAMETERS</h3>
                <form method="POST">
                    <label style="font-size: 12px;">JSON Key (e.g. owner):</label>
                    <input type="text" name="p_key" value="{{ api.params.key }}" required>
                    <label style="font-size: 12px;">Replacement Text:</label>
                    <input type="text" name="p_val" value="{{ api.params.val }}" required>
                    <button type="submit">UPDATE CHANGES</button>
                </form>
                <br>
                <a href="/admin" style="color: #888; text-decoration: none;">← Back</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- রাউটস ---

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
        api['params']['key'] = request.form.get('p_key')
        api['params']['val'] = request.form.get('p_val')
        return redirect(url_for('admin'))
    return render_template_string(HTML_LAYOUT, page='edit', api=api)

@app.route('/key', methods=['POST'])
def key_gen():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    c_key = request.form.get('custom_key')
    key = c_key if c_key else "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATABASE['keys'][key] = {"limit": int(request.form.get('limit')), "expiry": request.form.get('expiry'), "used": 0}
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
    if not k_info or k_info['used'] >= k_info['limit'] or k_info['expiry'] < time.strftime("%Y-%m-%d"):
        return jsonify({"error": "Invalid Key or Limit Reached"}), 403

    try:
        r = requests.get(api['url'], params={"term": term}).json()
        # প্যারামিটার চেঞ্জ
        r[api['params']['key']] = api['params']['val']
        k_info['used'] += 1
        return jsonify(r)
    except:
        return jsonify({"error": "Main API Error"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

@app.route('/')
def home():
    return redirect(url_for('admin'))
