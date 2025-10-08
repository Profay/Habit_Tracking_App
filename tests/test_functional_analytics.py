# test_functional_analytics.py

"""
Unit tests for the Functional Analytics module.

This test suite covers:
- Pure functional analytics methods
- HabitAnalytics and PeriodAnalytics data classes
- AnalyticsPeriod enum
- AnalyticsPresets configurations
- Higher-order functions and pipelines
- Edge cases and error conditions
- Performance with large datasets
- Integration with Habit objects
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dateutil.relativedelta import relativedelta


from habit_tracker.functional_analytics import (
    # Classes and Enums
    HabitAnalytics,
    PeriodAnalytics,
    AnalyticsPeriod,
    FunctionalAnalytics,
    AnalyticsPresets,
    
    # Higher-order functions
    create_analytics_pipeline,
    analyze_with_filters,
    
    # Type aliases (for type checking)
    HabitList,
    HabitDict,
    StreakInfo,
    PeriodicityStats
)
from habit_tracker.habit import Habit, Periodicity

class TestAnalyticsPeriod:
    """Test the AnalyticsPeriod enum."""
    
    def test_period_values(self):
        """Test that all period values are correct."""
        assert AnalyticsPeriod.TODAY.value == "today"
        assert AnalyticsPeriod.WEEK.value == "week"
        assert AnalyticsPeriod.MONTH.value == "month"
        assert AnalyticsPeriod.YEAR.value == "year"
        assert AnalyticsPeriod.ALL_TIME.value == "all_time"
    
    def test_period_creation(self):
        """Test creating AnalyticsPeriod from string."""
        assert AnalyticsPeriod("today") == AnalyticsPeriod.TODAY
        assert AnalyticsPeriod("week") == AnalyticsPeriod.WEEK
        assert AnalyticsPeriod("month") == AnalyticsPeriod.MONTH
        assert AnalyticsPeriod("year") == AnalyticsPeriod.YEAR
        assert AnalyticsPeriod("all_time") == AnalyticsPeriod.ALL_TIME
    
    def test_period_invalid(self):
        """Test creating AnalyticsPeriod with invalid value."""
        with pytest.raises(ValueError):
            AnalyticsPeriod("invalid")

class TestHabitAnalytics:
    """Test the HabitAnalytics data class."""
    
    def test_habit_analytics_creation(self):
        """Test creating HabitAnalytics with all fields."""
        creation_date = datetime(2024, 1, 1)
        last_completion = datetime(2024, 1, 15)
        
        analytics = HabitAnalytics(
            name="Exercise",
            periodicity="daily",
            current_streak=5,
            longest_streak=10,
            total_completions=25,
            completion_rate=85.5,
            is_broken=False,
            last_completion=last_completion,
            created_date=creation_date,
            days_tracked=15
        )
        
        assert analytics.name == "Exercise"
        assert analytics.periodicity == "daily"
        assert analytics.current_streak == 5
        assert analytics.longest_streak == 10
        assert analytics.total_completions == 25
        assert analytics.completion_rate == 85.5
        assert analytics.is_broken is False
        assert analytics.last_completion == last_completion
        assert analytics.created_date == creation_date
        assert analytics.days_tracked == 15
    
    def test_habit_analytics_immutability(self):
        """Test that HabitAnalytics is immutable."""
        analytics = HabitAnalytics(
            name="Test",
            periodicity="daily",
            current_streak=1,
            longest_streak=1,
            total_completions=1,
            completion_rate=100.0,
            is_broken=False,
            last_completion=datetime.now(),
            created_date=datetime.now(),
            days_tracked=1
        )
        
        # Should raise AttributeError when trying to modify
        with pytest.raises(AttributeError):
            analytics.name = "New Name"
        
        with pytest.raises(AttributeError):
            analytics.current_streak = 5
    
    def test_habit_analytics_optional_last_completion(self):
        """Test HabitAnalytics with optional last_completion."""
        analytics = HabitAnalytics(
            name="New Habit",
            periodicity="daily",
            current_streak=0,
            longest_streak=0,
            total_completions=0,
            completion_rate=0.0,
            is_broken=False,
            last_completion=None,
            created_date=datetime.now(),
            days_tracked=0
        )
        
        assert analytics.last_completion is None

class TestPeriodAnalytics:
    """Test the PeriodAnalytics data class."""
    
    def test_period_analytics_creation(self):
        """Test creating PeriodAnalytics with all fields."""
        analytics = PeriodAnalytics(
            period="January 2024",
            total_habits=5,
            completed_habits=3,
            completion_rate=60.0,
            broken_habits=2,
            streaks=[("Exercise", 5), ("Read", 3)]
        )
        
        assert analytics.period == "January 2024"
        assert analytics.total_habits == 5
        assert analytics.completed_habits == 3
        assert analytics.completion_rate == 60.0
        assert analytics.broken_habits == 2
        assert analytics.streaks == [("Exercise", 5), ("Read", 3)]
    
    def test_period_analytics_immutability(self):
        """Test that PeriodAnalytics is immutable."""
        analytics = PeriodAnalytics(
            period="Test Period",
            total_habits=1,
            completed_habits=1,
            completion_rate=100.0,
            broken_habits=0,
            streaks=[]
        )
        
        with pytest.raises(AttributeError):
            analytics.total_habits = 5

@pytest.fixture
def sample_habits():
    """Create sample habits for testing."""
    habits = {}
    
    # Daily habit with consistent completions
    daily_habit = Habit(
        name="Exercise",
        description="30 min workout",
        periodicity=Periodicity.DAILY,
        creation_date=datetime(2024, 1, 1)
    )
    for i in range(10):
        daily_habit.check_off(datetime(2024, 1, 15 - i))
    habits["Exercise"] = daily_habit
    
    # Daily habit with missed days
    daily_habit2 = Habit(
        name="Read",
        description="Read for 20 minutes",
        periodicity=Periodicity.DAILY,
        creation_date=datetime(2024, 1, 1)
    )
    for i in [0, 1, 2, 4, 5, 7, 8, 9]:  # Skip some days
        daily_habit2.check_off(datetime(2024, 1, 15 - i))
    habits["Read"] = daily_habit2
    
    # Weekly habit
    weekly_habit = Habit(
        name="Weekly Review",
        description="Review weekly progress",
        periodicity=Periodicity.WEEKLY,
        creation_date=datetime(2024, 1, 1)
    )
    for i in range(3):
        weekly_habit.check_off(datetime(2024, 1, 15 - i*7))
    habits["Weekly Review"] = weekly_habit
    
    # Monthly habit
    monthly_habit = Habit(
        name="Pay Bills",
        description="Pay monthly bills",
        periodicity=Periodicity.MONTHLY,
        creation_date=datetime(2024, 1, 1)
    )
    monthly_habit.check_off(datetime(2024, 1, 15))
    monthly_habit.check_off(datetime(2024, 2, 15))
    habits["Pay Bills"] = monthly_habit
    
    # Broken habit
    broken_habit = Habit(
        name="Meditation",
        description="Daily meditation",
        periodicity=Periodicity.DAILY,
        creation_date=datetime(2024, 1, 1)
    )
    broken_habit.check_off(datetime(2024, 1, 10))  # Last completed 5 days ago
    habits["Meditation"] = broken_habit
    
    return habits

@pytest.fixture
def empty_habits():
    """Create empty habits dictionary for testing."""
    return {}

class TestFunctionalAnalyticsBasicQueries:
    """Test basic query methods of FunctionalAnalytics."""
    
    def test_get_all_habits(self, sample_habits):
        """Test getting all habits."""
        result = FunctionalAnalytics.get_all_habits(sample_habits)
        
        assert isinstance(result, list)
        assert len(result) == 5
        habit_names = [h.name for h in result]
        assert "Exercise" in habit_names
        assert "Read" in habit_names
        assert "Weekly Review" in habit_names
        assert "Pay Bills" in habit_names
        assert "Meditation" in habit_names
    
    def test_get_all_habits_empty(self, empty_habits):
        """Test getting all habits from empty dictionary."""
        result = FunctionalAnalytics.get_all_habits(empty_habits)
        
        assert result == []
    
    def test_get_habits_by_periodicity_daily(self, sample_habits):
        """Test getting daily habits."""
        result = FunctionalAnalytics.get_habits_by_periodicity(sample_habits, Periodicity.DAILY)
        
        assert len(result) == 3
        habit_names = [h.name for h in result]
        assert "Exercise" in habit_names
        assert "Read" in habit_names
        assert "Meditation" in habit_names
    
    def test_get_habits_by_periodicity_weekly(self, sample_habits):
        """Test getting weekly habits."""
        result = FunctionalAnalytics.get_habits_by_periodicity(sample_habits, Periodicity.WEEKLY)
        
        assert len(result) == 1
        assert result[0].name == "Weekly Review"
    
    def test_get_habits_by_periodicity_monthly(self, sample_habits):
        """Test getting monthly habits."""
        result = FunctionalAnalytics.get_habits_by_periodicity(sample_habits, Periodicity.MONTHLY)
        
        assert len(result) == 1
        assert result[0].name == "Pay Bills"
    
    def test_get_habits_by_periodicity_none_found(self, sample_habits):
        """Test getting habits with periodicity that doesn't exist."""
        result = FunctionalAnalytics.get_habits_by_periodicity(sample_habits, Periodicity.YEARLY)
        
        assert result == []
    
    def test_get_habit_by_name_found(self, sample_habits):
        """Test getting habit by name when found."""
        result = FunctionalAnalytics.get_habit_by_name(sample_habits, "Exercise")
        
        assert result is not None
        assert result.name == "Exercise"
        assert result.periodicity == Periodicity.DAILY
    
    def test_get_habit_by_name_not_found(self, sample_habits):
        """Test getting habit by name when not found."""
        result = FunctionalAnalytics.get_habit_by_name(sample_habits, "NonExistent")
        
        assert result is None

