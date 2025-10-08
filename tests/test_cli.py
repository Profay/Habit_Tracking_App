# test_cli.py

"""
Unit tests for the CLI Interface component.

This test suite covers:
- Command parsing and execution
- CLI output verification
- Error handling
- Integration with HabitManager
- Both interactive and single command modes
"""

import pytest
import sys
import io
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from pathlib import Path

# Import the components we're testing
from habit_tracker.cli import CLIInterface, CLIArgumentParser
from habit_tracker.habitmanager import HabitManager
from habit_tracker.habit import Habit, Periodicity
from habit_tracker.functional_analytics import HabitAnalytics

class TestCLIArgumentParser:
    """Test the CLI argument parser."""
    
    def test_parse_empty_args(self):
        """Test parsing empty arguments."""
        parser = CLIArgumentParser()
        args = parser.parse_args([])
        
        assert args.command is None
        assert args.args == []
        assert args.storage == 'json'
        assert args.file is None
    
    def test_parse_command_with_args(self):
        """Test parsing command with arguments."""
        parser = CLIArgumentParser()
        args = parser.parse_args(['create', 'Exercise', 'daily', '30 min workout'])
        
        assert args.command == 'create'
        assert args.args == ['Exercise', 'daily', '30 min workout']
        assert args.storage == 'json'
        assert args.file is None
    
    def test_parse_with_storage_option(self):
        """Test parsing with storage option."""
        parser = CLIArgumentParser()
        args = parser.parse_args(['--storage', 'sqlite', 'list'])
        
        assert args.command == 'list'
        assert args.storage == 'sqlite'
    
    def test_parse_with_file_option(self):
        """Test parsing with custom file path."""
        parser = CLIArgumentParser()
        args = parser.parse_args(['--file', 'custom.json', 'list'])
        
        assert args.command == 'list'
        assert args.file == 'custom.json'

