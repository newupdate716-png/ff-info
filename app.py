import os
import requests
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta, datetime

app = Flask(__name__)

# সিকিউরিটি কনফিগারেশন
app.secret_key = os.getenv("SECRET_KEY", "SAKIB_ULTRA_PREMIUM_V4_CORE")
app.permanent_session_lifetime = timedelta(days=30)

ADMIN_PASS = "sakib123"

# ডাটাবেস স্ট্রাকচার
DATABASE = {
    "apis": {},
    "keys": {}
}

# প্রিমিয়াম এনিমেটেড UI (Glassmorphism + Neon Effect)
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | PREMIUM MANAGER V4</title>
    <style>
        :root{--accent:#00ffcc;--bg:#050508;--card:#0f0f1c;--danger:#ff4d4d;--edit:#ffcc00;--success:#2ecc71;--border:rgba(255,255,255,0.08);}
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes glow { 0% { box-shadow: 0 0 5px rgba(0,255,204,0.2); } 50% { box-shadow: 0 0 15px rgba(0,255,204,0.5); } 100% { box-shadow: 0 0 5px rgba(0,255,204,0.2); } }

        body{font-family:'Segoe UI', Roboto, sans-serif;background:var(--bg);color:#e0e0e0;margin:0;padding:0;overflow-x:hidden;}
        
        .nav{background:rgba(15, 15, 28, 0.9);padding:22px;text-align:center;border-bottom:1px solid var(--accent);color:var(--accent);font-size:26px;font-weight:900;letter-spacing:3px;backdrop-filter: blur(15px);position: sticky;top: 0;z-index: 1000;text-shadow: 0 0 10px rgba(0,255,204,0.5);}
        
        .container{max-width:900px;margin:auto;padding:30px;animation: fadeIn 0.8s ease;}
        .card{background:var(--card);border-radius:24px;padding:30px;margin-bottom:30px;border:1px solid var(--border);box-shadow: 0 15px 35px rgba(0,0,0,0.6);transition: 0.4s;position: relative;overflow: hidden;}
        .card:hover{border-color: var(--accent);transform: translateY(-5px);}
        
        h3{margin-top:0;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:15px;text-transform: uppercase;font-size:18px;letter-spacing:1px;}
        
        input, select{width:100%;padding:15px;margin:12px 0;border-radius:12px;border:1px solid var(--border);background:rgba(0,0,0,0.4);color:#fff;box-sizing:border-box;outline:none;transition: 0.3s;font-size:14px;}
        input:focus{border-color: var(--accent);background:rgba(0,0,0,0.6);}
        
        .btn{padding:14px 24px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;transition:0.3s;display:inline-flex;align-items:center;justify-content:center;text-decoration:none;font-size:14px;gap:8px;}
        .btn-primary{background:var(--accent);color:#000;animation: glow 3s infinite;}
        .btn-danger{background:var(--danger);color:#fff;}
        .btn-edit{background:var(--edit);color:#000;}
        .btn-back{background:rgba(255,255,255,0.05);color:#fff;margin-bottom:20px;border:1px solid var(--border);}
        .btn:hover{filter: brightness(1.2);transform: scale(1.03);}

        .item{background:rgba(255,255,255,0.02);padding:20px;border-radius:18px;margin-top:15px;border:1px solid var(--border);position:relative;transition: 0.3s;}
        .item:hover{background: rgba(255,255,255,0.05);border-color: var(--accent);}
        
        .perm-box{background:rgba(0,0,0,0.3);padding:15px;border-radius:15px;margin:10px 0;border:1px solid var(--border);}
        .perm-item{display: flex;align-items: center;justify-content: space-between;padding:8px 0;border-bottom: 1px solid rgba(255,255,255,0.05);}
        .perm-item:last-child{border:none;}
        
        .checkbox-container { display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: bold;}
        .checkbox-container input { width: 20px; height: 20px; cursor: pointer; margin: 0;}
        
        .badge{font-size:10px;padding:5px 12px;border-radius:20px;background:rgba(0,255,204,0.1);color:var(--accent);border: 1px solid var(--accent);font-weight: bold;}
        code{color:var(--edit);background:#000;padding:12px;border-radius:12px;display:block;margin-top:15px;font-size:12px;border:1px solid var(--border);word-wrap: break-word;}
        
        .limit-input{width: 100px !important; padding: 5px !important; margin: 0 !important; text-align: center;}
    </style>
</head>
<body>
    <div class="nav">SB SAKIB PREMIUM V4</div>
    <div class="container">

    {% if page == 'login' %}
        <div class="card" style="max-width:400px;margin:100px auto;">
            <h3>ADMIN LOGIN</h3>
            <form method="POST">
                <input type="password" name="password" placeholder="Enter Password" required>
                <button type="submit" class="btn btn-primary" style="width:100%;">LOGIN CORE</button>
            </form>
            {% if error %}<p style="color:var(--danger);text-align:center;margin-top:15px;">Access Denied!</p>{% endif %}
        </div>

    {% elif page == 'dash' %}
        <div class="card">
            <h3>DEPLOY NEW API SOURCE</h3>
            <form action="/add" method="POST">
                <input type="text" name="slug" placeholder="API Slug (e.g. fb_dl)" required>
                <input type="url" name="url" placeholder="Original API Endpoint URL" required>
                <input type="text" name="param" placeholder="Query Parameter (e.g. url, id, link)" required>
                <button type="submit" class="btn btn-primary" style="width:100%;">DEPLOY NOW</button>
            </form>
        </div>

        <div class="card">
            <h3>GENERATE MULTI-API KEY</h3>
            <form action="/key-gen" method="POST">
                <input type="text" name="c_key" placeholder="Custom Access Key (Optional)">
                <input type="date" name="expiry" required>
                
                <p style="font-size:13px; color:var(--accent); margin-bottom:10px;">Configure API Access & Limits:</p>
                <div class="perm-box">
                    {% if not data['apis'] %}<p style="font-size:12px; color:#666;">No APIs deployed yet.</p>{% endif %}
                    {% for slug in data['apis'].keys() %}
                    <div class="perm-item">
                        <label class="checkbox-container">
                            <input type="checkbox" name="allowed_apis" value="{{ slug }}" checked>
                            {{ slug|upper }}
                        </label>
                        <div>
                            <span style="font-size:11px; color:#aaa;">Limit:</span>
                            <input type="number" name="limit_{{ slug }}" value="100" class="limit-input">
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;">GENERATE MASTER KEY</button>
            </form>
        </div>

        <h3>SYSTEM ENDPOINTS</h3>
        {% for slug, api in data['apis'].items() %}
        <div class="item">
            <a href="/settings/{{ slug }}" class="btn btn-edit" style="float:right; padding:5px 12px; font-size:11px;">CONFIG</a>
            <strong>{{ slug|upper }}</strong> <span class="badge">ACTIVE</span>
            <code>{{ root }}{{ slug }}?key=[KEY]&{{ api.param }}=[VALUE]</code>
        </div>
        {% endfor %}

        <h3 style="margin-top:40px;">MANAGED KEYS</h3>
        {% for key, info in data['keys'].items() %}
        <div class="item">
            <strong>KEY: {{ key }}</strong>
            <div style="font-size:12px; margin-top:10px;">
                {% for s, l in info.permissions.items() %}
                <span style="background:rgba(255,255,255,0.05); padding:3px 8px; border-radius:5px; margin-right:5px; border:1px solid var(--border);">
                    {{ s|upper }}: {{ info.usage[s] }}/{{ l }}
                </span>
                {% endfor %}
            </div>
            <p style="font-size:11px; color:#777;">Expires: {{ info.expiry }}</p>
            <div class="action-btns" style="display:flex; gap:10px;">
                <form action="/del-key" method="POST" style="margin:0;">
                    <input type="hidden" name="key_id" value="{{ key }}">
                    <button type="submit" class="btn btn-danger" style="padding:5px 15px; font-size:11px;">REVOKE</button>
                </form>
            </div>
        </div>
        {% endfor %}
        <br><a href="/logout" style="color:var(--danger); text-decoration:none; font-size:13px;">→ SHUTDOWN SESSION</a>

    {% elif page == 'edit_api' %}
        <a href="/admin" class="btn btn-back">← BACK TO DASHBOARD</a>
        <div class="card">
            <h3>CONFIGURING: {{ slug|upper }}</h3>
            <form method="POST">
                <input type="text" name="param" value="{{ api.param }}" placeholder="Main Parameter" required>
                <p style="font-size:13px; color:var(--accent);">JSON Key Mapping:</p>
                <div id="param-fields">
                    {% for orig, rule in api['mapping'].items() %}
                    <div class="item" style="display:flex; gap:10px; align-items:center; margin-bottom:10px;">
                        <input type="text" name="orig_keys" value="{{ orig }}" placeholder="API Key" style="margin:0;">
                        <input type="text" name="new_vals" value="{{ rule.value }}" placeholder="Custom Text" style="margin:0;">
                        <button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">×</button>
                    </div>
                    {% endfor %}
                </div>
                <button type="button" class="btn btn-back" onclick="addRow()" style="width:100%;">+ ADD NEW RULE</button>
                <button type="submit" class="btn btn-primary" style="width:100%; margin-top:10px;">SAVE CONFIGURATION</button>
            </form>
        </div>
        <script>
            function addRow(){
                const div = document.createElement('div');
                div.className = 'item';
                div.style.cssText = 'display:flex; gap:10px; align-items:center; margin-bottom:10px;';
                div.innerHTML = `<input type="text" name="orig_keys" placeholder="API Key" style="margin:0;"><input type="text" name="new_vals" placeholder="Custom Text" style="margin:0;"><button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">×</button>`;
                document.getElementById('param-fields').appendChild(div);
            }
        </script>
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
        "mapping": {
            "status": {"value": "SUCCESS BY SAKIB", "hidden": False},
            "owner": {"value": "SB-SAKIB @sakib01994", "hidden": False}
        }
    }
    return redirect('/admin')

@app.route('/key-gen', methods=['POST'])
def key_gen():
    if not session.get('logged_in'): return redirect('/admin')
    key = request.form.get('c_key') or "SAKIB-" + os.urandom(3).hex().upper()
    
    allowed_list = request.form.getlist('allowed_apis')
    permissions = {}
    usage = {}
    
    for slug in allowed_list:
        limit_val = request.form.get(f'limit_{slug}', '100')
        permissions[slug] = int(limit_val)
        usage[slug] = 0

    DATABASE['keys'][key] = {
        "expiry": request.form.get('expiry'),
        "permissions": permissions, # {api_slug: limit}
        "usage": usage # {api_slug: used_count}
    }
    return redirect('/admin')

@app.route('/settings/<slug>', methods=['GET', 'POST'])
def settings(slug):
    if not session.get('logged_in'): return redirect('/admin')
    api = DATABASE['apis'].get(slug)
    if request.method == 'POST':
        api['param'] = request.form.get('param')
        keys = request.form.getlist('orig_keys')
        vals = request.form.getlist('new_vals')
        api['mapping'] = {k: {"value": v, "hidden": False} for k, v in zip(keys, vals) if k}
        return redirect('/admin')
    return render_template_string(HTML_LAYOUT, page='edit_api', api=api, slug=slug)

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
    k_data = DATABASE['keys'].get(key_code)

    if not k_data: return jsonify({"status": "error", "message": "Invalid Access Key", "contact": "@sakib01994"}), 403
    
    # চেক: এই এপিআই-তে এক্সেস আছে কি না
    if slug not in k_data['permissions']:
        return jsonify({"status": "error", "message": f"No permission for {slug}", "contact": "@sakib01994"}), 403

    # চেক: মেয়াদ্দ
    if datetime.now().date() > datetime.strptime(k_data['expiry'], "%Y-%m-%d").date():
        return jsonify({"status": "error", "message": "Key Expired", "contact": "@sakib01994"}), 403

    # চেক: স্পেসিফিক এপিআই লিমিট
    if k_data['usage'][slug] >= k_data['permissions'][slug]:
        return jsonify({"status": "LIMIT_EXCEEDED", "message": f"Limit for {slug} is over. Contact owner.", "contact": "@sakib01994"}), 403

    term = request.args.get(api['param'])
    if not term: return jsonify({"error": f"Missing param: {api['param']}"}), 400

    try:
        r = requests.get(api['url'], params={api['param']: term}, timeout=15)
        res_json = r.json()
        if not isinstance(res_json, dict): res_json = {"result": res_json}

        # ম্যাপিং প্রয়োগ
        for k_orig, rule in api['mapping'].items():
            res_json[k_orig] = rule['value']
        
        # ইউজেস আপডেট (শুধুমাত্র ওই এপিআই এর জন্য)
        k_data['usage'][slug] += 1
        return jsonify(res_json)
    except Exception as e:
        return jsonify({"error": "Origin Error", "details": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')

@app.route('/')
def home():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
