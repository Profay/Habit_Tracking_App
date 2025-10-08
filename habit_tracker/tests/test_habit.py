# test_habit.py

"""
Unit tests for the Habit class and Periodicity enum.

This test suite covers:
- Habit initialization and attributes
- Check-off functionality for all periodicities
- Streak calculations (current and longest)
- Habit status (broken/not broken)
- Period calculations and edge cases
- Serialization (to_dict/from_dict)
- String representations
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from habit import Habit, Periodicity

class TestPeriodicity:
    """Test the Periodicity enum."""
    
    def test_periodicity_values(self):
        """Test that all periodicity values are correct."""
        assert Periodicity.DAILY.value == "daily"
        assert Periodicity.WEEKLY.value == "weekly"
        assert Periodicity.MONTHLY.value == "monthly"
        assert Periodicity.YEARLY.value == "yearly"
    
    def test_periodicity_creation(self):
        """Test creating Periodicity from string."""
        assert Periodicity("daily") == Periodicity.DAILY
        assert Periodicity("weekly") == Periodicity.WEEKLY
        assert Periodicity("monthly") == Periodicity.MONTHLY
        assert Periodicity("yearly") == Periodicity.YEARLY
    
    def test_periodicity_invalid(self):
        """Test creating Periodicity with invalid value."""
        with pytest.raises(ValueError):
            Periodicity("invalid")

class TestHabitInitialization:
    """Test Habit class initialization."""
    
    def test_habit_creation_full(self):
        """Test creating a habit with all parameters."""
        creation_date = datetime(2024, 1, 1, 12, 0, 0)
        habit = Habit(
            name="Exercise",
            description="30 minutes of workout",
            periodicity=Periodicity.DAILY,
            creation_date=creation_date
        )
        
        assert habit.name == "Exercise"
        assert habit.description == "30 minutes of workout"
        assert habit.periodicity == Periodicity.DAILY
        assert habit.creation_date == creation_date
        assert habit.completion_history == []
    
    def test_habit_creation_default_date(self):
        """Test creating a habit with default creation date."""
        before_creation = datetime.now()
        habit = Habit(
            name="Read",
            description="Read for 20 minutes",
            periodicity=Periodicity.DAILY
        )
        after_creation = datetime.now()
        
        assert habit.name == "Read"
        assert habit.description == "Read for 20 minutes"
        assert habit.periodicity == Periodicity.DAILY
        assert before_creation <= habit.creation_date <= after_creation
        assert habit.completion_history == []
    
    def test_habit_creation_weekly(self):
        """Test creating a weekly habit."""
        habit = Habit(
            name="Grocery Shopping",
            description="Buy weekly groceries",
            periodicity=Periodicity.WEEKLY
        )
        
        assert habit.periodicity == Periodicity.WEEKLY
        assert habit.completion_history == []
    
    def test_habit_creation_monthly(self):
        """Test creating a monthly habit."""
        habit = Habit(
            name="Pay Bills",
            description="Pay monthly bills",
            periodicity=Periodicity.MONTHLY
        )
        
        assert habit.periodicity == Periodicity.MONTHLY
        assert habit.completion_history == []
    
    def test_habit_creation_yearly(self):
        """Test creating a yearly habit."""
        habit = Habit(
            name="Dentist Visit",
            description="Annual dental checkup",
            periodicity=Periodicity.YEARLY
        )
        
        assert habit.periodicity == Periodicity.YEARLY
        assert habit.completion_history == []

class TestHabitCheckOff:
    """Test habit check-off functionality."""
    
    @pytest.fixture
    def daily_habit(self):
        """Create a daily habit for testing."""
        return Habit(
            name="Exercise",
            description="Daily workout",
            periodicity=Periodicity.DAILY,
            creation_date=datetime(2024, 1, 1)
        )
    
    @pytest.fixture
    def weekly_habit(self):
        """Create a weekly habit for testing."""
        return Habit(
            name="Weekly Review",
            description="Review weekly progress",
            periodicity=Periodicity.WEEKLY,
            creation_date=datetime(2024, 1, 1)
        )
    
    @pytest.fixture
    def monthly_habit(self):
        """Create a monthly habit for testing."""
        return Habit(
            name="Pay Rent",
            description="Monthly rent payment",
            periodicity=Periodicity.MONTHLY,
            creation_date=datetime(2024, 1, 1)
        )
    
    @pytest.fixture
    def yearly_habit(self):
        """Create a yearly habit for testing."""
        return Habit(
            name="Birthday",
            description="Annual celebration",
            periodicity=Periodicity.YEARLY,
            creation_date=datetime(2020, 1, 1)
        )
    
    def test_check_off_daily_default_time(self, daily_habit):
        """Test checking off a daily habit with default time."""
        before_check = datetime.now()
        daily_habit.check_off()
        after_check = datetime.now()
        
        assert len(daily_habit.completion_history) == 1
        assert before_check <= daily_habit.completion_history[0] <= after_check
    
    def test_check_off_daily_specific_time(self, daily_habit):
        """Test checking off a daily habit with specific time."""
        check_time = datetime(2024, 1, 15, 10, 30, 0)
        daily_habit.check_off(check_time)
        
        assert len(daily_habit.completion_history) == 1
        assert daily_habit.completion_history[0] == check_time
    
    def test_check_off_daily_duplicate_same_day(self, daily_habit):
        """Test that duplicate daily check-offs are prevented."""
        check_time = datetime(2024, 1, 15, 10, 0, 0)
        daily_habit.check_off(check_time)
        
        with pytest.raises(ValueError, match="already completed for this daily period"):
            daily_habit.check_off(datetime(2024, 1, 15, 18, 0, 0))
        
        assert len(daily_habit.completion_history) == 1
    
    def test_check_off_daily_different_days(self, daily_habit):
        """Test checking off daily habit on different days."""
        daily_habit.check_off(datetime(2024, 1, 15))
        daily_habit.check_off(datetime(2024, 1, 16))
        
        assert len(daily_habit.completion_history) == 2
        assert daily_habit.completion_history[0].date() == datetime(2024, 1, 15).date()
        assert daily_habit.completion_history[1].date() == datetime(2024, 1, 16).date()
    
    def test_check_off_weekly_same_week(self, weekly_habit):
        """Test that duplicate weekly check-offs are prevented."""
        # Monday and Wednesday of same week
        weekly_habit.check_off(datetime(2024, 1, 15))  # Monday
        with pytest.raises(ValueError, match="already completed for this weekly period"):
            weekly_habit.check_off(datetime(2024, 1, 17))  # Wednesday
        
        assert len(weekly_habit.completion_history) == 1
    
    def test_check_off_weekly_different_weeks(self, weekly_habit):
        """Test checking off weekly habit in different weeks."""
        weekly_habit.check_off(datetime(2024, 1, 15))  # Monday week 1
        weekly_habit.check_off(datetime(2024, 1, 22))  # Monday week 2
        
        assert len(weekly_habit.completion_history) == 2
    
    def test_check_off_monthly_same_month(self, monthly_habit):
        """Test that duplicate monthly check-offs are prevented."""
        monthly_habit.check_off(datetime(2024, 1, 15))
        with pytest.raises(ValueError, match="already completed for this monthly period"):
            monthly_habit.check_off(datetime(2024, 1, 20))
        
        assert len(monthly_habit.completion_history) == 1
    
    def test_check_off_monthly_different_months(self, monthly_habit):
        """Test checking off monthly habit in different months."""
        monthly_habit.check_off(datetime(2024, 1, 15))
        monthly_habit.check_off(datetime(2024, 2, 15))
        
        assert len(monthly_habit.completion_history) == 2
    
    def test_check_off_yearly_same_year(self, yearly_habit):
        """Test that duplicate yearly check-offs are prevented."""
        yearly_habit.check_off(datetime(2024, 1, 15))
        with pytest.raises(ValueError, match="already completed for this yearly period"):
            yearly_habit.check_off(datetime(2024, 6, 15))
        
        assert len(yearly_habit.completion_history) == 1
    
    def test_check_off_yearly_different_years(self, yearly_habit):
        """Test checking off yearly habit in different years."""
        yearly_habit.check_off(datetime(2024, 1, 15))
        yearly_habit.check_off(datetime(2025, 1, 15))
        
        assert len(yearly_habit.completion_history) == 2
    
    def test_check_off_maintains_sorted_order(self, daily_habit):
        """Test that completion history remains sorted."""
        daily_habit.check_off(datetime(2024, 1, 15))
        daily_habit.check_off(datetime(2024, 1, 13))
        daily_habit.check_off(datetime(2024, 1, 14))
        
        assert len(daily_habit.completion_history) == 3
        assert daily_habit.completion_history[0] == datetime(2024, 1, 13)
        assert daily_habit.completion_history[1] == datetime(2024, 1, 14)
        assert daily_habit.completion_history[2] == datetime(2024, 1, 15)

class TestHabitStreaks:
    """Test habit streak calculations."""
    
    @pytest.fixture
    def daily_habit(self):
        """Create a daily habit for testing."""
        return Habit(
            name="Exercise",
            description="Daily workout",
            periodicity=Periodicity.DAILY,
            creation_date=datetime(2024, 1, 1)
        )
    
    def test_current_streak_no_completions(self, daily_habit):
        """Test current streak with no completions."""
        assert daily_habit.calculate_current_streak() == 0
    
    def test_current_streak_one_completion(self, daily_habit):
        """Test current streak with one completion."""
        daily_habit.check_off(datetime(2024, 1, 15))
        assert daily_habit.calculate_current_streak() == 1
    
    def test_current_streak_consecutive_days(self, daily_habit):
        """Test current streak with consecutive days."""
        for i in range(5):
            daily_habit.check_off(datetime(2024, 1, 15 - i))
        assert daily_habit.calculate_current_streak() == 5
    
    def test_current_streak_broken(self, daily_habit):
        """Test current streak when broken."""
        daily_habit.check_off(datetime(2024, 1, 15))
        daily_habit.check_off(datetime(2024, 1, 14))
        # Skip Jan 13
        daily_habit.check_off(datetime(2024, 1, 12))
        
        assert daily_habit.calculate_current_streak() == 2  # Only Jan 14-15
    
    def test_current_streak_with_future_check(self, daily_habit):
        """Test current streak with future completion time."""
        future_time = datetime.now() + timedelta(days=1)
        daily_habit.check_off(future_time)
        
        assert daily_habit.calculate_current_streak() == 1
    
    def test_longest_streak_no_completions(self, daily_habit):
        """Test longest streak with no completions."""
        assert daily_habit.calculate_longest_streak() == 0
    
    def test_longest_streak_single_period(self, daily_habit):
        """Test longest streak with single completion."""
        daily_habit.check_off(datetime(2024, 1, 15))
        assert daily_habit.calculate_longest_streak() == 1
    
    def test_longest_streak_multiple_periods(self, daily_habit):
        """Test longest streak with multiple consecutive periods."""
        for i in range(10):
            daily_habit.check_off(datetime(2024, 1, 15 - i))
        assert daily_habit.calculate_longest_streak() == 10
    
    def test_longest_streak_with_breaks(self, daily_habit):
        """Test longest streak with breaks in between."""
        # First streak: 3 days
        daily_habit.check_off(datetime(2024, 1, 10))
        daily_habit.check_off(datetime(2024, 1, 9))
        daily_habit.check_off(datetime(2024, 1, 8))
        
        # Break
        # Second streak: 5 days
        daily_habit.check_off(datetime(2024, 1, 5))
        daily_habit.check_off(datetime(2024, 1, 4))
        daily_habit.check_off(datetime(2024, 1, 3))
        daily_habit.check_off(datetime(2024, 1, 2))
        daily_habit.check_off(datetime(2024, 1, 1))
        
        assert daily_habit.calculate_longest_streak() == 5
    
    def test_weekly_streak_calculation(self):
        """Test streak calculation for weekly habits."""
        habit = Habit(
            name="Weekly Review",
            description="Weekly progress review",
            periodicity=Periodicity.WEEKLY,
            creation_date=datetime(2024, 1, 1)
        )
        
        # Complete 3 consecutive weeks
        habit.check_off(datetime(2024, 1, 15))  # Monday week 3
        habit.check_off(datetime(2024, 1, 8))   # Monday week 2
        habit.check_off(datetime(2024, 1, 1))   # Monday week 1
        
        assert habit.calculate_current_streak() == 3
        assert habit.calculate_longest_streak() == 3
    
    def test_monthly_streak_calculation(self):
        """Test streak calculation for monthly habits."""
        habit = Habit(
            name="Pay Rent",
            description="Monthly rent payment",
            periodicity=Periodicity.MONTHLY,
            creation_date=datetime(2023, 12, 1)
        )
        
        # Complete 3 consecutive months
        habit.check_off(datetime(2024, 3, 1))
        habit.check_off(datetime(2024, 2, 1))
        habit.check_off(datetime(2024, 1, 1))
        
        assert habit.calculate_current_streak() == 3
        assert habit.calculate_longest_streak() == 3
    
    def test_yearly_streak_calculation(self):
        """Test streak calculation for yearly habits."""
        habit = Habit(
            name="Annual Checkup",
            description="Annual health checkup",
            periodicity=Periodicity.YEARLY,
            creation_date=datetime(2020, 1, 1)
        )
        
        # Complete 3 consecutive years
        habit.check_off(datetime(2024, 1, 1))
        habit.check_off(datetime(2023, 1, 1))
        habit.check_off(datetime(2022, 1, 1))
        
        assert habit.calculate_current_streak() == 3
        assert habit.calculate_longest_streak() == 3

class TestHabitStatus:
    """Test habit status methods."""
    
    @pytest.fixture
    def daily_habit(self):
        """Create a daily habit for testing."""
        return Habit(
            name="Exercise",
            description="Daily workout",
            periodicity=Periodicity.DAILY,
            creation_date=datetime(2024, 1, 1)
        )
    
    def test_is_broken_no_completions_old_habit(self, daily_habit):
        """Test is_broken for old habit with no completions."""
        # Habit created more than 1 day ago, no completions
        check_date = datetime(2024, 1, 3)
        assert daily_habit.is_broken(check_date) == True
    
    def test_is_broken_no_completions_new_habit(self, daily_habit):
        """Test is_broken for new habit with no completions."""
        # Habit created today, no completions
        check_date = datetime(2024, 1, 1, 12, 0, 0)
        assert daily_habit.is_broken(check_date) == False
    
    def test_is_broken_completed_today(self, daily_habit):
        """Test is_broken when completed today."""
        daily_habit.check_off(datetime(2024, 1, 15, 10, 0, 0))
        assert daily_habit.is_broken(datetime(2024, 1, 15, 18, 0, 0)) == False
    
    def test_is_broken_missed_today(self, daily_habit):
        """Test is_broken when missed today."""
        daily_habit.check_off(datetime(2024, 1, 14))
        assert daily_habit.is_broken(datetime(2024, 1, 15, 18, 0, 0)) == True
    
    def test_is_broken_weekly_completed_this_week(self):
        """Test is_broken for weekly habit completed this week."""
        habit = Habit(
            name="Weekly Review",
            description="Weekly review",
            periodicity=Periodicity.WEEKLY,
            creation_date=datetime(2024, 1, 1)
        )
        
        # Completed on Monday of this week
        habit.check_off(datetime(2024, 1, 15))  # Monday
        assert habit.is_broken(datetime(2024, 1, 17)) == False  # Wednesday
    
    def test_is_broken_weekly_missed_this_week(self):
        """Test is_broken for weekly habit missed this week."""
        habit = Habit(
            name="Weekly Review",
            description="Weekly review",
            periodicity=Periodicity.WEEKLY,
            creation_date=datetime(2024, 1, 1)
        )
        
        # Completed last week
        habit.check_off(datetime(2024, 1, 8))  # Monday last week
        assert habit.is_broken(datetime(2024, 1, 17)) == True  # Wednesday this week
    
    def test_is_broken_monthly_completed_this_month(self):
        """Test is_broken for monthly habit completed this month."""
        habit = Habit(
            name="Pay Rent",
            description="Monthly rent",
            periodicity=Periodicity.MONTHLY,
            creation_date=datetime(2024, 1, 1)
        )
        
        habit.check_off(datetime(2024, 1, 15))
        assert habit.is_broken(datetime(2024, 1, 20)) == False
    
    def test_is_broken_monthly_missed_this_month(self):
        """Test is_broken for monthly habit missed this month."""
        habit = Habit(
            name="Pay Rent",
            description="Monthly rent",
            periodicity=Periodicity.MONTHLY,
            creation_date=datetime(2023, 12, 1)
        )
        
        habit.check_off(datetime(2023, 12, 15))
        assert habit.is_broken(datetime(2024, 1, 20)) == True

class TestHabitPeriodCalculations:
    """Test period calculation helper methods."""
    
    def test_get_period_start_daily(self):
        """Test _get_period_start for daily habits."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        test_time = datetime(2024, 1, 15, 14, 30, 45)
        period_start = habit._get_period_start(test_time)
        
        assert period_start == datetime(2024, 1, 15, 0, 0, 0)
    
    def test_get_period_start_weekly(self):
        """Test _get_period_start for weekly habits."""
        habit = Habit("Test", "Test", Periodicity.WEEKLY)
        
        # Wednesday
        test_time = datetime(2024, 1, 17, 14, 30, 45)
        period_start = habit._get_period_start(test_time)
        
        # Should be Monday of that week
        assert period_start == datetime(2024, 1, 15, 0, 0, 0)
        
        # Monday
        test_time = datetime(2024, 1, 15, 8, 0, 0)
        period_start = habit._get_period_start(test_time)
        assert period_start == datetime(2024, 1, 15, 0, 0, 0)
        
        # Sunday
        test_time = datetime(2024, 1, 21, 23, 59, 59)
        period_start = habit._get_period_start(test_time)
        assert period_start == datetime(2024, 1, 15, 0, 0, 0)
    
    def test_get_period_start_monthly(self):
        """Test _get_period_start for monthly habits."""
        habit = Habit("Test", "Test", Periodicity.MONTHLY)
        
        test_time = datetime(2024, 1, 15, 14, 30, 45)
        period_start = habit._get_period_start(test_time)
        
        assert period_start == datetime(2024, 1, 1, 0, 0, 0)
        
        test_time = datetime(2024, 12, 31, 23, 59, 59)
        period_start = habit._get_period_start(test_time)
        assert period_start == datetime(2024, 12, 1, 0, 0, 0)
    
    def test_get_period_start_yearly(self):
        """Test _get_period_start for yearly habits."""
        habit = Habit("Test", "Test", Periodicity.YEARLY)
        
        test_time = datetime(2024, 6, 15, 14, 30, 45)
        period_start = habit._get_period_start(test_time)
        
        assert period_start == datetime(2024, 1, 1, 0, 0, 0)
    
    def test_get_previous_period_start_daily(self):
        """Test _get_previous_period_start for daily habits."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        current_period = datetime(2024, 1, 15, 0, 0, 0)
        previous_period = habit._get_previous_period_start(current_period)
        
        assert previous_period == datetime(2024, 1, 14, 0, 0, 0)
    
    def test_get_previous_period_start_weekly(self):
        """Test _get_previous_period_start for weekly habits."""
        habit = Habit("Test", "Test", Periodicity.WEEKLY)
        
        current_period = datetime(2024, 1, 15, 0, 0, 0)  # Monday
        previous_period = habit._get_previous_period_start(current_period)
        
        assert previous_period == datetime(2024, 1, 8, 0, 0, 0)  # Previous Monday
    
    def test_get_previous_period_start_monthly(self):
        """Test _get_previous_period_start for monthly habits."""
        habit = Habit("Test", "Test", Periodicity.MONTHLY)
        
        current_period = datetime(2024, 2, 1, 0, 0, 0)
        previous_period = habit._get_previous_period_start(current_period)
        
        assert previous_period == datetime(2024, 1, 1, 0, 0, 0)
        
        # Test year transition
        current_period = datetime(2024, 1, 1, 0, 0, 0)
        previous_period = habit._get_previous_period_start(current_period)
        
        assert previous_period == datetime(2023, 12, 1, 0, 0, 0)
    
    def test_get_previous_period_start_yearly(self):
        """Test _get_previous_period_start for yearly habits."""
        habit = Habit("Test", "Test", Periodicity.YEARLY)
        
        current_period = datetime(2024, 1, 1, 0, 0, 0)
        previous_period = habit._get_previous_period_start(current_period)
        
        assert previous_period == datetime(2023, 1, 1, 0, 0, 0)
    
    def test_leap_year_handling(self):
        """Test period calculations handle leap years correctly."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        # Feb 28 in leap year
        test_time = datetime(2024, 2, 28, 12, 0, 0)
        period_start = habit._get_period_start(test_time)
        assert period_start == datetime(2024, 2, 28, 0, 0, 0)
        
        # Feb 29 in leap year
        test_time = datetime(2024, 2, 29, 12, 0, 0)
        period_start = habit._get_period_start(test_time)
        assert period_start == datetime(2024, 2, 29, 0, 0, 0)
        
        # Mar 1 in leap year
        test_time = datetime(2024, 3, 1, 12, 0, 0)
        period_start = habit._get_period_start(test_time)
        assert period_start == datetime(2024, 3, 1, 0, 0, 0)

