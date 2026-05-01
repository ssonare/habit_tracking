# Name: Samruddhi, Stuti, Sandhya
# Date: 04/10/2026
# Automated tests for the Habit Tracking Flask application.

import pytest
import pandas as pd
import app as app_module
from app import app
from habit_tracker import HabitTracker


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Set up a test Flask client with a temporary CSV file."""
    test_csv = str(tmp_path / 'habits.csv')
    test_user = str(tmp_path / 'users.json')
    monkeypatch.setattr(app_module, 'tracker', HabitTracker(test_csv))
    monkeypatch.setattr('app.USERS_FILE', test_user)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


def register_user(client,
                  username='testuser',
                  email='test@example.com',
                  password='secret123'):
    return client.post('/register', data={
        'username': username,
        'email': email,
        'password': password}, follow_redirects=True)


def login_user(client,
               email='test@example.com',
               password='secret123'):
    return client.post('/login', data={
        'email': email,
        'password': password}, follow_redirects=True)


# --- Home page ---

def test_home_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Habit Tracking' in response.data


# --- Registration ---
def test_register_page_loads(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data


def test_register_valid_user(client):
    response = register_user(client)
    assert response.status_code == 200
    assert b'Welcome' in response.data


def test_register_missing_fields(client):
    response = client.post('/register', data={
        'username': '',
        'email': '',
        'password': ''}, follow_redirects=True)
    assert b'required' in response.data


def test_register_short_password(client):
    response = client.post('/register', data={
        'username': 'alice',
        'email': 'alice@example.com',
        'password': '123'}, follow_redirects=True)
    assert b'6 characters' in response.data


def test_register_duplicate_email(client):
    register_user(client)
    client.get('/logout')
    response = register_user(client)
    assert b'already exists' in response.data


def test_register_redirects_to_habits(client):
    response = client.post('/register', data={
        'username': 'bob',
        'email': 'bob@example.com',
        'password': 'password123'}, follow_redirects=False)
    assert response.status_code == 302
    assert '/habits' in response.headers['Location']


# --- Login ---

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Log In' in response.data


def test_login_valid_credentials(client):
    register_user(client)
    client.get('/logout')
    response = login_user(client)
    assert b'Welcome back' in response.data


def test_login_invalid_password(client):
    register_user(client)
    client.get('/logout')
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'}, follow_redirects=True)
    assert b'Invalid email or password' in response.data


def test_login_unknown_email(client):
    response = client.post('/login', data={
        'email': 'nobody@example.com',
        'password': 'secret123'}, follow_redirects=True)
    assert b'Invalid email or password' in response.data


def test_login_redirects_to_habits(client):
    register_user(client)
    client.get('/logout')
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'secret123'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/habits' in response.headers['Location']


# --- Route protection ---

def test_habits_page_requires_login(client):
    response = client.get('/habits', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_add_habit_page_requires_login(client):
    response = client.get('/habits/add', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_add_habit_post_requires_login(client):
    response = client.post('/habits/add', data={
        'name': 'Drink Water', 'frequency': 'Daily'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


# --- Habits list page ---

def test_habits_page_loads_empty(client):
    register_user(client)
    response = client.get('/habits')
    assert response.status_code == 200
    assert b'No habits yet' in response.data


# --- Add habit form ---

def test_add_habit_form_loads(client):
    register_user(client)
    response = client.get('/habits/add')
    assert response.status_code == 200
    assert b'Add New Habit' in response.data


def test_add_habit_valid_submission(client):
    """Valid form data should save the habit and redirect to /habits."""
    register_user(client)
    response = client.post('/habits/add', data={
        'name': 'Drink Water',
        'description': 'Drink 8 glasses a day',
        'frequency': 'Daily'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Drink Water' in response.data
    assert b'added successfully' in response.data


def test_add_habit_missing_name(client):
    """Submitting without a name should show a validation error."""
    register_user(client)
    response = client.post('/habits/add', data={
        'name': '',
        'description': 'Some description',
        'frequency': 'Daily'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'required' in response.data


def test_add_habit_missing_frequency(client):
    """Submitting without a frequency should show a validation error."""
    register_user(client)
    response = client.post('/habits/add', data={
        'name': 'Exercise',
        'description': '',
        'frequency': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'required' in response.data


def test_add_habit_saves_to_csv(client):
    """Habit data should be persisted in the CSV file."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Read Books',
        'description': 'Read for 30 minutes',
        'frequency': 'Daily'
    })

    test_csv = app_module.tracker.habits_file
    df = pd.read_csv(test_csv)
    assert len(df) == 1
    assert df.iloc[0]['name'] == 'Read Books'
    assert df.iloc[0]['frequency'] == 'Daily'


# --- Delete habit ---


def test_delete_habit_success(client):
    """Adding then deleting a habit should remove it from the list."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Meditate',
        'description': 'Meditate for 10 minutes',
        'frequency': 'Daily'
    })

    response = client.post('/habits/delete/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'deleted successfully' in response.data

    # Check habit is gone from the habits list
    response = client.get('/habits')
    assert b'Meditate' not in response.data


def test_delete_habit_not_found(client):
    """Deleting a non-existent habit ID should show an error."""
    register_user(client)
    response = client.post('/habits/delete/999', follow_redirects=True)
    assert response.status_code == 200
    assert b'not found' in response.data


def test_delete_habit_removes_from_csv(client):
    """Deleted habit should no longer exist in the CSV."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Journal',
        'description': 'Write daily journal',
        'frequency': 'Daily'
    })

    client.post('/habits/delete/1')

    test_csv = app_module.tracker.habits_file
    df = pd.read_csv(test_csv)
    assert len(df) == 0


# --- Edit habit ---


