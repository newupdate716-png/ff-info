import os
import json
import requests
import time
import uuid
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = "SB_SAKIB_PREMIUM_SECRET" # আপনার সিক্রেট কী

# অ্যাডমিন পাসওয়ার্ড (সিকিউরিটির জন্য এটি পরিবর্তন করুন)
ADMIN_PASSWORD = "YOUR_SECURE_PASSWORD" 

# ডাটাবেস ফাইল
DB_FILE = 'db.json'

def load_db():
    if not os.path.exists(DB_FILE):
        return {"apis": {}, "keys": {}}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# লগইন ডেকোরেটর
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return "API System is Running!"

# --- অ্যাডমিন প্যানেল ---

@app.route('/admin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    db = load_db()
    return render_template('dashboard.html', apis=db['apis'], keys=db['keys'])

@app.route('/add_api', methods=['POST'])
@login_required
def add_api():
    db = load_db()
    api_id = str(uuid.uuid4())[:8]
    db['apis'][api_id] = {
        "type": request.form.get('type'),
        "main_url": request.form.get('main_url'),
        "custom_params": {} # { "owner": "Sakib", "status": "Active" }
    }
    save_db(db)
    return redirect(url_for('dashboard'))

@app.route('/generate_key', methods=['POST'])
@login_required
def generate_key():
    db = load_db()
    new_key = "KEY-" + str(uuid.uuid4())[:12].upper()
    db['keys'][new_key] = {
        "limit": int(request.form.get('limit')),
        "expiry": request.form.get('expiry'), # YYYY-MM-DD
        "used": 0
    }
    save_db(db)
    return redirect(url_for('dashboard'))

# --- মেইন এপিআই গেটওয়ে ---

@app.route('/api/<api_id>')
def proxy_api(api_id):
    db = load_db()
    api_info = db['apis'].get(api_id)
    user_key = request.args.get('key')

    if not api_info:
        return jsonify({"error": "API not found"}), 404

    # এপিআই কী চেক
    key_data = db['keys'].get(user_key)
    if not key_data:
        return jsonify({"error": "Invalid API Key"}), 403
    
    # লিমিট ও এক্সপায়ারি চেক
    current_date = time.strftime("%Y-%m-%d")
    if key_data['used'] >= key_data['limit'] or key_data['expiry'] < current_date:
        return jsonify({"error": "Key expired or limit reached"}), 403

    # মেইন এপিআই থেকে ডাটা আনা
    main_res = requests.get(api_info['main_url'], params=request.args).json()
    
    # ডাটা মডিফিকেশন (আপনার রিকোয়েস্ট অনুযায়ী প্যারামিটার চেঞ্জ)
    for p_key, p_val in api_info['custom_params'].items():
        if p_key in main_res:
            main_res[p_key] = p_val
            
    # লিমিট আপডেট
    db['keys'][user_key]['used'] += 1
    save_db(db)

    return jsonify(main_res)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
