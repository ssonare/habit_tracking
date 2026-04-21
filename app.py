# Name: Samruddhi, stuti, sandhya
# Date: 04/10/2026
# Automated tests for the Habit Tracking Flask application.
# Tests cover home page, habit list, add habit form,
# form validation, and CSV data persistence.

import os
import pandas as pd
from datetime import date
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user, UserMixin)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'habit_tracker_secret'

# Path to the CSV file that stores habits
HABITS_FILE = 'habits.csv'
USERS_FILE = 'users.json'

# ---------------------------------------------------------------------------
# Flask-Login setup
# ---------------------------------------------------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'


class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ---------------------------------------------------------------------------
# User persistence helpers
# ---------------------------------------------------------------------------


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def get_user_by_email(email):
    users = load_users()
    for uid, data in users.items():
        if data['email'].lower() == email.lower():
            return User(uid, data['username'], data['email'],
                        data['password_hash'])
    return None


def get_user_by_id(user_id):
    users = load_users()
    data = users.get(str(user_id))
    if data:
        return User(str(user_id), data['username'], data['email'],
                    data['password_hash'])
    return None


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


# ---------------------------------------------------------------------------
# Habit persistence helpers
# ---------------------------------------------------------------------------


def load_habits():
    """Read habits from CSV. Returns empty DataFrame if file doesn't exist."""
    if os.path.exists(HABITS_FILE):
        df = pd.read_csv(HABITS_FILE)
        if 'archived' not in df.columns:
            df['archived'] = 0
        if 'category' not in df.columns:
            df['category'] = 'Uncategorized'
        if 'status' not in df.columns:
            df['status'] = 'active'
        return df
    return pd.DataFrame(
        columns=['id', 'name', 'description', 'frequency', 'date_added',
                 'archived', 'category', 'status']
    )


