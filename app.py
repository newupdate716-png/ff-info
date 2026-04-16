import os
import json
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "SB_SAKIB_PREMIUM_ADMIN_v3"
app.permanent_session_lifetime = timedelta(days=30) # ৩০ দিন পর্যন্ত লগইন থাকবে

# --- সেটিংস (পাসওয়ার্ড কোডের মধ্যেই আছে) ---
ADMIN_PASS = "sakib123" 

# Vercel-এ ডাটা সংরক্ষণের জন্য টেম্পোরারি ডিকশনারি
DATA = {
    "apis": {},
    "keys": {}
}

# --- প্রিমিয়াম ডার্ক থিম UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | API MANAGER</title>
    <style>
        :root { --main: #00f2fe; --bg: #0a0a0c; --card: #151518; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: #fff; margin: 0; padding: 0; }
        .header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; text-align: center; font-size: 24px; font-weight: 800; box-shadow: 0 5px 20px rgba(0,242,254,0.2); }
        .container { max-width: 800px; margin: 30px auto; padding: 0 15px; }
        .card { background: var(--card); border: 1px solid #222; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #1c1c21; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 14px; background: #00f2fe; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #4facfe; transform: translateY(-2px); }
        .api-box { border-left: 4px solid #00f2fe; background: #1c1c21; padding: 15px; margin: 15px 0; border-radius: 5px; }
        code { color: #00f2fe; word-break: break-all; }
        .badge { background: #00f2fe; color: #000; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="header">SB SAKIB PREMIUM API PANEL</div>
    <div class="container">
        {% if page == 'login' %}
        <div class="card" style="max-width: 400px; margin: 50px auto;">
            <h2 style="text-align: center;">Admin Access</h2>
            <form method="POST" action="/admin">
                <input type="password" name="password" placeholder="Enter Admin Password" required>
                <button type="submit">Login Now</button>
            </form>
            {% if error %}<p style="color: red; text-align: center;">Incorrect Password!</p>{% endif %}
        </div>
        {% elif page == 'dashboard' %}
        <div class="card">
            <h3>➕ Add New Main API</h3>
            <form action="/add-api" method="POST">
                <input type="text" name="type" placeholder="Type (e.g. TG Number)" required>
                <input type="text" name="url" placeholder="Original API URL (e.g. https://site.com/api?id=)" required>
                <button type="submit">Deploy Sub-API</button>
            </form>
        </div>

        <div class="card">
            <h3>🔑 Generate API Key</h3>
            <form action="/gen-key" method="POST">
                <input type="number" name="limit" placeholder="Request Limit" required>
                <input type="date" name="expiry" required>
                <button type="submit" style="background: #ff4b2b; color: white;">Generate Premium Key</button>
            </form>
        </div>

        <h3>📦 Active Sub-APIs</h3>
        {% for id, item in data.apis.items() %}
        <div class="api-box">
            <span class="badge">{{ item.type }}</span><br>
            <p>Vercel URL: <code>{{ root_url }}api/{{ id }}?key=YOUR_KEY&term=SEARCH_VALUE</code></p>
            <small style="color: #666;">Target: {{ item.url }}</small>
        </div>
        {% endfor %}

        <h3>🎫 Active Keys</h3>
        {% for key, info in data.keys.items() %}
        <div class="api-box" style="border-left-color: #ff4b2b;">
            <b>Key:</b> {{ key }} <br>
            <b>Usage:</b> {{ info.used }}/{{ info.limit }} | <b>Expiry:</b> {{ info.expiry }}
        </div>
        {% endfor %}

        <p style="text-align: center;"><a href="/logout" style="color: #666; text-decoration: none;">Logout Panel</a></p>
        {% endif %}
    </div>
</body>
</html>
"""

# --- রাউট লজিক ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASS:
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return render_template_string(HTML_TEMPLATE, page='login', error=True)
    
    if session.get('logged_in'):
        return render_template_string(HTML_TEMPLATE, page='dashboard', data=DATA, root_url=request.url_root)
    
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/add-api', methods=['POST'])
def add_api():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    api_id = str(uuid.uuid4())[:6]
    DATA['apis'][api_id] = {
        "type": request.form.get('type'),
        "url": request.form.get('url')
    }
    return redirect(url_for('admin'))

@app.route('/gen-key', methods=['POST'])
def gen_key():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    new_key = "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATA['keys'][new_key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'),
        "used": 0
    }
    return redirect(url_for('admin'))

@app.route('/api/<api_id>')
def gateway(api_id):
    api = DATA['apis'].get(api_id)
    key = request.args.get('key')
    term = request.args.get('term', '')

    if not api or not key:
        return jsonify({"error": "Unauthorized Access"}), 401

    key_info = DATA['keys'].get(key)
    if not key_info:
        return jsonify({"error": "Invalid API Key"}), 403

    # লিমিট ও এক্সপায়ারি চেক
    today = time.strftime("%Y-%m-%d")
    if key_info['used'] >= key_info['limit'] or key_info['expiry'] < today:
        return jsonify({"error": "Key Expired or Limit Reached"}), 403

    try:
        # মেইন এপিআই কল করা হচ্ছে
        # আপনার অরিজিনাল ইউআরএল এ যদি প্যারামিটার যোগ করতে হয়:
        resp = requests.get(f"{api['url']}{term}").json()
        
        # আপনার রিকোয়েস্ট অনুযায়ী JSON প্যারামিটার এডিট
        resp['owner'] = "SB-SAKIB @sakib01994"
        resp['status'] = "SUCCESS BY SAKIB"
        resp['contact'] = "@sakib01994"

        # লিমিট আপডেট
        key_info['used'] += 1
        return jsonify(resp)
    except:
        return jsonify({"error": "Main API not responding"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

@app.route('/')
def index():
    return "<h1>System Active. Visit /admin to login.</h1>"
