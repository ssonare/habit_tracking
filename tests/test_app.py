import pytest
import pandas as pd
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Set up a test Flask client with a temporary CSV file."""
    test_csv = str(tmp_path / 'habits.csv')
    monkeypatch.setattr('app.HABITS_FILE', test_csv)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


# --- Home page ---

def test_home_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Habit Tracking' in response.data


# --- Habits list page ---

def test_habits_page_loads_empty(client):
    response = client.get('/habits')
    assert response.status_code == 200
    assert b'No habits yet' in response.data


# --- Add habit form ---

def test_add_habit_form_loads(client):
    response = client.get('/habits/add')
    assert response.status_code == 200
    assert b'Add New Habit' in response.data


def test_add_habit_valid_submission(client):
    """Valid form data should save the habit and redirect to /habits."""
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
    response = client.post('/habits/add', data={
        'name': '',
        'description': 'Some description',
        'frequency': 'Daily'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'required' in response.data


def test_add_habit_missing_frequency(client):
    """Submitting without a frequency should show a validation error."""
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
    monkeypatch.setattr('app.HABITS_FILE', test_csv)

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
    response = client.post('/habits/delete/999', follow_redirects=True)
    assert response.status_code == 200
    assert b'not found' in response.data


def test_delete_habit_removes_from_csv(client, tmp_path, monkeypatch):
    """Deleted habit should no longer exist in the CSV."""
    test_csv = str(tmp_path / 'habits.csv')
    monkeypatch.setattr('app.HABITS_FILE', test_csv)

    client.post('/habits/add', data={
        'name': 'Journal',
        'description': 'Write daily journal',
        'frequency': 'Daily'
    })

    client.post('/habits/delete/1')

    df = pd.read_csv(test_csv)
    assert len(df) == 0