import sqlite3
import json
import datetime
from flask import Flask, render_template, g, jsonify, request, session, redirect, url_for
from functools import wraps

# Import functions from log_manager
try:
    from log_manager import get_all_logs, mark_as_reviewed, DB_FILE
except ImportError:
    print("ERROR: Could not import dashboard functions from log_manager.")
    get_all_logs = None
    mark_as_reviewed = None
    DB_FILE = "safewatch_db.sqlite" 

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# *** SECURITY CONFIGURATION ***
app.secret_key = 'qwertyui' 
ADMIN_PASSCODE = 'qwertyui' 

# --- Login Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Database Helper ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['passcode'] == ADMIN_PASSCODE:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Passcode. Please try again.'
    return render_template('login.html', error=error)

# --- NEW: Logout Route ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Remove the session key
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('index.html')

# --- API Routes ---
@app.route('/api/logs')
@login_required 
def api_get_logs():
    if not get_all_logs:
        return jsonify({"error": "Log manager not imported"}), 500

    db_logs = get_all_logs() 
    processed_logs = []
    for log in db_logs:
        log_dict = dict(log)
        try:
            log_dict['violations'] = json.loads(log_dict['violations'])
        except (TypeError, json.JSONDecodeError):
            log_dict['violations'] = [] 
        try:
            dt = datetime.datetime.fromisoformat(log_dict['timestamp'])
            log_dict['timestamp'] = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
             pass 
        processed_logs.append(log_dict)
    return jsonify(processed_logs)

@app.route('/api/review/<int:log_id>', methods=['POST'])
@login_required
def api_review_log(log_id):
    if not mark_as_reviewed:
        return jsonify({"error": "Log manager not imported"}), 500
    success = mark_as_reviewed(log_id)
    if success:
        return jsonify({"success": True, "message": f"Log {log_id} marked as reviewed."})
    else:
        return jsonify({"success": False, "message": "Failed to update log in database."}), 500

if __name__ == '__main__':
    print("Starting SafeWatch Dashboard...")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, port=5000)