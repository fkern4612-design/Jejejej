from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta
from pathlib import Path
import json

app = Flask(__name__)
app.secret_key = 'daily_routine_secret_key_2025'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

USERS = {
    'Husband': 'DailyRoutine',
    'Wife': 'DailyRoutine',
    'Admin': 'AdminMaster2025'
}

ADMIN_USERS = ['Admin']

PARTNER = {
    'Husband': 'Wife',
    'Wife': 'Husband'
}

def get_feelings_file(username):
    return DATA_DIR / f'{username}_feelings.json'

def load_feelings_history(username):
    feelings_file = get_feelings_file(username)
    if feelings_file.exists():
        with open(feelings_file, 'r') as f:
            return json.load(f)
    return []

def save_feeling(username, feeling, notes=''):
    history = load_feelings_history(username)
    history.append({
        'emoji': feeling,
        'notes': notes,
        'timestamp': datetime.now().isoformat(),
        'date': date.today().isoformat()
    })
    with open(get_feelings_file(username), 'w') as f:
        json.dump(history, f, indent=2)
    return history

def get_today_feelings(username):
    history = load_feelings_history(username)
    today = date.today().isoformat()
    return [f for f in history if f.get('date') == today]

ROUTINE_FILE = Path.home() / '.daily_routine' / 'default_routine.json'

