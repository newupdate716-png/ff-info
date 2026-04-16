import os
import requests
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta, datetime

app = Flask(__name__)

# সিকিউরিটি কনফিগারেশন
app.secret_key = os.getenv("SECRET_KEY", "SAKIB_ULTRA_PREMIUM_V4_CORE_FINAL")
app.permanent_session_lifetime = timedelta(days=30)

ADMIN_PASS = "sakib123"

# ডাটাবেস স্ট্রাকচার
DATABASE = {
    "apis": {},
    "keys": {}
}

# প্রিমিয়াম এনিমেটেড UI
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SB SAKIB | PREMIUM MANAGER V4</title>
    <style>
        :root{--accent:#00ffcc;--bg:#050508;--card:#0f0f1c;--danger:#ff4d4d;--edit:#ffcc00;--success:#2ecc71;--border:rgba(255,255,255,0.08);--hide:#7f8c8d;}
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes glow { 0% { box-shadow: 0 0 5px rgba(0,255,204,0.2); } 50% { box-shadow: 0 0 15px rgba(0,255,204,0.5); } 100% { box-shadow: 0 0 5px rgba(0,255,204,0.2); } }

        body{font-family:'Segoe UI', Roboto, sans-serif;background:var(--bg);color:#e0e0e0;margin:0;padding:0;overflow-x:hidden;}
        
        .nav{background:rgba(15, 15, 28, 0.9);padding:22px;text-align:center;border-bottom:1px solid var(--accent);color:var(--accent);font-size:26px;font-weight:900;letter-spacing:3px;backdrop-filter: blur(15px);position: sticky;top: 0;z-index: 1000;text-shadow: 0 0 10px rgba(0,255,204,0.5);}
        
        .container{max-width:900px;margin:auto;padding:30px;animation: fadeIn 0.8s ease;}
        .card{background:var(--card);border-radius:24px;padding:30px;margin-bottom:30px;border:1px solid var(--border);box-shadow: 0 15px 35px rgba(0,0,0,0.6);transition: 0.4s;position: relative;}
        .card:hover{border-color: var(--accent);}
        
        h3{margin-top:0;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:15px;text-transform: uppercase;font-size:18px;display: flex;justify-content: space-between;align-items: center;}
        
        input, select{width:100%;padding:15px;margin:12px 0;border-radius:12px;border:1px solid var(--border);background:rgba(0,0,0,0.4);color:#fff;box-sizing:border-box;outline:none;transition: 0.3s;}
        input:focus{border-color: var(--accent);background:rgba(0,0,0,0.6);}
        
        .btn{padding:12px 20px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;transition:0.3s;display:inline-flex;align-items:center;justify-content:center;text-decoration:none;font-size:13px;gap:8px;}
        .btn-primary{background:var(--accent);color:#000;animation: glow 3s infinite;}
        .btn-danger{background:var(--danger);color:#fff;}
        .btn-edit{background:var(--edit);color:#000;}
        .btn-hide{background:var(--hide);color:#fff;}
        .btn-back{background:rgba(255,255,255,0.05);color:#fff;margin-bottom:20px;border:1px solid var(--border);}
        
        .item{background:rgba(255,255,255,0.02);padding:20px;border-radius:18px;margin-top:15px;border:1px solid var(--border);transition: 0.3s;}
        .item:hover{background: rgba(255,255,255,0.05);}
        
        .perm-box{background:rgba(0,0,0,0.3);padding:15px;border-radius:15px;margin:10px 0;border:1px solid var(--border);}
        .perm-item{display: flex;align-items: center;justify-content: space-between;padding:10px 0;border-bottom: 1px solid rgba(255,255,255,0.05);}
        
        .hidden-row{opacity: 0.4; filter: grayscale(1);}
        code{color:var(--edit);background:#000;padding:12px;border-radius:12px;display:block;margin-top:10px;font-size:12px;border:1px solid var(--border);word-break: break-all;}
        .limit-input{width: 80px !important; padding: 8px !important; margin: 0 !important; text-align: center;}
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
            {% if error %}<p style="color:var(--danger);text-align:center;">Access Denied!</p>{% endif %}
        </div>

    {% elif page == 'dash' %}
        <div class="card">
            <h3>DEPLOY NEW API</h3>
            <form action="/add" method="POST">
                <input type="text" name="slug" placeholder="API Path (e.g. fb_dl)" required>
                <input type="url" name="url" placeholder="Original API URL" required>
                <input type="text" name="param" placeholder="Input Parameter (e.g. url)" required>
                <button type="submit" class="btn btn-primary" style="width:100%;">DEPLOY NOW</button>
            </form>
        </div>

        <div class="card">
            <h3>GENERATE MASTER KEY</h3>
            <form action="/key-gen" method="POST">
                <input type="text" name="c_key" placeholder="Custom Access Key (Optional)">
                <input type="date" name="expiry" required>
                <p style="font-size:13px; color:var(--accent);">API Access & Limits:</p>
                <div class="perm-box">
                    {% for slug in data['apis'].keys() %}
                    <div class="perm-item">
                        <label><input type="checkbox" name="allowed_apis" value="{{ slug }}" checked> {{ slug|upper }}</label>
                        <input type="number" name="limit_{{ slug }}" value="100" class="limit-input" placeholder="Limit">
                    </div>
                    {% endfor %}
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;">GENERATE KEY</button>
            </form>
        </div>

        <h3>SYSTEM ENDPOINTS</h3>
        {% for slug, api in data['apis'].items() %}
        <div class="item">
            <a href="/settings/{{ slug }}" class="btn btn-edit" style="float:right;">CONFIG</a>
            <strong>{{ slug|upper }}</strong>
            <code>{{ root }}{{ slug }}?key=[KEY]&{{ api.param }}=[VALUE]</code>
        </div>
        {% endfor %}

        <h3 style="margin-top:40px;">MANAGED KEYS</h3>
        {% for key, info in data['keys'].items() %}
        <div class="item">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <strong>KEY: {{ key }}</strong>
                    <div style="font-size:12px; margin-top:8px; color:#aaa;">
                        {% for s, l in info.permissions.items() %}
                        <span style="display:inline-block; background:rgba(255,255,255,0.05); padding:3px 8px; border-radius:5px; margin:2px;">
                            {{ s|upper }}: {{ info.usage[s] }}/{{ l }}
                        </span>
                        {% endfor %}
                    </div>
                </div>
                <div style="display:flex; gap:8px;">
                    <a href="/edit-key/{{ key }}" class="btn btn-edit">EDIT</a>
                    <form action="/del-key" method="POST" style="margin:0;">
                        <input type="hidden" name="key_id" value="{{ key }}">
                        <button type="submit" class="btn btn-danger">REVOKE</button>
                    </form>
                </div>
            </div>
            <p style="font-size:11px; color:#666;">Expires: {{ info.expiry }}</p>
        </div>
        {% endfor %}

    {% elif page == 'edit_api' %}
        <a href="/admin" class="btn btn-back">← BACK</a>
        <div class="card">
            <h3>EDITING: {{ slug|upper }}</h3>
            <form method="POST">
                <input type="text" name="param" value="{{ api.param }}" placeholder="Main Parameter" required>
                <div id="param-fields">
                    {% for orig, rule in api['mapping'].items() %}
                    <div class="item {% if rule.hidden %}hidden-row{% endif %}" style="display:flex; gap:10px; align-items:center; margin-bottom:10px; padding:10px;">
                        <input type="text" name="orig_keys" value="{{ orig }}" style="margin:0;">
                        <input type="text" name="new_vals" value="{{ rule.value }}" style="margin:0;">
                        <input type="hidden" name="hidden_states" value="{{ '1' if rule.hidden else '0' }}" class="h-state">
                        <button type="button" class="btn btn-hide" onclick="toggleHide(this)">{{ 'SHOW' if rule.hidden else 'HIDE' }}</button>
                        <button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">×</button>
                    </div>
                    {% endfor %}
                </div>
                <button type="button" class="btn btn-back" onclick="addRow()" style="width:100%;">+ ADD RULE</button>
                <button type="submit" class="btn btn-primary" style="width:100%; margin-top:10px;">SAVE SETTINGS</button>
            </form>
        </div>
        <script>
            function addRow(){
                const div = document.createElement('div');
                div.className = 'item';
                div.style.cssText = 'display:flex; gap:10px; align-items:center; margin-bottom:10px; padding:10px;';
                div.innerHTML = `<input type="text" name="orig_keys" placeholder="Key" style="margin:0;"><input type="text" name="new_vals" placeholder="Value" style="margin:0;"><input type="hidden" name="hidden_states" value="0" class="h-state"><button type="button" class="btn btn-hide" onclick="toggleHide(this)">HIDE</button><button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">×</button>`;
                document.getElementById('param-fields').appendChild(div);
            }
            function toggleHide(btn){
                const row = btn.parentElement;
                const hState = row.querySelector('.h-state');
                if(hState.value === '0'){ hState.value = '1'; row.classList.add('hidden-row'); btn.innerText = 'SHOW'; }
                else { hState.value = '0'; row.classList.remove('hidden-row'); btn.innerText = 'HIDE'; }
            }
        </script>

    {% elif page == 'edit_key' %}
        <a href="/admin" class="btn btn-back">← BACK</a>
        <div class="card">
            <h3>EDIT KEY: {{ key_id }}</h3>
            <form method="POST">
                <input type="date" name="expiry" value="{{ key_info.expiry }}" required>
                <div class="perm-box">
                    {% for slug in data['apis'].keys() %}
                    <div class="perm-item">
                        <label><input type="checkbox" name="allowed_apis" value="{{ slug }}" {% if slug in key_info.permissions %}checked{% endif %}> {{ slug|upper }}</label>
                        <input type="number" name="limit_{{ slug }}" value="{{ key_info.permissions.get(slug, 100) }}" class="limit-input">
                    </div>
                    {% endfor %}
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;">UPDATE KEY</button>
            </form>
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
            session['logged_in'] = True
            return redirect('/admin')
    if session.get('logged_in'):
        return render_template_string(HTML_LAYOUT, page='dash', data=DATABASE, root=request.url_root)
    return render_template_string(HTML_LAYOUT, page='login')

@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'): return redirect('/admin')
    slug = request.form.get('slug').strip().lower()
    DATABASE['apis'][slug] = {"url": request.form.get('url'), "param": request.form.get('param'), "mapping": {}}
    return redirect('/admin')

@app.route('/key-gen', methods=['POST'])
def key_gen():
    if not session.get('logged_in'): return redirect('/admin')
    key = request.form.get('c_key') or "SAKIB-" + os.urandom(3).hex().upper()
    allowed = request.form.getlist('allowed_apis')
    permissions = {s: int(request.form.get(f'limit_{s}', 100)) for s in allowed}
    DATABASE['keys'][key] = {"expiry": request.form.get('expiry'), "permissions": permissions, "usage": {s: 0 for s in allowed}}
    return redirect('/admin')

@app.route('/edit-key/<key_id>', methods=['GET', 'POST'])
def edit_key(key_id):
    if not session.get('logged_in'): return redirect('/admin')
    k_info = DATABASE['keys'].get(key_id)
    if request.method == 'POST':
        allowed = request.form.getlist('allowed_apis')
        k_info['expiry'] = request.form.get('expiry')
        k_info['permissions'] = {s: int(request.form.get(f'limit_{s}', 100)) for s in allowed}
        for s in allowed:
            if s not in k_info['usage']: k_info['usage'][s] = 0
        return redirect('/admin')
    return render_template_string(HTML_LAYOUT, page='edit_key', key_id=key_id, key_info=k_info, data=DATABASE)

@app.route('/settings/<slug>', methods=['GET', 'POST'])
def settings(slug):
    if not session.get('logged_in'): return redirect('/admin')
    api = DATABASE['apis'].get(slug)
    if request.method == 'POST':
        api['param'] = request.form.get('param')
        keys, vals, hiddens = request.form.getlist('orig_keys'), request.form.getlist('new_vals'), request.form.getlist('hidden_states')
        api['mapping'] = {k: {"value": v, "hidden": h == '1'} for k, v, h in zip(keys, vals, hiddens) if k}
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
    if not api: return jsonify({"error": "API Not Found"}), 404
    k_code = request.args.get('key')
    k_data = DATABASE['keys'].get(k_code)
    if not k_data or slug not in k_data['permissions']:
        return jsonify({"status": "error", "message": "Access Denied"}), 403
    if datetime.now().date() > datetime.strptime(k_data['expiry'], "%Y-%m-%d").date():
        return jsonify({"status": "error", "message": "Key Expired"}), 403
    if k_data['usage'][slug] >= k_data['permissions'][slug]:
        return jsonify({"status": "error", "message": "Limit Reached"}), 403
    
    term = request.args.get(api['param'])
    try:
        r = requests.get(api['url'], params={api['param']: term}, timeout=10)
        res = r.json()
        if not isinstance(res, dict): res = {"result": res}
        for k_orig, rule in api['mapping'].items():
            if rule['hidden']:
                if k_orig in res: res.pop(k_orig)
            else: res[k_orig] = rule['value']
        k_data['usage'][slug] += 1
        return jsonify(res)
    except: return jsonify({"error": "Origin Error"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')

@app.route('/')
def home():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
