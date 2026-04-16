import os
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

app = Flask(__name__)
# Vercel-এ সেশন এরর এড়াতে ফিক্সড কী
app.secret_key = "SAKIB_ULTIMATE_SECURE_FIX_100"
app.permanent_session_lifetime = timedelta(days=30)

# অ্যাডমিন পাসওয়ার্ড
ADMIN_PASS = "sakib123"

# ডাটাবেস (মেমোরি স্টোরেজ)
DATABASE = {
    "apis": {}, 
    "keys": {}  
}

# --- প্রিমিয়াম UI (একদম ক্লিন এবং ফাস্ট) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | API MANAGER</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --accent: #00ffcc; --bg: #0a0a0f; --card: #15151b; --danger: #ff4d4d; }
        body { font-family: sans-serif; background: var(--bg); color: #e0e0e0; margin: 0; padding: 0; }
        .nav { background: #1a1a24; padding: 20px; text-align: center; border-bottom: 2px solid var(--accent); color: var(--accent); font-size: 20px; font-weight: bold; }
        .container { max-width: 600px; margin: auto; padding: 20px; }
        .card { background: var(--card); border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #252530; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #000; color: #fff; box-sizing: border-box; outline: none; }
        button { width: 100%; padding: 12px; background: var(--accent); border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: #000; }
        .item { background: #1f1f29; padding: 15px; border-radius: 10px; margin-top: 15px; border-left: 4px solid var(--accent); }
        .btn-edit { background: #ffcc00; color: #000; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 12px; float: right; }
        .btn-del { background: var(--danger); color: #fff; padding: 5px 10px; border-radius: 4px; border:none; font-size: 12px; float: right; margin-left: 10px; cursor:pointer;}
        code { color: #ffcc00; background: #000; padding: 2px 6px; border-radius: 4px; word-break: break-all; font-size: 12px; }
    </style>
</head>
<body>
    <div class="nav">SB SAKIB PREMIUM PANEL</div>
    <div class="container">
        {% if page == 'login' %}
            <div class="card" style="max-width: 350px; margin: 50px auto;">
                <h3 style="text-align: center;">ADMIN LOGIN</h3>
                <form method="POST" action="/admin">
                    <input type="password" name="password" placeholder="Admin Password" required>
                    <button type="submit">LOGIN</button>
                </form>
                {% if error %}<p style="color:red; text-align:center;">Wrong Password!</p>{% endif %}
            </div>
        {% elif page == 'dash' %}
            <div class="card">
                <h3><i class="fas fa-plus"></i> ADD API</h3>
                <form action="/add" method="POST">
                    <input type="text" name="type" placeholder="API Type (e.g. TG INFO)" required>
                    <input type="text" name="url" placeholder="Main URL (https://...)" required>
                    <button type="submit">DEPLOY</button>
                </form>
            </div>
            <div class="card">
                <h3><i class="fas fa-key"></i> CREATE KEY</h3>
                <form action="/key" method="POST">
                    <input type="text" name="c_key" placeholder="Custom Key (Optional)">
                    <input type="number" name="limit" placeholder="Request Limit" required>
                    <input type="date" name="expiry" required>
                    <button type="submit" style="background: #ffcc00;">GENERATE</button>
                </form>
            </div>
            <h3>ACTIVE APIS</h3>
            {% for id, api in data.apis.items() %}
                <div class="item">
                    <a href="/settings/{{ id }}" class="btn-edit">SETTINGS</a>
                    <b>{{ api.type }}</b><br><br>
                    <code>{{ root }}api/{{ id }}?key=[KEY]&term=[VALUE]</code>
                </div>
            {% endfor %}
            <h3>ACTIVE KEYS</h3>
            {% for key, info in data.keys.items() %}
                <div class="item" style="border-left-color: #ffcc00;">
                    <form action="/del-key" method="POST" style="display:inline;">
                        <input type="hidden" name="key_id" value="{{ key }}">
                        <button type="submit" class="btn-del">DELETE</button>
                    </form>
                    <b>Key:</b> <code>{{ key }}</code><br>
                    <small>Used: {{ info.used }}/{{ info.limit }} | Exp: {{ info.expiry }}</small>
                </div>
            {% endfor %}
            <p style="text-align: center;"><a href="/logout" style="color: var(--danger); text-decoration: none;">Logout Panel</a></p>
        {% elif page == 'edit' %}
            <div class="card">
                <h3>EDIT PARAMETERS</h3>
                <form method="POST">
                    <label>JSON Key (e.g. owner):</label>
                    <input type="text" name="p_key" value="{{ api.params.key }}" required>
                    <label>New Value:</label>
                    <input type="text" name="p_val" value="{{ api.params.val }}" required>
                    <button type="submit">SAVE CHANGES</button>
                </form>
                <br><a href="/admin" style="color: #888;">← Cancel</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = False
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASS:
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        error = True
    
    if session.get('logged_in'):
        return render_template_string(HTML_LAYOUT, page='dash', data=DATABASE, root=request.url_root)
    return render_template_string(HTML_LAYOUT, page='login', error=error)

@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    uid = str(uuid.uuid4())[:6]
    DATABASE['apis'][uid] = {
        "type": request.form.get('type'), "url": request.form.get('url'),
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
    key = request.form.get('c_key') or "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATABASE['keys'][key] = {"limit": int(request.form.get('limit')), "expiry": request.form.get('expiry'), "used": 0}
    return redirect(url_for('admin'))

@app.route('/del-key', methods=['POST'])
def del_key():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    DATABASE['keys'].pop(request.form.get('key_id'), None)
    return redirect(url_for('admin'))

@app.route('/api/<api_id>')
def gateway(api_id):
    api = DATABASE['apis'].get(api_id)
    key = request.args.get('key')
    term = request.args.get('term', '')
    if not api or not key: return jsonify({"error": "Auth Failed"}), 401
    k_info = DATABASE['keys'].get(key)
    if not k_info or k_info['used'] >= k_info['limit'] or k_info['expiry'] < time.strftime("%Y-%m-%d"):
        return jsonify({"error": "Key Invalid/Expired"}), 403
    try:
        r = requests.get(api['url'], params={"term": term}).json()
        r[api['params']['key']] = api['params']['val']
        r['status'] = "SUCCESS BY SAKIB"
        k_info['used'] += 1
        return jsonify(r)
    except: return jsonify({"error": "Main API Error"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

@app.route('/')
def home():
    return redirect(url_for('admin'))

# Vercel-এর জন্য এক্সপোর্ট
app = app 
