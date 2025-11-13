from flask import Flask, render_template, jsonify, g
import log_manager # Import our log manager
import json
import sqlite3

app = Flask(__name__)
# This makes sure that responses are not cached
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# --- Database Helper ---
# We use this to get the DB connection in the context of a web request
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = log_manager.get_db_conn() # Use our manager's function
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Main Dashboard Route ---
@app.route('/')
def dashboard():
    """Main dashboard page."""
    print("Fetching logs for dashboard...")
    raw_logs = log_manager.get_all_logs()
    
    processed_logs = []
    for log in raw_logs:
        log_dict = dict(log) 
        
        # Parse the JSON string from the DB back into a Python list
        try:
            log_dict['violations'] = json.loads(log_dict['violations'])
        except (TypeError, json.JSONDecodeError):
            log_dict['violations'] = [] # Set to empty list on error
            
        # Format timestamp to be more readable
        try:
            # Parse from ISO format and make it friendlier
            log_dict['timestamp'] = log_dict['timestamp'].split('.')[0].replace('T', ' ')
        except Exception:
            pass # Ignore timestamp formatting errors

        processed_logs.append(log_dict)

    print(f"Found {len(processed_logs)} logs to display.")
    
    # 'render_template' will look for 'index.html' in a folder named 'templates'
    return render_template('index.html', logs=processed_logs)

# --- API Endpoint for Interaction ---
@app.route('/review/<int:log_id>', methods=['POST'])
def review_log(log_id):
    """API endpoint to mark a log as reviewed."""
    print(f"Received request to mark log ID {log_id} as reviewed.")
    
    success = log_manager.mark_as_reviewed(log_id)
    
    if success:
        return jsonify({'status': 'success', 'message': f'Log {log_id} marked as reviewed.'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to update database.'}), 500

# --- Run the App ---
if __name__ == '__main__':
    print("Starting SafeWatch Dashboard...")
    print("Open http://127.0.0.1:5000 in your browser.")
    # debug=True automatically reloads the server when you save this file
    app.run(debug=True, port=5000)