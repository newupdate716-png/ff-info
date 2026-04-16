import os
import requests
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import timedelta, datetime

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "SAKIB_ULTIMATE_SECURE_FIX_100")
app.permanent_session_lifetime = timedelta(days=30)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

ADMIN_PASS = "sakib123"

DATABASE = {
    "apis": {},
    "keys": {}
}

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SB SAKIB | API MANAGER</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root{--accent:#00ffcc;--bg:#0a0a0f;--card:#15151b;--danger:#ff4d4d;}
body{font-family:sans-serif;background:var(--bg);color:#e0e0e0;margin:0;padding:0;}
.nav{background:#1a1a24;padding:20px;text-align:center;border-bottom:2px solid var(--accent);color:var(--accent);font-size:20px;font-weight:bold;}
.container{max-width:650px;margin:auto;padding:20px;}
.card{background:var(--card);border-radius:12px;padding:20px;margin-bottom:20px;border:1px solid #252530;}
input{width:100%;padding:12px;margin:10px 0;border-radius:8px;border:1px solid #333;background:#000;color:#fff;box-sizing:border-box;}
button{width:100%;padding:12px;background:var(--accent);border:none;border-radius:8px;font-weight:bold;cursor:pointer;color:#000;}
.item{background:#1f1f29;padding:15px;border-radius:10px;margin-top:15px;border-left:4px solid var(--accent);}
.btn-edit{background:#ffcc00;color:#000;padding:5px 10px;border-radius:4px;text-decoration:none;font-size:12px;float:right;}
.btn-del{background:var(--danger);color:#fff;padding:5px 10px;border-radius:4px;border:none;font-size:12px;float:right;margin-left:10px;cursor:pointer;}
code{color:#ffcc00;background:#000;padding:2px 6px;border-radius:4px;word-break:break-all;font-size:12px;}
</style>
</head>
<body>
<div class="nav">SB SAKIB PREMIUM PANEL</div>
<div class="container">

{% if page == 'login' %}
<div class="card" style="max-width:350px;margin:50px auto;">
<h3 style="text-align:center;">ADMIN LOGIN</h3>
<form method="POST" action="/admin">
<input type="password" name="password" placeholder="Admin Password" required>
<button type="submit">LOGIN</button>
</form>
{% if error %}<p style="color:red;text-align:center;">Wrong Password!</p>{% endif %}
</div>

{% elif page == 'dash' %}
<div class="card">
<h3>ADD API</h3>
<form action="/add" method="POST">
<input type="text" name="slug" placeholder="API SLUG (e.g ff-info)" required>
<input type="text" name="type" placeholder="API Type" required>
<input type="text" name="url" placeholder="Main URL" required>
<input type="text" name="param" placeholder="Forward Param Name (e.g uid/phone/number)" required>
<button type="submit">DEPLOY</button>
</form>
</div>

<div class="card">
<h3>CREATE KEY</h3>
<form action="/key" method="POST">
<input type="text" name="c_key" placeholder="Custom Key">
<input type="number" name="limit" placeholder="Limit" required>
<input type="date" name="expiry" required>
<button style="background:#ffcc00;">GENERATE</button>
</form>
</div>

<h3>ACTIVE APIS</h3>
{% for slug, api in data['apis'].items() %}
<div class="item">
<a href="/settings/{{ slug }}" class="btn-edit">SETTINGS</a>
<b>{{ api.type }}</b><br><br>
<code>{{ root }}{{ slug }}?key=[KEY]&{{ api.param }}=[VALUE]</code>
</div>
{% endfor %}

<h3>ACTIVE KEYS</h3>
{% for key, info in data['keys'].items() %}
<div class="item" style="border-left-color:#ffcc00;">
<form action="/del-key" method="POST" style="display:inline;">
<input type="hidden" name="key_id" value="{{ key }}">
<button class="btn-del">DELETE</button>
</form>
<b>Key:</b> <code>{{ key }}</code><br>
<small>{{ info.used }}/{{ info.limit }} | Exp: {{ info.expiry }}</small>
</div>
{% endfor %}

<p style="text-align:center;"><a href="/logout" style="color:red;">Logout</a></p>

{% elif page == 'edit' %}
<div class="card">
<h3>EDIT API SETTINGS</h3>
<form method="POST">
<input type="text" name="p_key" value="{{ api.params.key }}" required>
<input type="text" name="p_val" value="{{ api.params.val }}" required>
<input type="text" name="param" value="{{ api.param }}" required>
<button>SAVE</button>
</form>
</div>
{% endif %}

</div>
</body>
</html>
"""

@app.route('/admin', methods=['GET','POST'])
def admin():
    error=False
    if request.method=='POST':
        if request.form.get('password')==ADMIN_PASS:
            session['logged_in']=True
            session.permanent=True
            return redirect('/admin')
        error=True

    if session.get('logged_in'):
        return render_template_string(HTML_LAYOUT,page='dash',data=DATABASE,root=request.url_root)

    return render_template_string(HTML_LAYOUT,page='login',error=error)


@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'):
        return redirect('/admin')

    slug=request.form.get('slug').strip().lower()
    DATABASE['apis'][slug]={
        "type":request.form.get('type'),
        "url":request.form.get('url'),
        "param":request.form.get('param'),
        "params":{
            "key":"owner",
            "val":"SB-SAKIB @sakib01994"
        }
    }

    return redirect('/admin')


@app.route('/settings/<slug>', methods=['GET','POST'])
def settings(slug):
    if not session.get('logged_in'):
        return redirect('/admin')

    api=DATABASE['apis'].get(slug)
    if not api:
        return "API Not Found",404

    if request.method=='POST':
        api['params']['key']=request.form.get('p_key')
        api['params']['val']=request.form.get('p_val')
        api['param']=request.form.get('param')
        return redirect('/admin')

    return render_template_string(HTML_LAYOUT,page='edit',api=api)


@app.route('/key', methods=['POST'])
def key_gen():
    if not session.get('logged_in'):
        return redirect('/admin')

    key=request.form.get('c_key') or "SAKIB-"+os.urandom(4).hex().upper()

    DATABASE['keys'][key]={
        "limit":int(request.form.get('limit')),
        "expiry":request.form.get('expiry'),
        "used":0
    }

    return redirect('/admin')


@app.route('/del-key', methods=['POST'])
def del_key():
    if not session.get('logged_in'):
        return redirect('/admin')

    DATABASE['keys'].pop(request.form.get('key_id'),None)
    return redirect('/admin')


@app.route('/<slug>')
def dynamic_api(slug):
    api=DATABASE['apis'].get(slug)
    if not api:
        return jsonify({"error":"API Not Found"}),404

    key=request.args.get('key')
    if not key:
        return jsonify({"error":"Key Required"}),401

    k=DATABASE['keys'].get(key)
    if not k:
        return jsonify({"error":"Invalid Key"}),403

    if datetime.now().date()>datetime.strptime(k['expiry'],"%Y-%m-%d").date():
        return jsonify({"error":"Key Expired"}),403

    if k['used']>=k['limit']:
        return jsonify({"error":"Limit Exceeded"}),403

    term=request.args.get(api['param'])
    if not term:
        return jsonify({"error":f"{api['param']} Required"}),400

    try:
        r=requests.get(
            api['url'],
            params={api['param']:term},
            timeout=15
        )

        data=r.json()

        if not isinstance(data,dict):
            data={"response":data}

        data[api['params']['key']]=api['params']['val']
        data['status']="SUCCESS BY SAKIB"

        k['used']+=1

        return jsonify(data)

    except Exception as e:
        return jsonify({"error":"Main API Error","details":str(e)}),500


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')


@app.route('/')
def home():
    return redirect('/admin')


app = app