class TestFunctionalAnalyticsStreaks:
    """Test streak calculation methods."""
    
    def test_get_longest_streak_all(self, sample_habits):
        """Test getting longest streak across all habits."""
        streak, habit = FunctionalAnalytics.get_longest_streak_all(sample_habits)
        
        assert streak == 10  # Exercise has 10-day streak
        assert habit.name == "Exercise"
        assert habit.periodicity == Periodicity.DAILY
    
    def test_get_longest_streak_all_empty(self, empty_habits):
        """Test getting longest streak with no habits."""
        streak, habit = FunctionalAnalytics.get_longest_streak_all(empty_habits)
        
        assert streak == 0
        assert habit is None
    
    def test_get_longest_streak_for_habit_found(self, sample_habits):
        """Test getting longest streak for specific habit."""
        streak = FunctionalAnalytics.get_longest_streak_for_habit(sample_habits, "Exercise")
        
        assert streak == 10
    
    def test_get_longest_streak_for_habit_not_found(self, sample_habits):
        """Test getting longest streak for non-existent habit."""
        streak = FunctionalAnalytics.get_longest_streak_for_habit(sample_habits, "NonExistent")
        
        assert streak == 0
    
    def test_get_all_current_streaks(self, sample_habits):
        """Test getting current streaks for all habits."""
        streaks = FunctionalAnalytics.get_all_current_streaks(sample_habits)
        
        assert isinstance(streaks, list)
        assert len(streaks) == 5
        
        # Convert to dict for easier testing
        streak_dict = dict(streaks)
        assert streak_dict["Exercise"] == 10
        assert streak_dict["Read"] == 3  # Current streak (missed some days)
        assert streak_dict["Weekly Review"] == 3
        assert streak_dict["Pay Bills"] == 2
        assert streak_dict["Meditation"] == 0  # Broken
    
    def test_get_active_streaks(self, sample_habits):
        """Test getting active streaks above minimum."""
        active = FunctionalAnalytics.get_active_streaks(sample_habits, min_streak=3)
        
        assert len(active) == 3  # Exercise, Read, Weekly Review
        habit_names = [name for name, streak in active]
        assert "Exercise" in habit_names
        assert "Read" in habit_names
        assert "Weekly Review" in habit_names
    
    def test_get_active_streaks_high_threshold(self, sample_habits):
        """Test getting active streaks with high threshold."""
        active = FunctionalAnalytics.get_active_streaks(sample_habits, min_streak=10)
        
        assert len(active) == 1
        assert active[0][0] == "Exercise"
        assert active[0][1] == 10

