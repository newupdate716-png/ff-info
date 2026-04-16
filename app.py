import os
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

app = Flask(__name__)
# Vercel-এ সেশন ঠিক রাখতে একটি ইউনিক সিক্রেট কী
app.secret_key = "SB_SAKIB_ULTRA_SECURE_999"
app.permanent_session_lifetime = timedelta(days=30)

# অ্যাডমিন পাসওয়ার্ড (আপনার চাহিদা অনুযায়ী)
ADMIN_PASS = "sakib123" 

# ডাটাবেস (Vercel ইন্সট্যান্স চালু থাকা পর্যন্ত মেমোরিতে থাকবে)
DATABASE = {
    "apis": {}, 
    "keys": {}  
}

# --- প্রিমিয়াম ডার্ক থিম UI ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | API MANAGER PRO</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --accent: #00ffcc; --bg: #0d0d12; --card: #16161d; --danger: #ff4d4d; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #e0e0e0; margin: 0; padding-bottom: 50px; }
        .nav { background: #1a1a24; padding: 20px; text-align: center; border-bottom: 2px solid var(--accent); color: var(--accent); font-size: 22px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .container { max-width: 800px; margin: auto; padding: 20px; }
        .card { background: var(--card); border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #252530; }
        h3 { color: var(--accent); margin-top: 0; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #0d0d12; color: #fff; box-sizing: border-box; outline: none; transition: 0.3s; }
        input:focus { border-color: var(--accent); }
        button { width: 100%; padding: 12px; background: var(--accent); border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: #000; transition: 0.3s; }
        button:hover { opacity: 0.8; transform: translateY(-1px); }
        .item { background: #1f1f29; padding: 15px; border-radius: 10px; margin-top: 15px; border-left: 4px solid var(--accent); position: relative; }
        .btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 4px; text-decoration: none; font-weight: bold; cursor: pointer; display: inline-block; }
        .btn-edit { background: #ffcc00; color: #000; float: right; border: none; }
        .btn-del { background: var(--danger); color: #fff; float: right; margin-left: 10px; border: none; }
        code { color: #ffcc00; background: #000; padding: 2px 6px; border-radius: 4px; word-break: break-all; font-size: 13px; }
    </style>
</head>
<body>
    <div class="nav"><i class="fas fa-crown"></i> SB SAKIB PREMIUM API PANEL</div>
    <div class="container">
        {% if page == 'login' %}
            <div class="card" style="max-width: 380px; margin: 100px auto;">
                <h2 style="text-align: center; color: var(--accent);">ADMIN LOGIN</h2>
                <form method="POST" action="/admin">
                    <input type="password" name="password" placeholder="Enter Admin Password" required>
                    <button type="submit">UNLOCK SYSTEM</button>
                </form>
            </div>
        {% elif page == 'dash' %}
            <div class="card">
                <h3><i class="fas fa-plus-circle"></i> ADD NEW API</h3>
                <form action="/add" method="POST">
                    <input type="text" name="type" placeholder="API Type (e.g. TG INFO)" required>
                    <input type="text" name="url" placeholder="Main API URL (https://...)" required>
                    <button type="submit">ADD & CONVERT</button>
                </form>
            </div>
            <div class="card">
                <h3><i class="fas fa-key"></i> CREATE KEY</h3>
                <form action="/key" method="POST">
                    <input type="text" name="c_key" placeholder="Custom Key Name (Optional)">
                    <input type="number" name="limit" placeholder="Usage Limit" required>
                    <input type="date" name="expiry" required>
                    <button type="submit" style="background: #ffcc00;">GENERATE PREMIUM KEY</button>
                </form>
            </div>
            <h3><i class="fas fa-server"></i> MANAGED APIS</h3>
            {% for id, api in data.apis.items() %}
                <div class="item">
                    <a href="/settings/{{ id }}" class="btn-sm btn-edit"><i class="fas fa-edit"></i> SETTINGS</a>
                    <b>Type:</b> {{ api.type }}<br><br>
                    <code>{{ root }}api/{{ id }}?key=[KEY]&term=[VALUE]</code>
                </div>
            {% endfor %}
            <h3><i class="fas fa-id-card"></i> ACTIVE KEYS</h3>
            {% for key, info in data.keys.items() %}
                <div class="item" style="border-left-color: #ffcc00;">
                    <form action="/del-key" method="POST" style="display:inline;">
                        <input type="hidden" name="key_id" value="{{ key }}">
                        <button type="submit" class="btn-sm btn-del" style="width: auto;"><i class="fas fa-trash"></i></button>
                    </form>
                    <b>Key:</b> <code>{{ key }}</code><br>
                    <small>Usage: {{ info.used }}/{{ info.limit }} | Expire: {{ info.expiry }}</small>
                </div>
            {% endfor %}
            <p style="text-align: center;"><a href="/logout" style="color: var(--danger); text-decoration: none;">Logout Panel</a></p>
        {% elif page == 'edit' %}
            <div class="card" style="max-width: 500px; margin: 50px auto;">
                <h3>EDIT JSON PARAMS</h3>
                <form method="POST">
                    <label style="font-size: 12px; color: #888;">JSON Parameter Key:</label>
                    <input type="text" name="p_key" value="{{ api.params.key }}" required>
                    <label style="font-size: 12px; color: #888;">Replacement Value:</label>
                    <input type="text" name="p_val" value="{{ api.params.val }}" required>
                    <button type="submit">SAVE CHANGES</button>
                </form>
                <br>
                <a href="/admin" style="color: #666; text-decoration: none;">← Cancel</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

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
    c_key = request.form.get('c_key')
    key = c_key if c_key else "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATABASE['keys'][key] = {"limit": int(request.form.get('limit')), "expiry": request.form.get('expiry'), "used": 0}
    return redirect(url_for('admin'))

@app.route('/del-key', methods=['POST'])
def del_key():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    key_id = request.form.get('key_id')
    DATABASE['keys'].pop(key_id, None)
    return redirect(url_for('admin'))

@app.route('/api/<api_id>')
def gateway(api_id):
    api = DATABASE['apis'].get(api_id)
    key = request.args.get('key')
    term = request.args.get('term', '')
    if not api or not key: return jsonify({"error": "Auth Failed"}), 401
    
    k_info = DATABASE['keys'].get(key)
    if not k_info or k_info['used'] >= k_info['limit'] or k_info['expiry'] < time.strftime("%Y-%m-%d"):
        return jsonify({"error": "Invalid/Expired Key"}), 403

    try:
        # মেইন এপিআই কল
        r = requests.get(api['url'], params={"term": term}).json()
        # কাস্টম প্যারামিটার রিপ্লেস
        r[api['params']['key']] = api['params']['val']
        # ক্রেডিট সবসময় ফিক্সড রাখতে চাইলে:
        r['status'] = "SUCCESS BY SAKIB"
        
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

# Vercel এর জন্য অ্যাপ এক্সপোর্ট
app_instance = app