def save_habits(df):
    """Write the habits DataFrame to CSV."""
    df.to_csv(HABITS_FILE, index=False)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('habits'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if get_user_by_email(email):
            flash('An account with that email already exists.', 'error')
            return render_template('register.html')

        users = load_users()
        new_id = str(max((int(k) for k in users.keys()), default=0) + 1)
        users[new_id] = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
        }
        save_users(users)

        new_user = User(
            new_id, username, email, users[new_id]['password_hash']
        )
        login_user(new_user)
        flash(
            f'Welcome, {username}! Your account has been created.', 'success'
        )
        return redirect(url_for('habits'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('habits'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = get_user_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('habits'))

        flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/habits')
@login_required
def habits():
    """Display active (non-archived) habits."""
    df = load_habits()
    active = df[df['archived'] != 1]
    habits_list = active.to_dict(orient='records')
    return render_template('habits.html', habits=habits_list)


@app.route('/habits/archived')
@login_required
def archived_habits():
    """Display archived habits."""
    df = load_habits()
    archived = df[df['archived'] == 1]
    habits_list = archived.to_dict(orient='records')
    return render_template('archived.html', habits=habits_list)


@app.route('/habits/archive/<int:habit_id>', methods=['POST'])
@login_required
def archive_habit(habit_id):
    """Archive a habit by ID."""
    df = load_habits()

    if habit_id not in df['id'].values:
        flash('Habit not found.', 'error')
        return redirect(url_for('habits'))

    habit_name = df.loc[df['id'] == habit_id, 'name'].values[0]
    df.loc[df['id'] == habit_id, 'archived'] = 1
    save_habits(df)

    flash(f'Habit "{habit_name}" archived successfully!', 'success')
    return redirect(url_for('habits'))


@app.route('/habits/unarchive/<int:habit_id>', methods=['POST'])
@login_required
def unarchive_habit(habit_id):
    """Restore an archived habit."""
    df = load_habits()

    if habit_id not in df['id'].values:
        flash('Habit not found.', 'error')
        return redirect(url_for('archived_habits'))

    habit_name = df.loc[df['id'] == habit_id, 'name'].values[0]
    df.loc[df['id'] == habit_id, 'archived'] = 0
    save_habits(df)

    flash(f'Habit "{habit_name}" restored to active habits!', 'success')
    return redirect(url_for('archived_habits'))


@app.route('/habits/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    """Show add-habit form (GET) and handle form submission (POST)."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        frequency = request.form.get('frequency', '').strip()
        category = request.form.get('category', 'Uncategorized').strip()

        # Basic validation
        if not name or not frequency:
            flash('Habit name and frequency are required.', 'error')
            return redirect(url_for('add_habit'))

        df = load_habits()

        # Generate a simple incremental ID
        new_id = int(df['id'].max()) + 1 if not df.empty else 1

        new_habit = {
            'id': new_id,
            'name': name,
            'description': description,
            'frequency': frequency,
            'date_added': date.today().strftime('%Y-%m-%d'),
            'category': category if category else 'Uncategorized',
            'status': 'active'
        }

        # Append the new habit and persist
        df = pd.concat([df, pd.DataFrame([new_habit])], ignore_index=True)
        save_habits(df)

        flash(f'Habit "{name}" added successfully!', 'success')
        return redirect(url_for('habits'))

    return render_template('add_habit.html')


@app.route('/habits/delete/<int:habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Delete a habit by ID."""
    df = load_habits()

    if habit_id not in df['id'].values:
        flash('Habit not found.', 'error')
        return redirect(url_for('habits'))

    habit_name = df.loc[df['id'] == habit_id, 'name'].values[0]
    df = df[df['id'] != habit_id]
    save_habits(df)

    flash(f'Habit "{habit_name}" deleted successfully!', 'success')
    return redirect(url_for('habits'))


@app.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Show edit form (GET) and handle form submission (POST)."""
    df = load_habits()

    if habit_id not in df['id'].values:
        flash('Habit not found.', 'error')
        return redirect(url_for('habits'))

    habit = df.loc[df['id'] == habit_id].iloc[0].to_dict()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        frequency = request.form.get('frequency', '').strip()
        category = request.form.get('category', 'Uncategorized').strip()

        if not name or not frequency:
            flash('Habit name and frequency are required.', 'error')
            return redirect(url_for('edit_habit', habit_id=habit_id))

        df.loc[df['id'] == habit_id, 'name'] = name
        df.loc[df['id'] == habit_id, 'description'] = description
        df.loc[df['id'] == habit_id, 'frequency'] = frequency
        df.loc[df['id'] == habit_id, 'category'] = category if category else 'Uncategorized'
        save_habits(df)

        flash(f'Habit "{name}" updated successfully!', 'success')
        return redirect(url_for('habits'))

    return render_template('edit_habit.html', habit=habit)


@app.route('/habits/stats')
@login_required
def habit_stats():
    """Display habit statistics dashboard."""
    df = load_habits()

    if df.empty:
        stats = {
            'total': 0, 'active': 0, 'completed': 0, 'paused': 0,
            'archived': 0, 'categories': [], 'most_recent': None,
            'oldest': None, 'journey_days': 0, 'active_rate': 0,
            'completed_rate': 0, 'paused_rate': 0, 'total_categories': 0
        }
        return render_template('stats.html', stats=stats)

    total = len(df)
    archived_count = int((df['archived'] == 1).sum())
    active_count = int(((df['archived'] != 1) & (df['status'] == 'active')).sum())
    completed_count = int((df['status'] == 'completed').sum())
    paused_count = int((df['status'] == 'paused').sum())

    non_archived = df[df['archived'] != 1].copy()
    if not non_archived.empty:
        cat_counts = non_archived.groupby('category').size().reset_index(name='count')
        max_count = int(cat_counts['count'].max())
        categories = [
            {
                'name': row['category'],
                'count': int(row['count']),
                'pct': round(row['count'] / max_count * 100)
            }
            for _, row in cat_counts.iterrows()
        ]
    else:
        categories = []

    most_recent = None
    oldest = None
    journey_days = 0
    try:
        df['date_added'] = pd.to_datetime(df['date_added'])
        most_recent_row = df.loc[df['date_added'].idxmax()]
        oldest_row = df.loc[df['date_added'].idxmin()]
        journey_days = int((most_recent_row['date_added'] - oldest_row['date_added']).days)
        most_recent = {
            'name': most_recent_row['name'],
            'category': most_recent_row.get('category', 'Uncategorized'),
            'date': most_recent_row['date_added'].strftime('%B %d, %Y')
        }
        oldest = {
            'name': oldest_row['name'],
            'category': oldest_row.get('category', 'Uncategorized'),
            'date': oldest_row['date_added'].strftime('%B %d, %Y')
        }
    except Exception:
        pass

    total_categories = int(df['category'].nunique()) if 'category' in df.columns else 0

    stats = {
        'total': total,
        'active': active_count,
        'completed': completed_count,
        'paused': paused_count,
        'archived': archived_count,
        'categories': categories,
        'most_recent': most_recent,
        'oldest': oldest,
        'journey_days': journey_days,
        'active_rate': round(active_count / total * 100, 1) if total > 0 else 0,
        'completed_rate': round(completed_count / total * 100, 1) if total > 0 else 0,
        'paused_rate': round(paused_count / total * 100, 1) if total > 0 else 0,
        'total_categories': total_categories
    }

    return render_template('stats.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True)