class TestFunctionalAnalyticsCompletions:
    """Test completion-related analytics methods."""
    
    def test_get_completion_rate_daily(self, sample_habits):
        """Test completion rate for daily habit."""
        exercise_habit = sample_habits["Exercise"]
        rate = FunctionalAnalytics.get_completion_rate(exercise_habit, days=30)
        
        # Exercise has 10 completions over ~15 days, so rate should be around 66.7%
        assert 60 <= rate <= 70
    
    def test_get_completion_rate_weekly(self, sample_habits):
        """Test completion rate for weekly habit."""
        weekly_habit = sample_habits["Weekly Review"]
        rate = FunctionalAnalytics.get_completion_rate(weekly_habit, days=30)
        
        # Weekly habit has 3 completions over 4 weeks, so 75%
        assert rate == 75.0
    
    def test_get_completion_rate_no_completions(self, sample_habits):
        """Test completion rate for habit with no completions."""
        # Create new habit with no completions
        new_habit = Habit("New", "Test", Periodicity.DAILY)
        rate = FunctionalAnalytics.get_completion_rate(new_habit, days=30)
        
        assert rate == 0.0
    
    def test_get_total_completions(self, sample_habits):
        """Test getting total completions across all habits."""
        total = FunctionalAnalytics.get_total_completions(sample_habits)
        
        # Exercise: 10, Read: 8, Weekly Review: 3, Pay Bills: 2, Meditation: 1
        assert total == 24
    
    def test_get_total_completions_empty(self, empty_habits):
        """Test getting total completions with no habits."""
        total = FunctionalAnalytics.get_total_completions(empty_habits)
        
        assert total == 0
    
    def test_get_completions_by_period_daily(self, sample_habits):
        """Test getting completions grouped by day."""
        completions = FunctionalAnalytics.get_completions_by_period(
            sample_habits, 
            AnalyticsPeriod.TODAY
        )
        
        assert isinstance(completions, dict)
        # Should have entries for recent days
        assert len(completions) > 0
    
    def test_get_completions_by_period_weekly(self, sample_habits):
        """Test getting completions grouped by week."""
        completions = FunctionalAnalytics.get_completions_by_period(
            sample_habits, 
            AnalyticsPeriod.WEEK
        )
        
        assert isinstance(completions, dict)
        # Should have entries for recent weeks
        assert len(completions) > 0
    
    def test_get_completions_by_period_monthly(self, sample_habits):
        """Test getting completions grouped by month."""
        completions = FunctionalAnalytics.get_completions_by_period(
            sample_habits, 
            AnalyticsPeriod.MONTH
        )
        
        assert isinstance(completions, dict)
        # Should have entries for recent months
        assert len(completions) > 0
    
    def test_get_completions_by_period_all_time(self, sample_habits):
        """Test getting completions for all time."""
        completions = FunctionalAnalytics.get_completions_by_period(
            sample_habits, 
            AnalyticsPeriod.ALL_TIME
        )
        
        assert isinstance(completions, dict)
        assert "all_time" in completions
        assert completions["all_time"] == 24  # Total completions

