# Habit Tracking — Web App

A habit tracking web application built with **Python Flask**.

---

## Team Members

- Samruddhi Sonare
- Stuti Patel
- Sandhya Gottimukka

---

## About This Project

This app helps users build and maintain daily habits. This submission includes
the **welcome/landing page** as the starting point. Full features will be added
in future assignments.

---

## Project Structure

```
Habit_Tracking/
│
├── app.py                  # Flask app — runs the server
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── templates/
│   ├── base.html           # Shared layout (navbar, footer)
│   └── index.html          # Welcome / landing page
│
├── static/
│   └── css/
│       └── style.css       # Page styling
│
└── tests/
    └── test_app.py         # pytest tests
```

---

## How To Run

### 1. Install Python 3.12 or higher
```bash
python --version
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

---

## How To Run Tests

```bash
pytest tests/
```

---

## Tech Stack

| Technology | Usage |
|------------|-------|
| Python 3.12 | Backend language |
| Flask | Web framework |
| HTML / CSS | Frontend |
| pytest | Testing |

---

## Planned Features (Coming in Future Assignments)

- User login / sign-up
- Add, edit, delete habits
- Daily check-off and progress tracking
- Categories: Health, Fitness, Learning, Wellness
- Streaks and statistics dashboard
- Database integration with pandas analytics
