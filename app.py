import os
import requests
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "SB_SAKIB_PREMIUM_FINAL_VERSION"
app.permanent_session_lifetime = timedelta(days=7)

# --- এডমিন সেটিংস ---
ADMIN_PASS = "sakib123" 

# গ্লোবাল ভেরিয়েবল (Vercel ইন্সট্যান্স চালু থাকা পর্যন্ত ডাটা থাকবে)
DATABASE = {
    "apis": {},
    "keys": {}
}

# --- প্রিমিয়াম ডার্ক ইউআই (একদম ক্লিন ডিজাইন) ---
UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAKIB API PANEL</title>
    <style>
        :root { --accent: #00ffcc; --bg: #0d0d12; --card: #16161d; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: #e0e0e0; margin: 0; }
        .nav { background: #1a1a24; padding: 20px; text-align: center; border-bottom: 2px solid var(--accent); font-weight: bold; font-size: 22px; letter-spacing: 1px; color: var(--accent); }
        .container { max-width: 700px; margin: 30px auto; padding: 0 20px; }
        .card { background: var(--card); border-radius: 15px; padding: 25px; margin-bottom: 25px; border: 1px solid #252530; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h3 { margin-top: 0; color: var(--accent); font-size: 18px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #0d0d12; color: #fff; box-sizing: border-box; outline: none; }
        input:focus { border-color: var(--accent); }
        button { width: 100%; padding: 14px; background: var(--accent); border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: #000; transition: 0.3s; }
        button:hover { opacity: 0.8; transform: translateY(-2px); }
        .api-item { background: #1f1f29; padding: 15px; border-radius: 10px; border-left: 4px solid var(--accent); margin-top: 15px; }
        code { color: #ffcc00; word-break: break-all; }
        .badge { background: var(--accent); color: #000; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: bold; }
        .logout-btn { display: block; text-align: center; color: #ff4d4d; text-decoration: none; margin-top: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="nav">SB SAKIB PREMIUM API PANEL</div>
    <div class="container">
        {% if page == 'login' %}
            <div class="card" style="max-width: 350px; margin: 100px auto;">
                <h3 style="text-align: center;">ADMIN LOGIN</h3>
                <form method="POST">
                    <input type="password" name="password" placeholder="Admin Password" required>
                    <button type="submit">LOGIN</button>
                </form>
                {% if error %}<p style="color: #ff4d4d; text-align: center; font-size: 13px;">Invalid Password!</p>{% endif %}
            </div>
        {% else %}
            <div class="card">
                <h3>➕ ADD NEW API</h3>
                <form action="/add" method="POST">
                    <input type="text" name="type" placeholder="API Type (e.g. TG Number)" required>
                    <input type="text" name="url" placeholder="Main API URL (https://...)" required>
                    <button type="submit">DEPLOY API</button>
                </form>
            </div>
            <div class="card">
                <h3>🔑 GENERATE KEY</h3>
                <form action="/key" method="POST">
                    <input type="number" name="limit" placeholder="Request Limit" required>
                    <input type="date" name="expiry" required>
                    <button type="submit" style="background: #ffcc00;">CREATE KEY</button>
                </form>
            </div>
            <h3>📦 DEPLOYED APIS</h3>
            {% for id, api in data.apis.items() %}
                <div class="api-item">
                    <span class="badge">{{ api.type }}</span><br>
                    <p style="font-size: 14px;">URL: <code>{{ root }}api/{{ id }}?key=YOUR_KEY&term=VALUE</code></p>
                </div>
            {% endfor %}
            <a href="/logout" class="logout-btn">LOGOUT SYSTEM</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    error = False
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        error = True
    
    if session.get('logged_in'):
        return render_template_string(UI_HTML, page='dash', data=DATABASE, root=request.url_root)
    return render_template_string(UI_HTML, page='login', error=error)

@app.route('/add', methods=['POST'])
def add_api():
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    uid = str(uuid.uuid4())[:6]
    DATABASE['apis'][uid] = {
        "type": request.form.get('type'),
        "url": request.form.get('url')
    }
    return redirect(url_for('admin_panel'))

@app.route('/key', methods=['POST'])
def gen_key():
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    key = "SAKIB-" + str(uuid.uuid4())[:8].upper()
    DATABASE['keys'][key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'),
        "used": 0
    }
    return redirect(url_for('admin_panel'))

@app.route('/api/<api_id>')
def api_handler(api_id):
    api = DATABASE['apis'].get(api_id)
    user_key = request.args.get('key')
    term = request.args.get('term', '')

    if not api or not user_key:
        return jsonify({"status": "error", "msg": "API or Key missing"}), 401

    key_info = DATABASE['keys'].get(user_key)
    if not key_info:
        return jsonify({"status": "error", "msg": "Invalid Key"}), 403

    # এক্সপায়ারি চেক
    if key_info['used'] >= key_info['limit'] or key_info['expiry'] < time.strftime("%Y-%m-%d"):
        return jsonify({"status": "error", "msg": "Key Expired or Limit Reached"}), 403

    try:
        # মেইন এপিআই কল
        main_url = api['url']
        if "?" in main_url:
            target = f"{main_url}&term={term}"
        else:
            target = f"{main_url}?term={term}"
            
        r = requests.get(target).json()
        
        # প্রিমিয়াম প্যারামিটার মডিফিকেশন
        r['owner'] = "SB-SAKIB @sakib01994"
        r['status'] = "SUCCESS BY SAKIB"
        r['contact'] = "@sakib01994"
        
        key_info['used'] += 1
        return jsonify(r)
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_panel'))

@app.route('/')
def home():
    return redirect(url_for('admin_panel'))

# Vercel এর জন্য গ্লোবাল এরর হ্যান্ডলিং
@app.errorhandler(500)
def internal_error(e):
    return "<h1>500 Error: Application Problem. Check Vercel Logs.</h1>", 500

if __name__ == '__main__':
    app.run(debug=True)
