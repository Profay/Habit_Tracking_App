from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum

class Periodicity(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Habit:
    """
    Represents a single habit with its attributes and behaviors.
    
    Attributes:
        name (str): The name of the habit
        description (str): Description of the habit
        periodicity (Periodicity): How often the habit should be completed
        creation_date (datetime): When the habit was created
        completion_history (List[datetime]): List of completion timestamps
    """
    
    def __init__(self, name: str, description: str, periodicity: Periodicity, 
                 creation_date: Optional[datetime] = None):
        """
        Initialize a new Habit instance.
        
        Args:
            name: Name of the habit
            description: Description of what the habit entails
            periodicity: How often the habit should be completed
            creation_date: When the habit was created (defaults to now)
        """
        self.name = name
        self.description = description
        self.periodicity = periodicity
        self.creation_date = creation_date or datetime.now()
        self.completion_history: List[datetime] = []
    
    def check_off(self, completion_time: Optional[datetime] = None) -> None:
        """
        Mark the habit as completed at a specific time.
        
        Args:
            completion_time: When the habit was completed (defaults to now)
        """
        if completion_time is None:
            completion_time = datetime.now()
        
        # Check if already completed for this period
        if not self._is_already_completed_in_period(completion_time):
            self.completion_history.append(completion_time)
            self.completion_history.sort()  # Keep history sorted
        else:
            raise ValueError(f"Habit '{self.name}' already completed for this {self.periodicity.value} period")
    
    def _is_already_completed_in_period(self, check_time: datetime) -> bool:
        """
        Check if the habit was already completed in the given period.
        
        Args:
            check_time: The time to check against
            
        Returns:
            bool: True if already completed in this period
        """
        if not self.completion_history:
            return False
        
        # Get the most recent completion
        last_completion = max(self.completion_history)
        
        # Check if last completion is in the same period as check_time
        if self.periodicity == Periodicity.DAILY:
            return last_completion.date() == check_time.date()
        elif self.periodicity == Periodicity.WEEKLY:
            # Get Monday of the week for both dates
            last_week_start = last_completion - timedelta(days=last_completion.weekday())
            check_week_start = check_time - timedelta(days=check_time.weekday())
            return last_week_start.date() == check_week_start.date()
        elif self.periodicity == Periodicity.MONTHLY:
            return (last_completion.year == check_time.year and 
                   last_completion.month == check_time.month)
        elif self.periodicity == Periodicity.YEARLY:
            return last_completion.year == check_time.year
        
        return False
    
    def calculate_current_streak(self) -> int:
        """
        Calculate the current streak of consecutive completed periods.
        
        Returns:
            int: Number of consecutive periods completed
        """
        if not self.completion_history:
            return 0
        
        # Sort completions in descending order
        sorted_completions = sorted(self.completion_history, reverse=True)
        
        streak = 0
        current_period_start = self._get_period_start(datetime.now())
        
        for completion in sorted_completions:
            completion_period_start = self._get_period_start(completion)
            
            if completion_period_start == current_period_start:
                streak += 1
                current_period_start = self._get_previous_period_start(current_period_start)
            elif completion_period_start < current_period_start:
                # Found a gap, streak is broken
                break
        
        return streak
    
    def calculate_longest_streak(self) -> int:
        """
        Calculate the longest streak ever achieved for this habit.
        
        Returns:
            int: Maximum number of consecutive periods completed
        """
        if not self.completion_history:
            return 0
        
        # Group completions by period
        periods = set()
        for completion in self.completion_history:
            period_start = self._get_period_start(completion)
            periods.add(period_start)
        
        # Sort periods in descending order
        sorted_periods = sorted(periods, reverse=True)
        
        max_streak = 0
        current_streak = 0
        expected_period = self._get_period_start(datetime.now())
        
        for period in sorted_periods:
            if period == expected_period:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
                expected_period = self._get_previous_period_start(expected_period)
            elif period < expected_period:
                # Gap found, reset streak
                current_streak = 1
                max_streak = max(max_streak, current_streak)
                expected_period = self._get_previous_period_start(period)
        
        return max_streak
    
    def is_broken(self, check_date: Optional[datetime] = None) -> bool:
        """
        Check if the habit is currently broken (missed in the last period).
        
        Args:
            check_date: Date to check from (defaults to now)
            
        Returns:
            bool: True if habit is broken
        """
        if check_date is None:
            check_date = datetime.now()
        
        if not self.completion_history:
            # If habit was created more than one period ago and never completed
            return self._is_more_than_one_period_old(self.creation_date, check_date)
        
        # Check if the most recent completion was in the current or previous period
        last_completion = max(self.completion_history)
        last_period_start = self._get_period_start(last_completion)
        current_period_start = self._get_period_start(check_date)
        
        return last_period_start < current_period_start
    
    def _get_period_start(self, date_time: datetime) -> datetime:
        """
        Get the start of the period for a given datetime.
        
        Args:
            date_time: The datetime to get period start for
            
        Returns:
            datetime: Start of the period
        """
        if self.periodicity == Periodicity.DAILY:
            return datetime(date_time.year, date_time.month, date_time.day)
        elif self.periodicity == Periodicity.WEEKLY:
            # Monday of the week
            monday = date_time - timedelta(days=date_time.weekday())
            return datetime(monday.year, monday.month, monday.day)
        elif self.periodicity == Periodicity.MONTHLY:
            return datetime(date_time.year, date_time.month, 1)
        elif self.periodicity == Periodicity.YEARLY:
            return datetime(date_time.year, 1, 1)
        
        return date_time
    
    def _get_previous_period_start(self, period_start: datetime) -> datetime:
        """
        Get the start of the previous period.
        
        Args:
            period_start: Start of current period
            
        Returns:
            datetime: Start of previous period
        """
        if self.periodicity == Periodicity.DAILY:
            return period_start - timedelta(days=1)
        elif self.periodicity == Periodicity.WEEKLY:
            return period_start - timedelta(weeks=1)
        elif self.periodicity == Periodicity.MONTHLY:
            if period_start.month == 1:
                return datetime(period_start.year - 1, 12, 1)
            else:
                return datetime(period_start.year, period_start.month - 1, 1)
        elif self.periodicity == Periodicity.YEARLY:
            return datetime(period_start.year - 1, 1, 1)
        
        return period_start
    
    def _is_more_than_one_period_old(self, creation_date: datetime, check_date: datetime) -> bool:
        """
        Check if a date is more than one period old from another date.
        
        Args:
            creation_date: The earlier date
            check_date: The later date
            
        Returns:
            bool: True if more than one period has passed
        """
        creation_period = self._get_period_start(creation_date)
        check_period = self._get_period_start(check_date)
        
        return self._get_previous_period_start(check_period) >= creation_period
    
    def to_dict(self) -> dict:
        """
        Convert habit to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of habit
        """
        return {
            'name': self.name,
            'description': self.description,
            'periodicity': self.periodicity.value,
            'creation_date': self.creation_date.isoformat(),
            'completion_history': [dt.isoformat() for dt in self.completion_history]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Habit':
        """
        Create habit from dictionary.
        
        Args:
            data: Dictionary containing habit data
            
        Returns:
            Habit: New habit instance
        """
        habit = cls(
            name=data['name'],
            description=data['description'],
            periodicity=Periodicity(data['periodicity']),
            creation_date=datetime.fromisoformat(data['creation_date'])
        )
        
        habit.completion_history = [
            datetime.fromisoformat(dt_str) for dt_str in data['completion_history']
        ]
        
        return habit
    
    def __str__(self) -> str:
        """String representation of the habit."""
        return f"Habit: {self.name} ({self.periodicity.value}) - Current Streak: {self.calculate_current_streak()}"
    
    def __repr__(self) -> str:
        """Official string representation of the habit."""
        return f"Habit(name='{self.name}', periodicity={self.periodicity.value}, completions={len(self.completion_history)})"