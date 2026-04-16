import os
import json
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = "SB_SAKIB_PREMIUM_ADMIN"

# --- সেটিংস ---
ADMIN_PASS = "sakib123"  # আপনার কাঙ্ক্ষিত পাসওয়ার্ড এখানে দিন
DATA = {
    "apis": {},
    "keys": {}
}

# --- ডেকোরেটর (সুরক্ষার জন্য) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- প্রিমিয়াম এইচটিএমএল ডিজাইন (CSS সহ) ---
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SB SAKIB | API Control Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --p: #00d2ff; --s: #3a7bd5; --dark: #1a1a2e; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--dark); color: white; margin: 0; }
        .nav { background: linear-gradient(90deg, var(--p), var(--s)); padding: 15px; text-align: center; font-weight: bold; font-size: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .container { max-width: 900px; margin: 20px auto; padding: 20px; }
        .card { background: #16213e; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #0f3460; box-shadow: 0 8px 20px rgba(0,0,0,0.2); }
        input, button, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: none; box-sizing: border-box; }
        input { background: #0f3460; color: white; border: 1px solid #1a1a2e; }
        button { background: linear-gradient(45deg, var(--p), var(--s)); color: white; cursor: pointer; font-weight: bold; border-radius: 8px; transition: 0.3s; }
        button:hover { transform: scale(1.02); opacity: 0.9; }
        .api-item { border-left: 5px solid var(--p); background: #1a1a2e; padding: 15px; margin: 10px 0; border-radius: 4px; position: relative; }
        .badge { background: #00d2ff; color: #1a1a2e; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .footer { text-align: center; font-size: 12px; color: #533483; margin-top: 50px; }
    </style>
</head>
<body>
    <div class="nav">SB SAKIB PREMIUM PANEL</div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    <div class="footer">Developed by SB-SAKIB &copy; 2026</div>
</body>
</html>
"""

LOGIN_HTML = """
{% extends "base" %}
{% block content %}
<div class="card" style="max-width: 400px; margin: auto; text-align: center;">
    <h2>Admin Access</h2>
    <form method="POST">
        <input type="password" name="password" placeholder="Enter Secure Password" required>
        <button type="submit">Login to Panel</button>
    </form>
</div>
{% endblock %}
"""

DASHBOARD_HTML = """
{% extends "base" %}
{% block content %}
<div class="card">
    <h3>🚀 Add New Main API</h3>
    <form action="/add-api" method="POST">
        <input type="text" name="type" placeholder="API Type Name (e.g. TG Info)" required>
        <input type="text" name="url" placeholder="Full API URL with parameters" required>
        <button type="submit">Add & Auto-Convert</button>
    </form>
</div>

<div class="card">
    <h3>🔑 Create API Key</h3>
    <form action="/gen-key" method="POST">
        <input type="number" name="limit" placeholder="Request Limit (e.g. 100)" required>
        <input type="date" name="expiry" required>
        <button type="submit" style="background: #e94560;">Generate Premium Key</button>
    </form>
</div>

<h3>📦 Managed APIs (Converted to Vercel)</h3>
{% for id, item in data.apis.items() %}
<div class="api-item">
    <span class="badge">{{ item.type }}</span><br>
    <small>Vercel Sub-API:</small><br>
    <code>{{ root_url }}api/{{ id }}?key=[YOUR_KEY]&term=[VALUE]</code>
    <hr style="border: 0.1px solid #333;">
    <p>Target: {{ item.url }}</p>
</div>
{% endfor %}

<h3>🎫 Active Keys</h3>
{% for key, info in data.keys.items() %}
<div class="api-item" style="border-left-color: #e94560;">
    <b>Key:</b> {{ key }} <br>
    <b>Status:</b> Used {{ info.used }}/{{ info.limit }} | Expires: {{ info.expiry }}
</div>
{% endfor %}

<a href="/logout" style="color: #ff4d4d; text-decoration: none;">Logout Panel</a>
{% endblock %}
"""

# --- রাউটস ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('dashboard'))
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', LOGIN_HTML))

@app.route('/admin')
@login_required
def dashboard():
    root_url = request.url_root
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', DASHBOARD_HTML), data=DATA, root_url=root_url)

@app.route('/add-api', methods=['POST'])
@login_required
def add_api():
    api_id = str(uuid.uuid4())[:6]
    DATA['apis'][api_id] = {
        "type": request.form.get('type'),
        "url": request.form.get('url'),
        "params_map": {"owner": "SB-SAKIB", "status": "Premium User"}
    }
    return redirect(url_for('dashboard'))

@app.route('/gen-key', methods=['POST'])
@login_required
def gen_key():
    new_key = "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATA['keys'][new_key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'),
        "used": 0
    }
    return redirect(url_for('dashboard'))

@app.route('/api/<api_id>')
def api_gateway(api_id):
    api = DATA['apis'].get(api_id)
    key = request.args.get('key')
    term = request.args.get('term', '')

    if not api or not key:
        return jsonify({"error": "Unauthorized or Invalid API"}), 401

    key_info = DATA['keys'].get(key)
    if not key_info:
        return jsonify({"error": "Invalid Key"}), 403

    # লিমিট ও ডেট চেক
    today = time.strftime("%Y-%m-%d")
    if key_info['used'] >= key_info['limit'] or key_info['expiry'] < today:
        return jsonify({"error": "Key Expired or Limit Reached"}), 403

    try:
        # মেইন এপিআই কল (এখানে term প্যারামিটারটি পাস করা হচ্ছে)
        final_url = api['url'].replace('TERM_PLACEHOLDER', term) # যদি ইউআরএল এ প্লেসহোল্ডার থাকে
        # অথবা সিম্পল ডায়নামিক কল:
        response = requests.get(api['url'], params={"term": term}).json()
        
        # জেসন প্যারামিটার এডিট (আপনার রিকোয়েস্ট অনুযায়ী)
        response['owner'] = "SB-SAKIB @sakib01994"
        response['status'] = "SUCCESS BY SAKIB"
        response['credit'] = "Premium API System"

        # লিমিট কমানো
        key_info['used'] += 1
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": "Main API Error", "msg": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return "<h1>API Server Active</h1>"

if __name__ == '__main__':
    app.run(debug=True)
