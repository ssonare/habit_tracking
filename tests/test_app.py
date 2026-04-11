# Name: Samruddhi, stuti, sandhya
# Date: 04/10/2026
#Automated tests for the Habit Tracking Flask application. Tests cover home page, habit list, add habit form, form validation, and CSV data persistence.

import pytest
import pandas as pd
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Set up a test Flask client with a temporary CSV file."""
    test_csv = str(tmp_path / 'habits.csv')
    test_user = str(tmp_path / 'users.json')
    monkeypatch.setattr('app.HABITS_FILE', test_csv)
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


def test_add_habit_saves_to_csv(client, tmp_path, monkeypatch):
    """Habit data should be persisted in the CSV file."""
    test_csv = str(tmp_path / 'habits.csv')
    test_user = str(tmp_path / 'users.json')
    monkeypatch.setattr('app.HABITS_FILE', test_csv)
    monkeypatch.setattr('app.USERS_FILE', test_user)

    register_user(client)
    client.post('/habits/add', data={
        'name': 'Read Books',
        'description': 'Read for 30 minutes',
        'frequency': 'Daily'
    })

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


def test_delete_habit_removes_from_csv(client, tmp_path, monkeypatch):
    """Deleted habit should no longer exist in the CSV."""
    test_csv = str(tmp_path / 'habits.csv')
    test_user = str(tmp_path / 'users.json')
    monkeypatch.setattr('app.HABITS_FILE', test_csv)
    monkeypatch.setattr('app.USERS_FILE', test_user)

    register_user(client)
    client.post('/habits/add', data={
        'name': 'Journal',
        'description': 'Write daily journal',
        'frequency': 'Daily'
    })

    client.post('/habits/delete/1')

    df = pd.read_csv(test_csv)
    assert len(df) == 0
