# main.py

#!/usr/bin/env python3
"""
Habit Tracker - Main Entry Point

This is the main entry point for the Habit Tracking application.
It initializes the necessary components and starts the CLI interface.
"""

import sys
from cli import CLIInterface
from habitmanager import HabitManager

def main():
    """Main function to start the habit tracker application."""
    try:
        # Initialize the habit manager with JSON storage (default)
        manager = HabitManager(storage_type='json')
        
        # Initialize and run the CLI interface
        cli = CLIInterface(manager)
        
        # Check if command line arguments were provided
        if len(sys.argv) > 1:
            # Run single command mode
            cli.run_single_command(sys.argv[1:])
        else:
            # Run interactive mode
            cli.run_interactive()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Keep tracking those habits!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()