# Habit Tracking — Web App

Habit Tracker is a Python Flask-based web application designed to help users build and maintain meaningful daily habits. Whether you're working on your fitness, mental wellness, or personal growth, the app lets you create and organize habits by category and priority, mark them as complete each day, and monitor your progress through streaks and statistics. With a clean, browser-based interface and a dedicated analytics page powered by pandas, staying consistent has never been more straightforward.

---

## Team Members

- Samruddhi Sonare
- Stuti Patel
- Sandhya Gottimukka

---

## About This Project

This Habit Tracking application was developed as part of a collaborative academic project by Group 9. The goal was to design and build a fully functional, Python-based web application that solves a real-world problem — helping people stay consistent with their daily habits and personal goals.
The application is built using Flask as the web framework, giving users a clean and interactive browser-based experience. Habits can be created, categorized, prioritized, and tracked on a day-to-day basis. A dedicated statistics page powered by pandas provides meaningful insights such as completion rates, category breakdowns, and streak tracking — turning raw habit data into actionable progress reports.
Behind the scenes, the app is structured around two core classes — Habit and HabitTracker — with data persisted through a local JSON file, ensuring nothing is lost between sessions. The project also includes a suite of automated pytest tests to ensure reliability across key features.
This project was built by three team members — Sandhya Gottimukkala, Stuti Patel, and Samruddhi Sonare — who collaborated through weekly Zoom check-ins, a shared Trello board, and a structured deadline management strategy to bring the application to life.

---

## Project Structure

```
Habit_Tracking/
│
├── app.py                  # Flask app — routes, login, habit management
├── conftest.py             # Pytest path configuration
├── requirements.txt        # Python dependencies
├── habits.csv              # Habit data storage
├── users.json              # User account storage
├── .gitignore
│
├── templates/
│   ├── base.html           # Shared layout (navbar, footer)
│   ├── index.html          # Welcome / landing page
│   ├── login.html          # User login page
│   ├── register.html       # User registration page
│   ├── habits.html         # Habit list page
│   └── add_habit.html      # Add new habit form
│
├── static/
│   └── css/
│       └── style.css       # Page styling
│
├── tests/
│   └── test_app.py         # pytest tests
│
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI pipeline

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
|pandas | Habit data processing and storage |
| Flask-Login | User authentication |
| flake8 | Code linting |

---

## Branch Strategy

We use two protected branches:

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready code only |
| `develop` | Active development and testing |

**Rules (apply to both `main` and `develop`):**
- No one can push code directly to `main` or `develop`
- All changes must be made on a separate feature branch (e.g. `feature/add-login`)
- A Pull Request must be opened to merge into `develop` or `main`
- **2 team members must approve** the Pull Request before it can be merged

**Workflow:**
1. Create a feature branch from `develop`
2. Make changes and push to your feature branch
3. Open a Pull Request → `develop`
4. Get 2 approvals → merge into `develop`
5. Once stable → open a Pull Request → `main`

---

## Project Tracking

We track tasks, progress, and assignments on our Trello board:
[https://trello.com/b/qLoWOtQb/habit-tracker](https://trello.com/b/qLoWOtQb/habit-tracker)

All team members should update the board when starting or completing a task.

---

## CI/CD Pipeline

We plan to set up a GitHub Actions pipeline that will automatically run on every push:

| Step | Tool | Purpose |
|------|------|---------|
| Lint | `flake8` | Check Python code for errors and style issues |
| Test | `pytest` | Run all automated tests |
| Security Scan | `Trivy` | Check for known vulnerabilities |

The pipeline will run automatically — no manual steps needed.

---

## Planned Features (Coming in Future Assignments)

- edit habits
- Daily check-off and progress tracking
- Categories: Health, Fitness, Learning, Wellness
- Streaks and statistics dashboard
- Database integration with pandas analytics