def get_default_routine():
    if ROUTINE_FILE.exists():
        with open(ROUTINE_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_ROUTINE

def save_default_routine(routine):
    with open(ROUTINE_FILE, 'w') as f:
        json.dump(routine, f, indent=2)

DATA_DIR = Path.home() / '.daily_routine'
DATA_DIR.mkdir(exist_ok=True)

# Partnership data file
PARTNERSHIP_FILE = DATA_DIR / 'partnership.json'
DEFAULT_PARTNERSHIP = {
    'together_since': '2020-01-15',
    'location': 'Berlin, Germany',
    'couple_name': 'Us',
    'goals': [
        'Build a stronger relationship',
        'Maintain healthy routines',
        'Support each other emotionally',
        'Create beautiful memories together'
    ],
    'notes': 'Welcome to your couple routine tracker! Track activities together and strengthen your bond.',
    'anniversaries': [
        {'date': '2020-01-15', 'name': 'Together Anniversary'},
        {'date': '2024-06-15', 'name': 'Last Special Date'}
    ]
}

DEFAULT_ROUTINE = {
    'Morning': [
        {'name': 'Alarm at 9 AM', 'emoji': '⏰', 'time': '09:00', 'completed': False},
        {'name': 'Get up immediately (no snooze)', 'emoji': '🛏️', 'time': '09:05', 'completed': False},
        {'name': 'Brush teeth', 'emoji': '🪥', 'time': '09:10', 'completed': False},
        {'name': 'Wash face', 'emoji': '🧼', 'time': '09:15', 'completed': False},
        {'name': 'Drink water', 'emoji': '💧', 'time': '09:20', 'completed': False},
        {'name': 'Breakfast together', 'emoji': '🍽️', 'time': '09:30', 'completed': False},
        {'name': 'Discuss daily goals', 'emoji': '💬', 'time': '10:00', 'completed': False},
    ],
    'Daily': [
        {'name': 'Breakfast', 'emoji': '🥞', 'time': '09:30', 'completed': False},
        {'name': 'Drink plenty of water', 'emoji': '💧', 'time': '12:00', 'completed': False},
        {'name': 'Lunch', 'emoji': '🥗', 'time': '12:30', 'completed': False},
        {'name': 'At least one walk per day', 'emoji': '🚶', 'time': '15:00', 'completed': False},
        {'name': 'Get daylight (good for mental health)', 'emoji': '☀️', 'time': '15:30', 'completed': False},
        {'name': 'Plan 1 activity per day', 'emoji': '📋', 'time': '14:00', 'completed': False},
        {'name': 'Don\'t delay household tasks', 'emoji': '🏠', 'time': '16:00', 'completed': False},
        {'name': 'Tidy up 15-20 minutes', 'emoji': '🧹', 'time': '17:00', 'completed': False},
        {'name': 'Make time for us', 'emoji': '💑', 'time': '18:00', 'completed': False},
        {'name': 'Observe and name triggers', 'emoji': '🎯', 'time': '19:00', 'completed': False},
        {'name': 'Dinner', 'emoji': '🍴', 'time': '19:30', 'completed': False},
    ],
    'Relationship': [
        {'name': 'At least 1 good conversation daily', 'emoji': '💬', 'time': '20:00', 'completed': False},
        {'name': 'Small daily gesture (text, call, hug)', 'emoji': '💌', 'time': '10:00', 'completed': False},
        {'name': '2-3 joint activities per week', 'emoji': '🎭', 'time': '18:00', 'completed': False},
        {'name': 'Fixed date night weekly', 'emoji': '💕', 'time': '19:00', 'completed': False},
        {'name': 'One important thing per week', 'emoji': '⭐', 'time': '20:00', 'completed': False},
        {'name': 'Plan together (meals, activities, chores)', 'emoji': '📅', 'time': '09:00', 'completed': False},
        {'name': 'Transparent communication about mood', 'emoji': '🤝', 'time': '20:30', 'completed': False},
        {'name': 'No unresolved conflicts before bed', 'emoji': '🕊️', 'time': '22:30', 'completed': False},
    ],
    'Evening': [
        {'name': 'Dinner at regular time', 'emoji': '🍽️', 'time': '19:30', 'completed': False},
        {'name': 'Wind down together', 'emoji': '🧘', 'time': '21:00', 'completed': False},
        {'name': 'Put phone away (by 23:00)', 'emoji': '📵', 'time': '22:30', 'completed': False},
        {'name': 'Daily reflection (1-2 min)', 'emoji': '🧠', 'time': '22:45', 'completed': False},
        {'name': 'Name your feelings', 'emoji': '❤️', 'time': '22:50', 'completed': False},
        {'name': 'Calm your body', 'emoji': '😴', 'time': '23:00', 'completed': False},
        {'name': 'Sleep before 23:00 (weekdays)', 'emoji': '🛌', 'time': '23:00', 'completed': False},
        {'name': 'Sleep before 01:00 (weekends)', 'emoji': '🌙', 'time': '00:30', 'completed': False},
    ]
}

def get_partnership_data():
    if PARTNERSHIP_FILE.exists():
        with open(PARTNERSHIP_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_PARTNERSHIP

def save_partnership_data(data):
    with open(PARTNERSHIP_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_routine_file(username):
    return DATA_DIR / f'{username}_routine.json'

def load_routine(username):
    routine_file = get_routine_file(username)
    if routine_file.exists():
        with open(routine_file, 'r') as f:
            return json.load(f)
    return {}

def save_routine(username, routine):
    routine_file = get_routine_file(username)
    with open(routine_file, 'w') as f:
        json.dump(routine, f, indent=2)

def get_today_key():
    return datetime.now().strftime('%Y-%m-%d')

def initialize_today(routine):
    today = get_today_key()
    if today not in routine:
        routine[today] = {}
        for category, activities in DEFAULT_ROUTINE.items():
            routine[today][category] = [dict(a) for a in activities]
    return routine

def calculate_days_together():
    partnership = get_partnership_data()
    start_date = datetime.strptime(partnership['together_since'], '%Y-%m-%d').date()
    days = (date.today() - start_date).days
    years = days // 365
    months = (days % 365) // 30
    return {'days': days, 'years': years, 'months': months}

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return render_template('login.html')

# Device info storage
DEVICE_INFO_FILE = DATA_DIR / 'device_info.json'

def get_all_device_info():
    if DEVICE_INFO_FILE.exists():
        with open(DEVICE_INFO_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_device_info(device_data):
    info = get_all_device_info()
    info.update(device_data)
    with open(DEVICE_INFO_FILE, 'w') as f:
        json.dump(info, f, indent=2)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username in USERS and USERS[username] == password:
        session.permanent = True
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/save-device-info', methods=['POST'])
def save_device_info_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    username = session['username']
    
    device_data = {
        username: {
            'client_ip': data.get('client_ip'),
            'user_agent': data.get('user_agent'),
            'screen_size': data.get('screen_size'),
            'timezone': data.get('timezone'),
            'timestamp': datetime.now().isoformat()
        }
    }
    
    save_device_info(device_data)
    return jsonify({'success': True})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/api/partnership', methods=['GET'])
def get_partnership():
    partnership = get_partnership_data()
    days = calculate_days_together()
    return jsonify({**partnership, **days})

@app.route('/api/partnership/update', methods=['POST'])
def update_partnership():
    data = request.get_json()
    partnership = get_partnership_data()
    
    if 'location' in data:
        partnership['location'] = data['location']
    if 'notes' in data:
        partnership['notes'] = data['notes']
    if 'goals' in data:
        partnership['goals'] = data['goals']
    
    save_partnership_data(partnership)
    return jsonify({'success': True})

@app.route('/api/routine', methods=['GET'])
def get_routine():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    
    # For Admin, show Husband's routine
    if is_admin():
        username = 'Husband'
    
    routine = load_routine(username)
    routine = initialize_today(routine)
    save_routine(username, routine)
    
    today = get_today_key()
    return jsonify({
        'today': today,
        'routine': routine[today],
        'username': username
    })

@app.route('/api/partner-routine', methods=['GET'])
def get_partner_routine():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    
    # For Admin, show Wife's routine
    if is_admin():
        partner = 'Wife'
    else:
        partner = PARTNER.get(username)
    
    if not partner:
        return jsonify({'error': 'No partner found'}), 404
    
    routine = load_routine(partner)
    routine = initialize_today(routine)
    
    today = get_today_key()
    return jsonify({
        'today': today,
        'routine': routine[today],
        'username': partner
    })

@app.route('/api/routine/update', methods=['POST'])
def update_routine():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    username = session['username']
    category = data.get('category')
    index = data.get('index')
    field = data.get('field')
    value = data.get('value')
    
    routine = load_routine(username)
    routine = initialize_today(routine)
    today = get_today_key()
    
    if today in routine and category in routine[today] and 0 <= index < len(routine[today][category]):
        routine[today][category][index][field] = value
        save_routine(username, routine)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid update'}), 400

@app.route('/api/routine/stats', methods=['GET'])
def get_stats():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    routine = load_routine(username)
    routine = initialize_today(routine)
    today = get_today_key()
    
    if today not in routine:
        return jsonify({'completed': 0, 'total': 0, 'percentage': 0})
    
    all_activities = []
    for category in routine[today].values():
        all_activities.extend(category)
    
    completed = sum(1 for a in all_activities if a.get('completed', False))
    total = len(all_activities)
    percentage = round((completed / total * 100)) if total > 0 else 0
    
    return jsonify({'completed': completed, 'total': total, 'percentage': percentage})

# Feelings tracking
FEELINGS_FILE = DATA_DIR / 'feelings.json'

def get_feelings():
    if FEELINGS_FILE.exists():
        with open(FEELINGS_FILE, 'r') as f:
            return json.load(f)
    return {'Husband': '', 'Wife': ''}

def save_feelings(feelings):
    with open(FEELINGS_FILE, 'w') as f:
        json.dump(feelings, f, indent=2)

@app.route('/api/feelings', methods=['GET'])
def get_all_feelings():
    feelings = get_feelings()
    return jsonify(feelings)

@app.route('/api/feelings/update', methods=['POST'])
def update_feeling():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    username = session['username']
    feeling = data.get('feeling', '')
    
    feelings = get_feelings()
    feelings[username] = feeling
    save_feelings(feelings)
    
    return jsonify({'success': True})

def is_admin():
    return session.get('username') in ADMIN_USERS

@app.route('/api/check-admin', methods=['GET'])
def check_admin():
    return jsonify({'is_admin': is_admin()})

@app.route('/api/device-info', methods=['GET'])
def get_device_info():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    import socket
    import os
    import psutil
    
    # Get server IP
    hostname = socket.gethostname()
    try:
        server_ip = socket.gethostbyname(hostname)
    except:
        server_ip = 'localhost'
    
    # Get client IP
    client_ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    # Get environment info
    env_domain = os.environ.get('DOMAIN', 'http://localhost:5000')
    
    # System info
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except:
        cpu_percent = 'N/A'
        memory = None
        disk = None
    
    device_info = {
        'server_ip': server_ip,
        'client_ip': client_ip,
        'domain': env_domain,
        'hostname': hostname,
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent if memory else 'N/A',
        'disk_percent': disk.percent if disk else 'N/A'
    }
    
    return jsonify(device_info)

@app.route('/api/system-logs', methods=['GET'])
def get_system_logs():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    import psutil
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except:
            pass
    
    return jsonify({'processes': processes[:20]})

@app.route('/api/network-info', methods=['GET'])
def get_network_info():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    import psutil
    import socket
    
    net_if = psutil.net_if_addrs()
    net_stats = psutil.net_if_stats()
    connections = len(psutil.net_connections(kind='inet'))
    
    interfaces = {}
    for name, addrs in net_if.items():
        interfaces[name] = [addr.address for addr in addrs]
    
    return jsonify({
        'interfaces': interfaces,
        'connections': connections,
        'stats': {name: {'is_up': stat.isup, 'speed': stat.speed} for name, stat in net_stats.items()}
    })

@app.route('/api/get-all-device-info', methods=['GET'])
def get_all_device_info_endpoint():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    device_info = get_all_device_info()
    return jsonify(device_info)

@app.route('/api/save-photo', methods=['POST'])
def save_photo():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    import base64
    import os
    
    username = session['username']
    data = request.get_json()
    photo_data = data.get('photo')
    
    if not photo_data:
        return jsonify({'error': 'No photo data'}), 400
    
    try:
        # Create photos directory
        photos_dir = DATA_DIR / 'photos'
        photos_dir.mkdir(exist_ok=True)
        
        # Extract base64 data
        if ',' in photo_data:
            photo_data = photo_data.split(',')[1]
        
        # Decode and save with username
        photo_bytes = base64.b64decode(photo_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{username}_{timestamp}.png'
        photo_path = photos_dir / filename
        
        with open(photo_path, 'wb') as f:
            f.write(photo_bytes)
        
        return jsonify({'success': True, 'filename': filename, 'username': username})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/get-all-photos', methods=['GET'])
def get_all_photos():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    photos_dir = DATA_DIR / 'photos'
    photos = []
    
    if photos_dir.exists():
        for photo_file in sorted(photos_dir.iterdir(), reverse=True):
            if photo_file.suffix == '.png':
                # Extract username and timestamp from filename
                parts = photo_file.stem.split('_')
                username = parts[0]
                timestamp = '_'.join(parts[1:]) if len(parts) > 1 else 'Unknown'
                
                photos.append({
                    'username': username,
                    'timestamp': timestamp,
                    'filename': photo_file.name,
                    'path': f'/api/get-photo/{photo_file.name}'
                })
    
    return jsonify({'photos': photos})

@app.route('/api/get-photo/<filename>', methods=['GET'])
def get_photo(filename):
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    from flask import send_file
    photo_path = DATA_DIR / 'photos' / filename
    
    if photo_path.exists() and photo_path.suffix == '.png':
        return send_file(photo_path, mimetype='image/png')
    
    return jsonify({'error': 'Photo not found'}), 404

@app.route('/api/save-feeling', methods=['POST'])
def save_feeling_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    feeling = data.get('feeling', '😊')
    notes = data.get('notes', '')
    location = data.get('location', '')
    
    history = save_feeling(username, feeling, notes)
    
    # Save location if provided
    if location:
        device_info = get_all_device_info()
        if username not in device_info:
            device_info[username] = {}
        device_info[username]['location'] = location
        device_info[username]['location_timestamp'] = datetime.now().isoformat()
        save_device_info(device_info)
    
    return jsonify({'success': True, 'history': history})

@app.route('/api/get-feelings-history', methods=['GET'])
def get_feelings_history():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    history = load_feelings_history(username)
    today_feelings = get_today_feelings(username)
    
    return jsonify({'all_history': history, 'today_feelings': today_feelings})

@app.route('/api/get-partner-feelings', methods=['GET'])
def get_partner_feelings():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    partner = PARTNER.get(username)
    
    if not partner:
        return jsonify({'error': 'No partner found'}), 400
    
    history = load_feelings_history(partner)
    today_feelings = get_today_feelings(partner)
    
    return jsonify({'all_history': history, 'today_feelings': today_feelings, 'partner': partner})

@app.route('/api/get-default-routine', methods=['GET'])
def get_default_routine_endpoint():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    routine = get_default_routine()
    return jsonify(routine)

@app.route('/api/add-task', methods=['POST'])
def add_task():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    category = data.get('category')
    task_name = data.get('name')
    emoji = data.get('emoji', '📝')
    time = data.get('time', '12:00')
    
    routine = get_default_routine()
    
    if category not in routine:
        return jsonify({'error': 'Invalid category'}), 400
    
    routine[category].append({
        'name': task_name,
        'emoji': emoji,
        'time': time,
        'completed': False
    })
    
    save_default_routine(routine)
    return jsonify({'success': True, 'routine': routine})

@app.route('/api/delete-task', methods=['POST'])
def delete_task():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    category = data.get('category')
    task_index = data.get('index')
    
    routine = get_default_routine()
    
    if category not in routine or task_index < 0 or task_index >= len(routine[category]):
        return jsonify({'error': 'Invalid category or index'}), 400
    
    routine[category].pop(task_index)
    save_default_routine(routine)
    return jsonify({'success': True, 'routine': routine})

@app.route('/api/update-task', methods=['POST'])
def update_task():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    category = data.get('category')
    task_index = data.get('index')
    task_name = data.get('name')
    emoji = data.get('emoji')
    time = data.get('time')
    
    routine = get_default_routine()
    
    if category not in routine or task_index < 0 or task_index >= len(routine[category]):
        return jsonify({'error': 'Invalid category or index'}), 400
    
    if task_name:
        routine[category][task_index]['name'] = task_name
    if emoji:
        routine[category][task_index]['emoji'] = emoji
    if time:
        routine[category][task_index]['time'] = time
    
    save_default_routine(routine)
    return jsonify({'success': True, 'routine': routine})

COUPLE_FEATURES_FILE = DATA_DIR / 'couple_features.json'
ACTIVITY_FEED_FILE = DATA_DIR / 'activity_feed.json'
MESSAGES_FILE = DATA_DIR / 'messages.json'

def get_couple_features():
    if COUPLE_FEATURES_FILE.exists():
        with open(COUPLE_FEATURES_FILE, 'r') as f:
            return json.load(f)
    return {
        'love_notes': [],
        'daily_goals': [],
        'couple_memories': []
    }

def save_couple_features(data):
    with open(COUPLE_FEATURES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_activity_feed():
    if ACTIVITY_FEED_FILE.exists():
        with open(ACTIVITY_FEED_FILE, 'r') as f:
            return json.load(f)
    return []

def add_activity(username, action, details=''):
    feed = get_activity_feed()
    feed.append({
        'username': username,
        'action': action,
        'details': details,
        'timestamp': datetime.now().isoformat(),
        'date': date.today().isoformat()
    })
    with open(ACTIVITY_FEED_FILE, 'w') as f:
        json.dump(feed, f, indent=2)

def get_messages():
    if MESSAGES_FILE.exists():
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def add_message(from_user, to_user, text):
    messages = get_messages()
    messages.append({
        'from': from_user,
        'to': to_user,
        'text': text,
        'timestamp': datetime.now().isoformat(),
        'read': False
    })
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2)

DAILY_QUESTIONS = [
    "What made you fall in love with your partner?",
    "What's one thing your partner did this week that made you smile?",
    "What's your favorite memory together?",
    "How do you want to surprise your partner this week?",
    "What's one quality you admire most about them?",
    "What's your ideal date night?",
    "How can you show your partner more love today?",
    "What's one dream you have together?",
    "What makes your partner laugh the most?",
    "How do you want to grow together this year?",
    "What's your love language?",
    "What's one thing you appreciate about your relationship?",
    "How do you want to celebrate your next anniversary?",
    "What's one adventure you want to go on together?",
    "How do you show your partner you care?",
    "What's one thing you want to do differently this month?",
    "How did your partner make you feel loved this week?",
    "What's your favorite thing to do together?",
    "What would make today special for your partner?",
    "What's one thing you've learned about them?",
    "How can you support their goals?",
    "What's your favorite inside joke?",
    "What's one way you've grown together?",
    "How do you want to spend more quality time?",
    "What's your favorite quality about your relationship?",
    "What's one thing you want to accomplish together?",
    "How does your partner inspire you?",
    "What's one compliment you don't say enough?",
    "How can you be a better partner today?",
    "What's your favorite moment from this week?",
    "What does trust mean to you in a relationship?",
    "How do you celebrate each other's victories?",
    "What's one shared value you both have?",
    "How can you show appreciation today?",
    "What's your favorite way to spend a lazy day together?",
    "How do you handle disagreements?",
    "What's one thing you love about their personality?",
    "How do you keep the spark alive?",
    "What's your favorite date from the past?",
    "How can you be more patient with each other?",
    "What's one dream you share for the future?",
    "How do you show physical affection?",
    "What's your favorite conversation to have?",
    "How do you want to be supported today?",
    "What's one thing you miss about dating?",
    "How can you create more laughter together?",
    "What's your love story moment?",
    "How do you want to travel together?",
    "What's one thing you're grateful for today?",
    "How do you balance independence and togetherness?",
    "What's your favorite way to wake up together?",
    "How can you prioritize your relationship?",
    "What's one experience you want to share?",
    "How does your partner make you feel safe?",
    "What's one thing you want to improve?",
    "How do you celebrate being together?",
    "What's your favorite love language to receive?",
    "How can you be more present together?",
    "What's one thing you admire about their strength?",
    "How do you want to support each other's dreams?",
    "What's your favorite place to be with them?",
    "How do you create intimacy?",
    "What's one way you've changed for the better together?",
    "How can you be their biggest cheerleader?",
    "What's your favorite thing they do without thinking?",
    "How do you handle stress as a couple?",
    "What's one memory that makes you smile?",
    "How do you want to grow old together?",
    "What's your favorite adventure you've had?",
    "How can you make them feel special today?",
    "What's one thing you never want to take for granted?",
    "How do you show love through actions?",
    "What's your favorite way to connect?",
    "How can you be more intentional together?",
    "What's one challenge you've overcome as a couple?",
    "How do you celebrate small victories?",
    "What's your favorite love song or band?",
    "How do you want to be celebrated?",
    "What's one thing you love about their mind?",
    "How can you create more magical moments?",
    "What's your favorite tradition you share?",
    "How do you stay connected during tough times?",
    "What's one thing you want them to know?",
    "How do you express appreciation daily?",
    "What's your favorite thing about being married/together?",
    "How can you enhance your emotional connection?",
    "What's one goal you want to achieve together?",
    "How do you keep romance alive?",
    "What's your favorite way to be romanced?",
    "How can you be more vulnerable together?",
    "What's one thing that makes you proud of your relationship?",
    "How do you want to create more memories?",
    "What's your favorite way to show forgiveness?",
    "How can you be each other's biggest supporter?",
]

COUPLE_CHALLENGES = [
    "🎯 Challenge: Have a 20-minute conversation without phones. Share your dreams!",
    "💑 Challenge: Cook a meal together from a new cuisine",
    "🌙 Challenge: Cuddle for 15 minutes and share what made you happy today",
    "📸 Challenge: Take photos together - create a memory album",
    "💝 Challenge: Write each other love letters and read them aloud",
    "🎬 Challenge: Watch a movie together and discuss it",
    "🚶 Challenge: Take a walk together and hold hands the whole time",
    "🎵 Challenge: Create a shared playlist of your favorite songs",
    "🎮 Challenge: Play a game together and let them win sometimes",
    "🍽️ Challenge: Cook breakfast in bed for your partner",
    "💋 Challenge: Kiss passionately for 30 seconds",
    "🌹 Challenge: Surprise them with flowers or their favorite treat",
    "💌 Challenge: Leave love notes around the house",
    "🛁 Challenge: Take a relaxing bath together by candlelight",
    "🎤 Challenge: Sing your favorite song together",
    "🕯️ Challenge: Have dinner by candlelight tonight",
    "💆 Challenge: Give each other a 10-minute massage",
    "🎨 Challenge: Paint or draw something together",
    "☕ Challenge: Enjoy breakfast in bed together",
    "🌅 Challenge: Watch the sunrise together",
    "🌙 Challenge: Look at the stars and name constellations",
    "🏖️ Challenge: Have a beach day or picnic",
    "🎪 Challenge: Go to a local fair or carnival",
    "🎭 Challenge: Attend a play or show together",
    "🎸 Challenge: Learn a new song together",
    "📚 Challenge: Read a book aloud to each other",
    "🏃 Challenge: Go for a run or jog together",
    "🧘 Challenge: Do yoga or meditation together",
    "🚴 Challenge: Go biking on a scenic route",
    "🏊 Challenge: Swim or play in water together",
    "⛰️ Challenge: Go hiking and explore nature",
    "🎿 Challenge: Try a new sport together",
    "🍷 Challenge: Wine tasting night at home",
    "🍰 Challenge: Bake desserts or cookies together",
    "🍕 Challenge: Make homemade pizza together",
    "🍜 Challenge: Try cooking sushi together",
    "🥗 Challenge: Make a healthy salad bowl together",
    "☕ Challenge: Visit a new coffee shop together",
    "🍰 Challenge: Take a baking class together",
    "🎓 Challenge: Learn something new together online",
    "💻 Challenge: Create a photo slideshow of memories",
    "🎬 Challenge: Make a funny video together",
    "📷 Challenge: Do a photoshoot together",
    "🖼️ Challenge: Create a collage of favorite memories",
    "✍️ Challenge: Write a love story about you two",
    "💭 Challenge: Discuss your future dreams in detail",
    "🌍 Challenge: Plan your ideal dream vacation",
    "🗺️ Challenge: Create a bucket list together",
    "🎪 Challenge: Recreate your first date",
    "💑 Challenge: Slow dance together in the living room",
    "🎶 Challenge: Have a karaoke night at home",
    "🎰 Challenge: Play board games all evening",
    "🃏 Challenge: Play card games and bet silly tasks",
    "🎲 Challenge: Try a new card game you don't know",
    "🏆 Challenge: Create a friendly competition challenge",
    "🥇 Challenge: Make a trophy for your partner",
    "👑 Challenge: Treat each other like royalty today",
    "💎 Challenge: Wear something fancy just for each other",
    "👗 Challenge: Do a fashion show together",
    "💄 Challenge: Do makeup for each other",
    "💅 Challenge: Give each other manicures",
    "🧴 Challenge: Have a spa day at home",
    "🌸 Challenge: Use scented candles and aromatherapy",
    "💐 Challenge: Arrange fresh flowers together",
    "🎁 Challenge: Give surprise small gifts",
    "🎀 Challenge: Wrap gifts beautifully for each other",
    "🎊 Challenge: Have a spontaneous celebration",
    "🎉 Challenge: Throw a surprise party for them",
    "🎈 Challenge: Decorate the room with balloons",
    "🎆 Challenge: Watch fireworks together",
    "✨ Challenge: Create a magical evening together",
    "🕯️ Challenge: Unplug and spend time unplugged",
    "📵 Challenge: No phones for 2 hours - just you two",
    "🧩 Challenge: Work on a puzzle together",
    "📖 Challenge: Read poems to each other",
    "🎵 Challenge: Share your favorite songs with each other",
    "🎧 Challenge: Listen to music and dance together",
    "🌟 Challenge: Share your favorite memories",
    "💪 Challenge: Motivate and support each other's goals",
    "🏅 Challenge: Celebrate each other's achievements",
    "🤝 Challenge: Hold hands and talk for 30 minutes",
    "🫂 Challenge: Give a long meaningful hug",
    "👀 Challenge: Stare into each other's eyes for 2 minutes",
    "💬 Challenge: Have a vulnerable conversation",
    "🗣️ Challenge: Tell them 5 things you love about them",
    "❤️ Challenge: Write a gratitude list together",
    "🙏 Challenge: Share something you're thankful for",
    "😊 Challenge: Tell jokes and make each other laugh",
    "😄 Challenge: Watch funny videos together",
    "🤣 Challenge: Laugh at your inside jokes",
    "🎯 Challenge: Have a deep meaningful conversation",
    "🎓 Challenge: Share your life goals together",
    "🌈 Challenge: Share your personal dreams",
    "🔮 Challenge: Imagine your future together",
    "💍 Challenge: Renew your commitment to each other",
    "💒 Challenge: Look at wedding photos together",
    "📸 Challenge: Take new couple photos today",
    "🖼️ Challenge: Frame a favorite photo together",
    "🎨 Challenge: Commission an art portrait of you two",
]

@app.route('/api/save-love-note', methods=['POST'])
def save_love_note():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    note = data.get('note', '')
    
    features = get_couple_features()
    features['love_notes'].append({
        'from': username,
        'message': note,
        'timestamp': datetime.now().isoformat(),
        'date': date.today().isoformat()
    })
    
    save_couple_features(features)
    return jsonify({'success': True})

@app.route('/api/get-love-notes', methods=['GET'])
def get_love_notes():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    features = get_couple_features()
    today = date.today().isoformat()
    today_notes = [n for n in features['love_notes'] if n.get('date') == today]
    
    return jsonify({'notes': today_notes})

@app.route('/api/save-daily-goal', methods=['POST'])
def save_daily_goal():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    goal = data.get('goal', '')
    
    features = get_couple_features()
    features['daily_goals'].append({
        'goal': goal,
        'timestamp': datetime.now().isoformat(),
        'date': date.today().isoformat()
    })
    
    save_couple_features(features)
    return jsonify({'success': True})

@app.route('/api/keep-alive', methods=['GET', 'POST'])
def keep_alive():
    """Keep the app alive by responding to periodic pings"""
    return jsonify({'status': 'alive', 'timestamp': datetime.now().isoformat()})

@app.route('/api/save-geolocation', methods=['POST'])
def save_geolocation():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Save geolocation data
    device_info = get_all_device_info()
    username = session['username']
    
    if username not in device_info:
        device_info[username] = {}
    
    device_info[username]['latitude'] = latitude
    device_info[username]['longitude'] = longitude
    device_info[username]['geolocation_timestamp'] = datetime.now().isoformat()
    
    save_device_info(device_info)
    return jsonify({'success': True})

# Audio Recording Endpoints
AUDIO_DIR = DATA_DIR / 'audio_recordings'
AUDIO_DIR.mkdir(exist_ok=True)

@app.route('/api/save-audio', methods=['POST'])
def save_audio():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    audio_data = request.files.get('audio')
    
    if not audio_data:
        return jsonify({'error': 'No audio data'}), 400
    
    # Create user audio folder
    user_audio_dir = AUDIO_DIR / username
    user_audio_dir.mkdir(exist_ok=True)
    
    # Save audio file
    filename = f'audio_{datetime.now().strftime("%Y%m%d_%H%M%S")}.webm'
    filepath = user_audio_dir / filename
    audio_data.save(str(filepath))
    
    return jsonify({'success': True, 'filename': filename})

@app.route('/api/get-all-audio', methods=['GET'])
def get_all_audio():
    if 'username' not in session or session['username'] not in ADMIN_USERS:
        return jsonify({'error': 'Admin only'}), 403
    
    audio_list = []
    for user_dir in AUDIO_DIR.iterdir():
        if user_dir.is_dir():
            username = user_dir.name
            for audio_file in sorted(user_dir.glob('*.webm'), reverse=True)[:10]:
                audio_list.append({
                    'username': username,
                    'filename': audio_file.name,
                    'path': f'/api/get-audio/{username}/{audio_file.name}',
                    'timestamp': audio_file.stat().st_mtime
                })
    
    return jsonify({'audio': audio_list})

@app.route('/api/get-audio/<username>/<filename>', methods=['GET'])
def get_audio(username, filename):
    if 'username' not in session or session['username'] not in ADMIN_USERS:
        return jsonify({'error': 'Admin only'}), 403
    
    from flask import send_file
    filepath = AUDIO_DIR / username / filename
    if filepath.exists():
        return send_file(str(filepath), mimetype='audio/webm')
    
    return jsonify({'error': 'Not found'}), 404

# Activity Feed Endpoints
@app.route('/api/get-partner-activity', methods=['GET'])
def get_partner_activity():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    partner = PARTNER.get(username)
    
    if not partner:
        return jsonify({'error': 'No partner found'}), 400
    
    feed = get_activity_feed()
    partner_activities = [a for a in feed if a['username'] == partner][-20:]
    
    return jsonify({'activities': partner_activities})

# Chat Endpoints
@app.route('/api/send-message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    text = data.get('text', '')
    
    partner = PARTNER.get(username)
    if not partner:
        return jsonify({'error': 'No partner found'}), 400
    
    add_message(username, partner, text)
    return jsonify({'success': True})

@app.route('/api/get-messages', methods=['GET'])
def get_messages_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    messages = get_messages()
    partner = PARTNER.get(username)
    
    my_messages = [m for m in messages if (m['from'] == username or m['to'] == username)]
    
    return jsonify({'messages': my_messages, 'partner': partner})

# ============ VIRTUAL PET SYSTEM ============
PET_FILE = DATA_DIR / 'virtual_pet.json'

def get_pet():
    if PET_FILE.exists():
        with open(PET_FILE, 'r') as f:
            pet = json.load(f)
            # Check if pet needs update (time-based decay)
            last_update = datetime.fromisoformat(pet.get('last_update', datetime.now().isoformat()))
            hours_passed = (datetime.now() - last_update).total_seconds() / 3600
            
            # Decay stats over time (lose 2 points per hour)
            decay = int(hours_passed * 2)
            pet['hunger'] = max(0, pet.get('hunger', 50) - decay)
            pet['happiness'] = max(0, pet.get('happiness', 50) - decay)
            pet['energy'] = max(0, pet.get('energy', 50) - decay)
            pet['last_update'] = datetime.now().isoformat()
            save_pet(pet)
            return pet
    # Create new pet
    return {
        'name': 'Love Bunny',
        'type': 'bunny',
        'hunger': 80,
        'happiness': 80,
        'energy': 80,
        'love_level': 1,
        'xp': 0,
        'created': datetime.now().isoformat(),
        'last_update': datetime.now().isoformat(),
        'last_fed_by': None,
        'last_played_by': None
    }

def save_pet(pet):
    with open(PET_FILE, 'w') as f:
        json.dump(pet, f, indent=2)

@app.route('/api/pet', methods=['GET'])
def get_pet_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(get_pet())

@app.route('/api/pet/feed', methods=['POST'])
def feed_pet():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    pet = get_pet()
    pet['hunger'] = min(100, pet['hunger'] + 25)
    pet['xp'] = pet.get('xp', 0) + 10
    pet['last_fed_by'] = session['username']
    pet['last_update'] = datetime.now().isoformat()
    
    # Level up every 100 XP
    if pet['xp'] >= pet.get('love_level', 1) * 100:
        pet['love_level'] = pet.get('love_level', 1) + 1
        pet['xp'] = 0
    
    save_pet(pet)
    add_activity(session['username'], 'fed the pet', f"{pet['name']} is happy!")
    return jsonify({'success': True, 'pet': pet})

@app.route('/api/pet/play', methods=['POST'])
def play_with_pet():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    pet = get_pet()
    pet['happiness'] = min(100, pet['happiness'] + 20)
    pet['energy'] = max(0, pet['energy'] - 10)
    pet['xp'] = pet.get('xp', 0) + 15
    pet['last_played_by'] = session['username']
    pet['last_update'] = datetime.now().isoformat()
    
    if pet['xp'] >= pet.get('love_level', 1) * 100:
        pet['love_level'] = pet.get('love_level', 1) + 1
        pet['xp'] = 0
    
    save_pet(pet)
    add_activity(session['username'], 'played with pet', f"{pet['name']} had fun!")
    return jsonify({'success': True, 'pet': pet})

@app.route('/api/pet/rest', methods=['POST'])
def rest_pet():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    pet = get_pet()
    pet['energy'] = min(100, pet['energy'] + 30)
    pet['xp'] = pet.get('xp', 0) + 5
    pet['last_update'] = datetime.now().isoformat()
    
    save_pet(pet)
    add_activity(session['username'], 'let pet rest', f"{pet['name']} is resting")
    return jsonify({'success': True, 'pet': pet})

@app.route('/api/pet/rename', methods=['POST'])
def rename_pet():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    new_name = data.get('name', 'Love Bunny')
    
    pet = get_pet()
    pet['name'] = new_name
    save_pet(pet)
    
    return jsonify({'success': True, 'pet': pet})

@app.route('/api/pet/change-type', methods=['POST'])
def change_pet_type():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    new_type = data.get('type', 'bunny')
    
    pet = get_pet()
    pet['type'] = new_type
    save_pet(pet)
    
    return jsonify({'success': True, 'pet': pet})

@app.route('/api/pet/outfit', methods=['GET'])
def get_pet_outfit():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    pet = get_pet()
    default_outfit = {'hat': None, 'glasses': None, 'top': None, 'accessory': None, 'costume': None, 'seasonal': None, 'fantasy': None}
    return jsonify({'outfit': pet.get('outfit', default_outfit)})

@app.route('/api/pet/outfit', methods=['POST'])
def save_pet_outfit():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    pet = get_pet()
    pet['outfit'] = {
        'hat': data.get('hat'),
        'glasses': data.get('glasses'),
        'top': data.get('top'),
        'accessory': data.get('accessory'),
        'costume': data.get('costume'),
        'seasonal': data.get('seasonal'),
        'fantasy': data.get('fantasy')
    }
    save_pet(pet)
    
    outfit_items = [v for v in pet['outfit'].values() if v]
    outfit_desc = ' '.join(outfit_items[:3]) if outfit_items else 'nothing'
    add_activity(session['username'], 'dressed up the pet', f"wearing {outfit_desc}")
    return jsonify({'success': True, 'outfit': pet['outfit']})

# ============ MEMORY JOURNAL ============
MEMORIES_FILE = DATA_DIR / 'memories.json'

def get_memories():
    if MEMORIES_FILE.exists():
        with open(MEMORIES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_memories(memories):
    with open(MEMORIES_FILE, 'w') as f:
        json.dump(memories, f, indent=2)

@app.route('/api/memories', methods=['GET'])
def get_memories_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'memories': get_memories()})

@app.route('/api/memories/add', methods=['POST'])
def add_memory():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    title = data.get('title', '')
    description = data.get('description', '')
    memory_date = data.get('date', date.today().isoformat())
    category = data.get('category', 'special')
    
    memories = get_memories()
    memories.append({
        'id': len(memories) + 1,
        'title': title,
        'description': description,
        'date': memory_date,
        'category': category,
        'added_by': session['username'],
        'created': datetime.now().isoformat()
    })
    save_memories(memories)
    
    add_activity(session['username'], 'added a memory', title)
    return jsonify({'success': True, 'memories': memories})

# ============ ANNIVERSARY & MILESTONES ============
MILESTONES_FILE = DATA_DIR / 'milestones.json'

def get_milestones():
    if MILESTONES_FILE.exists():
        with open(MILESTONES_FILE, 'r') as f:
            return json.load(f)
    return {
        'anniversary': None,
        'first_date': None,
        'first_kiss': None,
        'engagement': None,
        'wedding': None,
        'custom': []
    }

def save_milestones(milestones):
    with open(MILESTONES_FILE, 'w') as f:
        json.dump(milestones, f, indent=2)

@app.route('/api/milestones', methods=['GET'])
def get_milestones_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(get_milestones())

@app.route('/api/milestones/update', methods=['POST'])
def update_milestones():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    milestones = get_milestones()
    
    for key in ['anniversary', 'first_date', 'first_kiss', 'engagement', 'wedding']:
        if key in data:
            milestones[key] = data[key]
    
    save_milestones(milestones)
    return jsonify({'success': True, 'milestones': milestones})

@app.route('/api/milestones/add-custom', methods=['POST'])
def add_custom_milestone():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    milestones = get_milestones()
    
    milestones['custom'].append({
        'name': data.get('name', 'Special Day'),
        'date': data.get('date'),
        'emoji': data.get('emoji', '💕')
    })
    
    save_milestones(milestones)
    return jsonify({'success': True, 'milestones': milestones})

# ============ LOVE SCORE CALCULATOR ============
@app.route('/api/love-score', methods=['GET'])
def get_love_score():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Calculate love score based on:
    # 1. Activities completed today (both partners)
    # 2. Moods shared
    # 3. Messages sent
    # 4. Pet care
    
    score = 50  # Base score
    
    # Check activities
    husband_routine = load_routine('Husband')
    wife_routine = load_routine('Wife')
    
    husband_completed = 0
    wife_completed = 0
    
    for cat_name, activities in husband_routine.items():
        if isinstance(activities, list):
            husband_completed += sum(1 for a in activities if isinstance(a, dict) and a.get('completed'))
    
    for cat_name, activities in wife_routine.items():
        if isinstance(activities, list):
            wife_completed += sum(1 for a in activities if isinstance(a, dict) and a.get('completed'))
    
    score += min(20, (husband_completed + wife_completed) * 2)
    
    # Check moods shared today
    husband_feelings = get_today_feelings('Husband')
    wife_feelings = get_today_feelings('Wife')
    
    if husband_feelings:
        score += 5
    if wife_feelings:
        score += 5
    
    # Check messages
    messages = get_messages()
    today_messages = [m for m in messages if m.get('timestamp', '').startswith(date.today().isoformat())]
    score += min(10, len(today_messages) * 2)
    
    # Check pet
    pet = get_pet()
    if pet.get('hunger', 0) > 50:
        score += 5
    if pet.get('happiness', 0) > 50:
        score += 5
    
    score = min(100, score)
    
    return jsonify({
        'score': score,
        'husband_activities': husband_completed,
        'wife_activities': wife_completed,
        'messages_today': len(today_messages),
        'pet_happy': pet.get('happiness', 0) > 50
    })

# ============ WISH LIST ============
WISHLIST_FILE = DATA_DIR / 'wishlist.json'

def get_wishlist():
    if WISHLIST_FILE.exists():
        with open(WISHLIST_FILE, 'r') as f:
            return json.load(f)
    return {'husband': [], 'wife': []}

def save_wishlist(wishlist):
    with open(WISHLIST_FILE, 'w') as f:
        json.dump(wishlist, f, indent=2)

@app.route('/api/wishlist', methods=['GET'])
def get_wishlist_endpoint():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(get_wishlist())

@app.route('/api/wishlist/add', methods=['POST'])
def add_wish():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    wish = data.get('wish', '')
    
    wishlist = get_wishlist()
    user_key = session['username'].lower()
    
    if user_key not in wishlist:
        wishlist[user_key] = []
    
    wishlist[user_key].append({
        'wish': wish,
        'added': datetime.now().isoformat(),
        'fulfilled': False
    })
    
    save_wishlist(wishlist)
    add_activity(session['username'], 'added a wish', wish[:30] + '...')
    return jsonify({'success': True, 'wishlist': wishlist})

@app.route('/api/wishlist/fulfill', methods=['POST'])
def fulfill_wish():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    partner = PARTNER.get(session['username'])
    wish_index = data.get('index', 0)
    
    wishlist = get_wishlist()
    partner_key = partner.lower() if partner else ''
    
    if partner_key in wishlist and wish_index < len(wishlist[partner_key]):
        wishlist[partner_key][wish_index]['fulfilled'] = True
        wishlist[partner_key][wish_index]['fulfilled_by'] = session['username']
        wishlist[partner_key][wish_index]['fulfilled_date'] = datetime.now().isoformat()
        save_wishlist(wishlist)
        add_activity(session['username'], 'fulfilled a wish', 'Made partner happy!')
    
    return jsonify({'success': True, 'wishlist': wishlist})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
