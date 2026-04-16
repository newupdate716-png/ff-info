import os
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

# Flask অ্যাপ ডিক্লারেশন
app = Flask(__name__)
app.secret_key = "SB_SAKIB_ULTIMATE_KEY_99" # এটি পরিবর্তন করবেন না
app.permanent_session_lifetime = timedelta(days=30)

# অ্যাডমিন পাসওয়ার্ড
ADMIN_PASS = "sakib123" 

# ডাটাবেস (Vercel ইন্সট্যান্স চালু থাকা পর্যন্ত থাকবে)
DATABASE = {
    "apis": {},
    "keys": {}
}

# প্রিমিয়াম ডিজাইন
HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>SB SAKIB | API PANEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #050505; color: #fff; font-family: sans-serif; margin: 0; padding: 0; }
        .header { background: #00ffcc; color: #000; padding: 15px; text-align: center; font-weight: bold; font-size: 20px; }
        .box { background: #111; margin: 20px; padding: 20px; border-radius: 10px; border: 1px solid #222; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 5px; border: 1px solid #333; background: #000; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #00ffcc; border: none; font-weight: bold; cursor: pointer; border-radius: 5px; }
        .api-card { border-left: 4px solid #00ffcc; background: #1a1a1a; padding: 10px; margin-top: 10px; }
        code { color: #00ffcc; font-size: 13px; }
    </style>
</head>
<body>
    <div class="header">SB SAKIB PREMIUM API CREATOR</div>
    <div class="container">
        {% if page == 'login' %}
        <div class="box" style="max-width: 350px; margin: 50px auto;">
            <h2 style="text-align: center;">LOGIN</h2>
            <form method="POST" action="/admin">
                <input type="password" name="password" placeholder="Admin Password" required>
                <button type="submit">LOGIN</button>
            </form>
        </div>
        {% else %}
        <div class="box">
            <h3>ADD NEW API</h3>
            <form action="/add" method="POST">
                <input type="text" name="type" placeholder="API Type (e.g. TG INFO)" required>
                <input type="text" name="url" placeholder="Main API URL" required>
                <button type="submit">DEPLOY SUB-API</button>
            </form>
        </div>
        <div class="box">
            <h3>GENERATE KEY</h3>
            <form action="/key" method="POST">
                <input type="number" name="limit" placeholder="Request Limit" required>
                <input type="date" name="expiry" required>
                <button type="submit">CREATE KEY</button>
            </form>
        </div>
        <div class="box">
            <h3>ACTIVE APIS</h3>
            {% for id, api in data.apis.items() %}
            <div class="api-card">
                <b>Type:</b> {{ api.type }}<br>
                <code>{{ root }}api/{{ id }}?key=KEY&term=VALUE</code>
            </div>
            {% endfor %}
        </div>
        <p style="text-align: center;"><a href="/logout" style="color: red;">Logout</a></p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return redirect(url_for('admin_panel'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASS:
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
    
    if session.get('logged_in'):
        return render_template_string(HTML_LAYOUT, page='dash', data=DATABASE, root=request.url_root)
    return render_template_string(HTML_LAYOUT, page='login')

@app.route('/add', methods=['POST'])
def add_api():
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    uid = str(uuid.uuid4())[:6]
    DATABASE['apis'][uid] = {"type": request.form.get('type'), "url": request.form.get('url')}
    return redirect(url_for('admin_panel'))

@app.route('/key', methods=['POST'])
def gen_key():
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    key = "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATABASE['keys'][key] = {"limit": int(request.form.get('limit')), "expiry": request.form.get('expiry'), "used": 0}
    return redirect(url_for('admin_panel'))

@app.route('/api/<api_id>')
def gateway(api_id):
    api = DATABASE['apis'].get(api_id)
    key = request.args.get('key')
    term = request.args.get('term', '')
    if not api or not key: return jsonify({"error": "Auth Failed"}), 401
    
    key_info = DATABASE['keys'].get(key)
    if not key_info: return jsonify({"error": "Invalid Key"}), 403
    
    if key_info['used'] >= key_info['limit'] or key_info['expiry'] < time.strftime("%Y-%m-%d"):
        return jsonify({"error": "Limit Reached"}), 403

    try:
        # মেইন এপিআই কল এবং ডাটা রিপ্লেস
        r = requests.get(api['url'], params={"term": term}).json()
        r['owner'] = "SB-SAKIB @sakib01994"
        r['status'] = "SUCCESS BY SAKIB"
        key_info['used'] += 1
        return jsonify(r)
    except:
        return jsonify({"error": "Failed to fetch data"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_panel'))

# Vercel এর জন্য এক্সপোর্ট
app_instance = app 
