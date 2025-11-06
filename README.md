
## README.md

```markdown
# 🎯 Habit Tracking Application

A comprehensive habit tracking application built with Python 3.7+ that combines Object-Oriented Programming (OOP) and Functional Programming (FP) paradigms. This application helps users create, monitor, and analyze personal habits to build consistency and achieve their goals.

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Components](#-components)
- [Testing](#-testing)
- [Portfolio Submission](#-portfolio-submission)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Functionality
- ✅ **Habit Management**: Create, view, update, and delete habits
- ✅ **Multiple Periodicities**: Support for daily, weekly, monthly, and yearly habits
- ✅ **Streak Tracking**: Track current and longest streaks for motivation
- ✅ **Completion Tracking**: Mark habits as complete with timestamps
- ✅ **Data Persistence**: Choose between JSON file or SQLite database storage
- ✅ **Analytics**: Comprehensive analytics using functional programming
- ✅ **Command-Line Interface**: Intuitive CLI for all operations

### Analytics Features
- 📊 **Daily Overview**: Quick summary of today's progress
- 📈 **Weekly Reports**: Detailed weekly performance analysis
- 📅 **Monthly Analysis**: Long-term trend analysis
- 🔥 **Streak Analytics**: Track and compare streaks across habits
- 📉 **Struggling Habits**: Identify habits needing attention
- 🏆 **Habit Rankings**: Compare habits by various metrics

### Technical Features
- 🏗️ **Object-Oriented Design**: Clean, maintainable code structure
- ⚡ **Functional Programming**: Pure functions for analytics
- 🔄 **Multiple Storage Backends**: JSON and SQLite support
- 🧪 **Comprehensive Testing**: Full test suite with pytest
- 📦 **Modular Architecture**: Loosely coupled, extensible design
- 🛡️ **Error Handling**: Robust error handling and validation

## 📁 Project Structure

```
── main.py                    # Application entry point

habit_tracker/
├── __init__.py                 # Package initialization
├── habit.py                    # Habit class and Periodicity enum
├── storage_handler.py          # Storage abstraction layer
├── functional_analytics.py     # Analytics module (FP)
├── habitmanager.py            # Main application controller
└── cli.py                     # Command-line interface

tests/                         # Test suite
├── __init__.py
├── test_habit.py              # Habit class tests
├── test_storage_handler.py    # Storage layer tests
├── test_functional_analytics.py # Analytics tests
├── test_habitmanager.py       # Manager tests
└── test_cli.py                # CLI tests

── README.md                  # This file



requirements.txt               # Python dependencies
pytest.ini                     # Pytest configuration
.gitignore                     # Git ignore file
```

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Clone the Repository
```bash
git clone https://github.com/profay/Habit_Tracking_App.git
cd Habit_Tracking_App
```
### Create Virtual Environment (Recommended)
```bash
sudo apt install python3.12-venv
python3 -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

```
### Install Dependencies
```bash
python3 -m pip install --upgrade pip  #optional
python3 -m pip install -r requirements.txt
```

## 🎮 Usage

### Running the Application

#### Interactive Mode (Default)
```bash
python3 main.py
```
### CLI Commands

#### Habit Management
```bash
# Create a new habit
create <name> <periodicity> [description]
Example: create Exercise daily "30 min workout"
         create Read_Book daily "30 min Reading

# Delete a habit
delete <name>
Example: delete Exercise

# Update a habit
update <name> <property> <value>
Example: update Exercise description "45 min workout"

# Complete a habit
complete <name> [date]
Example: complete Exercise
Example: complete Exercise 2024-01-15

# Undo a completion
undo <name> <date>
Example: undo Exercise 2024-01-15
```

#### Viewing Habits
```bash
# List all habits
list

# List habits by periodicity
list [daily|weekly|monthly|yearly]
Example: list daily

# Show habit status
status <name>
Example: status Exercise
```

#### Analytics
```bash
# Run analytics reports
analytics <daily|weekly|monthly>
Example: analytics daily

# Show current streaks
streaks

# Show longest streak
longest [habit_name]
Example: longest
Example: longest Exercise

# Show broken habits
broken

# Show struggling habits
struggling [threshold]
Example: struggling 50

# Compare habits
compare <habit1> <habit2> [...]
Example: compare Exercise Read Meditation

# Show habit rankings
rankings
```

#### Data Management
```bash
# Create backup
backup [path]
Example: backup
Example: backup /path/to/backup.json

# Restore from backup
restore <path>
Example: restore backup_20240115.json

# Export data
export <path> <format>
Example: export export.json json
Example: export export.csv csv

# Load sample data
preload

# Show statistics
stats

# Validate data integrity
validate
```

#### Help
```bash
# Show help
help

# Exit application
exit
```


#### Single Command Mode
```bash
# Create a habit
python habit_tracker/main.py create Exercise daily "30 min workout"

# Complete a habit
python habit_tracker/main.py complete Exercise

# View analytics
python habit_tracker/main.py analytics daily

# List all habits
python habit_tracker/main.py list
```
## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Files
```bash
pytest tests/test_habit.py
pytest tests/test_storage_handler.py
pytest tests/test_functional_analytics.py
pytest tests/test_cli.py


## 🏗️ Components

### 1. Habit Class (`habit.py`)
The core data model representing a habit with its attributes and behaviors.

