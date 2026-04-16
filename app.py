import os
import requests
from flask import Flask, request, jsonify, render_template_string, session, redirect
from datetime import timedelta, datetime

app = Flask(__name__)

# সিকিউরিটি কনফিগারেশন
app.secret_key = os.getenv("SECRET_KEY", "SAKIB_ULTIMATE_PREMIUM_999")
app.permanent_session_lifetime = timedelta(days=30)

ADMIN_PASS = "sakib123"

# ইন-মেমোরি ডাটাবেস (সার্ভার রিস্টার্ট দিলে ডাটা মুছে যাবে)
DATABASE = {
    "apis": {},
    "keys": {}
}

# উন্নত UI এবং ডাইনামিক ইনপুট হ্যান্ডলিং
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | PREMIUM MANAGER</title>
    <style>
        :root{--accent:#00ffcc;--bg:#08080c;--card:#12121a;--danger:#ff4d4d;--edit:#ffcc00;}
        body{font-family:'Segoe UI',sans-serif;background:var(--bg);color:#e0e0e0;margin:0;padding:0;}
        .nav{background:#161622;padding:20px;text-align:center;border-bottom:2px solid var(--accent);color:var(--accent);font-size:22px;font-weight:bold;letter-spacing:1px;}
        .container{max-width:800px;margin:auto;padding:20px;}
        .card{background:var(--card);border-radius:15px;padding:25px;margin-bottom:25px;border:1px solid #252535;box-shadow: 0 4px 15px rgba(0,0,0,0.3);}
        h3{margin-top:0;color:var(--accent);border-bottom:1px solid #333;padding-bottom:10px;}
        input, select{width:100%;padding:12px;margin:10px 0;border-radius:8px;border:1px solid #333;background:#000;color:#fff;box-sizing:border-box;}
        button{width:100%;padding:12px;background:var(--accent);border:none;border-radius:8px;font-weight:bold;cursor:pointer;color:#000;transition:0.3s;}
        button:hover{opacity:0.8;}
        .item{background:#1a1a26;padding:15px;border-radius:10px;margin-top:15px;border-left:4px solid var(--accent);position:relative;}
        .badge{font-size:10px;padding:3px 8px;border-radius:10px;background:#333;color:var(--accent);margin-left:5px;}
        .action-btns{display:flex;gap:10px;margin-top:10px;}
        .btn-sm{padding:5px 12px;border-radius:5px;text-decoration:none;font-size:12px;font-weight:bold;cursor:pointer;border:none;}
        .btn-edit{background:var(--edit);color:#000;}
        .btn-del{background:var(--danger);color:#fff;}
        .param-row{display:flex;gap:10px;margin-bottom:5px;}
        code{color:var(--edit);background:#000;padding:4px 8px;border-radius:5px;display:block;margin-top:10px;font-size:11px;border:1px dashed #444;}
        .checkbox-group{display:grid;grid-template-columns: 1fr 1fr;gap:10px;margin:10px 0;text-align:left;}
    </style>
</head>
<body>
    <div class="nav">SB SAKIB PREMIUM PANEL</div>
    <div class="container">

    {% if page == 'login' %}
        <div class="card" style="max-width:400px;margin:100px auto;">
            <h3>ADMIN LOGIN</h3>
            <form method="POST">
                <input type="password" name="password" placeholder="Enter Admin Password" required>
                <button type="submit">LOGIN SYSTEM</button>
            </form>
            {% if error %}<p style="color:var(--danger);text-align:center;">Invalid Password!</p>{% endif %}
        </div>

    {% elif page == 'dash' %}
        <div class="card">
            <h3>ADD NEW API SOURCE</h3>
            <form action="/add" method="POST">
                <input type="text" name="slug" placeholder="API Path (e.g. facebook)" required>
                <input type="url" name="url" placeholder="Main API URL (https://...)" required>
                <input type="text" name="param" placeholder="Query Parameter Name (e.g. url, link, id)" required>
                <button type="submit">DEPLOY API</button>
            </form>
        </div>

        <div class="card">
            <h3>GENERATE ACCESS KEY</h3>
            <form action="/key-gen" method="POST">
                <input type="text" name="c_key" placeholder="Custom Key (Optional)">
                <input type="number" name="limit" placeholder="Usage Limit (e.g. 100)" required>
                <input type="date" name="expiry" required>
                <p style="font-size:12px;margin-bottom:5px;">Select Permitted APIs:</p>
                <div class="checkbox-group">
                    {% for slug in data['apis'].keys() %}
                    <label><input type="checkbox" name="allowed_apis" value="{{ slug }}" checked> {{ slug|upper }}</label>
                    {% endfor %}
                </div>
                <button type="submit">CREATE KEY</button>
            </form>
        </div>

        <h3>ACTIVE API ENDPOINTS</h3>
        {% for slug, api in data['apis'].items() %}
        <div class="item">
            <a href="/settings/{{ slug }}" class="btn-sm btn-edit" style="float:right;">SETTINGS</a>
            <strong>{{ slug|upper }}</strong> <span class="badge">GET</span>
            <code>{{ root }}{{ slug }}?key=[KEY]&{{ api.param }}=[VALUE]</code>
        </div>
        {% endfor %}

        <h3 style="margin-top:30px;">MANAGE KEYS</h3>
        {% for key, info in data['keys'].items() %}
        <div class="item">
            <strong>Key: {{ key }}</strong> 
            <div style="font-size:13px;margin-top:5px;color:#aaa;">
                Usage: {{ info.used }}/{{ info.limit }} | Expiry: {{ info.expiry }} <br>
                Permissions: {{ info.allowed|join(', ') }}
            </div>
            <div class="action-btns">
                <a href="/edit-key/{{ key }}" class="btn-sm btn-edit">EDIT / TIME / LIMIT</a>
                <form action="/del-key" method="POST" style="display:inline;">
                    <input type="hidden" name="key_id" value="{{ key }}">
                    <button type="submit" class="btn-sm btn-del">DELETE</button>
                </form>
            </div>
        </div>
        {% endfor %}
        <br><a href="/logout" style="color:var(--danger);text-decoration:none;font-weight:bold;">Logout Admin</a>

    {% elif page == 'edit_api' %}
        <div class="card">
            <h3>EDIT API: {{ slug }}</h3>
            <form method="POST">
                <p>Main Parameter:</p>
                <input type="text" name="param" value="{{ api.param }}" placeholder="Main Parameter">
                
                <p>Custom JSON Response Fields:</p>
                <div id="param-fields">
                    {% for k, v in api['custom_params'].items() %}
                    <div class="param-row">
                        <input type="text" name="p_keys" value="{{ k }}" placeholder="Field Name">
                        <input type="text" name="p_vals" value="{{ v }}" placeholder="Field Value">
                    </div>
                    {% endfor %}
                </div>
                <button type="button" onclick="addParamRow()" style="background:#444;color:#fff;margin-bottom:10px;">+ ADD NEW FIELD</button>
                <button type="submit">SAVE SETTINGS</button>
            </form>
        </div>
        <script>
            function addParamRow(){
                const div = document.createElement('div');
                div.className = 'param-row';
                div.innerHTML = '<input type="text" name="p_keys" placeholder="Field Name"><input type="text" name="p_vals" placeholder="Field Value">';
                document.getElementById('param-fields').appendChild(div);
            }
        </script>

    {% elif page == 'edit_key' %}
        <div class="card">
            <h3>EDIT KEY: {{ key_id }}</h3>
            <form method="POST">
                <p>Usage Limit:</p>
                <input type="number" name="limit" value="{{ key_info.limit }}">
                <p>Expiry Date:</p>
                <input type="date" name="expiry" value="{{ key_info.expiry }}">
                <p>Modify Permissions:</p>
                <div class="checkbox-group">
                    {% for slug in data['apis'].keys() %}
                    <label><input type="checkbox" name="allowed_apis" value="{{ slug }}" {% if slug in key_info.allowed %}checked{% endif %}> {{ slug|upper }}</label>
                    {% endfor %}
                </div>
                <button type="submit">UPDATE KEY</button>
            </form>
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
            session['logged_in'] = True
            session.permanent = True
            return redirect('/admin')
        error = True
    
    if session.get('logged_in'):
        return render_template_string(HTML_LAYOUT, page='dash', data=DATABASE, root=request.url_root)
    return render_template_string(HTML_LAYOUT, page='login', error=error)

@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'): return redirect('/admin')
    slug = request.form.get('slug').strip().lower()
    DATABASE['apis'][slug] = {
        "url": request.form.get('url'),
        "param": request.form.get('param'),
        "custom_params": {"owner": "SB-SAKIB", "credit": "@sakib01994"}
    }
    return redirect('/admin')

@app.route('/settings/<slug>', methods=['GET', 'POST'])
def settings(slug):
    if not session.get('logged_in'): return redirect('/admin')
    api = DATABASE['apis'].get(slug)
    if request.method == 'POST':
        api['param'] = request.form.get('param')
        keys = request.form.getlist('p_keys')
        vals = request.form.getlist('p_vals')
        api['custom_params'] = {k: v for k, v in zip(keys, vals) if k}
        return redirect('/admin')
    return render_template_string(HTML_LAYOUT, page='edit_api', api=api, slug=slug)

@app.route('/key-gen', methods=['POST'])
def key_gen():
    if not session.get('logged_in'): return redirect('/admin')
    key = request.form.get('c_key') or "SAKIB-" + os.urandom(3).hex().upper()
    DATABASE['keys'][key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'),
        "used": 0,
        "allowed": request.form.getlist('allowed_apis')
    }
    return redirect('/admin')

@app.route('/edit-key/<key_id>', methods=['GET', 'POST'])
def edit_key(key_id):
    if not session.get('logged_in'): return redirect('/admin')
    key_info = DATABASE['keys'].get(key_id)
    if request.method == 'POST':
        key_info['limit'] = int(request.form.get('limit'))
        key_info['expiry'] = request.form.get('expiry')
        key_info['allowed'] = request.form.getlist('allowed_apis')
        return redirect('/admin')
    return render_template_string(HTML_LAYOUT, page='edit_key', key_id=key_id, key_info=key_info, data=DATABASE)

@app.route('/del-key', methods=['POST'])
def del_key():
    if not session.get('logged_in'): return redirect('/admin')
    DATABASE['keys'].pop(request.form.get('key_id'), None)
    return redirect('/admin')

@app.route('/<slug>')
def dynamic_api(slug):
    api = DATABASE['apis'].get(slug)
    if not api: return jsonify({"status": "error", "message": "API Not Found"}), 404

    key_code = request.args.get('key')
    if not key_code: return jsonify({"status": "error", "message": "Access Key Required"}), 401

    k = DATABASE['keys'].get(key_code)
    if not k: return jsonify({"status": "error", "message": "Invalid Key"}), 403

    # পারমিশন চেক
    if slug not in k['allowed']:
        return jsonify({
            "status": "NOT_PERMITTED",
            "message": f"You don't have access to {slug} API",
            "owner": "SB-SAKIB"
        }), 403

    # এক্সপায়ারি চেক
    if datetime.now().date() > datetime.strptime(k['expiry'], "%Y-%m-%d").date():
        return jsonify({"status": "error", "message": "Key Expired", "owner": "SB-SAKIB"}), 403

    # লিমিট চেক
    if k['used'] >= k['limit']:
        return jsonify({
            "status": "LIMIT_EXCEEDED", 
            "message": "Usage limit finished",
            "owner": "SB-SAKIB"
        }), 403

    term = request.args.get(api['param'])
    if not term: return jsonify({"status": "error", "message": f"Parameter '{api['param']}' missing"}), 400

    try:
        r = requests.get(api['url'], params={api['param']: term}, timeout=15)
        res_data = r.json()
        
        # কাস্টম প্যারামিটার ইনজেকশন
        final_resp = res_data if isinstance(res_data, dict) else {"data": res_data}
        for ck, cv in api['custom_params'].items():
            final_resp[ck] = cv
        
        final_resp['status'] = "SUCCESS BY SAKIB"
        final_resp['remaining_limit'] = k['limit'] - (k['used'] + 1)
        
        k['used'] += 1  # লিমিট কমানো
        return jsonify(final_resp)
    except Exception as e:
        return jsonify({"status": "error", "message": "Origin API Error", "details": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')

@app.route('/')
def home():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, port=5000)