class TestFunctionalAnalyticsAdvanced:
    """Test advanced analytics methods."""
    
    def test_get_habit_analytics(self, sample_habits):
        """Test getting comprehensive analytics for a habit."""
        analytics = FunctionalAnalytics.get_habit_analytics(sample_habits, "Exercise")
        
        assert analytics is not None
        assert analytics.name == "Exercise"
        assert analytics.periodicity == "daily"
        assert analytics.current_streak == 10
        assert analytics.longest_streak == 10
        assert analytics.total_completions == 10
        assert analytics.completion_rate > 0
        assert analytics.is_broken is False
        assert analytics.last_completion is not None
        assert analytics.created_date is not None
        assert analytics.days_tracked > 0
    
    def test_get_habit_analytics_not_found(self, sample_habits):
        """Test getting analytics for non-existent habit."""
        analytics = FunctionalAnalytics.get_habit_analytics(sample_habits, "NonExistent")
        
        assert analytics is None
    
    def test_get_all_habits_analytics(self, sample_habits):
        """Test getting analytics for all habits."""
        all_analytics = FunctionalAnalytics.get_all_habits_analytics(sample_habits)
        
        assert len(all_analytics) == 5
        habit_names = [a.name for a in all_analytics]
        assert "Exercise" in habit_names
        assert "Read" in habit_names
        
        # Verify each analytics object has required fields
        for analytics in all_analytics:
            assert analytics.name is not None
            assert analytics.periodicity is not None
            assert analytics.current_streak >= 0
            assert analytics.longest_streak >= 0
            assert analytics.total_completions >= 0
            assert 0 <= analytics.completion_rate <= 100
    
    def test_get_periodicity_stats(self, sample_habits):
        """Test getting statistics grouped by periodicity."""
        stats = FunctionalAnalytics.get_periodicity_stats(sample_habits)
        
        assert "daily" in stats
        assert "weekly" in stats
        assert "monthly" in stats
        assert "yearly" in stats
        
        # Check daily stats
        daily_stats = stats["daily"]
        assert daily_stats["count"] == 3
        assert daily_stats["total_completions"] == 19  # Exercise + Read + Meditation
        assert daily_stats["average_streak"] > 0
        assert daily_stats["broken_count"] == 1  # Meditation
        assert 0 <= daily_stats["completion_rate"] <= 100
        
        # Check weekly stats
        weekly_stats = stats["weekly"]
        assert weekly_stats["count"] == 1
        assert weekly_stats["total_completions"] == 3
        
        # Check monthly stats
        monthly_stats = stats["monthly"]
        assert monthly_stats["count"] == 1
        assert monthly_stats["total_completions"] == 2
    
    def test_get_broken_habits(self, sample_habits):
        """Test getting broken habits."""
        broken = FunctionalAnalytics.get_broken_habits(sample_habits)
        
        assert len(broken) == 1
        assert "Meditation" in broken
    
    def test_get_broken_habits_none(self, empty_habits):
        """Test getting broken habits with none broken."""
        broken = FunctionalAnalytics.get_broken_habits(empty_habits)
        
        assert broken == []
    
    def test_get_most_consistent_habit(self, sample_habits):
        """Test getting most consistent habit."""
        result = FunctionalAnalytics.get_most_consistent_habit(sample_habits)
        
        assert result is not None
        name, rate = result
        assert name in ["Exercise", "Read", "Weekly Review", "Pay Bills", "Meditation"]
        assert 0 <= rate <= 100
    
    def test_get_most_consistent_habit_empty(self, empty_habits):
        """Test getting most consistent habit with no habits."""
        result = FunctionalAnalytics.get_most_consistent_habit(empty_habits)
        
        assert result is None
    
    def test_get_struggling_habits(self, sample_habits):
        """Test getting struggling habits below threshold."""
        struggling = FunctionalAnalytics.get_struggling_habits(sample_habits, threshold=50.0)
        
        # Should include habits with completion rate below 50%
        assert len(struggling) >= 0
        for name, rate in struggling:
            assert rate < 50.0
    
    def test_get_struggling_habits_high_threshold(self, sample_habits):
        """Test getting struggling habits with high threshold."""
        struggling = FunctionalAnalytics.get_struggling_habits(sample_habits, threshold=99.0)
        
        # Should include most habits since threshold is very high
        assert len(struggling) >= 1

