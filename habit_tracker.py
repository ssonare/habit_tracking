# Name: Samruddhi, Stuti, Sandhya
# Date: 04/10/2026
# Description: HabitTracker class for managing all habits using pandas for
# data processing and CSV persistence.

import os
from datetime import date
import pandas as pd
from habit import Habit


class HabitTracker:
    """Manages the full collection of habits with CSV-backed persistence."""

    # CSV columns used for storage
    COLUMNS = ['id', 'name', 'description', 'frequency', 'date_added',
               'archived', 'category', 'status', 'pause_until']

    def __init__(self, habits_file='habits.csv'):
        # Path to the CSV file storing all habits
        self.habits_file = habits_file

    def load(self):
        """Load habits from CSV and return a DataFrame with all required columns."""
        if os.path.exists(self.habits_file):
            df = pd.read_csv(self.habits_file)
            # Add missing columns for backward compatibility
            if 'archived' not in df.columns:
                df['archived'] = 0
            if 'category' not in df.columns:
                df['category'] = 'Uncategorized'
            if 'status' not in df.columns:
                df['status'] = 'active'
            if 'pause_until' not in df.columns:
                df['pause_until'] = None
            df['pause_until'] = df['pause_until'].astype(object)

            # Auto-resume habits whose pause period has expired
            today = date.today().strftime('%Y-%m-%d')
            expired_mask = (
                (df['status'] == 'paused') &
                (df['pause_until'].notna()) &
                (df['pause_until'].astype(str) < today)
            )
            if expired_mask.any():
                df.loc[expired_mask, 'status'] = 'active'
                df.loc[expired_mask, 'pause_until'] = None
                self.save(df)

            return df

        return pd.DataFrame(columns=self.COLUMNS)

    def save(self, df):
        """Persist the habits DataFrame to CSV."""
        df.to_csv(self.habits_file, index=False)

    def get_active(self):
        """Return list of non-archived habits as dicts."""
        df = self.load()
        return df[df['archived'] != 1].to_dict(orient='records')

    def get_archived(self):
        """Return list of archived habits as dicts."""
        df = self.load()
        return df[df['archived'] == 1].to_dict(orient='records')

    def add_habit(self, name, description, frequency, category='Uncategorized'):
        """Create and persist a new Habit. Returns the new Habit object."""
        df = self.load()
        new_id = int(df['id'].max()) + 1 if not df.empty else 1
        habit = Habit(new_id, name, description, frequency,
                      category=category)
        df = pd.concat([df, pd.DataFrame([habit.to_dict()])],
                       ignore_index=True)
        self.save(df)
        return habit

    def get_habit(self, habit_id):
        """Return a Habit object by ID, or None if not found."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        row = df.loc[df['id'] == habit_id].iloc[0].to_dict()
        return Habit.from_dict(row)

    def delete_habit(self, habit_id):
        """Delete a habit by ID. Returns habit name or None if not found."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        name = df.loc[df['id'] == habit_id, 'name'].values[0]
        df = df[df['id'] != habit_id]
        self.save(df)
        return name

    def update_habit(self, habit_id, name, description, frequency,
                     category='Uncategorized'):
        """Update fields of an existing habit. Returns updated Habit or None."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        df.loc[df['id'] == habit_id, 'name'] = name
        df.loc[df['id'] == habit_id, 'description'] = description
        df.loc[df['id'] == habit_id, 'frequency'] = frequency
        df.loc[df['id'] == habit_id, 'category'] = (
            category if category else 'Uncategorized'
        )
        self.save(df)
        return self.get_habit(habit_id)

    def archive_habit(self, habit_id):
        """Archive a habit by ID. Returns habit name or None if not found."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        name = df.loc[df['id'] == habit_id, 'name'].values[0]
        df.loc[df['id'] == habit_id, 'archived'] = 1
        self.save(df)
        return name

    def unarchive_habit(self, habit_id):
        """Restore an archived habit. Returns habit name or None if not found."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        name = df.loc[df['id'] == habit_id, 'name'].values[0]
        df.loc[df['id'] == habit_id, 'archived'] = 0
        self.save(df)
        return name

    def pause_habit(self, habit_id, pause_until):
        """Pause a habit until a given date. Returns habit name or None."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        name = df.loc[df['id'] == habit_id, 'name'].values[0]
        df.loc[df['id'] == habit_id, 'status'] = 'paused'
        df.loc[df['id'] == habit_id, 'pause_until'] = pause_until
        self.save(df)
        return name

    def resume_habit(self, habit_id):
        """Resume a paused habit. Returns habit name or None."""
        df = self.load()
        if habit_id not in df['id'].values:
            return None
        name = df.loc[df['id'] == habit_id, 'name'].values[0]
        df.loc[df['id'] == habit_id, 'status'] = 'active'
        df.loc[df['id'] == habit_id, 'pause_until'] = None
        self.save(df)
        return name

    def get_stats(self):
        """Compute and return statistics dict for the stats dashboard."""
        df = self.load()

        if df.empty:
            return {
                'total': 0, 'active': 0, 'completed': 0, 'paused': 0,
                'archived': 0, 'categories': [], 'most_recent': None,
                'oldest': None, 'journey_days': 0, 'active_rate': 0,
                'completed_rate': 0, 'paused_rate': 0, 'total_categories': 0
            }

        total = len(df)
        archived_count = int((df['archived'] == 1).sum())
        active_count = int(
            ((df['archived'] != 1) & (df['status'] == 'active')).sum()
        )
        completed_count = int((df['status'] == 'completed').sum())
        paused_count = int((df['status'] == 'paused').sum())

        # Category breakdown using pandas groupby
        non_archived = df[df['archived'] != 1].copy()
        if not non_archived.empty:
            cat_counts = (
                non_archived.groupby('category')
                .size().reset_index(name='count')
            )
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
            journey_days = int(
                (most_recent_row['date_added']
                 - oldest_row['date_added']).days
            )
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

        total_categories = (
            int(df['category'].nunique()) if 'category' in df.columns else 0
        )

        return {
            'total': total,
            'active': active_count,
            'completed': completed_count,
            'paused': paused_count,
            'archived': archived_count,
            'categories': categories,
            'most_recent': most_recent,
            'oldest': oldest,
            'journey_days': journey_days,
            'active_rate': (
                round(active_count / total * 100, 1) if total > 0 else 0
            ),
            'completed_rate': (
                round(completed_count / total * 100, 1) if total > 0 else 0
            ),
            'paused_rate': (
                round(paused_count / total * 100, 1) if total > 0 else 0
            ),
            'total_categories': total_categories
        }
