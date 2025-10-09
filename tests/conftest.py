# tests/conftest.py

import pytest
from datetime import datetime, timedelta
from habit_tracker.habit import Habit, Periodicity

@pytest.fixture
def sample_habits():
    """Fixture providing a dictionary of sample habits for testing."""
    now = datetime.now()
    
    # Create habits with different periodicities and completion histories
    habits = {
        "Exercise": Habit(
            name="Exercise",
            periodicity=Periodicity.DAILY,
            description="30 min workout"
        ),
        "Read": Habit(
            name="Read",
            periodicity=Periodicity.DAILY,
            description="Read a book chapter"
        ),
        "Weekly Review": Habit(
            name="Weekly Review",
            periodicity=Periodicity.WEEKLY,
            description="Review weekly goals"
        ),
        "Pay Bills": Habit(
            name="Pay Bills",
            periodicity=Periodicity.MONTHLY,
            description="Pay monthly bills"
        ),
        "Meditation": Habit(
            name="Meditation",
            periodicity=Periodicity.DAILY,
            description="10 min meditation"
        )
    }
    
    # Add completion history for each habit
    # Exercise: 10-day streak (completed today)
    for i in range(10):
        habits["Exercise"].complete_habit(now - timedelta(days=i))
    
    # Read: 8-day streak, but missed yesterday
    for i in range(8):
        habits["Read"].complete_habit(now - timedelta(days=i + 1))
    
    # Weekly Review: 3-week streak (completed this week)
    for i in range(3):
        habits["Weekly Review"].complete_habit(now - timedelta(weeks=i))
    
    # Pay Bills: 2-month streak (completed this month)
    for i in range(2):
        habits["Pay Bills"].complete_habit(now - timedelta(days=i * 30))
    
    # Meditation: 5-day streak, but long break since then
    for i in range(5):
        habits["Meditation"].complete_habit(now - timedelta(days=i + 20))
    
    return habits