class TestFunctionalAnalyticsTimeBased:
    """Test time-based analytics methods."""
    
    def test_get_productivity_trend(self, sample_habits):
        """Test getting productivity trend over time."""
        trend = FunctionalAnalytics.get_productivity_trend(sample_habits, days=7)
        
        assert isinstance(trend, dict)
        assert len(trend) == 7  # Should have 7 days
        
        # Check that all dates are recent
        today = datetime.now().date()
        for date_str, count in trend.items():
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            assert (today - date).days < 7
            assert count >= 0
    
    def test_get_productivity_trend_empty(self, empty_habits):
        """Test productivity trend with no habits."""
        trend = FunctionalAnalytics.get_productivity_trend(empty_habits, days=7)
        
        assert isinstance(trend, dict)
        assert len(trend) == 7
        # All counts should be 0
        for count in trend.values():
            assert count == 0
    
    def test_get_best_performing_day(self, sample_habits):
        """Test finding best performing day of week."""
        result = FunctionalAnalytics.get_best_performing_day(sample_habits, weeks=4)
        
        if result is not None:
            day_name, count = result
            assert day_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            assert count >= 0
    
    def test_get_best_performing_day_empty(self, empty_habits):
        """Test best performing day with no habits."""
        result = FunctionalAnalytics.get_best_performing_day(empty_habits, weeks=4)
        
        assert result is None

