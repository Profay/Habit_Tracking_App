# habitmanager.py

"""
HabitManager - Central Controller for Habit Tracking Application

This module integrates all components of the habit tracking application:
- Habit class for data modeling
- StorageHandler for data persistence
- FunctionalAnalytics for data analysis
- Provides a clean API for CLI and other interfaces
"""

from typing import List, Dict, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import all components
from habit import Habit, Periodicity
from storage_handler import (
    StorageHandler, 
    StorageFactory, 
    StorageError,
    JSONStorageHandler,
    SQLiteStorageHandler
)
from functional_analytics import (
    FunctionalAnalytics,
    AnalyticsPresets,
    HabitAnalytics,
    AnalyticsPeriod,
    create_analytics_pipeline,
    analyze_with_filters
)

class HabitManager:
    """
    Central controller for managing habits in the tracking application.
    
    This class serves as the main hub that integrates:
    - Habit CRUD operations
    - Data persistence through StorageHandler
    - Analytics through FunctionalAnalytics
    - Predefined data management
    - Help and documentation
    
    Attributes:
        storage (StorageHandler): Storage backend instance
        habits (Dict[str, Habit]): In-memory cache of habits
        analytics (FunctionalAnalytics): Analytics engine instance
    """
    
    def __init__(self, storage_type: str = 'json', storage_path: Optional[str] = None):
        """
        Initialize the HabitManager with specified storage backend.
        
        Args:
            storage_type: Type of storage ('json' or 'sqlite')
            storage_path: Custom path for storage file
            
        Raises:
            ValueError: If storage_type is not supported
            StorageError: If storage initialization fails
        """
        # Initialize storage
        if storage_path is None:
            storage_path = f"habits.{storage_type}"
        
        try:
            self.storage = StorageFactory.create_storage_handler(
                storage_type=storage_type,
                file_path=storage_path
            )
        except ValueError as e:
            raise ValueError(f"Invalid storage type: {e}")
        except Exception as e:
            raise StorageError(f"Failed to initialize storage: {e}")
        
        # Initialize other components
        self.habits: Dict[str, Habit] = {}
        self.analytics = FunctionalAnalytics()
        
        # Load existing data
        self.load_data()
    
    # ==================== HABIT MANAGEMENT METHODS ====================
    
    def create_habit(self, name: str, description: str, periodicity: Periodicity) -> Habit:
        """
        Create a new habit and add it to the manager.
        
        Args:
            name: Name of the habit (must be unique)
            description: Description of what the habit entails
            periodicity: How often the habit should be completed
            
        Returns:
            Habit: The created habit instance
            
        Raises:
            ValueError: If habit with same name already exists
        """
        if name in self.habits:
            raise ValueError(f"Habit '{name}' already exists")
        
        habit = Habit(name, description, periodicity)
        self.habits[name] = habit
        self.save_data()
        return habit
    
    def delete_habit(self, name: str) -> bool:
        """
        Delete a habit by name.
        
        Args:
            name: Name of the habit to delete
            
        Returns:
            bool: True if habit was deleted, False if not found
        """
        if name in self.habits:
            del self.habits[name]
            self.save_data()
            return True
        return False
    
    def get_habit(self, name: str) -> Optional[Habit]:
        """
        Get a habit by name.
        
        Args:
            name: Name of the habit to retrieve
            
        Returns:
            Optional[Habit]: The habit if found, None otherwise
        """
        return self.habits.get(name)
    
    def update_habit(self, name: str, **kwargs) -> bool:
        """
        Update habit properties.
        
        Args:
            name: Name of the habit to update
            **kwargs: Properties to update (description, periodicity)
            
        Returns:
            bool: True if updated successfully, False if not found
        """
        habit = self.get_habit(name)
        if not habit:
            return False
        
        # Update allowed properties
        if 'description' in kwargs:
            habit.description = kwargs['description']
        
        if 'periodicity' in kwargs:
            if isinstance(kwargs['periodicity'], str):
                habit.periodicity = Periodicity(kwargs['periodicity'])
            else:
                habit.periodicity = kwargs['periodicity']
        
        self.save_data()
        return True
    
    # ==================== COMPLETION METHODS ====================
    
    def complete_habit(self, name: str, completion_time: Optional[datetime] = None) -> bool:
        """
        Mark a habit as completed at a specific time.
        
        Args:
            name: Name of the habit to complete
            completion_time: When the habit was completed (defaults to now)
            
        Returns:
            bool: True if successfully completed, False if habit not found
            
        Raises:
            ValueError: If habit already completed for this period
        """
        habit = self.get_habit(name)
        if habit:
            habit.check_off(completion_time)
            self.save_data()
            return True
        return False
    
    def complete_multiple_habits(self, habit_names: List[str], 
                                completion_time: Optional[datetime] = None) -> Dict[str, bool]:
        """
        Complete multiple habits at once.
        
        Args:
            habit_names: List of habit names to complete
            completion_time: Completion time for all habits
            
        Returns:
            Dict[str, bool]: Mapping of habit names to success status
        """
        results = {}
        for name in habit_names:
            results[name] = self.complete_habit(name, completion_time)
        return results
    
    def undo_completion(self, name: str, completion_time: datetime) -> bool:
        """
        Undo a habit completion.
        
        Args:
            name: Name of the habit
            completion_time: The completion time to undo
            
        Returns:
            bool: True if successfully undone
        """
        habit = self.get_habit(name)
        if habit and completion_time in habit.completion_history:
            habit.completion_history.remove(completion_time)
            self.save_data()
            return True
        return False
    
    # ==================== DATA PERSISTENCE METHODS ====================
    
    def save_data(self) -> None:
        """Save all habits to storage."""
        try:
            self.storage.save_habits(self.habits)
        except StorageError as e:
            raise StorageError(f"Failed to save data: {e}")
    
    def load_data(self) -> None:
        """Load habits from storage."""
        try:
            self.habits = self.storage.load_habits()
        except StorageError as e:
            print(f"Warning: Failed to load data: {e}")
            self.habits = {}
    
    def backup_data(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the current data.
        
        Args:
            backup_path: Custom path for backup file
            
        Returns:
            bool: True if backup successful
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_type = type(self.storage).__name__.lower().replace('storagehandler', '')
            backup_path = f"backups/habits_backup_{timestamp}.{storage_type}"
        
        return self.storage.backup_data(backup_path)
    
    def restore_data(self, backup_path: str) -> bool:
        """
        Restore data from a backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore successful
        """
        try:
            # Create temporary storage handler for backup
            backup_storage = StorageFactory.create_storage_handler(
                storage_type='json' if backup_path.endswith('.json') else 'sqlite',
                file_path=backup_path
            )
            
            # Load from backup
            backup_habits = backup_storage.load_habits()
            
            # Validate data
            for name, habit in backup_habits.items():
                if not isinstance(habit, Habit):
                    raise ValueError(f"Invalid habit data in backup: {name}")
            
            # Replace current data
            self.habits = backup_habits
            self.save_data()
            return True
            
        except Exception as e:
            print(f"Failed to restore backup: {e}")
            return False
    
    def export_data(self, export_path: str, format: str = 'json') -> bool:
        """
        Export habits data to a file.
        
        Args:
            export_path: Path to export file
            format: Export format ('json' or 'csv')
            
        Returns:
            bool: True if export successful
        """
        try:
            if format.lower() == 'json':
                data = {
                    'export_date': datetime.now().isoformat(),
                    'habits': {name: habit.to_dict() for name, habit in self.habits.items()}
                }
                
                with open(export_path, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            elif format.lower() == 'csv':
                import csv
                
                with open(export_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Name', 'Description', 'Periodicity', 
                                   'Creation Date', 'Total Completions', 
                                   'Current Streak', 'Longest Streak'])
                    
                    for habit in self.habits.values():
                        writer.writerow([
                            habit.name,
                            habit.description,
                            habit.periodicity.value,
                            habit.creation_date.isoformat(),
                            len(habit.completion_history),
                            habit.calculate_current_streak(),
                            habit.calculate_longest_streak()
                        ])
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the current storage backend."""
        return self.storage.get_storage_info()
    
    # ==================== ANALYTICS INTEGRATION METHODS ====================
    
    def get_all_habits(self) -> List[Habit]:
        """Return all habits using functional analytics."""
        return self.analytics.get_all_habits(self.habits)
    
    def get_habits_by_periodicity(self, periodicity: Periodicity) -> List[Habit]:
        """Return habits by periodicity using functional analytics."""
        return self.analytics.get_habits_by_periodicity(self.habits, periodicity)
    
    def get_longest_streak_all(self) -> Tuple[int, Optional[Habit]]:
        """Get longest streak using functional analytics."""
        return self.analytics.get_longest_streak_all(self.habits)
    
    def get_longest_streak_for_habit(self, habit_name: str) -> int:
        """Get longest streak for specific habit using functional analytics."""
        return self.analytics.get_longest_streak_for_habit(self.habits, habit_name)
    
    def get_daily_overview(self) -> Dict[str, Any]:
        """Get daily overview using preset analytics."""
        return AnalyticsPresets.daily_overview(self.habits)
    
    def get_weekly_report(self) -> Dict[str, Any]:
        """Get weekly report using preset analytics."""
        return AnalyticsPresets.weekly_report(self.habits)
    
    def get_monthly_analysis(self) -> Dict[str, Any]:
        """Get monthly analysis using preset analytics."""
        return AnalyticsPresets.monthly_analysis(self.habits)
    
    def get_habit_analytics(self, habit_name: str) -> Optional[HabitAnalytics]:
        """Get detailed analytics for a specific habit."""
        return self.analytics.get_habit_analytics(self.habits, habit_name)
    
    def get_all_habits_analytics(self) -> List[HabitAnalytics]:
        """Get detailed analytics for all habits."""
        return self.analytics.get_all_habits_analytics(self.habits)
    
    def get_broken_habits(self) -> List[str]:
        """Get list of currently broken habits."""
        return self.analytics.get_broken_habits(self.habits)
    
    def get_active_streaks(self) -> List[Tuple[str, int]]:
        """Get all habits with their current streaks."""
        return self.analytics.get_all_current_streaks(self.habits)
    
    def get_struggling_habits(self, threshold: float = 50.0) -> List[Tuple[str, float]]:
        """Get habits with completion rate below threshold."""
        return self.analytics.get_struggling_habits(self.habits, threshold)
    
    def get_periodicity_stats(self) -> Dict[str, Any]:
        """Get statistics grouped by periodicity."""
        return self.analytics.get_periodicity_stats(self.habits)
    
    def get_completion_rate(self, habit_name: str, days: int = 30) -> float:
        """Get completion rate for a specific habit."""
        habit = self.get_habit(habit_name)
        return self.analytics.get_completion_rate(habit, days) if habit else 0.0
    
    def get_total_completions(self) -> int:
        """Get total number of completions across all habits."""
        return self.analytics.get_total_completions(self.habits)
    
    def get_productivity_trend(self, days: int = 30) -> Dict[str, int]:
        """Get productivity trend over time."""
        return self.analytics.get_productivity_trend(self.habits, days)
    
    def get_best_performing_day(self, weeks: int = 4) -> Optional[Tuple[str, int]]:
        """Find the best performing day of the week."""
        return self.analytics.get_best_performing_day(self.habits, weeks)
    
    def compare_habits(self, habit_names: List[str]) -> Dict[str, Any]:
        """Compare multiple habits side by side."""
        return self.analytics.compare_habits(self.habits, habit_names)
    
    def get_habit_rankings(self) -> Dict[str, List[Tuple[str, Any]]]:
        """Get rankings of habits by various metrics."""
        return self.analytics.get_habit_rankings(self.habits)
    
    # ==================== ADVANCED ANALYTICS METHODS ====================
    
    def run_custom_analytics(self, 
                           filters: List[callable] = None,
                           analyzer: callable = None) -> Any:
        """
        Run custom analytics with filters and analyzer.
        
        Args:
            filters: List of filter functions
            analyzer: Analysis function to apply
            
        Returns:
            Any: Analysis result
        """
        if filters is None:
            filters = []
        
        if analyzer is None:
            analyzer = lambda habits: len(habits)
        
        return analyze_with_filters(self.habits, filters, analyzer)
    
    def create_analytics_pipeline(self, *operations: callable) -> Any:
        """
        Create a pipeline of analytics operations.
        
        Args:
            *operations: Functions to apply in sequence
            
        Returns:
            Any: Result of the pipeline
        """
        return create_analytics_pipeline(self.habits, *operations)
    
    # ==================== PREDEFINED HABITS METHODS ====================
    
    def create_predefined_habits(self) -> None:
        """Create predefined habits with sample data for testing."""
        predefined_habits = [
            {
                'name': 'Drink Water',
                'description': 'Drink 8 glasses of water daily',
                'periodicity': Periodicity.DAILY,
                'completions': self._generate_sample_completions(Periodicity.DAILY, 28)
            },
            {
                'name': 'Exercise',
                'description': '30 minutes of physical activity',
                'periodicity': Periodicity.DAILY,
                'completions': self._generate_sample_completions(Periodicity.DAILY, 25)
            },
            {
                'name': 'Read',
                'description': 'Read for 20 minutes',
                'periodicity': Periodicity.DAILY,
                'completions': self._generate_sample_completions(Periodicity.DAILY, 20)
            },
            {
                'name': 'Weekly Review',
                'description': 'Review weekly goals and progress',
                'periodicity': Periodicity.WEEKLY,
                'completions': self._generate_sample_completions(Periodicity.WEEKLY, 4)
            },
            {
                'name': 'Grocery Shopping',
                'description': 'Buy weekly groceries',
                'periodicity': Periodicity.WEEKLY,
                'completions': self._generate_sample_completions(Periodicity.WEEKLY, 3)
            }
        ]
        
        created_count = 0
        for habit_data in predefined_habits:
            if habit_data['name'] not in self.habits:
                habit = self.create_habit(
                    habit_data['name'],
                    habit_data['description'],
                    habit_data['periodicity']
                )
                
                # Add sample completions
                for completion_time in habit_data['completions']:
                    try:
                        habit.check_off(completion_time)
                    except ValueError:
                        # Ignore duplicate completions in sample data
                        pass
                
                created_count += 1
        
        if created_count > 0:
            self.save_data()
            print(f"Created {created_count} predefined habits with sample data.")
    
    def _generate_sample_completions(self, periodicity: Periodicity, days: int) -> List[datetime]:
        """Generate sample completion data for testing."""
        completions = []
        now = datetime.now()
        
        if periodicity == Periodicity.DAILY:
            for i in range(days):
                # Randomly miss some days (about 20%)
                if i % 5 != 0:
                    completion_time = now - timedelta(days=i)
                    completions.append(completion_time)
        elif periodicity == Periodicity.WEEKLY:
            weeks = min(days // 7, 4)
            for i in range(weeks):
                completion_time = now - timedelta(weeks=i)
                completions.append(completion_time)
        elif periodicity == Periodicity.MONTHLY:
            months = min(days // 30, 3)
            for i in range(months):
                completion_time = now - timedelta(days=i*30)
                completions.append(completion_time)
        
        return completions
    
    # ==================== UTILITY METHODS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about all habits."""
        return {
            'total_habits': len(self.habits),
            'daily_habits': len(self.get_habits_by_periodicity(Periodicity.DAILY)),
            'weekly_habits': len(self.get_habits_by_periodicity(Periodicity.WEEKLY)),
            'monthly_habits': len(self.get_habits_by_periodicity(Periodicity.MONTHLY)),
            'yearly_habits': len(self.get_habits_by_periodicity(Periodicity.YEARLY)),
            'total_completions': self.get_total_completions(),
            'broken_habits': len(self.get_broken_habits()),
            'active_streaks': len([s for s in self.get_active_streaks() if s[1] > 0]),
            'storage_info': self.get_storage_info()
        }
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of habit data.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        issues = []
        warnings = []
        
        for name, habit in self.habits.items():
            # Check for duplicate completions
            if len(habit.completion_history) != len(set(habit.completion_history)):
                issues.append(f"Habit '{name}' has duplicate completions")
            
            # Check for future completions
            future_completions = [c for c in habit.completion_history if c > datetime.now()]
            if future_completions:
                warnings.append(f"Habit '{name}' has {len(future_completions)} future completions")
            
            # Check for very old creation dates
            if (datetime.now() - habit.creation_date).days > 365:
                warnings.append(f"Habit '{name}' is over a year old")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'total_habits': len(self.habits)
        }
    
    # ==================== HELP AND DOCUMENTATION ====================
    
    @staticmethod
    def get_help_text() -> str:
        """Get comprehensive help text for all available commands."""
        return """
╔══════════════════════════════════════════════════════════════╗
║                    HABIT TRACKER - HELP                       ║
╠══════════════════════════════════════════════════════════════╣
║ COMMANDS:                                                     ║
║                                                               ║
║  HABIT MANAGEMENT:                                            ║
║  create <name> <periodicity> [description]                   ║
║    Create a new habit                                         ║
║    Example: create Exercise daily "30 min workout"           ║
║                                                               ║
║  delete <name>                                               ║
║    Delete a habit                                             ║
║    Example: delete Exercise                                   ║
║                                                               ║
║  update <name> <property> <value>                            ║
║    Update habit properties                                    ║
║    Example: update Exercise description "45 min workout"     ║
║                                                               ║
║  complete <name> [date]                                      ║
║    Mark a habit as completed                                  ║
║    Example: complete Exercise                                 ║
║    Example: complete Exercise 2024-01-15                      ║
║                                                               ║
║  undo <name> <date>                                          ║
║    Undo a habit completion                                    ║
║    Example: undo Exercise 2024-01-15                          ║
║                                                               ║
║  VIEWING HABITS:                                              ║
║  list [periodicity]                                          ║
║    List all habits or filter by periodicity                   ║
║    Example: list                                              ║
║    Example: list daily                                        ║
║                                                               ║
║  status <name>                                               ║
║    Show detailed status of a specific habit                   ║
║    Example: status Exercise                                   ║
║                                                               ║
║  ANALYTICS:                                                   ║
║  analytics <type>                                            ║
║    Run analytics: daily, weekly, monthly                     ║
║    Example: analytics daily                                   ║
║                                                               ║
║  streaks                                                      ║
║    Show all habits with their current streaks                 ║
║                                                               ║
║  longest [habit_name]                                        ║
║    Show longest streak (all habits or specific one)           ║
║    Example: longest                                           ║
║    Example: longest Exercise                                  ║
║                                                               ║
║  broken                                                       ║
║    Show all currently broken habits                           ║
║                                                               ║
║  struggling [threshold]                                      ║
║    Show habits with low completion rates                      ║
║    Example: struggling 50                                     ║
║                                                               ║
║  compare <habit1> <habit2> [...]                             ║
║    Compare multiple habits side by side                       ║
║    Example: compare Exercise Read Meditation                  ║
║                                                               ║
║  rankings                                                     ║
║    Show habit rankings by various metrics                     ║
║                                                               ║
║  DATA MANAGEMENT:                                             ║
║  backup [path]                                                ║
║    Create a backup of habit data                              ║
║    Example: backup                                            ║
║    Example: backup /path/to/backup.json                       ║
║                                                               ║
║  restore <path>                                               ║
║    Restore data from backup                                   ║
║    Example: restore backup_20240115.json                      ║
║                                                               ║
║  export <path> <format>                                      ║
║    Export data to JSON or CSV                                 ║
║    Example: export export.json json                           ║
║    Example: export export.csv csv                             ║
║                                                               ║
║  preload                                                      ║
║    Load predefined habits with sample data                    ║
║                                                               ║
║  stats                                                        ║
║    Show comprehensive statistics                              ║
║                                                               ║
║  validate                                                     ║
║    Validate data integrity                                    ║
║                                                               ║
║  help                                                         ║
║    Show this help message                                     ║
║                                                               ║
║  exit                                                         ║
║    Exit the application                                       ║
║                                                               ║
║ PERIODICITY OPTIONS:                                          ║
║  daily, weekly, monthly, yearly                               ║
║                                                               ║
║ DATE FORMAT:                                                  ║
║  YYYY-MM-DD (e.g., 2024-01-15)                               ║
║                                                               ║
║ EXAMPLES:                                                     ║
║  > create Exercise daily "30 min workout"                    ║
║  > complete Exercise                                          ║
║  > analytics daily                                            ║
║  > streaks                                                    ║
║  > backup                                                     ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
        """
    
    @staticmethod
    def get_command_examples() -> str:
        """Get example commands for quick reference."""
        return """
╔══════════════════════════════════════════════════════════════╗
║                    QUICK EXAMPLES                             ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Creating habits:                                             ║
║    > create Exercise daily "30 min workout"                  ║
║    > create Meditation daily "10 min meditation"              ║
║    > create WeeklyReview weekly "Review weekly goals"         ║
║                                                               ║
║  Managing habits:                                             ║
║    > complete Exercise                                        ║
║    > list daily                                               ║
║    > status Exercise                                          ║
║    > delete Exercise                                          ║
║                                                               ║
║  Analytics:                                                   ║
║    > analytics daily                                          ║
║    > streaks                                                  ║
║    > longest                                                  ║
║    > broken                                                   ║
║                                                               ║
║  Data management:                                             ║
║    > backup                                                   ║
║    > export habits.csv csv                                    ║
║    > preload                                                  ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
        """
    
    def __str__(self) -> str:
        """String representation of the manager."""
        return f"HabitManager with {len(self.habits)} habits ({type(self.storage).__name__})"
    
    def __repr__(self) -> str:
        """Official string representation of the manager."""
        return f"HabitManager(habits={len(self.habits)}, storage={type(self.storage).__name__})"

