# Name: Samruddhi, Stuti, Sandhya
# Date: 04/10/2026
# Description: Habit class representing a single habit entity.

from datetime import date


class Habit:
    """Represents a single habit with its attributes and state."""

    def __init__(self, habit_id, name, description, frequency,
                 date_added=None, archived=0, category='Uncategorized',
                 status='active', pause_until=None):
        # Unique identifier for the habit
        self.habit_id = habit_id
        # Name of the habit
        self.name = name
        # Optional description
        self.description = description
        # Frequency: Daily or Weekly
        self.frequency = frequency
        # Date the habit was created
        self.date_added = date_added or date.today().strftime('%Y-%m-%d')
        # 1 if archived, 0 if not
        self.archived = archived
        # Category label
        self.category = category if category else 'Uncategorized'
        # Status: active, paused, or completed
        self.status = status
        # Date until habit is paused (YYYY-MM-DD string or None)
        self.pause_until = pause_until

    def pause(self, pause_until_date):
        """Pause the habit until a given date string (YYYY-MM-DD)."""
        self.status = 'paused'
        self.pause_until = pause_until_date

    def resume(self):
        """Resume the habit and clear the pause date."""
        self.status = 'active'
        self.pause_until = None

    def archive(self):
        """Mark the habit as archived."""
        self.archived = 1

    def unarchive(self):
        """Restore the habit to active state."""
        self.archived = 0

    def to_dict(self):
        """Convert the Habit to a dictionary for CSV storage."""
        return {
            'id': self.habit_id,
            'name': self.name,
            'description': self.description,
            'frequency': self.frequency,
            'date_added': self.date_added,
            'archived': self.archived,
            'category': self.category,
            'status': self.status,
            'pause_until': self.pause_until,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Habit instance from a dictionary row."""
        return cls(
            habit_id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            frequency=data['frequency'],
            date_added=data.get('date_added'),
            archived=int(data.get('archived', 0)),
            category=data.get('category', 'Uncategorized'),
            status=data.get('status', 'active'),
            pause_until=data.get('pause_until') or None,
        )