class TestFunctionalAnalyticsComparative:
    """Test comparative analytics methods."""
    
    def test_compare_habits(self, sample_habits):
        """Test comparing multiple habits."""
        comparison = FunctionalAnalytics.compare_habits(
            sample_habits, 
            ["Exercise", "Read"]
        )
        
        assert "Exercise" in comparison
        assert "Read" in comparison
        
        # Check that each habit has comparison metrics
        for habit_name in ["Exercise", "Read"]:
            metrics = comparison[habit_name]
            assert "current_streak" in metrics
            assert "longest_streak" in metrics
            assert "completion_rate" in metrics
            assert "total_completions" in metrics
            assert "is_broken" in metrics
    
    def test_compare_habits_non_existent(self, sample_habits):
        """Test comparing with non-existent habit."""
        comparison = FunctionalAnalytics.compare_habits(
            sample_habits, 
            ["Exercise", "NonExistent"]
        )
        
        assert "Exercise" in comparison
        assert "NonExistent" not in comparison
    
    def test_get_habit_rankings(self, sample_habits):
        """Test getting habit rankings by various metrics."""
        rankings = FunctionalAnalytics.get_habit_rankings(sample_habits)
        
        assert "by_current_streak" in rankings
        assert "by_longest_streak" in rankings
        assert "by_completion_rate" in rankings
        assert "by_total_completions" in rankings
        assert "by_days_tracked" in rankings
        
        # Check that rankings are sorted in descending order
        for ranking_type, ranking_list in rankings.items():
            if ranking_list:  # Skip empty rankings
                for i in range(len(ranking_list) - 1):
                    current_value = ranking_list[i][1]
                    next_value = ranking_list[i + 1][1]
                    assert current_value >= next_value

