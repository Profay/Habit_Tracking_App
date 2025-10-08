# Habit_Tracking_App
Tracking User Habit 
# Create a daily habit
daily_habit = Habit("Exercise", "30 minutes of exercise", Periodicity.DAILY)

# Create a weekly habit
weekly_habit = Habit("Grocery Shopping", "Buy weekly groceries", Periodicity.WEEKLY)

# Check off habits
daily_habit.check_off()
weekly_habit.check_off()

# Calculate streaks
print(daily_habit.calculate_current_streak())  # Output: 1
print(weekly_habit.calculate_longest_streak())  # Output: 1

# Check if broken
print(daily_habit.is_broken())  # Output: False


# Initialize the manager
manager = HabitManager()

# Create habits
manager.create_habit("Exercise", "30 min workout", Periodicity.DAILY)
manager.create_habit("Weekly Review", "Review goals", Periodicity.WEEKLY)

# Complete habits
manager.complete_habit("Exercise")

# Get analytics
all_habits = manager.get_all_habits()
daily_habits = manager.get_habits_by_periodicity(Periodicity.DAILY)
longest_streak, habit = manager.get_longest_streak_all()

# Load predefined habits with sample data
manager.create_predefined_habits()

# Get help
print(manager.get_help_text())
print(manager.get_command_examples())

# CLI command mapping examples
cli_commands = {
    'create': manager.create_habit,
    'delete': manager.delete_habit,
    'complete': manager.complete_habit,
    'list': manager.get_all_habits,
    'longest': manager.get_longest_streak_all,
    'help': manager.get_help_text
}

# Using JSON storage (default)
json_manager = HabitManager(storage_type='json')

# Using SQLite storage
sqlite_manager = HabitManager(storage_type='sqlite')

# Create habits
json_manager.create_habit("Exercise", "30 min workout", Periodicity.DAILY)

# Get storage information
print(json_manager.get_storage_info())

# Create backup
json_manager.backup_data()

# Get storage help
print(StorageFactory.get_storage_help())

# Create a habit
python main.py create Exercise daily "30 min workout"

# Complete a habit
python main.py complete Exercise

# List all habits
python main.py list

# View analytics
python main.py analytics daily

# Show help
python main.py help

habit_tracker/
├── habit.py                    # Habit class and Periodicity enum
├── functional_analytics.py     # FunctionalAnalytics class and presets
├── storage_handler.py          # StorageHandler classes and factory
├── habitmanager.py            # HabitManager class with analytics
├── cli.py                     # CLI interface
├── main.py                    # Entry point
├── tests/                     # Unit tests
│   ├── test_habit.py
│   ├── test_analytics.py
│   ├── test_storage.py
│   └── test_cli.py
└── README.md