**Key Features:**
- Encapsulates habit properties (name, description, periodicity)
- Manages completion history
- Calculates streaks (current and longest)
- Handles period-based logic
- Serialization support

**Example:**
```python
from habit_tracker.habit import Habit, Periodicity

# Create a habit
habit = Habit(
    name="Exercise",
    description="30 min workout",
    periodicity=Periodicity.DAILY
)

# Complete the habit
habit.check_off()

# Check streak
print(f"Current streak: {habit.calculate_current_streak()} days")
```

### 2. Storage Handler (`storage_handler.py`)
Abstract storage layer supporting multiple backends.

**Features:**
- JSON file storage (default)
- SQLite database storage
- Automatic backups
- Data migration support
- Error handling

**Example:**
```python
from habit_tracker.storage_handler import StorageFactory

# Create JSON storage
storage = StorageFactory.create_storage_handler('json', 'habits.json')

# Create SQLite storage
storage = StorageFactory.create_storage_handler('sqlite', 'habits.db')
```

### 3. Functional Analytics (`functional_analytics.py`)
Pure functional analytics module for data analysis.

**Features:**
- Pure functions (no side effects)
- Comprehensive analytics
- Preset configurations
- Higher-order functions
- Performance optimized

**Example:**
```python
from habit_tracker.functional_analytics import FunctionalAnalytics

# Get all habits
habits = FunctionalAnalytics.get_all_habits(habit_dict)

# Get longest streak
streak, habit = FunctionalAnalytics.get_longest_streak_all(habit_dict)

# Get daily overview
overview = AnalyticsPresets.daily_overview(habit_dict)
```

### 4. Habit Manager (`habitmanager.py`)
Central controller integrating all components.

**Features:**
- CRUD operations
- Analytics integration
- Data persistence
- Predefined habits
- Validation

**Example:**
```python
from habit_tracker.habitmanager import HabitManager

# Create manager
manager = HabitManager(storage_type='json')

# Create habit
manager.create_habit("Exercise", "Workout", Periodicity.DAILY)

# Complete habit
manager.complete_habit("Exercise")

# Get analytics
overview = manager.get_daily_overview()
```

### 5. CLI Interface (`cli.py`)
Command-line interface for user interaction.

**Features:**
- Interactive menu mode
- Single command mode
- Comprehensive help
- Error handling
- Formatted output

**Example:**
```python
from habit_tracker.cli import CLIInterface
from habit_tracker.habitmanager import HabitManager

# Create CLI
manager = HabitManager()
cli = CLIInterface(manager)

# Run interactive mode
cli.run_interactive()

# Run single command
cli.run_single_command(['create', 'Exercise', 'daily'])
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Files
```bash
pytest tests/test_habit.py
pytest tests/test_storage_handler.py
pytest tests/test_functional_analytics.py
pytest tests/test_habitmanager.py
pytest tests/test_cli.py
```

### Run with Coverage
```bash
pytest --cov=habit_tracker --cov-report=html
```

### Run Verbose Tests
```bash
pytest -v
```

### Run Specific Test Classes
```bash
pytest tests/test_habit.py::TestHabitStreaks -v
```

### Run Specific Test Methods
```bash
pytest tests/test_habit.py::TestHabitStreaks::test_current_streak_one_completion -v
```

## 📚 Portfolio Submission

This project is structured for portfolio submission with three phases:

### Phase 1: Conception Phase
- **File**: `docs/conception_phase.pdf`
- **Content**: Technical concept with UML diagrams
- **Focus**: System design and component interaction

### Phase 2: Development Phase
- **File**: `docs/development_phase.pdf`
- **Content**: Implementation presentation (5-10 slides)
- **Focus**: Features and usage demonstration

### Phase 3: Finalization Phase
- **Files**: 
  - `docs/abstract.pdf` (1-2 pages)
  - GitHub repository with all code
  - ZIP file with complete project
- **Content**: Final product and reflection


## 🔧 Development

### Code Style
This project follows PEP 8 style guidelines. Use tools like:
```bash
# Check style
flake8 habit_tracker/

# Format code
black habit_tracker/

# Sort imports
isort habit_tracker/
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement with tests
3. Ensure all tests pass: `pytest`
4. Update documentation
5. Submit pull request

### Debugging
```bash
# Run with debugger
python -m pdb main.py

# Run tests with debugging
pytest --pdb tests/test_habit.py::TestHabitStreaks::test_current_streak_one_completion
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Contributing Guidelines
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit a pull request


## 🙏 Acknowledgments

- IU International University for the project requirements
- Python community for excellent libraries and tools
- pytest for the testing framework
- All contributors and testers

## 📞 Support

For questions or support:
- Create an issue on GitHub
- Email: oyewaletimmy01@gmail.com
- Check the documentation and existing issues first

## 🔗 Links

- [GitHub Repository](https://github.com/profay/habit-tracking-app)
- [Python Documentation](https://docs.python.org/3/)
- [pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://pep8.org/)

---

**Built with ❤️ using Python 3.7+**
```

## Additional Files You Might Need

### requirements.txt
```txt
# Core dependencies
python-dateutil>=2.8.0

# Development dependencies
pytest>=7.0.0
pytest-mock>=3.6.0
pytest-cov>=3.0.0
black>=22.0.0
flake8>=4.0.0
isort>=5.10.0
```

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Project specific
habits.json
habits.db
*.log
backups/

# OS
.DS_Store
Thumbs.db
```