class TestHigherOrderFunctions:
    """Test higher-order functions for analytics."""
    
    def test_create_analytics_pipeline(self, sample_habits):
        """Test creating analytics pipeline."""
        # Create pipeline that counts daily habits
        pipeline_result = create_analytics_pipeline(
            sample_habits,
            FunctionalAnalytics.get_all_habits,
            lambda habits: list(filter(lambda h: h.periodicity == Periodicity.DAILY, habits)),
            len
        )
        
        assert pipeline_result == 3  # 3 daily habits
    
    def test_create_analytics_pipeline_empty(self, empty_habits):
        """Test pipeline with empty habits."""
        result = create_analytics_pipeline(
            empty_habits,
            FunctionalAnalytics.get_all_habits,
            len
        )
        
        assert result == 0
    
    def test_create_analytics_pipeline_multiple_operations(self, sample_habits):
        """Test pipeline with multiple operations."""
        # Pipeline to get names of habits with streak > 5
        result = create_analytics_pipeline(
            sample_habits,
            FunctionalAnalytics.get_all_current_streaks,
            lambda streaks: [name for name, streak in streaks if streak > 5],
            len
        )
        
        assert result == 1  # Only Exercise has streak > 5
    
    def test_analyze_with_filters(self, sample_habits):
        """Test analyzing with filters."""
        # Filter for daily habits and count completions
        result = analyze_with_filters(
            sample_habits,
            [lambda h: h.periodicity == Periodicity.DAILY],
            lambda habits: sum(len(h.completion_history) for h in habits)
        )
        
        assert result == 19  # Total completions for daily habits
    
    def test_analyze_with_filters_multiple(self, sample_habits):
        """Test analyzing with multiple filters."""
        # Filter for daily habits with streak > 0
        result = analyze_with_filters(
            sample_habits,
            [
                lambda h: h.periodicity == Periodicity.DAILY,
                lambda h: h.calculate_current_streak() > 0
            ],
            len
        )
        
        assert result == 2  # Exercise and Read have streak > 0
    
    def test_analyze_with_filters_no_matches(self, sample_habits):
        """Test analyzing with filters that match nothing."""
        result = analyze_with_filters(
            sample_habits,
            [lambda h: h.periodicity == Periodicity.YEARLY],
            len
        )
        
        assert result == 0

class TestAnalyticsPresets:
    """Test analytics preset configurations."""
    
    def test_daily_overview(self, sample_habits):
        """Test daily overview preset."""
        overview = AnalyticsPresets.daily_overview(sample_habits)
        
        assert "total_habits" in overview
        assert "completed_today" in overview
        assert "active_streaks" in overview
        assert "longest_streak" in overview
        assert "most_consistent" in overview
        assert "broken_habits" in overview
        
        assert overview["total_habits"] == 5
        assert isinstance(overview["active_streaks"], list)
        assert isinstance(overview["broken_habits"], list)
    
    def test_daily_overview_empty(self, empty_habits):
        """Test daily overview with no habits."""
        overview = AnalyticsPresets.daily_overview(empty_habits)
        
        assert overview["total_habits"] == 0
        assert overview["completed_today"] == 0
        assert overview["active_streaks"] == []
        assert overview["longest_streak"] == (0, None)
        assert overview["most_consistent"] is None
        assert overview["broken_habits"] == []
    
    def test_weekly_report(self, sample_habits):
        """Test weekly report preset."""
        report = AnalyticsPresets.weekly_report(sample_habits)
        
        assert "periodicity_stats" in report
        assert "productivity_trend" in report
        assert "best_day" in report
        assert "struggling_habits" in report
        assert "rankings" in report
        
        assert isinstance(report["periodicity_stats"], dict)
        assert isinstance(report["productivity_trend"], dict)
        assert isinstance(report["struggling_habits"], list)
        assert isinstance(report["rankings"], dict)
    
    def test_monthly_analysis(self, sample_habits):
        """Test monthly analysis preset."""
        analysis = AnalyticsPresets.monthly_analysis(sample_habits)
        
        assert "all_analytics" in analysis
        assert "completions_by_month" in analysis
        assert "habit_comparison" in analysis
        assert "total_completions" in analysis
        
        assert len(analysis["all_analytics"]) == 5
        assert isinstance(analysis["completions_by_month"], dict)
        assert isinstance(analysis["habit_comparison"], dict)
        assert analysis["total_completions"] == 24

class TestFunctionalAnalyticsEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_habit_with_future_completions(self):
        """Test analytics with future completion dates."""
        habit = Habit("Future", "Test", Periodicity.DAILY)
        habit.check_off(datetime.now() + timedelta(days=1))
        
        habits = {"Future": habit}
        
        # Should handle future dates gracefully
        total = FunctionalAnalytics.get_total_completions(habits)
        assert total == 1
        
        streaks = FunctionalAnalytics.get_all_current_streaks(habits)
        assert streaks[0][1] >= 0
    
    def test_habit_with_very_old_creation_date(self):
        """Test analytics with very old creation date."""
        old_date = datetime.now() - timedelta(days=1000)
        habit = Habit("Old", "Test", Periodicity.DAILY, creation_date=old_date)
        
        habits = {"Old": habit}
        
        analytics = FunctionalAnalytics.get_habit_analytics(habits, "Old")
        assert analytics is not None
        assert analytics.days_tracked > 365
    
    def test_habit_with_duplicate_completions(self):
        """Test analytics with duplicate completion times."""
        habit = Habit("Duplicate", "Test", Periodicity.DAILY)
        completion_time = datetime.now()
        
        # Manually add duplicate completions (shouldn't happen normally)
        habit.completion_history = [completion_time, completion_time]
        
        habits = {"Duplicate": habit}
        
        # Should handle duplicates gracefully
        total = FunctionalAnalytics.get_total_completions(habits)
        assert total == 2  # Counts what's in history
    
    def test_zero_day_period_for_completion_rate(self):
        """Test completion rate with zero day period."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        
        rate = FunctionalAnalytics.get_completion_rate(habit, days=0)
        assert rate == 0.0
    
    def test_negative_day_period(self):
        """Test completion rate with negative day period."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        habit.check_off(datetime.now())
        
        rate = FunctionalAnalytics.get_completion_rate(habit, days=-5)
        assert rate == 0.0
    
    def test_very_large_day_period(self):
        """Test completion rate with very large day period."""
        habit = Habit("Test", "Test", Periodicity.DAILY)
        habit.check_off(datetime.now())
        
        rate = FunctionalAnalytics.get_completion_rate(habit, days=36500)  # 100 years
        assert 0 <= rate <= 100
    
    def test_habit_with_zero_second_completions(self):
        """Test habit with completions at same second."""
        habit = Habit("Same Second", "Test", Periodicity.DAILY)
        same_time = datetime(2024, 1, 15, 12, 0, 0)
        
        # Add completions at same time but different days
        habit.completion_history = [
            same_time,
            same_time + timedelta(days=1),
            same_time + timedelta(days=2)
        ]
        
        habits = {"Same Second": habit}
        
        streaks = FunctionalAnalytics.get_all_current_streaks(habits)
        assert len(streaks) == 1
        assert streaks[0][1] >= 0

class TestFunctionalAnalyticsPerformance:
    """Test performance with large datasets."""
    
    def test_large_habit_dataset(self):
        """Test analytics with large number of habits."""
        habits = {}
        
        # Create 1000 habits
        for i in range(1000):
            habit = Habit(f"Habit_{i}", f"Description {i}", Periodicity.DAILY)
            
            # Add random completions
            for j in range(50):
                habit.check_off(datetime.now() - timedelta(days=j))
            
            habits[f"Habit_{i}"] = habit
        
        # Test that analytics complete in reasonable time
        import time
        
        start_time = time.time()
        total = FunctionalAnalytics.get_total_completions(habits)
        end_time = time.time()
        
        assert total == 50000  # 1000 habits * 50 completions
        assert end_time - start_time < 1.0  # Should complete in under 1 second
        
        start_time = time.time()
        streaks = FunctionalAnalytics.get_all_current_streaks(habits)
        end_time = time.time()
        
        assert len(streaks) == 1000
        assert end_time - start_time < 1.0
    
    def test_habit_with_many_completions(self):
        """Test habit with very many completions."""
        habit = Habit("Many", "Many completions", Periodicity.DAILY)
        
        # Add 1000 completions
        for i in range(1000):
            habit.check_off(datetime.now() - timedelta(days=i))
        
        habits = {"Many": habit}
        
        # Test analytics
        analytics = FunctionalAnalytics.get_habit_analytics(habits, "Many")
        assert analytics.total_completions == 1000
        assert analytics.longest_streak == 1000
        
        streaks = FunctionalAnalytics.get_all_current_streaks(habits)
        assert streaks[0][1] == 1000

# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "analytics: mark test as an analytics test")
    config.addinivalue_line("markers", "streak: mark test as a streak test")
    config.addinivalue_line("markers", "completion: mark test as a completion test")
    config.addinivalue_line("markers", "preset: mark test as a preset test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")

if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])