# ==================== FACTORY FUNCTIONS ====================

def create_habit_manager(storage_type: str = 'json', 
                        storage_path: Optional[str] = None,
                        create_sample_data: bool = False) -> HabitManager:
    """
    Factory function to create a configured HabitManager.
    
    Args:
        storage_type: Type of storage backend
        storage_path: Custom storage path
        create_sample_data: Whether to create sample data
        
    Returns:
        HabitManager: Configured instance
    """
    manager = HabitManager(storage_type=storage_type, storage_path=storage_path)
    
    if create_sample_data and not manager.habits:
        manager.create_predefined_habits()
    
    return manager

def migrate_storage(source_path: str, 
                   source_type: str,
                   target_path: str,
                   target_type: str) -> bool:
    """
    Migrate data from one storage type to another.
    
    Args:
        source_path: Path to source storage file
        source_type: Type of source storage
        target_path: Path to target storage file
        target_type: Type of target storage
        
    Returns:
        bool: True if migration successful
    """
    try:
        # Load from source
        source_storage = StorageFactory.create_storage_handler(
            storage_type=source_type,
            file_path=source_path
        )
        habits = source_storage.load_habits()
        
        # Save to target
        target_storage = StorageFactory.create_storage_handler(
            storage_type=target_type,
            file_path=target_path
        )
        target_storage.save_habits(habits)
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False