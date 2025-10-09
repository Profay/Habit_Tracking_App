# test_cli.py

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from io import StringIO
import sys

# Adjust imports based on your project structure
from habit_tracker.cli import CLIInterface, CLIArgumentParser, main
from habit_tracker.habit import Periodicity

# --- Mocks and Fixtures ---

class MockHabit:
    """A simple mock for the Habit class."""
    def __init__(self, name, periodicity, description="Test description", is_broken=False):
        self.name = name
        self.periodicity = periodicity
        self.description = description
        self.completion_history = [datetime.now() - timedelta(days=i) for i in range(5)]
        self._is_broken = is_broken

    def calculate_current_streak(self):
        return 5 if not self._is_broken else 0

    def is_broken(self):
        return self._is_broken

@pytest.fixture
def mock_manager():
    """Provides a MagicMock of HabitManager with common methods configured."""
    manager = MagicMock()
    
    # --- FIX: Use side_effect for dynamic return values based on arguments ---
    
    # Mock create_habit to return a habit with the correct name
    def mock_create_habit(name, description, periodicity):
        return MockHabit(name, periodicity, description)
    manager.create_habit.side_effect = mock_create_habit

    # Mock get_habit to find a habit in a predefined list
    mock_habits = [
        MockHabit("Exercise", Periodicity.DAILY, "30 min workout"),
        MockHabit("Read", Periodicity.WEEKLY, "Read a book chapter")
    ]
    def mock_get_habit(name):
        return next((h for h in mock_habits if h.name == name), None)
    manager.get_habit.side_effect = mock_get_habit

    # --- End of Fixes ---

    # Mock return values for other manager methods
    manager.delete_habit.return_value = True
    manager.complete_habit.return_value = True
    manager.get_all_habits.return_value = mock_habits
    manager.get_habits_by_periodicity.return_value = [mock_habits[0]]

    manager.get_active_streaks.return_value = [("Exercise", 10), ("Read", 2)]
    manager.get_longest_streak_all.return_value = (15, mock_habits[0])
    manager.get_longest_streak_for_habit.return_value = 12
    manager.get_broken_habits.return_value = []
    
    # --- FIX: Correctly configure the mock_analytics object ---
    mock_analytics = MagicMock()
    mock_analytics.name = "Exercise"
    mock_analytics.periodicity = "daily"
    mock_analytics.created_date = datetime.now() - timedelta(days=30)
    mock_analytics.days_tracked = 25
    mock_analytics.current_streak = 5
    mock_analytics.longest_streak = 10
    mock_analytics.total_completions = 20
    mock_analytics.completion_rate = 80.0
    mock_analytics.is_broken = False
    mock_analytics.last_completion = datetime.now()
    # --- End of Fix ---

    manager.get_habit_analytics.return_value = mock_analytics
    
    manager.get_daily_overview.return_value = {
        'total_habits': 2, 'completed_today': 1, 'longest_streak': (10, mock_habits[0]),
        'most_consistent': ("Exercise", 90.0), 'broken_habits': []
    }
    manager.get_weekly_report.return_value = {
        'periodicity_stats': {'daily': {'count': 1, 'completion_rate': 100.0}},
        'best_day': ('Monday', 5), 'struggling_habits': []
    }
    manager.get_monthly_analysis.return_value = {
        'all_analytics': [mock_analytics],
        'completions_by_month': {'2023-11': 15, '2023-12': 20}
    }
    
    manager.get_help_text.return_value = "This is the help text."
    manager.backup_data.return_value = True
    manager.create_predefined_habits.return_value = None
    
    return manager

@pytest.fixture
def cli(mock_manager):
    """Provides a CLIInterface instance with a mock manager."""
    return CLIInterface(mock_manager)

# --- Test Cases for CLIInterface ---