class TestHabitSerialization:
    """Test habit serialization methods."""
    
    @pytest.fixture
    def habit_with_data(self):
        """Create a habit with completion data."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity=Periodicity.DAILY,
            creation_date=datetime(2024, 1, 1, 10, 0, 0)
        )
        
        habit.check_off(datetime(2024, 1, 15, 9, 0, 0))
        habit.check_off(datetime(2024, 1, 14, 8, 30, 0))
        
        return habit
    
    def test_to_dict(self, habit_with_data):
        """Test converting habit to dictionary."""
        data = habit_with_data.to_dict()
        
        assert data['name'] == "Exercise"
        assert data['description'] == "30 min workout"
        assert data['periodicity'] == "daily"
        assert data['creation_date'] == "2024-01-01T10:00:00"
        assert len(data['completion_history']) == 2
        assert "2024-01-15T09:00:00" in data['completion_history']
        assert "2024-01-14T08:30:00" in data['completion_history']
    
    def test_from_dict(self):
        """Test creating habit from dictionary."""
        data = {
            'name': 'Read',
            'description': 'Read for 20 minutes',
            'periodicity': 'weekly',
            'creation_date': '2024-01-01T10:00:00',
            'completion_history': [
                '2024-01-15T09:00:00',
                '2024-01-08T09:00:00'
            ]
        }
        
        habit = Habit.from_dict(data)
        
        assert habit.name == "Read"
        assert habit.description == "Read for 20 minutes"
        assert habit.periodicity == Periodicity.WEEKLY
        assert habit.creation_date == datetime(2024, 1, 1, 10, 0, 0)
        assert len(habit.completion_history) == 2
        assert datetime(2024, 1, 15, 9, 0, 0) in habit.completion_history
        assert datetime(2024, 1, 8, 9, 0, 0) in habit.completion_history
    
    def test_round_trip_serialization(self, habit_with_data):
        """Test that to_dict/from_dict preserves all data."""
        # Convert to dict
        data = habit_with_data.to_dict()
        
        # Create new habit from dict
        new_habit = Habit.from_dict(data)
        
        # Check all attributes match
        assert new_habit.name == habit_with_data.name
        assert new_habit.description == habit_with_data.description
        assert new_habit.periodicity == habit_with_data.periodicity
        assert new_habit.creation_date == habit_with_data.creation_date
        assert len(new_habit.completion_history) == len(habit_with_data.completion_history)
        
        for completion in habit_with_data.completion_history:
            assert completion in new_habit.completion_history
    
    def test_from_dict_empty_completion_history(self):
        """Test from_dict with empty completion history."""
        data = {
            'name': 'New Habit',
            'description': 'A new habit',
            'periodicity': 'daily',
            'creation_date': '2024-01-01T10:00:00',
            'completion_history': []
        }
        
        habit = Habit.from_dict(data)
        assert habit.completion_history == []
    
    def test_from_dict_missing_completion_history(self):
        """Test from_dict with missing completion_history key."""
        data = {
            'name': 'New Habit',
            'description': 'A new habit',
            'periodicity': 'daily',
            'creation_date': '2024-01-01T10:00:00'
        }
        
        habit = Habit.from_dict(data)
        assert habit.completion_history == []

class TestHabitStringRepresentations:
    """Test habit string representation methods."""
    
    def test_str_representation(self):
        """Test __str__ method."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity=Periodicity.DAILY,
            creation_date=datetime(2024, 1, 1)
        )
        
        habit.check_off(datetime(2024, 1, 15))
        habit.check_off(datetime(2024, 1, 14))
        
        str_repr = str(habit)
        
        assert "Habit: Exercise" in str_repr
        assert "(daily)" in str_repr
        assert "Current Streak: 2" in str_repr
    
    def test_str_representation_no_completions(self):
        """Test __str__ method with no completions."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity=Periodicity.DAILY
        )
        
        str_repr = str(habit)
        
        assert "Habit: Exercise" in str_repr
        assert "(daily)" in str_repr
        assert "Current Streak: 0" in str_repr
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity=Periodicity.DAILY
        )
        
        habit.check_off(datetime(2024, 1, 15))
        
        repr_str = repr(habit)
        
        assert "Habit(" in repr_str
        assert "name='Exercise'" in repr_str
        assert "periodicity=daily" in repr_str
        assert "completions=1" in repr_str

class TestHabitEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_check_off_with_none_time(self):
        """Test checking off with None time (should use current time)."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        before = datetime.now()
        habit.check_off(None)
        after = datetime.now()
        
        assert len(habit.completion_history) == 1
        assert before <= habit.completion_history[0] <= after
    
    def test_habit_created_at_midnight(self):
        """Test habit created exactly at midnight."""
        midnight = datetime(2024, 1, 1, 0, 0, 0)
        habit = Habit("Test", "Test", Periodicity.DAILY, creation_date=midnight)
        
        assert habit.creation_date == midnight
        assert habit.is_broken(midnight) == False
        assert habit.is_broken(midnight + timedelta(hours=23, minutes=59)) == False
        assert habit.is_broken(midnight + timedelta(days=1)) == True
    
    def test_check_off_at_period_boundary(self):
        """Test checking off exactly at period boundaries."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        # Check off at midnight
        midnight = datetime(2024, 1, 15, 0, 0, 0)
        habit.check_off(midnight)
        
        # Should be able to check off next day at midnight
        next_midnight = datetime(2024, 1, 16, 0, 0, 0)
        habit.check_off(next_midnight)
        
        assert len(habit.completion_history) == 2
    
    def test_weekly_habit_sunday_completion(self):
        """Test weekly habit completed on Sunday."""
        habit = Habit("Test", "Test", Periodicity.WEEKLY)
        
        # Complete on Sunday
        sunday = datetime(2024, 1, 21)  # Sunday
        habit.check_off(sunday)
        
        # Should not be able to complete again in same week
        monday = datetime(2024, 1, 15)  # Monday of same week
        with pytest.raises(ValueError):
            habit.check_off(monday)
        
        # Should be able to complete next Monday
        next_monday = datetime(2024, 1, 22)
        habit.check_off(next_monday)
        
        assert len(habit.completion_history) == 2
    
    def test_monthly_habit_end_of_month(self):
        """Test monthly habit completed on last day of month."""
        habit = Habit("Test", "Test", Periodicity.MONTHLY)
        
        # Complete on Jan 31
        habit.check_off(datetime(2024, 1, 31))
        
        # Should be able to complete on Feb 29 (leap year)
        habit.check_off(datetime(2024, 2, 29))
        
        # Should be able to complete on Mar 31
        habit.check_off(datetime(2024, 3, 31))
        
        assert len(habit.completion_history) == 3
    
    def test_yearly_habit_leap_year(self):
        """Test yearly habit across leap years."""
        habit = Habit("Test", "Test", Periodicity.YEARLY)
        
        # Complete on Feb 29, 2024 (leap year)
        habit.check_off(datetime(2024, 2, 29))
        
        # Next completion should be in 2025 (any date)
        habit.check_off(datetime(2025, 2, 28))
        
        # Next in 2026
        habit.check_off(datetime(2026, 3, 1))
        
        assert len(habit.completion_history) == 3
    
    def test_unsorted_completion_history_input(self):
        """Test habit with unsorted completion history (from deserialization)."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        # Manually add unsorted completions
        habit.completion_history = [
            datetime(2024, 1, 15),
            datetime(2024, 1, 13),
            datetime(2024, 1, 14)
        ]
        
        # Streak calculation should still work
        streak = habit.calculate_current_streak()
        assert streak >= 0  # Should not crash
    
    def test_future_creation_date(self):
        """Test habit created in the future."""
        future_date = datetime.now() + timedelta(days=1)
        habit = Habit("Test", "Test", Periodicity.DAILY, creation_date=future_date)
        
        # Should not be broken immediately
        assert habit.is_broken() == False
        
        # But should be broken after the period passes
        assert habit.is_broken(future_date + timedelta(days=2)) == True

# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "habit: mark test as a habit test")
    config.addinivalue_line("markers", "streak: mark test as a streak test")
    config.addinivalue_line("markers", "period: mark test as a period test")
    config.addinivalue_line("markers", "serialization: mark test as a serialization test")

if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])