def test_edit_habit_form_loads(client):
    """Edit form should load pre-filled with habit details."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run 30 minutes',
        'frequency': 'Daily'
    })

    response = client.get('/habits/edit/1')
    assert response.status_code == 200
    assert b'Exercise' in response.data
    assert b'Run 30 minutes' in response.data


def test_edit_habit_valid_submission(client):
    """Valid edit should update the habit and redirect to /habits."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run 30 minutes',
        'frequency': 'Daily'
    })

    response = client.post('/habits/edit/1', data={
        'name': 'Yoga',
        'description': 'Do yoga for 20 minutes',
        'frequency': 'Daily'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'updated successfully' in response.data
    assert b'Yoga' in response.data


def test_edit_habit_missing_name(client):
    """Submitting edit without a name should show a validation error."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run 30 minutes',
        'frequency': 'Daily'
    })

    response = client.post('/habits/edit/1', data={
        'name': '',
        'description': 'Run 30 minutes',
        'frequency': 'Daily'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'required' in response.data


def test_edit_habit_not_found(client):
    """Editing a non-existent habit ID should show an error."""
    register_user(client)
    response = client.post('/habits/edit/999', data={
        'name': 'Ghost',
        'description': '',
        'frequency': 'Daily'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'not found' in response.data


def test_edit_habit_requires_login(client):
    """Edit route should redirect to login if not authenticated."""
    response = client.get('/habits/edit/1', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_edit_habit_saves_to_csv(client):
    """Updated habit should be persisted correctly in the CSV."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run 30 minutes',
        'frequency': 'Daily'
    })

    client.post('/habits/edit/1', data={
        'name': 'Yoga',
        'description': 'Do yoga',
        'frequency': 'Weekly'
    })

    test_csv = app_module.tracker.habits_file
    df = pd.read_csv(test_csv)
    assert df.iloc[0]['name'] == 'Yoga'
    assert df.iloc[0]['frequency'] == 'Weekly'


# --- Pause habit ---

def test_pause_habit_success(client):
    """Pausing a habit should set its status to paused with a future date."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run daily',
        'frequency': 'Daily'
    })

    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    response = client.post('/habits/pause/1', data={
        'pause_until': future_date
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'paused until' in response.data


def test_pause_habit_missing_date(client):
    """Pausing without a resume date should show a validation error."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run daily',
        'frequency': 'Daily'
    })

    response = client.post('/habits/pause/1', data={
        'pause_until': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'resume date' in response.data


def test_pause_habit_past_date(client):
    """Pausing with a past or today date should show a validation error."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run daily',
        'frequency': 'Daily'
    })

    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    response = client.post('/habits/pause/1', data={
        'pause_until': today
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'future' in response.data


def test_pause_habit_not_found(client):
    """Pausing a non-existent habit should show an error."""
    register_user(client)

    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
    response = client.post('/habits/pause/999', data={
        'pause_until': future_date
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'not found' in response.data


def test_pause_habit_saves_to_csv(client):
    """Paused status and pause_until date should be persisted in the CSV."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Meditate',
        'description': '10 minutes',
        'frequency': 'Daily'
    })

    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
    client.post('/habits/pause/1', data={'pause_until': future_date})

    test_csv = app_module.tracker.habits_file
    df = pd.read_csv(test_csv)
    assert df.iloc[0]['status'] == 'paused'
    assert df.iloc[0]['pause_until'] == future_date


def test_pause_habit_requires_login(client):
    """Pause route should redirect to login if not authenticated."""
    response = client.post('/habits/pause/1', data={
        'pause_until': '2099-12-31'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


# --- Resume habit ---

def test_resume_habit_success(client):
    """Resuming a paused habit should set its status back to active."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Exercise',
        'description': 'Run daily',
        'frequency': 'Daily'
    })

    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    client.post('/habits/pause/1', data={'pause_until': future_date})

    response = client.post('/habits/resume/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'resumed successfully' in response.data


def test_resume_habit_not_found(client):
    """Resuming a non-existent habit should show an error."""
    register_user(client)
    response = client.post('/habits/resume/999', follow_redirects=True)
    assert response.status_code == 200
    assert b'not found' in response.data


def test_resume_habit_clears_pause_until(client):
    """Resuming should clear the pause_until date in the CSV."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Read',
        'description': '30 minutes',
        'frequency': 'Daily'
    })

    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
    client.post('/habits/pause/1', data={'pause_until': future_date})
    client.post('/habits/resume/1')

    test_csv = app_module.tracker.habits_file
    df = pd.read_csv(test_csv)
    assert df.iloc[0]['status'] == 'active'
    assert pd.isna(df.iloc[0]['pause_until'])


def test_resume_habit_requires_login(client):
    """Resume route should redirect to login if not authenticated."""
    response = client.post('/habits/resume/1', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_auto_resume_expired_pause(client):
    """Habits with expired pause_until dates should auto-resume on load."""
    register_user(client)
    client.post('/habits/add', data={
        'name': 'Yoga',
        'description': 'Morning yoga',
        'frequency': 'Daily'
    })

    # Manually write an expired pause_until into the CSV
    test_csv = app_module.tracker.habits_file
    df = pd.read_csv(test_csv, dtype={'pause_until': object})
    df.loc[0, 'status'] = 'paused'
    df.loc[0, 'pause_until'] = '2000-01-01'
    df.to_csv(test_csv, index=False)

    # Hitting /habits triggers load() which auto-resumes expired pauses
    response = client.get('/habits', follow_redirects=True)
    assert response.status_code == 200

    df = pd.read_csv(test_csv)
    assert df.iloc[0]['status'] == 'active'
    assert pd.isna(df.iloc[0]['pause_until'])
