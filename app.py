import os
import requests
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta, datetime

app = Flask(__name__)

# সিকিউরিটি কনফিগারেশন
app.secret_key = os.getenv("SECRET_KEY", "SAKIB_ULTIMATE_PREMIUM_FINAL_ULTRA")
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
    <title>SB SAKIB | PREMIUM MANAGER</title>
    <style>
        :root{--accent:#00ffcc;--bg:#050508;--card:#0f0f18;--danger:#ff4d4d;--edit:#ffcc00;--success:#2ecc71;--hide:#7f8c8d;}
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideIn { from { transform: translateX(-20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

        body{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;background:var(--bg);color:#e0e0e0;margin:0;padding:0;overflow-x:hidden;}
        .nav{background:rgba(22, 22, 34, 0.95);padding:20px;text-align:center;border-bottom:2px solid var(--accent);color:var(--accent);font-size:24px;font-weight:bold;letter-spacing:2px;box-shadow: 0 4px 20px rgba(0,255,204,0.1);backdrop-filter: blur(10px);position: sticky;top: 0;z-index: 1000;}
        
        .container{max-width:850px;margin:auto;padding:25px;animation: fadeIn 0.6s ease-out;}
        .card{background:var(--card);border-radius:20px;padding:30px;margin-bottom:25px;border:1px solid #1f1f2e;box-shadow: 0 10px 30px rgba(0,0,0,0.5);transition: 0.3s;}
        .card:hover{border-color: var(--accent);box-shadow: 0 10px 40px rgba(0,255,204,0.05);}
        
        h3{margin-top:0;color:var(--accent);border-bottom:1px solid #222;padding-bottom:12px;display: flex;justify-content: space-between;align-items: center;}
        
        input, select{width:100%;padding:14px;margin:12px 0;border-radius:10px;border:1px solid #2a2a3d;background:#000;color:#fff;box-sizing:border-box;outline:none;transition: 0.3s;}
        input:focus{border-color: var(--accent);box-shadow: 0 0 10px rgba(0,255,204,0.2);}
        
        .btn{padding:12px 20px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;transition:0.3s;display:inline-flex;align-items:center;justify-content:center;text-decoration:none;font-size:14px;}
        .btn-primary{background:var(--accent);color:#000;}
        .btn-danger{background:var(--danger);color:#fff;}
        .btn-edit{background:var(--edit);color:#000;}
        .btn-hide{background:var(--hide);color:#fff;}
        .btn-back{background:#333;color:#fff;margin-bottom:15px;}
        .btn:hover{transform: scale(1.02);opacity: 0.9;}
        .btn:active{transform: scale(0.98);}

        .item{background:#161625;padding:18px;border-radius:15px;margin-top:15px;border-left:5px solid var(--accent);animation: slideIn 0.4s ease-out;position:relative;transition: 0.3s;}
        .item:hover{background: #1c1c2e;}
        
        .param-row{display:flex;gap:10px;margin-bottom:12px;align-items:center;background:rgba(0,0,0,0.3);padding:12px;border-radius:12px;border:1px solid #222;}
        .action-group{display: flex;gap: 8px;}
        
        .badge{font-size:11px;padding:4px 10px;border-radius:8px;background:#000;color:var(--accent);border: 1px solid var(--accent);text-transform: uppercase;}
        code{color:var(--edit);background:#000;padding:8px;border-radius:8px;display:block;margin-top:12px;font-size:12px;border:1px solid #222;word-break: break-all;}
        
        .hidden-row{opacity: 0.5;filter: grayscale(1);}
    </style>
</head>
<body>
    <div class="nav">SB SAKIB PREMIUM V3</div>
    <div class="container">

    {% if page == 'login' %}
        <div class="card" style="max-width:400px;margin:100px auto;">
            <h3>ADMIN LOGIN</h3>
            <form method="POST">
                <input type="password" name="password" placeholder="Enter Admin Password" required>
                <button type="submit" class="btn btn-primary" style="width:100%;">ACCESS SYSTEM</button>
            </form>
            {% if error %}<p style="color:var(--danger);text-align:center;margin-top:15px;">Invalid Password!</p>{% endif %}
        </div>

    {% elif page == 'dash' %}
        <div class="card">
            <h3>ADD NEW API</h3>
            <form action="/add" method="POST">
                <input type="text" name="slug" placeholder="API Path (e.g. facebook)" required>
                <input type="url" name="url" placeholder="Main API URL (https://...)" required>
                <input type="text" name="param" placeholder="Input Parameter (e.g. url)" required>
                <button type="submit" class="btn btn-primary" style="width:100%;">DEPLOY API</button>
            </form>
        </div>

        <div class="card">
            <h3>GENERATE KEY</h3>
            <form action="/key-gen" method="POST">
                <input type="text" name="c_key" placeholder="Custom Key (Optional)">
                <input type="number" name="limit" placeholder="Usage Limit" required>
                <input type="date" name="expiry" required>
                <button type="submit" class="btn btn-primary" style="width:100%;">CREATE KEY</button>
            </form>
        </div>

        <h3>ACTIVE APIS</h3>
        {% for slug, api in data['apis'].items() %}
        <div class="item">
            <a href="/settings/{{ slug }}" class="btn btn-edit" style="float:right;">SETTINGS</a>
            <strong>{{ slug|upper }}</strong> <span class="badge">Active</span>
            <code>{{ root }}{{ slug }}?key=[KEY]&{{ api.param }}=[VALUE]</code>
        </div>
        {% endfor %}

        <h3 style="margin-top:40px;">ACTIVE KEYS</h3>
        {% for key, info in data['keys'].items() %}
        <div class="item">
            <strong>Key: {{ key }}</strong>
            <div style="font-size:13px;margin-top:8px;color:#aaa;">
                Usage: {{ info.used }}/{{ info.limit }} | Exp: {{ info.expiry }}
            </div>
            <div class="action-btns" style="margin-top:12px; display:flex; gap:10px;">
                <a href="/edit-key/{{ key }}" class="btn btn-edit" style="padding:5px 15px;">EDIT</a>
                <form action="/del-key" method="POST" style="margin:0;">
                    <input type="hidden" name="key_id" value="{{ key }}">
                    <button type="submit" class="btn btn-danger" style="padding:5px 15px;">DELETE</button>
                </form>
            </div>
        </div>
        {% endfor %}
        <br><a href="/logout" style="color:var(--danger);font-weight:bold;text-decoration:none;">Logout Panel</a>

    {% elif page == 'edit_api' %}
        <a href="/admin" class="btn btn-back">← BACK TO DASHBOARD</a>
        <div class="card">
            <h3>
                EDIT API: {{ slug }}
                <a href="/reset-api/{{ slug }}" class="btn btn-danger" style="font-size:12px;padding:5px 10px;">RESET TO DEFAULT</a>
            </h3>
            <form method="POST">
                <p>Main Input Parameter:</p>
                <input type="text" name="param" value="{{ api.param }}" required>
                
                <p>Response Mapping & Rules:</p>
                <div id="param-fields">
                    {% for orig, rule in api['mapping'].items() %}
                    <div class="param-row {% if rule.hidden %}hidden-row{% endif %}" id="row-{{ loop.index }}">
                        <input type="text" name="orig_keys" value="{{ orig }}" placeholder="Original Key" style="flex:1;">
                        <input type="text" name="new_vals" value="{{ rule.value }}" placeholder="Replacement Text" style="flex:1;">
                        <input type="hidden" name="hidden_states" value="{{ '1' if rule.hidden else '0' }}" class="h-state">
                        
                        <div class="action-group">
                            <button type="button" class="btn btn-hide" onclick="toggleHide(this)">{{ 'SHOW' if rule.hidden else 'HIDE' }}</button>
                            <button type="button" class="btn btn-danger" onclick="this.parentElement.parentElement.remove()">×</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <button type="button" class="btn btn-primary" onclick="addRow()" style="margin-bottom:15px; background:#222; color:var(--accent);">+ ADD NEW MAPPING</button>
                <button type="submit" class="btn btn-primary" style="width:100%;">SAVE ALL CHANGES</button>
            </form>
        </div>
        <script>
            function addRow(){
                const div = document.createElement('div');
                div.className = 'param-row';
                div.innerHTML = `
                    <input type="text" name="orig_keys" placeholder="Original Key" style="flex:1;">
                    <input type="text" name="new_vals" placeholder="Replacement Text" style="flex:1;">
                    <input type="hidden" name="hidden_states" value="0" class="h-state">
                    <div class="action-group">
                        <button type="button" class="btn btn-hide" onclick="toggleHide(this)">HIDE</button>
                        <button type="button" class="btn btn-danger" onclick="this.parentElement.parentElement.remove()">×</button>
                    </div>`;
                document.getElementById('param-fields').appendChild(div);
            }
            function toggleHide(btn){
                const row = btn.parentElement.parentElement;
                const hState = row.querySelector('.h-state');
                if(hState.value === '0'){
                    hState.value = '1';
                    row.classList.add('hidden-row');
                    btn.innerText = 'SHOW';
                } else {
                    hState.value = '0';
                    row.classList.remove('hidden-row');
                    btn.innerText = 'HIDE';
                }
            }
        </script>

    {% elif page == 'edit_key' %}
        <a href="/admin" class="btn btn-back">← BACK TO DASHBOARD</a>
        <div class="card">
            <h3>EDIT KEY: {{ key_id }}</h3>
            <form method="POST">
                <p>Usage Limit:</p>
                <input type="number" name="limit" value="{{ key_info.limit }}">
                <p>Expiry Date:</p>
                <input type="date" name="expiry" value="{{ key_info.expiry }}">
                <button type="submit" class="btn btn-primary" style="width:100%;">UPDATE ACCESS KEY</button>
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
        "mapping": {
            "status": {"value": "SUCCESS BY SAKIB", "hidden": False},
            "owner": {"value": "SB-SAKIB @sakib01994", "hidden": False}
        }
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
        hiddens = request.form.getlist('hidden_states')
        
        new_mapping = {}
        for k, v, h in zip(keys, vals, hiddens):
            if k:
                new_mapping[k] = {"value": v, "hidden": h == '1'}
        api['mapping'] = new_mapping
        return redirect('/admin')
    return render_template_string(HTML_LAYOUT, page='edit_api', api=api, slug=slug)

@app.route('/reset-api/<slug>')
def reset_api(slug):
    if not session.get('logged_in'): return redirect('/admin')
    if slug in DATABASE['apis']:
        DATABASE['apis'][slug]['mapping'] = {
            "status": {"value": "SUCCESS BY SAKIB", "hidden": False},
            "owner": {"value": "SB-SAKIB @sakib01994", "hidden": False}
        }
    return redirect(url_for('settings', slug=slug))

@app.route('/key-gen', methods=['POST'])
def key_gen():
    if not session.get('logged_in'): return redirect('/admin')
    key = request.form.get('c_key') or "SAKIB-" + os.urandom(3).hex().upper()
    DATABASE['keys'][key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'),
        "used": 0,
        "allowed": list(DATABASE['apis'].keys())
    }
    return redirect('/admin')

@app.route('/edit-key/<key_id>', methods=['GET', 'POST'])
def edit_key(key_id):
    if not session.get('logged_in'): return redirect('/admin')
    key_info = DATABASE['keys'].get(key_id)
    if request.method == 'POST':
        key_info['limit'] = int(request.form.get('limit'))
        key_info['expiry'] = request.form.get('expiry')
        return redirect('/admin')
    return render_template_string(HTML_LAYOUT, page='edit_key', key_id=key_id, key_info=key_info)

@app.route('/del-key', methods=['POST'])
def del_key():
    if not session.get('logged_in'): return redirect('/admin')
    DATABASE['keys'].pop(request.form.get('key_id'), None)
    return redirect('/admin')

@app.route('/<slug>')
def dynamic_api(slug):
    api = DATABASE['apis'].get(slug)
    if not api: return jsonify({"error": "API NotFound"}), 404

    key_code = request.args.get('key')
    k = DATABASE['keys'].get(key_code)

    if not k: return jsonify({"status": "error", "message": "Access Key Required", "contact": "@sakib01994"}), 403
    
    if datetime.now().date() > datetime.strptime(k['expiry'], "%Y-%m-%d").date():
        return jsonify({"status": "error", "message": "Key Expired", "contact": "@sakib01994"}), 403

    if k['used'] >= k['limit']:
        return jsonify({"status": "LIMIT_EXCEEDED", "message": "Your limit is over. Contact owner.", "contact": "@sakib01994"}), 403

    term = request.args.get(api['param'])
    if not term: return jsonify({"error": f"Missing {api['param']}"}), 400

    try:
        r = requests.get(api['url'], params={api['param']: term}, timeout=15)
        raw_data = r.json()
        if not isinstance(raw_data, dict): raw_data = {"data": raw_data}

        # ম্যাপিং প্রসেসিং
        for k_orig, rule in api['mapping'].items():
            if rule['hidden']:
                if k_orig in raw_data: raw_data.pop(k_orig)
            else:
                raw_data[k_orig] = rule['value']
        
        k['used'] += 1
        return jsonify(raw_data)
    except Exception as e:
        return jsonify({"error": "Origin API Error", "msg": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')

@app.route('/')
def home():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