class TestCLIInterface:
    """Tests for the main CLIInterface class."""

    def test_init(self, cli, mock_manager):
        """Test CLIInterface initialization."""
        assert cli.manager == mock_manager
        assert cli.running is True
        assert 'create' in cli.commands
        assert 'exit' in cli.commands

    # --- Command Tests ---

    def test_cmd_create_success(self, cli, mock_manager, capsys):
        """Test successful habit creation."""
        cli.cmd_create(['Meditation', 'daily', '10 min of peace'])
        mock_manager.create_habit.assert_called_once_with('Meditation', '10 min of peace', Periodicity.DAILY)
        captured = capsys.readouterr()
        assert "✅ Created habit: Meditation (daily)" in captured.out
        assert "Description: 10 min of peace" in captured.out

    def test_cmd_create_missing_args(self, cli, mock_manager, capsys):
        """Test create command with missing arguments."""
        cli.cmd_create(['Meditation'])
        mock_manager.create_habit.assert_not_called()
        captured = capsys.readouterr()
        assert "❌ Usage: create <name> <periodicity> [description]" in captured.out

    def test_cmd_delete_success(self, cli, mock_manager, capsys):
        """Test successful habit deletion."""
        cli.cmd_delete(['Exercise'])
        mock_manager.delete_habit.assert_called_once_with('Exercise')
        captured = capsys.readouterr()
        assert "✅ Deleted habit: Exercise" in captured.out

    def test_cmd_delete_not_found(self, cli, mock_manager, capsys):
        """Test deleting a habit that doesn't exist."""
        mock_manager.delete_habit.return_value = False
        cli.cmd_delete(['NonExistent'])
        captured = capsys.readouterr()
        assert "❌ Habit not found: NonExistent" in captured.out

    def test_cmd_complete_success(self, cli, mock_manager, capsys):
        """Test successfully marking a habit as complete."""
        cli.cmd_complete(['Exercise'])
        mock_manager.complete_habit.assert_called_once_with('Exercise', None)
        captured = capsys.readouterr()
        assert "✅ Completed habit: Exercise" in captured.out

    def test_cmd_complete_with_date(self, cli, mock_manager, capsys):
        """Test marking a habit complete with a specific date."""
        cli.cmd_complete(['Exercise', '2024-01-15'])
        expected_date = datetime(2024, 1, 15)
        mock_manager.complete_habit.assert_called_once_with('Exercise', expected_date)
        captured = capsys.readouterr()
        assert "✅ Completed habit: Exercise on 2024-01-15" in captured.out

    def test_cmd_complete_invalid_date(self, cli, mock_manager, capsys):
        """Test complete command with an invalid date format."""
        cli.cmd_complete(['Exercise', 'yesterday'])
        mock_manager.complete_habit.assert_not_called()
        captured = capsys.readouterr()
        assert "❌ Invalid date format. Use YYYY-MM-DD" in captured.out

    def test_cmd_list_all(self, cli, mock_manager, capsys):
        """Test listing all habits."""
        cli.cmd_list([])
        mock_manager.get_all_habits.assert_called_once()
        captured = capsys.readouterr()
        assert "📋 All Habits (2 total):" in captured.out
        assert "Exercise" in captured.out
        assert "Read" in captured.out

    def test_cmd_list_by_periodicity(self, cli, mock_manager, capsys):
        """Test listing habits filtered by periodicity."""
        cli.cmd_list(['daily'])
        mock_manager.get_habits_by_periodicity.assert_called_once_with(Periodicity.DAILY)
        captured = capsys.readouterr()
        assert "📋 Daily Habits (1 total):" in captured.out
        assert "Exercise" in captured.out
        assert "Read" not in captured.out

    def test_cmd_analytics_daily(self, cli, mock_manager, capsys):
        """Test the daily analytics command."""
        cli.cmd_analytics(['daily'])
        mock_manager.get_daily_overview.assert_called_once()
        captured = capsys.readouterr()
        assert "📊 Daily Overview" in captured.out
        assert "Total Habits: 2" in captured.out

    def test_cmd_streaks(self, cli, mock_manager, capsys):
        """Test showing current streaks."""
        cli.cmd_streaks([])
        mock_manager.get_active_streaks.assert_called_once()
        captured = capsys.readouterr()
        assert "🔥 Current Streaks:" in captured.out
        assert "Exercise: 10 days" in captured.out

    def test_cmd_longest_all(self, cli, mock_manager, capsys):
        """Test showing the longest streak across all habits."""
        cli.cmd_longest([])
        mock_manager.get_longest_streak_all.assert_called_once()
        captured = capsys.readouterr()
        assert "🏆 Longest streak overall: 15 days" in captured.out
        assert "Habit: Exercise" in captured.out

    def test_cmd_status(self, cli, mock_manager, capsys):
        """Test showing the status of a specific habit."""
        cli.cmd_status(['Exercise'])
        mock_manager.get_habit_analytics.assert_called_once_with('Exercise')
        mock_manager.get_habit.assert_called_once_with('Exercise') # Check that get_habit was called for description
        captured = capsys.readouterr()
        assert "📊 Status Report: Exercise" in captured.out # This assertion should now pass
        assert "Description: 30 min workout" in captured.out
        assert "Completion Rate: 80.0%" in captured.out

    def test_cmd_broken_none(self, cli, mock_manager, capsys):
        """Test when there are no broken habits."""
        cli.cmd_broken([])
        captured = capsys.readouterr()
        assert "✅ No broken habits! Keep it up!" in captured.out

    def test_cmd_preload(self, cli, mock_manager, capsys):
        """Test the preload command."""
        cli.cmd_preload([])
        mock_manager.create_predefined_habits.assert_called_once()
        captured = capsys.readouterr()
        assert "✅ Predefined habits loaded with sample data!" in captured.out

    def test_cmd_backup(self, cli, mock_manager, capsys):
        """Test the backup command."""
        cli.cmd_backup([])
        mock_manager.backup_data.assert_called_once()
        captured = capsys.readouterr()
        assert "✅ Backup created successfully!" in captured.out

    def test_cmd_help(self, cli, mock_manager, capsys):
        """Test the help command."""
        cli.cmd_help([])
        mock_manager.get_help_text.assert_called_once()
        captured = capsys.readouterr()
        assert "This is the help text." in captured.out

    def test_cmd_exit(self, cli):
        """Test the exit command sets running to False."""
        assert cli.running is True
        cli.cmd_exit([])
        assert cli.running is False

    # --- Main Interface Method Tests ---

    def test_run_single_command(self, cli, mock_manager, capsys):
        """Test executing a single command directly."""
        cli.run_single_command(['create', 'TestHabit', 'weekly'])
        mock_manager.create_habit.assert_called_once_with('TestHabit', 'Track TestHabit', Periodicity.WEEKLY)
        captured = capsys.readouterr()
        assert "✅ Created habit: TestHabit (weekly)" in captured.out

    def test_run_single_command_unknown(self, cli, mock_manager, capsys):
        """Test executing an unknown single command triggers sys.exit."""
        with pytest.raises(SystemExit) as e:
            cli.run_single_command(['unknowncommand'])
        assert e.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Unknown command: unknowncommand" in captured.out

    @patch('builtins.input', side_effect=['help', 'exit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_interactive(self, mock_stdout, mock_input, cli):
        """Test the interactive mode loop."""
        cli.run_interactive()
        
        output = mock_stdout.getvalue()
        assert "🎯 HABIT TRACKER - CLI INTERFACE" in output
        assert "📋 Main Menu:" in output
        assert "This is the help text." in output
        assert "👋 Goodbye! Keep tracking those habits!" in output
        assert cli.running is False

# --- Test Cases for Argument Parser and Main ---

class TestCLIArgumentParser:
    """Tests for the CLIArgumentParser."""

    def test_parse_args_interactive_mode(self):
        """Test parsing arguments for interactive mode (no command)."""
        args = CLIArgumentParser.parse_args([])
        assert args.command is None
        assert args.storage == 'json'

    def test_parse_args_single_command(self):
        """Test parsing arguments for a single command."""
        args = CLIArgumentParser.parse_args(['list', '--storage', 'sqlite'])
        assert args.command == 'list'
        assert args.storage == 'sqlite'

class TestMainFunction:
    """Tests for the main entry point of the application."""

    @patch('habit_tracker.cli.CLIInterface')
    @patch('habit_tracker.cli.HabitManager')
    @patch('sys.argv', ['cli.py'])
    def test_main_interactive_mode(self, mock_manager_class, mock_cli_class):
        """Test main() enters interactive mode when no command is given."""
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        
        main()
        
        mock_manager_class.assert_called_once_with(storage_type='json', storage_path=None)
        mock_cli_class.assert_called_once()
        mock_cli_instance.run_interactive.assert_called_once()

    @patch('habit_tracker.cli.CLIInterface')
    @patch('habit_tracker.cli.HabitManager')
    @patch('sys.argv', ['cli.py', 'list', '--storage', 'sqlite'])
    def test_main_single_command_mode(self, mock_manager_class, mock_cli_class):
        """Test main() runs a single command when arguments are provided."""
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        
        main()
        
        mock_manager_class.assert_called_once_with(storage_type='sqlite', storage_path=None)
        mock_cli_instance.run_single_command.assert_called_once_with(['list'])