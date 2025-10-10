# cli.py

import sys
import argparse
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from habitmanager import HabitManager
from habit import Periodicity
from functional_analytics import HabitAnalytics
import json
import os

class CLIInterface:
    """
    Command Line Interface for the Habit Tracking Application.
    
    Provides both interactive menu mode and single command execution
    for managing and analyzing habits.
    """
    
    def __init__(self, manager: HabitManager):
        """
        Initialize the CLI interface.
        
        Args:
            manager: HabitManager instance for backend operations
        """
        self.manager = manager
        self.running = True
        self.commands = self._register_commands()
    
    def _register_commands(self) -> Dict[str, Callable]:
        """Register all available commands."""
        return {
            # Habit Management
            'create': self.cmd_create,
            'delete': self.cmd_delete,
            'update': self.cmd_update,
            'complete': self.cmd_complete,
            'undo': self.cmd_undo,
            
            # Viewing Habits
            'list': self.cmd_list,
            'status': self.cmd_status,
            
            # Analytics
            'analytics': self.cmd_analytics,
            'streaks': self.cmd_streaks,
            'longest': self.cmd_longest,
            'broken': self.cmd_broken,
            'struggling': self.cmd_struggling,
            'compare': self.cmd_compare,
            'rankings': self.cmd_rankings,
            
            # Data Management
            'backup': self.cmd_backup,
            'restore': self.cmd_restore,
            'export': self.cmd_export,
            'preload': self.cmd_preload,
            'stats': self.cmd_stats,
            'validate': self.cmd_validate,
            
            # Utility
            'menu': self.cmd_menu,
            'help': self.cmd_help,
            'examples': self.cmd_examples,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit
        }
    
    # ==================== MAIN INTERFACE METHODS ====================
    
    def run_interactive(self) -> None:
        """Run the CLI in interactive mode with a menu."""
        self._print_welcome()
        
        while self.running:
            try:
                #self._print_menu()
                command = input("\nEnter command (or 'help'): ").strip().lower()
                
                if not command:
                    continue
                
                self._execute_command(command)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! Keep tracking those habits! 👋")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'help' for assistance.")
    
    def run_single_command(self, command_args: List[str]) -> None:
        """
        Execute a single command from command line arguments.
        
        Args:
            command_args: List of command arguments
        """
        if not command_args:
            self.run_interactive()
            return
        
        command = command_args[0].lower()
        args = command_args[1:]
        
        if command in self.commands:
            try:
                self.commands[command](args)
            except Exception as e:
                print(f"❌ Error executing command: {e}")
                sys.exit(1)
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'help' to see available commands.")
            sys.exit(1)
    
    # ==================== COMMAND IMPLEMENTATIONS ====================
    
    # --- Habit Management ---
    
    def cmd_create(self, args: List[str]) -> None:
        """Create a new habit."""
        if len(args) < 2:
            print("❌ Usage: create <name> <periodicity> [description]")
            print("Example: create Exercise daily \"30 min workout\"")
            return
        
        name = args[0]
        periodicity_str = args[1].lower()
        description = " ".join(args[2:]) if len(args) > 2 else f"Track {name}"
        
        try:
            periodicity = Periodicity(periodicity_str)
            habit = self.manager.create_habit(name, description, periodicity)
            print(f"✅ Created habit: {habit.name} ({periodicity_str})")
            print(f"   Description: {description}")
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("Valid periodicities: daily, weekly, monthly, yearly")

    def cmd_delete(self, args: List[str]) -> None:
        """Delete a habit."""
        if len(args) < 1:
            print("❌ Usage: delete <name>")
            return
        
        name = args[0]
        if self.manager.delete_habit(name):
            print(f"✅ Deleted habit: {name}")
        else:
            print(f"❌ Habit not found: {name}")

    # In cli.py, inside the CLIInterface class

    def cmd_update(self, args: List[str]) -> None:
        """Update a habit's properties."""
        if len(args) < 3:
            print("❌ Usage: update <name> <property> <value>")
            print("Example: update Exercise description \"45 min workout\"")
            print("Example: update Exercise periodicity daily")
            return

        name = args[0]
        property_key = args[1].lower()
        
        # Rejoin all remaining arguments to form the full value string
        # This correctly handles values with spaces, like "45 min workout"
        property_value = " ".join(args[2:])

        # 1. Validate the property key
        if property_key not in ['description', 'periodicity']:
            print(f"❌ Cannot update property: '{property_key}'. Only 'description' or 'periodicity' are allowed.")
            return

        update_kwargs = {property_key: property_value}
        
        # 2. Handle potential ValueError from Periodicity creation
        try:
            if self.manager.update_habit(name, **update_kwargs):
                print(f"✅ Updated habit '{name}'. Set {property_key} to '{property_value}'")
            else:
                print(f"❌ Habit not found: {name}")

        except ValueError as e:
            # This catches errors primarily when updating periodicity with an invalid string
            if 'periodicity' in update_kwargs:
                print(f"❌ Error updating periodicity: {e}")
                print("Valid periodicities: daily, weekly, monthly, yearly")
            else:
                print(f"❌ Error: {e}") # Generic error catch
            
            name, property, value = args[0], args[1].lower(), " ".join(args[2:])
            
            if self.manager.update_habit(name, property, value):
                print(f"✅ Updated '{property}' for habit '{name}' to '{value}'.")
            else:
                print(f"❌ Failed to update. Check if habit exists and property is valid.")

    def cmd_complete(self, args: List[str]) -> None:
        """Mark a habit as completed."""
        if len(args) < 1:
            print("❌ Usage: complete <name> [date]")
            print("Example: complete Exercise")
            print("Example: complete Exercise 2024-01-15")
            return
        
        name = args[0]
        completion_time = None
        
        if len(args) >= 2:
            try:
                completion_time = datetime.strptime(args[1], "%Y-%m-%d")
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
                return
        
        if self.manager.complete_habit(name, completion_time):
            time_str = f" on {completion_time.strftime('%Y-%m-%d')}" if completion_time else ""
            print(f"✅ Completed habit: {name}{time_str}")
        else:
            print(f"❌ Habit not found: {name}")

    def cmd_undo(self, args: List[str]) -> None:
        """Undo a habit completion."""
        if len(args) < 2:
            print("❌ Usage: undo <name> <date>")
            print("Example: undo Exercise 2024-01-15")
            return
        
        name, date_str = args[0], args[1]
        try:
            undo_date = datetime.strptime(date_str, "%Y-%m-%d")
            if self.manager.undo_completion(name, undo_date):
                print(f"✅ Undid completion for '{name}' on {date_str}.")
            else:
                print(f"❌ No completion found for '{name}' on {date_str}.")
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD")

    # --- Viewing Habits ---
    
    def cmd_list(self, args: List[str]) -> None:
        """List habits."""
        periodicity = None
        
        if args:
            try:
                periodicity = Periodicity(args[0].lower())
            except ValueError:
                print(f"❌ Invalid periodicity: {args[0]}")
                return
        
        if periodicity:
            habits = self.manager.get_habits_by_periodicity(periodicity)
            title = f"{periodicity.value.capitalize()} Habits"
        else:
            habits = self.manager.get_all_habits()
            title = "All Habits"
        
        if not habits:
            print("📝 No habits found.")
            return
        
        print(f"\n📋 {title} ({len(habits)} total):")
        print("─" * 60)
        
        for habit in habits:
            streak = habit.calculate_current_streak()
            status = "✅" if not habit.is_broken() else "❌"
            last_completion = max(habit.completion_history) if habit.completion_history else "Never"
            
            print(f"{status} {habit.name}")
            print(f"   Periodicity: {habit.periodicity.value}")
            print(f"   Current Streak: {streak}")
            print(f"   Last Completion: {last_completion.strftime('%Y-%m-%d') if isinstance(last_completion, datetime) else last_completion}")
            print(f"   Description: {habit.description}")
            print()

    def cmd_status(self, args: List[str]) -> None:
        """Show detailed status of a specific habit."""
        if len(args) < 1:
            print("❌ Usage: status <name>")
            return
        
        habit_name = args[0]
        analytics = self.manager.get_habit_analytics(habit_name)
        
        if not analytics:
            print(f"❌ Habit not found: {habit_name}")
            return
        
        print(f"\n📊 Status Report: {analytics.name}")
        print("─" * 50)
        print(f"Description: {self.manager.get_habit(habit_name).description}")
        print(f"Periodicity: {analytics.periodicity}")
        print(f"Created: {analytics.created_date.strftime('%Y-%m-%d')}")
        print(f"Days Tracked: {analytics.days_tracked}")
        print()
        print("📈 Performance:")
        print(f"  Current Streak: {analytics.current_streak} {'day' if analytics.current_streak == 1 else 'days'}")
        print(f"  Longest Streak: {analytics.longest_streak} {'day' if analytics.longest_streak == 1 else 'days'}")
        print(f"  Total Completions: {analytics.total_completions}")
        print(f"  Completion Rate: {analytics.completion_rate:.1f}%")
        print()
        print(f"Status: {'🟢 Active' if not analytics.is_broken else '🔴 Broken'}")
        if analytics.last_completion:
            print(f"Last Completion: {analytics.last_completion.strftime('%Y-%m-%d %H:%M')}")

    # --- Analytics ---
    
    def cmd_analytics(self, args: List[str]) -> None:
        """Run analytics reports."""
        if not args:
            print("❌ Usage: analytics <type>")
            print("Available types: daily, weekly, monthly")
            return
        
        analytics_type = args[0].lower()
        
        if analytics_type == "daily":
            self._show_daily_overview()
        elif analytics_type == "weekly":
            self._show_weekly_report()
        elif analytics_type == "monthly":
            self._show_monthly_analysis()
        else:
            print("❌ Invalid analytics type. Use: daily, weekly, monthly")

    def cmd_streaks(self, args: List[str]) -> None:
        """Show current streaks for all habits."""
        streaks = self.manager.get_active_streaks()
        
        if not streaks:
            print("🔥 No active streaks found.")
            return
        
        print("\n🔥 Current Streaks:")
        print("─" * 40)
        
        # Sort by streak length
        streaks.sort(key=lambda x: x[1], reverse=True)
        
        for habit_name, streak in streaks:
            habit = self.manager.get_habit(habit_name)
            status = "🔥" if streak > 0 else "❌"
            print(f"{status} {habit_name}: {streak} {'day' if streak == 1 else 'days'}")

    def cmd_longest(self, args: List[str]) -> None:
        """Show longest streak."""
        if args:
            # Longest streak for specific habit
            habit_name = args[0]
            longest = self.manager.get_longest_streak_for_habit(habit_name)
            print(f"\n🏆 Longest streak for '{habit_name}': {longest} {'day' if longest == 1 else 'days'}")
        else:
            # Longest streak across all habits
            longest, habit = self.manager.get_longest_streak_all()
            if habit:
                print(f"\n🏆 Longest streak overall: {longest} {'day' if longest == 1 else 'days'}")
                print(f"   Habit: {habit.name}")
                print(f"   Periodicity: {habit.periodicity.value}")
            else:
                print("\n📝 No habits found.")

    def cmd_broken(self, args: List[str]) -> None:
        """Show broken habits."""
        broken = self.manager.get_broken_habits()
        
        if not broken:
            print("✅ No broken habits! Keep it up!")
            return
        
        print(f"\n❌ Broken Habits ({len(broken)}):")
        print("─" * 30)
        
        for habit_name in broken:
            habit = self.manager.get_habit(habit_name)
            print(f"❌ {habit_name} ({habit.periodicity.value})")
            print(f"   Missed period: {self._get_missed_period_info(habit)}")

    def cmd_struggling(self, args: List[str]) -> None:
        """Show habits with low completion rates."""
        threshold = float(args[0]) if args else 50.0
        struggling = self.manager.get_struggling_habits(threshold)
        
        if not struggling:
            print(f"✅ No habits struggling below {threshold}% completion rate.")
            return
        
        print(f"\n📉 Struggling Habits (< {threshold}% completion):")
        print("─" * 50)
        for name, rate in struggling:
            print(f"📉 {name}: {rate:.1f}%")

    def cmd_compare(self, args: List[str]) -> None:
        """Compare multiple habits side by side."""
        if len(args) < 2:
            print("❌ Usage: compare <habit1> <habit2> [...]")
            return
        
        comparison_data = self.manager.compare_habits(args)
        if not comparison_data:
            print("❌ Could not perform comparison. Check if habits exist.")
            return
            
        print("\n📊 Habit Comparison:")
        print("─" * 70)
        headers = ["Metric"] + args
        print(f"{headers[0]:<20} | {headers[1]:<15} | {headers[2]:<15}")
        print("─" * 70)
        for metric, values in comparison_data.items():
            print(f"{metric:<20} | {str(values[0]):<15} | {str(values[1]):<15}")

    def cmd_rankings(self, args: List[str]) -> None:
        """Show habit rankings by various metrics."""
        rankings = self.manager.get_habit_rankings()
        if not rankings:
            print("📝 No habits to rank.")
            return
            
        print("\n🏆 Habit Rankings:")
        print("─" * 40)
        for metric, habit_list in rankings.items():
            print(f"\n📈 {metric.capitalize()}:")
            for i, (name, value) in enumerate(habit_list, 1):
                print(f"  {i}. {name}: {value}")

    # --- Data Management ---
    
    def cmd_backup(self, args: List[str]) -> None:
        """Create a backup of habit data."""
        path = args[0] if args else None
        if self.manager.backup_data(path):
            backup_path = path if path else "default backup location"
            print(f"✅ Backup created successfully at {backup_path}!")
        else:
            print("❌ Failed to create backup.")

    def cmd_restore(self, args: List[str]) -> None:
        """Restore data from backup."""
        if not args:
            print("❌ Usage: restore <path>")
            return
        
        path = args[0]
        if not os.path.exists(path):
            print(f"❌ Backup file not found: {path}")
            return
            
        if self.manager.restore_data(path):
            print(f"✅ Data restored successfully from {path}!")
        else:
            print(f"❌ Failed to restore data from {path}.")

    def cmd_export(self, args: List[str]) -> None:
        """Export data to JSON or CSV."""
        if len(args) < 2:
            print("❌ Usage: export <path> <format>")
            return
        
        path, format_type = args[0], args[1].lower()
        if format_type not in ['json', 'csv']:
            print("❌ Invalid format. Use 'json' or 'csv'.")
            return
            
        if self.manager.export_data(path, format_type):
            print(f"✅ Data exported to {path} in {format_type.upper()} format.")
        else:
            print(f"❌ Failed to export data.")

    def cmd_preload(self, args: List[str]) -> None:
        """Load predefined habits with sample data."""
        self.manager.create_predefined_habits()
        print("✅ Predefined habits loaded with sample data!")
        print("   Use 'list' to see all habits.")

    def cmd_stats(self, args: List[str]) -> None:
        """Show comprehensive statistics."""
        stats = self.manager.get_statistics()
        print("\n📊 Comprehensive Statistics:")
        print("─" * 40)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').capitalize()}: {value}")

    def cmd_validate(self, args: List[str]) -> None:
        """Validate data integrity."""
        issues = self.manager.validate_data_integrity()
        if not issues:
            print("✅ All data is valid!")
        else:
            print("❌ Data integrity issues found:")
            for issue in issues:
                print(f"  - {issue}")

    # --- Utility ---
    
    def cmd_help(self, args: List[str]) -> None:
        """Show help information."""
        print(self.manager.get_help_text())

    def cmd_examples(self, args: List[str]) -> None:
        """Show example commands."""
        print(self.manager.get_command_examples())

    def cmd_exit(self, args: List[str]) -> None:
        """Exit the application."""
        print("\n👋 Goodbye! Keep tracking those habits!")
        self.running = False
    
    # ==================== DISPLAY METHODS ====================
    
    def _show_daily_overview(self) -> None:
        """Display daily overview analytics."""
        overview = self.manager.get_daily_overview()
        
        print("\n📊 Daily Overview")
        print("─" * 40)
        print(f"Total Habits: {overview['total_habits']}")
        print(f"Completed Today: {overview['completed_today']}")
        
        if overview['longest_streak'][1]:
            print(f"Longest Streak: {overview['longest_streak'][0]} days ({overview['longest_streak'][1].name})")
        
        if overview['most_consistent']:
            print(f"Most Consistent: {overview['most_consistent'][0]} ({overview['most_consistent'][1]:.1f}%)")
        
        if overview['broken_habits']:
            print(f"Broken Habits: {', '.join(overview['broken_habits'])}")
    
    def _show_weekly_report(self) -> None:
        """Display weekly report analytics."""
        report = self.manager.get_weekly_report()
        
        print("\n📊 Weekly Report")
        print("─" * 40)
        
        # Periodicity stats
        print("By Periodicity:")
        for period, stats in report['periodicity_stats'].items():
            if stats['count'] > 0:
                print(f"  {period.capitalize()}: {stats['count']} habits, {stats['completion_rate']:.1f}% avg completion")
        
        # Best day
        if report['best_day']:
            print(f"\nBest Day: {report['best_day'][0]} ({report['best_day'][1]} completions)")
        
        # Struggling habits
        if report['struggling_habits']:
            print(f"\nStruggling Habits (<70%):")
            for name, rate in report['struggling_habits']:
                print(f"  {name}: {rate:.1f}%")
    
    def _show_monthly_analysis(self) -> None:
        """Display monthly analysis analytics."""
        analysis = self.manager.get_monthly_analysis()
        
        print("\n📊 Monthly Analysis")
        print("─" * 40)
        
        # All habits analytics
        print("Habit Performance:")
        for analytics in analysis['all_analytics']:
            print(f"  {analytics.name}:")
            print(f"    Streak: {analytics.current_streak}/{analytics.longest_streak}")
            print(f"    Completion Rate: {analytics.completion_rate:.1f}%")
            print(f"    Total Completions: {analytics.total_completions}")
        
        # Completions by month
        if analysis['completions_by_month']:
            print(f"\nMonthly Completions:")
            for month, count in sorted(analysis['completions_by_month'].items()):
                print(f"  {month}: {count}")
    
    def _get_missed_period_info(self, habit) -> str:
        """Get information about the missed period for a broken habit."""
        now = datetime.now()
        if habit.periodicity == Periodicity.DAILY:
            return f"Today ({now.strftime('%Y-%m-%d')})"
        elif habit.periodicity == Periodicity.WEEKLY:
            monday = now - timedelta(days=now.weekday())
            return f"This week ({monday.strftime('%Y-%m-%d')} -)"
        elif habit.periodicity == Periodicity.MONTHLY:
            return f"This month ({now.strftime('%Y-%m')})"
        else:
            return f"This year ({now.strftime('%Y')})"
    
    # ==================== UI HELPER METHODS ====================
    
    def _print_welcome(self) -> None:
        """Print welcome message."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🎯 HABIT TRACKER - CLI INTERFACE                ║
║                                                              ║
║        Track your habits, build streaks, achieve goals!       ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def _print_menu(self) -> None:
        """Print the main menu."""
        print("""
