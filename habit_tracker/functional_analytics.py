from typing import List, Dict, Tuple, Optional, Callable, Any
from datetime import datetime, timedelta
from functools import reduce, partial
from dataclasses import dataclass
from enum import Enum
from habit import Habit, Periodicity

# Type aliases for better readability
HabitList = List[Habit]
HabitDict = Dict[str, Habit]
StreakInfo = Tuple[int, Optional[Habit]]
PeriodicityStats = Dict[str, Any]
AnalyticsResult = Dict[str, Any]

class AnalyticsPeriod(Enum):
    """Enumeration for analytics time periods."""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL_TIME = "all_time"

@dataclass(frozen=True)
class HabitAnalytics:
    """Immutable data class for habit analytics results."""
    name: str
    periodicity: str
    current_streak: int
    longest_streak: int
    total_completions: int
    completion_rate: float
    is_broken: bool
    last_completion: Optional[datetime]
    created_date: datetime
    days_tracked: int

@dataclass(frozen=True)
class PeriodAnalytics:
    """Immutable data class for period-based analytics."""
    period: str
    total_habits: int
    completed_habits: int
    completion_rate: float
    broken_habits: int
    streaks: List[Tuple[str, int]]

class FunctionalAnalytics:
    """
    Functional analytics module for habit tracking.
    
    All functions in this module are pure functions - they don't modify
    input data and have no side effects. They take data as input and
    return new data structures as output.
    """
    
    # ==================== BASIC HABIT QUERIES ====================
    
    @staticmethod
    def get_all_habits(habits: HabitDict) -> HabitList:
        """
        Return a list of all currently tracked habits.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            List[Habit]: List of all habits
        """
        return list(habits.values())
    
    @staticmethod
    def get_habits_by_periodicity(habits: HabitDict, periodicity: Periodicity) -> HabitList:
        """
        Return a list of all habits with the same periodicity.
        
        Args:
            habits: Dictionary of habits
            periodicity: The periodicity to filter by
            
        Returns:
            List[Habit]: List of habits with specified periodicity
        """
        return list(filter(
            lambda habit: habit.periodicity == periodicity,
            habits.values()
        ))
    
    @staticmethod
    def get_habit_by_name(habits: HabitDict, name: str) -> Optional[Habit]:
        """
        Get a specific habit by name.
        
        Args:
            habits: Dictionary of habits
            name: Name of the habit to find
            
        Returns:
            Optional[Habit]: The habit if found, None otherwise
        """
        return habits.get(name)
    
    # ==================== STREAK ANALYTICS ====================
    
    @staticmethod
    def get_longest_streak_all(habits: HabitDict) -> StreakInfo:
        """
        Return the longest run streak of all defined habits.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            Tuple[int, Optional[Habit]]: (streak_length, habit) or (0, None)
        """
        if not habits:
            return 0, None
        
        # Calculate streaks for all habits
        streak_pairs = list(map(
            lambda habit: (habit.calculate_longest_streak(), habit),
            habits.values()
        ))
        
        # Find the maximum streak
        if not streak_pairs:
            return 0, None
        
        max_streak, best_habit = max(streak_pairs, key=lambda pair: pair[0])
        return max_streak, best_habit
    
    @staticmethod
    def get_longest_streak_for_habit(habits: HabitDict, habit_name: str) -> int:
        """
        Return the longest run streak for a given habit.
        
        Args:
            habits: Dictionary of habits
            habit_name: Name of the habit
            
        Returns:
            int: Longest streak length (0 if habit not found)
        """
        habit = FunctionalAnalytics.get_habit_by_name(habits, habit_name)
        return habit.calculate_longest_streak() if habit else 0
    
    @staticmethod
    def get_all_current_streaks(habits: HabitDict) -> List[Tuple[str, int]]:
        """
        Get current streaks for all habits.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            List[Tuple[str, int]]: List of (habit_name, current_streak) pairs
        """
        return list(map(
            lambda habit: (habit.name, habit.calculate_current_streak()),
            habits.values()
        ))
    
    @staticmethod
    def get_active_streaks(habits: HabitDict, min_streak: int = 1) -> List[Tuple[str, int]]:
        """
        Get habits with active streaks above a minimum threshold.
        
        Args:
            habits: Dictionary of habits
            min_streak: Minimum streak length to include
            
        Returns:
            List[Tuple[str, int]]: List of (habit_name, current_streak) for active habits
        """
        return list(filter(
            lambda pair: pair[1] >= min_streak,
            FunctionalAnalytics.get_all_current_streaks(habits)
        ))
    
    # ==================== COMPLETION ANALYTICS ====================
    
    @staticmethod
    def get_completion_rate(habit: Habit, days: int = 30) -> float:
        """
        Calculate completion rate for a habit over specified days.
        
        Args:
            habit: The habit to analyze
            days: Number of days to look back
            
        Returns:
            float: Completion rate as percentage (0-100)
        """
        if not habit.completion_history:
            return 0.0
        
        # Calculate expected completions based on periodicity
        now = datetime.now()
        start_date = now - timedelta(days=days)
        
        # Filter completions within the period
        recent_completions = list(filter(
            lambda completion: completion >= start_date,
            habit.completion_history
        ))
        
        # Calculate expected completions
        if habit.periodicity == Periodicity.DAILY:
            expected = days
        elif habit.periodicity == Periodicity.WEEKLY:
            expected = days / 7
        elif habit.periodicity == Periodicity.MONTHLY:
            expected = days / 30
        else:  # YEARLY
            expected = days / 365
        
        if expected == 0:
            return 0.0
        
        return (len(recent_completions) / expected) * 100
    
    @staticmethod
    def get_total_completions(habits: HabitDict) -> int:
        """
        Get total number of completions across all habits.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            int: Total completions
        """
        return reduce(
            lambda total, habit: total + len(habit.completion_history),
            habits.values(),
            0
        )
    
    @staticmethod
    def get_completions_by_period(habits: HabitDict, period: AnalyticsPeriod) -> Dict[str, int]:
        """
        Get completions grouped by a time period.
        
        Args:
            habits: Dictionary of habits
            period: The period to group by
            
        Returns:
            Dict[str, int]: Dictionary mapping period to completion count
        """
        now = datetime.now()
        
        def get_period_key(completion_time: datetime) -> str:
            if period == AnalyticsPeriod.TODAY:
                return completion_time.strftime("%Y-%m-%d")
            elif period == AnalyticsPeriod.WEEK:
                # Get Monday of the week
                monday = completion_time - timedelta(days=completion_time.weekday())
                return monday.strftime("%Y-%W")
            elif period == AnalyticsPeriod.MONTH:
                return completion_time.strftime("%Y-%m")
            elif period == AnalyticsPeriod.YEAR:
                return completion_time.strftime("%Y")
            else:  # ALL_TIME
                return "all_time"
        
        # Collect all completions with their period keys
        all_completions = []
        for habit in habits.values():
            for completion in habit.completion_history:
                all_completions.append(get_period_key(completion))
        
        # Count completions by period
        period_counts = {}
        for period_key in all_completions:
            period_counts[period_key] = period_counts.get(period_key, 0) + 1
        
        return period_counts
    
    # ==================== ADVANCED ANALYTICS ====================
    
    @staticmethod
    def get_habit_analytics(habits: HabitDict, habit_name: str) -> Optional[HabitAnalytics]:
        """
        Get comprehensive analytics for a specific habit.
        
        Args:
            habits: Dictionary of habits
            habit_name: Name of the habit
            
        Returns:
            Optional[HabitAnalytics]: Detailed analytics or None if not found
        """
        habit = FunctionalAnalytics.get_habit_by_name(habits, habit_name)
        if not habit:
            return None
        
        now = datetime.now()
        days_tracked = (now - habit.creation_date).days
        
        return HabitAnalytics(
            name=habit.name,
            periodicity=habit.periodicity.value,
            current_streak=habit.calculate_current_streak(),
            longest_streak=habit.calculate_longest_streak(),
            total_completions=len(habit.completion_history),
            completion_rate=FunctionalAnalytics.get_completion_rate(habit),
            is_broken=habit.is_broken(),
            last_completion=max(habit.completion_history) if habit.completion_history else None,
            created_date=habit.creation_date,
            days_tracked=days_tracked
        )
    
    @staticmethod
    def get_all_habits_analytics(habits: HabitDict) -> List[HabitAnalytics]:
        """
        Get comprehensive analytics for all habits.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            List[HabitAnalytics]: List of detailed analytics for each habit
        """
        return list(filter(
            lambda analytics: analytics is not None,
            map(
                lambda habit: FunctionalAnalytics.get_habit_analytics(habits, habit.name),
                habits.values()
            )
        ))
    
    @staticmethod
    def get_periodicity_stats(habits: HabitDict) -> PeriodicityStats:
        """
        Get statistics grouped by periodicity.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            Dict[str, Any]: Statistics for each periodicity
        """
        periodicities = ['daily', 'weekly', 'monthly', 'yearly']
        stats = {}
        
        for period in periodicities:
            period_habits = FunctionalAnalytics.get_habits_by_periodicity(
                habits, 
                Periodicity(period)
            )
            
            if period_habits:
                total_completions = sum(len(h.completion_history) for h in period_habits)
                avg_streak = sum(h.calculate_current_streak() for h in period_habits) / len(period_habits)
                broken_count = sum(1 for h in period_habits if h.is_broken())
                
                stats[period] = {
                    'count': len(period_habits),
                    'total_completions': total_completions,
                    'average_streak': round(avg_streak, 2),
                    'broken_count': broken_count,
                    'completion_rate': round(
                        sum(FunctionalAnalytics.get_completion_rate(h) for h in period_habits) / len(period_habits),
                        2
                    )
                }
            else:
                stats[period] = {
                    'count': 0,
                    'total_completions': 0,
                    'average_streak': 0,
                    'broken_count': 0,
                    'completion_rate': 0
                }
        
        return stats
    
    @staticmethod
    def get_broken_habits(habits: HabitDict) -> List[str]:
        """
        Get list of currently broken habits.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            List[str]: List of broken habit names
        """
        return list(map(
            lambda habit: habit.name,
            filter(lambda habit: habit.is_broken(), habits.values())
        ))
    
    @staticmethod
    def get_most_consistent_habit(habits: HabitDict, days: int = 30) -> Optional[Tuple[str, float]]:
        """
        Find the most consistent habit based on completion rate.
        
        Args:
            habits: Dictionary of habits
            days: Number of days to consider
            
        Returns:
            Optional[Tuple[str, float]]: (habit_name, completion_rate) or None
        """
        if not habits:
            return None
        
        completion_rates = list(map(
            lambda habit: (habit.name, FunctionalAnalytics.get_completion_rate(habit, days)),
            habits.values()
        ))
        
        if not completion_rates:
            return None
        
        return max(completion_rates, key=lambda pair: pair[1])
    
    @staticmethod
    def get_struggling_habits(habits: HabitDict, threshold: float = 50.0) -> List[Tuple[str, float]]:
        """
        Get habits with completion rate below threshold.
        
        Args:
            habits: Dictionary of habits
            threshold: Completion rate threshold percentage
            
        Returns:
            List[Tuple[str, float]]: List of (habit_name, completion_rate) below threshold
        """
        return list(filter(
            lambda pair: pair[1] < threshold,
            map(
                lambda habit: (habit.name, FunctionalAnalytics.get_completion_rate(habit)),
                habits.values()
            )
        ))
    
    # ==================== TIME-BASED ANALYTICS ====================
    
    @staticmethod
    def get_productivity_trend(habits: HabitDict, days: int = 30) -> Dict[str, List[int]]:
        """
        Get productivity trend over time.
        
        Args:
            habits: Dictionary of habits
            days: Number of days to analyze
            
        Returns:
            Dict[str, List[int]]: Daily completion counts
        """
        now = datetime.now()
        daily_counts = {}
        
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            count = sum(
                1 for habit in habits.values()
                for completion in habit.completion_history
                if completion.date() == date.date()
            )
            
            daily_counts[date_str] = count
        
        return daily_counts
    
    @staticmethod
    def get_best_performing_day(habits: HabitDict, weeks: int = 4) -> Optional[Tuple[str, int]]:
        """
        Find the best performing day of the week.
        
        Args:
            habits: Dictionary of habits
            weeks: Number of weeks to analyze
            
        Returns:
            Optional[Tuple[str, int]]: (day_name, completion_count) or None
        """
        now = datetime.now()
        day_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # Monday=0 to Sunday=6
        
        for habit in habits.values():
            for completion in habit.completion_history:
                days_ago = (now - completion).days
                if days_ago <= weeks * 7:
                    day_counts[completion.weekday()] += 1
        
        if sum(day_counts.values()) == 0:
            return None
        
        best_day = max(day_counts.items(), key=lambda pair: pair[1])
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return (day_names[best_day[0]], best_day[1])
    
    # ==================== COMPARATIVE ANALYTICS ====================
    
    @staticmethod
    def compare_habits(habits: HabitDict, habit_names: List[str]) -> Dict[str, Any]:
        """
        Compare multiple habits side by side.
        
        Args:
            habits: Dictionary of habits
            habit_names: List of habit names to compare
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        comparison = {}
        
        for name in habit_names:
            analytics = FunctionalAnalytics.get_habit_analytics(habits, name)
            if analytics:
                comparison[name] = {
                    'current_streak': analytics.current_streak,
                    'longest_streak': analytics.longest_streak,
                    'completion_rate': analytics.completion_rate,
                    'total_completions': analytics.total_completions,
                    'is_broken': analytics.is_broken
                }
        
        return comparison
    
    @staticmethod
    def get_habit_rankings(habits: HabitDict) -> Dict[str, List[Tuple[str, Any]]]:
        """
        Get rankings of habits by various metrics.
        
        Args:
            habits: Dictionary of habits
            
        Returns:
            Dict[str, List[Tuple[str, Any]]]: Rankings by different metrics
        """
        analytics_list = FunctionalAnalytics.get_all_habits_analytics(habits)
        
        if not analytics_list:
            return {}
        
        rankings = {
            'by_current_streak': sorted(
                [(a.name, a.current_streak) for a in analytics_list],
                key=lambda x: x[1],
                reverse=True
            ),
            'by_longest_streak': sorted(
                [(a.name, a.longest_streak) for a in analytics_list],
                key=lambda x: x[1],
                reverse=True
            ),
            'by_completion_rate': sorted(
                [(a.name, a.completion_rate) for a in analytics_list],
                key=lambda x: x[1],
                reverse=True
            ),
            'by_total_completions': sorted(
                [(a.name, a.total_completions) for a in analytics_list],
                key=lambda x: x[1],
                reverse=True
            ),
            'by_days_tracked': sorted(
                [(a.name, a.days_tracked) for a in analytics_list],
                key=lambda x: x[1],
                reverse=True
            )
        }
        
        return rankings

# ==================== HIGHER-ORDER FUNCTIONS ====================

def create_analytics_pipeline(habits: HabitDict, *operations: Callable) -> Any:
    """
    Create a pipeline of analytics operations.
    
    Args:
        habits: Dictionary of habits
        *operations: Functions to apply in sequence
        
    Returns:
        Any: Result of the pipeline
    """
    return reduce(lambda data, op: op(data), operations, habits)

def analyze_with_filters(habits: HabitDict, 
                        filters: List[Callable[[Habit], bool]], 
                        analyzer: Callable) -> Any:
    """
    Apply filters to habits before analysis.
    
    Args:
        habits: Dictionary of habits
        filters: List of filter functions
        analyzer: Analysis function to apply
        
    Returns:
        Any: Analysis result
    """
    filtered_habits = list(filter(
        lambda habit: all(f(habit) for f in filters),
        habits.values()
    ))
    
    return analyzer(filtered_habits)

# ==================== PRESET ANALYTICS CONFIGURATIONS ====================

class AnalyticsPresets:
    """Preset analytics configurations for common use cases."""
    
    @staticmethod
    def daily_overview(habits: HabitDict) -> Dict[str, Any]:
        """Get a comprehensive daily overview."""
        return {
            'total_habits': len(habits),
            'completed_today': sum(
                1 for habit in habits.values()
                if any(c.date() == datetime.now().date() for c in habit.completion_history)
            ),
            'active_streaks': FunctionalAnalytics.get_active_streaks(habits),
            'broken_habits': FunctionalAnalytics.get_broken_habits(habits),
            'longest_streak': FunctionalAnalytics.get_longest_streak_all(habits),
            'most_consistent': FunctionalAnalytics.get_most_consistent_habit(habits)
        }
    
    @staticmethod
    def weekly_report(habits: HabitDict) -> Dict[str, Any]:
        """Generate a weekly performance report."""
        return {
            'periodicity_stats': FunctionalAnalytics.get_periodicity_stats(habits),
            'productivity_trend': FunctionalAnalytics.get_productivity_trend(habits, 7),
            'best_day': FunctionalAnalytics.get_best_performing_day(habits, 1),
            'struggling_habits': FunctionalAnalytics.get_struggling_habits(habits, 70),
            'rankings': FunctionalAnalytics.get_habit_rankings(habits)
        }
    
    @staticmethod
    def monthly_analysis(habits: HabitDict) -> Dict[str, Any]:
        """Perform a comprehensive monthly analysis."""
        return {
            'all_analytics': FunctionalAnalytics.get_all_habits_analytics(habits),
            'completions_by_month': FunctionalAnalytics.get_completions_by_period(
                habits, 
                AnalyticsPeriod.MONTH
            ),
            'habit_comparison': FunctionalAnalytics.compare_habits(
                habits,
                list(habits.keys())[:5]  # Compare first 5 habits
            ),
            'total_completions': FunctionalAnalytics.get_total_completions(habits)
        }