class TestCLIInterface:
    """Test the main CLI interface."""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock HabitManager for testing."""
        manager = MagicMock(spec=HabitManager)
        manager.habits = {}
        return manager
    
    @pytest.fixture
    def cli(self, mock_manager):
        """Create CLI instance with mock manager."""
        return CLIInterface(mock_manager)
    
    @pytest.fixture
    def sample_habit(self):
        """Create a sample habit for testing."""
        habit = MagicMock(spec=Habit)
        habit.name = "Exercise"
        habit.description = "30 min workout"
        habit.periodicity = Periodicity.DAILY
        habit.calculate_current_streak.return_value = 5
        habit.calculate_longest_streak.return_value = 10
        habit.is_broken.return_value = False
        habit.completion_history = [
            datetime.now() - timedelta(days=i) for i in range(5)
        ]
        return habit
    
    @pytest.fixture
    def sample_analytics(self):
        """Create sample analytics data."""
        analytics = MagicMock(spec=HabitAnalytics)
        analytics.name = "Exercise"
        analytics.periodicity = "daily"
        analytics.current_streak = 5
        analytics.longest_streak = 10
        analytics.total_completions = 20
        analytics.completion_rate = 85.5
        analytics.is_broken = False
        analytics.last_completion = datetime.now()
        analytics.created_date = datetime.now() - timedelta(days=30)
        analytics.days_tracked = 30
        return analytics

class TestCLICommands(TestCLIInterface):
    """Test individual CLI commands."""
    
    def test_cmd_create_success(self, cli, mock_manager):
        """Test successful habit creation."""
        mock_manager.create_habit.return_value = MagicMock()
        
        with patch('builtins.print') as mock_print:
            cli.cmd_create(['Exercise', 'daily', '30 min workout'])
        
        mock_manager.create_habit.assert_called_once_with(
            'Exercise', '30 min workout', Periodicity.DAILY
        )
        mock_print.assert_any_call("✅ Created habit: Exercise (daily)")
        mock_print.assert_any_call("   Description: 30 min workout")
    
    def test_cmd_create_missing_args(self, cli):
        """Test create command with missing arguments."""
        with patch('builtins.print') as mock_print:
            cli.cmd_create(['Exercise'])
        
        mock_print.assert_called_with("❌ Usage: create <name> <periodicity> [description]")
    
    def test_cmd_create_invalid_periodicity(self, cli):
        """Test create command with invalid periodicity."""
        with patch('builtins.print') as mock_print:
            cli.cmd_create(['Exercise', 'invalid'])
        
        mock_print.assert_any_call("❌ Error: Invalid periodicity: invalid")
        mock_print.assert_any_call("Valid periodicities: daily, weekly, monthly, yearly")
    
    def test_cmd_create_habit_exists(self, cli, mock_manager):
        """Test create command when habit already exists."""
        mock_manager.create_habit.side_effect = ValueError("Habit 'Exercise' already exists")
        
        with patch('builtins.print') as mock_print:
            cli.cmd_create(['Exercise', 'daily'])
        
        mock_print.assert_called_with("❌ Error: Habit 'Exercise' already exists")
    
    def test_cmd_delete_success(self, cli, mock_manager):
        """Test successful habit deletion."""
        mock_manager.delete_habit.return_value = True
        
        with patch('builtins.print') as mock_print:
            cli.cmd_delete(['Exercise'])
        
        mock_manager.delete_habit.assert_called_once_with('Exercise')
        mock_print.assert_called_with("✅ Deleted habit: Exercise")
    
    def test_cmd_delete_not_found(self, cli, mock_manager):
        """Test delete command when habit not found."""
        mock_manager.delete_habit.return_value = False
        
        with patch('builtins.print') as mock_print:
            cli.cmd_delete(['NonExistent'])
        
        mock_print.assert_called_with("❌ Habit not found: NonExistent")
    
    def test_cmd_complete_success(self, cli, mock_manager):
        """Test successful habit completion."""
        mock_manager.complete_habit.return_value = True
        
        with patch('builtins.print') as mock_print:
            cli.cmd_complete(['Exercise'])
        
        mock_manager.complete_habit.assert_called_once_with('Exercise', None)
        mock_print.assert_called_with("✅ Completed habit: Exercise")
    
    def test_cmd_complete_with_date(self, cli, mock_manager):
        """Test habit completion with specific date."""
        mock_manager.complete_habit.return_value = True
        expected_date = datetime(2024, 1, 15)
        
        with patch('builtins.print') as mock_print:
            cli.cmd_complete(['Exercise', '2024-01-15'])
        
        mock_manager.complete_habit.assert_called_once()
        args, kwargs = mock_manager.complete_habit.call_args
        assert args[0] == 'Exercise'
        assert args[1].date() == expected_date.date()
    
    def test_cmd_complete_invalid_date(self, cli):
        """Test complete command with invalid date."""
        with patch('builtins.print') as mock_print:
            cli.cmd_complete(['Exercise', 'invalid-date'])
        
        mock_print.assert_called_with("❌ Invalid date format. Use YYYY-MM-DD")
    
    def test_cmd_complete_not_found(self, cli, mock_manager):
        """Test complete command when habit not found."""
        mock_manager.complete_habit.return_value = False
        
        with patch('builtins.print') as mock_print:
            cli.cmd_complete(['NonExistent'])
        
        mock_print.assert_called_with("❌ Habit not found: NonExistent")
    
    def test_cmd_list_all(self, cli, mock_manager, sample_habit):
        """Test listing all habits."""
        mock_manager.get_all_habits.return_value = [sample_habit]
        
        with patch('builtins.print') as mock_print:
            cli.cmd_list([])
        
        mock_manager.get_all_habits.assert_called_once()
        # Check that output contains expected information
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'All Habits' in output_text
        assert 'Exercise' in output_text
    
    def test_cmd_list_by_periodicity(self, cli, mock_manager, sample_habit):
        """Test listing habits by periodicity."""
        mock_manager.get_habits_by_periodicity.return_value = [sample_habit]
        
        with patch('builtins.print') as mock_print:
            cli.cmd_list(['daily'])
        
        mock_manager.get_habits_by_periodicity.assert_called_once_with(Periodicity.DAILY)
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Daily Habits' in output_text
    
    def test_cmd_list_no_habits(self, cli, mock_manager):
        """Test listing when no habits exist."""
        mock_manager.get_all_habits.return_value = []
        
        with patch('builtins.print') as mock_print:
            cli.cmd_list([])
        
        mock_print.assert_called_with("📝 No habits found.")
    
    def test_cmd_analytics_daily(self, cli, mock_manager):
        """Test daily analytics command."""
        mock_manager.get_daily_overview.return_value = {
            'total_habits': 5,
            'completed_today': 3,
            'longest_streak': (10, MagicMock()),
            'most_consistent': ('Exercise', 85.5),
            'broken_habits': []
        }
        
        with patch('builtins.print') as mock_print:
            cli.cmd_analytics(['daily'])
        
        mock_manager.get_daily_overview.assert_called_once()
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Daily Overview' in output_text
        assert 'Total Habits: 5' in output_text
    
    def test_cmd_analytics_invalid_type(self, cli):
        """Test analytics command with invalid type."""
        with patch('builtins.print') as mock_print:
            cli.cmd_analytics(['invalid'])
        
        mock_print.assert_called_with("❌ Invalid analytics type. Use: daily, weekly, monthly")
    
    def test_cmd_streaks(self, cli, mock_manager):
        """Test streaks command."""
        mock_manager.get_active_streaks.return_value = [
            ('Exercise', 5),
            ('Read', 3),
            ('Meditation', 0)
        ]
        
        with patch('builtins.print') as mock_print:
            cli.cmd_streaks([])
        
        mock_manager.get_active_streaks.assert_called_once()
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Current Streaks' in output_text
        assert 'Exercise: 5 days' in output_text
    
    def test_cmd_streaks_no_active(self, cli, mock_manager):
        """Test streaks command with no active streaks."""
        mock_manager.get_active_streaks.return_value = []
        
        with patch('builtins.print') as mock_print:
            cli.cmd_streaks([])
        
        mock_print.assert_called_with("🔥 No active streaks found.")
    
    def test_cmd_longest_all(self, cli, mock_manager):
        """Test longest streak command for all habits."""
        mock_habit = MagicMock()
        mock_habit.name = "Exercise"
        mock_habit.periodicity = Periodicity.DAILY
        mock_manager.get_longest_streak_all.return_value = (15, mock_habit)
        
        with patch('builtins.print') as mock_print:
            cli.cmd_longest([])
        
        mock_manager.get_longest_streak_all.assert_called_once()
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Longest streak overall: 15 days' in output_text
        assert 'Exercise' in output_text
    
    def test_cmd_longest_specific(self, cli, mock_manager):
        """Test longest streak command for specific habit."""
        mock_manager.get_longest_streak_for_habit.return_value = 10
        
        with patch('builtins.print') as mock_print:
            cli.cmd_longest(['Exercise'])
        
        mock_manager.get_longest_streak_for_habit.assert_called_once_with('Exercise')
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert "Longest streak for 'Exercise': 10 days" in output_text
    
    def test_cmd_status(self, cli, mock_manager, sample_analytics):
        """Test status command."""
        mock_manager.get_habit_analytics.return_value = sample_analytics
        mock_habit = MagicMock()
        mock_habit.description = "30 min workout"
        mock_manager.get_habit.return_value = mock_habit
        
        with patch('builtins.print') as mock_print:
            cli.cmd_status(['Exercise'])
        
        mock_manager.get_habit_analytics.assert_called_once_with('Exercise')
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Status Report: Exercise' in output_text
        assert 'Current Streak: 5 days' in output_text
        assert 'Completion Rate: 85.5%' in output_text
    
    def test_cmd_status_not_found(self, cli, mock_manager):
        """Test status command for non-existent habit."""
        mock_manager.get_habit_analytics.return_value = None
        
        with patch('builtins.print') as mock_print:
            cli.cmd_status(['NonExistent'])
        
        mock_print.assert_called_with("❌ Habit not found: NonExistent")
    
    def test_cmd_broken(self, cli, mock_manager):
        """Test broken habits command."""
        mock_manager.get_broken_habits.return_value = ['Exercise', 'Read']
        mock_habit1 = MagicMock()
        mock_habit1.periodicity = Periodicity.DAILY
        mock_habit2 = MagicMock()
        mock_habit2.periodicity = Periodicity.WEEKLY
        mock_manager.get_habit.side_effect = [mock_habit1, mock_habit2]
        
        with patch('builtins.print') as mock_print:
            cli.cmd_broken([])
        
        mock_manager.get_broken_habits.assert_called_once()
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Broken Habits (2)' in output_text
        assert 'Exercise' in output_text
        assert 'Read' in output_text
    
    def test_cmd_broken_none(self, cli, mock_manager):
        """Test broken habits command with no broken habits."""
        mock_manager.get_broken_habits.return_value = []
        
        with patch('builtins.print') as mock_print:
            cli.cmd_broken([])
        
        mock_print.assert_called_with("✅ No broken habits! Keep it up!")
    
    def test_cmd_preload(self, cli, mock_manager):
        """Test preload command."""
        with patch('builtins.print') as mock_print:
            cli.cmd_preload([])
        
        mock_manager.create_predefined_habits.assert_called_once()
        mock_print.assert_called_with("✅ Predefined habits loaded with sample data!")
    
    def test_cmd_backup(self, cli, mock_manager):
        """Test backup command."""
        mock_manager.backup_data.return_value = True
        
        with patch('builtins.print') as mock_print:
            cli.cmd_backup([])
        
        mock_manager.backup_data.assert_called_once()
        mock_print.assert_called_with("✅ Backup created successfully!")
    
    def test_cmd_backup_failed(self, cli, mock_manager):
        """Test backup command when it fails."""
        mock_manager.backup_data.return_value = False
        
        with patch('builtins.print') as mock_print:
            cli.cmd_backup([])
        
        mock_print.assert_called_with("❌ Failed to create backup.")
    
    def test_cmd_help(self, cli, mock_manager):
        """Test help command."""
        mock_manager.get_help_text.return_value = "Help text here"
        
        with patch('builtins.print') as mock_print:
            cli.cmd_help([])
        
        mock_manager.get_help_text.assert_called_once()
        mock_print.assert_called_with("Help text here")
    
    def test_cmd_exit(self, cli):
        """Test exit command."""
        with patch('builtins.print') as mock_print:
            cli.cmd_exit([])
        
        assert cli.running == False
        mock_print.assert_called_with("\n👋 Goodbye! Keep tracking those habits!")

class TestCLIExecution(TestCLIInterface):
    """Test CLI command execution flow."""
    
    def test_execute_command_valid(self, cli, mock_manager):
        """Test executing a valid command."""
        mock_manager.create_habit.return_value = MagicMock()
        
        with patch('builtins.print'):
            cli._execute_command("create Exercise daily")
        
        mock_manager.create_habit.assert_called_once()
    
    def test_execute_command_invalid(self, cli):
        """Test executing an invalid command."""
        with patch('builtins.print') as mock_print:
            cli._execute_command("invalidcommand")
        
        mock_print.assert_any_call("❌ Unknown command: invalidcommand")
        mock_print.assert_any_call("Type 'help' to see available commands.")
    
    def test_run_single_command(self, cli, mock_manager):
        """Test running a single command."""
        mock_manager.create_habit.return_value = MagicMock()
        
        with patch('builtins.print'):
            cli.run_single_command(['create', 'Exercise', 'daily'])
        
        mock_manager.create_habit.assert_called_once()
    
    def test_run_single_command_error(self, cli, mock_manager):
        """Test running a single command that raises an error."""
        mock_manager.create_habit.side_effect = Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit):
                cli.run_single_command(['create', 'Exercise', 'daily'])
        
        mock_print.assert_any_call("❌ Error executing command: Test error")

class TestCLIInteractiveMode(TestCLIInterface):
    """Test CLI interactive mode."""
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_run_interactive_exit(self, mock_print, mock_input, cli):
        """Test interactive mode exit."""
        mock_input.side_effect = ['exit']
        
        cli.run_interactive()
        
        assert cli.running == False
        mock_print.assert_any_call("\n👋 Goodbye! Keep tracking those habits!")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_run_interactive_command_sequence(self, mock_print, mock_input, cli, mock_manager):
        """Test interactive mode with command sequence."""
        mock_manager.create_habit.return_value = MagicMock()
        mock_input.side_effect = ['create Exercise daily', 'exit']
        
        cli.run_interactive()
        
        mock_manager.create_habit.assert_called_once()
        assert cli.running == False
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_run_interactive_keyboard_interrupt(self, mock_print, mock_input, cli):
        """Test keyboard interrupt in interactive mode."""
        mock_input.side_effect = KeyboardInterrupt()
        
        with pytest.raises(SystemExit):
            cli.run_interactive()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_run_interactive_empty_input(self, mock_print, mock_input, cli):
        """Test empty input in interactive mode."""
        mock_input.side_effect = ['', '', 'exit']
        
        cli.run_interactive()
        
        # Should continue running after empty input
        assert cli.running == False

class TestCLIOutputFormatting(TestCLIInterface):
    """Test CLI output formatting."""
    
    def test_show_daily_overview(self, cli, mock_manager):
        """Test daily overview display formatting."""
        mock_manager.get_daily_overview.return_value = {
            'total_habits': 5,
            'completed_today': 3,
            'longest_streak': (10, MagicMock(name='Exercise')),
            'most_consistent': ('Exercise', 85.5),
            'broken_habits': ['Read']
        }
        
        with patch('builtins.print') as mock_print:
            cli._show_daily_overview()
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        assert 'Daily Overview' in output_text
        assert 'Total Habits: 5' in output_text
        assert 'Completed Today: 3' in output_text
        assert 'Longest Streak: 10 days' in output_text
        assert 'Most Consistent: Exercise (85.5%)' in output_text
        assert 'Broken Habits: Read' in output_text
    
    def test_show_weekly_report(self, cli, mock_manager):
        """Test weekly report display formatting."""
        mock_manager.get_weekly_report.return_value = {
            'periodicity_stats': {
                'daily': {'count': 3, 'completion_rate': 80.0},
                'weekly': {'count': 2, 'completion_rate': 90.0}
            },
            'best_day': ('Monday', 15),
            'struggling_habits': [('Read', 45.0)]
        }
        
        with patch('builtins.print') as mock_print:
            cli._show_weekly_report()
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        assert 'Weekly Report' in output_text
        assert 'daily: 3 habits, 80.0% avg completion' in output_text
        assert 'weekly: 2 habits, 90.0% avg completion' in output_text
        assert 'Best Day: Monday (15 completions)' in output_text
        assert 'Struggling Habits' in output_text
        assert 'Read: 45.0%' in output_text
    
    def test_show_monthly_analysis(self, cli, mock_manager):
        """Test monthly analysis display formatting."""
        mock_analytics = MagicMock()
        mock_analytics.name = "Exercise"
        mock_analytics.current_streak = 5
        mock_analytics.longest_streak = 10
        mock_analytics.completion_rate = 85.5
        mock_analytics.total_completions = 25
        
        mock_manager.get_monthly_analysis.return_value = {
            'all_analytics': [mock_analytics],
            'completions_by_month': {'2024-01': 20, '2024-02': 25}
        }
        
        with patch('builtins.print') as mock_print:
            cli._show_monthly_analysis()
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        assert 'Monthly Analysis' in output_text
        assert 'Exercise:' in output_text
        assert 'Streak: 5/10' in output_text
        assert 'Completion Rate: 85.5%' in output_text
        assert 'Total Completions: 25' in output_text
        assert '2024-01: 20' in output_text
        assert '2024-02: 25' in output_text

class TestCLIIntegration:
    """Test CLI integration with real HabitManager."""
    
    @pytest.fixture
    def real_manager(self, tmp_path):
        """Create a real HabitManager with temporary storage."""
        storage_path = tmp_path / "test_habits.json"
        return HabitManager(storage_type='json', storage_path=str(storage_path))
    
    @pytest.fixture
    def cli_with_real_manager(self, real_manager):
        """Create CLI with real HabitManager."""
        return CLIInterface(real_manager)
    
    def test_integration_create_complete_list(self, cli_with_real_manager):
        """Test full integration: create, complete, and list habits."""
        cli = cli_with_real_manager
        
        # Create habit
        with patch('builtins.print'):
            cli.cmd_create(['TestExercise', 'daily', 'Test description'])
        
        # Complete habit
        with patch('builtins.print'):
            cli.cmd_complete(['TestExercise'])
        
        # List habits
        with patch('builtins.print') as mock_print:
            cli.cmd_list([])
        
        # Verify habit was created and listed
        assert cli.manager.get_habit('TestExercise') is not None
        
        # Check output contains our habit
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'TestExercise' in output_text
    
    def test_integration_analytics_flow(self, cli_with_real_manager):
        """Test analytics integration flow."""
        cli = cli_with_real_manager
        
        # Create and complete some habits
        with patch('builtins.print'):
            cli.cmd_create(['Exercise', 'daily', 'Test'])
            cli.cmd_create(['Read', 'daily', 'Test'])
            
            # Complete habits multiple times
            for i in range(5):
                cli.cmd_complete(['Exercise'])
            for i in range(3):
                cli.cmd_complete(['Read'])
        
        # Test analytics commands
        with patch('builtins.print') as mock_print:
            cli.cmd_streaks([])
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Exercise: 5 days' in output_text
        assert 'Read: 3 days' in output_text
        
        # Test longest streak
        with patch('builtins.print') as mock_print:
            cli.cmd_longest([])
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Longest streak overall' in output_text

class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    @pytest.fixture
    def error_manager(self):
        """Create a manager that raises errors."""
        manager = MagicMock(spec=HabitManager)
        manager.create_habit.side_effect = ValueError("Test error")
        manager.complete_habit.side_effect = ValueError("Test error")
        manager.get_habit.side_effect = ValueError("Test error")
        return manager
    
    @pytest.fixture
    def cli_with_errors(self, error_manager):
        """Create CLI with error-prone manager."""
        return CLIInterface(error_manager)
    
    def test_handle_create_error(self, cli_with_errors):
        """Test handling of create errors."""
        with patch('builtins.print') as mock_print:
            cli_with_errors.cmd_create(['Exercise', 'daily'])
        
        mock_print.assert_any_call("❌ Error: Test error")
    
    def test_handle_complete_error(self, cli_with_errors):
        """Test handling of complete errors."""
        with patch('builtins.print') as mock_print:
            cli_with_errors.cmd_complete(['Exercise'])
        
        mock_print.assert_any_call("❌ Habit not found: Exercise")
    
    def test_handle_status_error(self, cli_with_errors):
        """Test handling of status errors."""
        with patch('builtins.print') as mock_print:
            cli_with_errors.cmd_status(['Exercise'])
        
        mock_print.assert_called_with("❌ Habit not found: Exercise")

# Pytest configuration and markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "cli: mark test as a CLI test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )

if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])