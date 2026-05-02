# Name: Samruddhi, Stuti, Sandhya
# Date: 04/10/2026
# Description: Main Flask application for the Habit Tracking system.
# Handles routing, authentication, and delegates habit management
# to the HabitTracker and Habit classes.

import os
import json
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user, UserMixin)
from werkzeug.security import generate_password_hash, check_password_hash
from habit_tracker import HabitTracker

app = Flask(__name__)
app.secret_key = 'habit_tracker_secret'

# Path to the JSON file that stores users
USERS_FILE = 'users.json'

# Shared HabitTracker instance used by all routes
tracker = HabitTracker('habits.csv')

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
    habits_list = tracker.get_active()
    return render_template('habits.html', habits=habits_list)


@app.route('/habits/archived')
@login_required
def archived_habits():
    """Display archived habits."""
    habits_list = tracker.get_archived()
    return render_template('archived.html', habits=habits_list)


@app.route('/habits/archive/<int:habit_id>', methods=['POST'])
@login_required
def archive_habit(habit_id):
    """Archive a habit by ID."""
    name = tracker.archive_habit(habit_id)
    if name is None:
        flash('Habit not found.', 'error')
    else:
        flash(f'Habit "{name}" archived successfully!', 'success')
    return redirect(url_for('habits'))


@app.route('/habits/unarchive/<int:habit_id>', methods=['POST'])
@login_required
def unarchive_habit(habit_id):
    """Restore an archived habit."""
    name = tracker.unarchive_habit(habit_id)
    if name is None:
        flash('Habit not found.', 'error')
    else:
        flash(f'Habit "{name}" restored to active habits!', 'success')
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

        if not name or not frequency:
            flash('Habit name and frequency are required.', 'error')
            return redirect(url_for('add_habit'))

        habit = tracker.add_habit(name, description, frequency, category)
        flash(f'Habit "{habit.name}" added successfully!', 'success')
        return redirect(url_for('habits'))

    return render_template('add_habit.html')


@app.route('/habits/delete/<int:habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Delete a habit by ID."""
    name = tracker.delete_habit(habit_id)
    if name is None:
        flash('Habit not found.', 'error')
    else:
        flash(f'Habit "{name}" deleted successfully!', 'success')
    return redirect(url_for('habits'))


@app.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Show edit form (GET) and handle form submission (POST)."""
    habit = tracker.get_habit(habit_id)
    if habit is None:
        flash('Habit not found.', 'error')
        return redirect(url_for('habits'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        frequency = request.form.get('frequency', '').strip()
        category = request.form.get('category', 'Uncategorized').strip()

        if not name or not frequency:
            flash('Habit name and frequency are required.', 'error')
            return redirect(url_for('edit_habit', habit_id=habit_id))

        tracker.update_habit(habit_id, name, description, frequency, category)
        flash(f'Habit "{name}" updated successfully!', 'success')
        return redirect(url_for('habits'))

    return render_template('edit_habit.html', habit=habit.to_dict())


@app.route('/habits/pause/<int:habit_id>', methods=['POST'])
@login_required
def pause_habit(habit_id):
    """Pause a habit until a user-defined date."""
    pause_until = request.form.get('pause_until', '').strip()

    if not pause_until:
        flash('Please select resume date.', 'error')
        return redirect(url_for('habits'))

    today = date.today().strftime('%Y-%m-%d')
    if pause_until <= today:
        flash('Resume date must be in the future.', 'error')
        return redirect(url_for('habits'))

    name = tracker.pause_habit(habit_id, pause_until)
    if name is None:
        flash('Habit not found.', 'error')
    else:
        flash(f'Habit "{name}" paused until {pause_until}.', 'success')
    return redirect(url_for('habits'))


@app.route('/habits/resume/<int:habit_id>', methods=['POST'])
@login_required
def resume_habit(habit_id):
    """Manually resume a paused habit before its pause_until date."""
    name = tracker.resume_habit(habit_id)
    if name is None:
        flash('Habit not found.', 'error')
    else:
        flash(f'Habit "{name}" resumed successfully!', 'success')
    return redirect(url_for('habits'))


@app.route('/habits/stats')
@login_required
def habit_stats():
    """Display habit statistics dashboard."""
    stats = tracker.get_stats()
    return render_template('stats.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True)