📋 Main Menu:
────────────────────────────────────────────────────────────
Habit Management:
  create <name> <periodicity> [description]  - Create new habit
  delete <name>                               - Delete habit
  update <name> <property> <value>            - Update habit
  complete <name> [date]                      - Mark complete
  undo <name> <date>                          - Undo completion

Viewing Habits:
  list [periodicity]                          - List habits
  status <name>                               - Habit status

Analytics:
  analytics <type>                            - View analytics
  streaks                                     - Show current streaks
  longest [name]                              - Show longest streak
  broken                                      - Show broken habits
  struggling [threshold]                      - Show struggling habits
  compare <habit1> <habit2> [...]             - Compare habits
  rankings                                    - Show rankings

Data Management:
  backup [path]                               - Create backup
  restore <path>                              - Restore backup
  export <path> <format>                      - Export data
  preload                                     - Load sample data
  stats                                       - Show statistics
  validate                                    - Validate data

Utility:
  help                                        - Show help
  examples                                    - Show examples
  exit                                        - Exit program
────────────────────────────────────────────────────────────
        """)
    
    def _execute_command(self, command: str) -> None:
        """Execute a command from user input."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            print(f"❌ Unknown command: {cmd}")
            print("Type 'help' to see available commands.")

class CLIArgumentParser:
    """Parser for command-line arguments when running in single command mode."""
    
    @staticmethod
    def parse_args(args: List[str]) -> Dict[str, Any]:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(
            description="Habit Tracker CLI - Track your habits and build streaks"
        )
        
        parser.add_argument(
            'command',
            nargs='?',
            help='Command to execute (or leave empty for interactive mode)'
        )
        
        parser.add_argument(
            'args',
            nargs='*',
            help='Arguments for the command'
        )
        
        parser.add_argument(
            '--storage',
            choices=['json', 'sqlite'],
            default='json',
            help='Storage backend to use (default: json)'
        )
        
        parser.add_argument(
            '--file',
            help='Custom storage file path'
        )
        
        return parser.parse_args(args)

def main():
    """Main entry point for the CLI application."""
    parser = CLIArgumentParser()
    parsed_args = parser.parse_args(sys.argv[1:])
    
    # Initialize manager with specified storage
    manager = HabitManager(
        storage_type=parsed_args.storage,
        storage_path=parsed_args.file
    )
    
    # Initialize CLI
    cli = CLIInterface(manager)
    
    # Run in appropriate mode
    if parsed_args.command:
        command_args = [parsed_args.command] + parsed_args.args
        cli.run_single_command(command_args)
    else:
        cli.run_interactive()

if __name__ == "__main__":
    main()