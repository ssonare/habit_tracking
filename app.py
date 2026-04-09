import os
import pandas as pd
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'habit_tracker_secret'

# Path to the CSV file that stores habits
HABITS_FILE = 'habits.csv'


def load_habits():
    """Read habits from CSV. Returns an empty DataFrame if file doesn't exist."""
    if os.path.exists(HABITS_FILE):
        return pd.read_csv(HABITS_FILE)
    return pd.DataFrame(columns=['id', 'name', 'description', 'frequency', 'date_added'])


def save_habits(df):
    """Write the habits DataFrame to CSV."""
    df.to_csv(HABITS_FILE, index=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/habits')
def habits():
    """Display all habits."""
    df = load_habits()
    habits_list = df.to_dict(orient='records')
    return render_template('habits.html', habits=habits_list)


@app.route('/habits/add', methods=['GET', 'POST'])
def add_habit():
    """Show add-habit form (GET) and handle form submission (POST)."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        frequency = request.form.get('frequency', '').strip()

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
            'date_added': date.today().strftime('%Y-%m-%d')
        }

        # Append the new habit and persist
        df = pd.concat([df, pd.DataFrame([new_habit])], ignore_index=True)
        save_habits(df)

        flash(f'Habit "{name}" added successfully!', 'success')
        return redirect(url_for('habits'))

    return render_template('add_habit.html')


if __name__ == '__main__':
    app.run(debug=True)
