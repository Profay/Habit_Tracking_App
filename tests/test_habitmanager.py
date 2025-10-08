# test_habitmanager.py

"""
Unit tests for the HabitManager class.

This test suite covers:
- HabitManager initialization and configuration
- CRUD operations for habits
- Habit completion and undo functionality
- Data persistence (save, load, backup, restore, export)
- Analytics integration and delegation
- Predefined habits creation
- Utility methods (statistics, validation)
- Factory functions
- Integration tests with real components
"""

import pytest
import json
import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, mock_open, call

from habit_tracker.habitmanager import (
    HabitManager, 
    create_habit_manager, 
    migrate_storage
)
from habit_tracker.habit import Habit, Periodicity
from habit_tracker.storage_handler import StorageError, StorageFactory
from habit_tracker.functional_analytics import HabitAnalytics

class TestHabitManagerInitialization:
    """Test HabitManager initialization."""
    
    def test_init_default_json(self):
        """Test initialization with default JSON storage."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_storage = MagicMock()
            mock_factory.return_value = mock_storage
            mock_storage.load_habits.return_value = {}
            
            manager = HabitManager()
            
            mock_factory.assert_called_once_with(storage_type='json', file_path='habits.json')
            mock_storage.load_habits.assert_called_once()
            assert manager.habits == {}
            assert manager.storage == mock_storage
            assert manager.analytics is not None
    
    def test_init_custom_json_path(self):
        """Test initialization with custom JSON path."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_storage = MagicMock()
            mock_factory.return_value = mock_storage
            mock_storage.load_habits.return_value = {}
            
            manager = HabitManager(storage_path='custom.json')
            
            mock_factory.assert_called_once_with(storage_type='json', file_path='custom.json')
    
    def test_init_sqlite_storage(self):
        """Test initialization with SQLite storage."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_storage = MagicMock()
            mock_factory.return_value = mock_storage
            mock_storage.load_habits.return_value = {}
            
            manager = HabitManager(storage_type='sqlite')
            
            mock_factory.assert_called_once_with(storage_type='sqlite', file_path='habits.db')
    
    def test_init_invalid_storage_type(self):
        """Test initialization with invalid storage type."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_factory.side_effect = ValueError("Invalid storage type")
            
            with pytest.raises(ValueError, match="Invalid storage type"):
                HabitManager(storage_type='invalid')
    
    def test_init_storage_error(self):
        """Test initialization when storage raises an error."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_factory.side_effect = StorageError("Storage failed")
            
            with pytest.raises(StorageError, match="Failed to initialize storage"):
                HabitManager()
    
    def test_init_loads_existing_data(self):
        """Test that initialization loads existing habits."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_storage = MagicMock()
            mock_factory.return_value = mock_storage
            
            # Mock existing habits
            existing_habits = {
                'Exercise': Habit('Exercise', 'Workout', Periodicity.DAILY)
            }
            mock_storage.load_habits.return_value = existing_habits
            
            manager = HabitManager()
            
            assert manager.habits == existing_habits
            mock_storage.load_habits.assert_called_once()
    
    def test_init_handles_load_error(self):
        """Test initialization handles load errors gracefully."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_storage = MagicMock()
            mock_factory.return_value = mock_storage
            mock_storage.load_habits.side_effect = StorageError("Load failed")
            
            with patch('builtins.print') as mock_print:
                manager = HabitManager()
            
            assert manager.habits == {}
            mock_print.assert_called_with("Warning: Failed to load data: Load failed")

@pytest.fixture
def mock_storage():
    """Create a mock storage handler."""
    storage = MagicMock()
    storage.load_habits.return_value = {}
    storage.save_habits.return_value = None
    storage.backup_data.return_value = True
    storage.get_storage_info.return_value = {'type': 'json'}
    return storage

@pytest.fixture
def mock_manager(mock_storage):
    """Create a HabitManager with mocked dependencies."""
    with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
        mock_factory.return_value = mock_storage
        manager = HabitManager()
        return manager

@pytest.fixture
def sample_habit():
    """Create a sample habit for testing."""
    return Habit(
        name="Exercise",
        description="30 min workout",
        periodicity=Periodicity.DAILY,
        creation_date=datetime(2024, 1, 1)
    )

class TestHabitManagerCRUD:
    """Test CRUD operations."""
    
    def test_create_habit_success(self, mock_manager, mock_storage):
        """Test successful habit creation."""
        habit = mock_manager.create_habit("Exercise", "Workout", Periodicity.DAILY)
        
        assert habit.name == "Exercise"
        assert habit.description == "Workout"
        assert habit.periodicity == Periodicity.DAILY
        assert "Exercise" in mock_manager.habits
        mock_storage.save_habits.assert_called_once_with(mock_manager.habits)
    
    def test_create_habit_duplicate_name(self, mock_manager):
        """Test creating habit with duplicate name."""
        mock_manager.create_habit("Exercise", "Workout", Periodicity.DAILY)
        
        with pytest.raises(ValueError, match="Habit 'Exercise' already exists"):
            mock_manager.create_habit("Exercise", "Another workout", Periodicity.WEEKLY)
    
    def test_delete_habit_success(self, mock_manager, mock_storage):
        """Test successful habit deletion."""
        mock_manager.create_habit("Exercise", "Workout", Periodicity.DAILY)
        
        result = mock_manager.delete_habit("Exercise")
        
        assert result is True
        assert "Exercise" not in mock_manager.habits
        mock_storage.save_habits.assert_called()
    
    def test_delete_habit_not_found(self, mock_manager):
        """Test deleting non-existent habit."""
        result = mock_manager.delete_habit("NonExistent")
        assert result is False
    
    def test_get_habit_found(self, mock_manager, sample_habit):
        """Test getting an existing habit."""
        mock_manager.habits["Exercise"] = sample_habit
        
        habit = mock_manager.get_habit("Exercise")
        
        assert habit == sample_habit
    
    def test_get_habit_not_found(self, mock_manager):
        """Test getting a non-existent habit."""
        habit = mock_manager.get_habit("NonExistent")
        assert habit is None
    
    def test_update_habit_success(self, mock_manager, mock_storage):
        """Test successful habit update."""
        habit = mock_manager.create_habit("Exercise", "Workout", Periodicity.DAILY)
        
        result = mock_manager.update_habit("Exercise", description="45 min workout")
        
        assert result is True
        assert habit.description == "45 min workout"
        mock_storage.save_habits.assert_called()
    
    def test_update_habit_periodicity_string(self, mock_manager):
        """Test updating habit periodicity with string."""
        habit = mock_manager.create_habit("Exercise", "Workout", Periodicity.DAILY)
        
        result = mock_manager.update_habit("Exercise", periodicity="weekly")
        
        assert result is True
        assert habit.periodicity == Periodicity.WEEKLY
    
    def test_update_habit_not_found(self, mock_manager):
        """Test updating non-existent habit."""
        result = mock_manager.update_habit("NonExistent", description="New desc")
        assert result is False

class TestHabitManagerCompletion:
    """Test habit completion functionality."""
    
    def test_complete_habit_success(self, mock_manager, mock_storage, sample_habit):
        """Test successful habit completion."""
        mock_manager.habits["Exercise"] = sample_habit
        
        result = mock_manager.complete_habit("Exercise")
        
        assert result is True
        sample_habit.check_off.assert_called_once()
        mock_storage.save_habits.assert_called_once()
    
    def test_complete_habit_with_time(self, mock_manager, sample_habit):
        """Test completing habit with specific time."""
        mock_manager.habits["Exercise"] = sample_habit
        completion_time = datetime(2024, 1, 15, 10, 0, 0)
        
        result = mock_manager.complete_habit("Exercise", completion_time)
        
        assert result is True
        sample_habit.check_off.assert_called_once_with(completion_time)
    
    def test_complete_habit_not_found(self, mock_manager):
        """Test completing non-existent habit."""
        result = mock_manager.complete_habit("NonExistent")
        assert result is False
    
    def test_complete_multiple_habits(self, mock_manager, sample_habit):
        """Test completing multiple habits."""
        habit2 = Habit("Read", "Read book", Periodicity.DAILY)
        mock_manager.habits["Exercise"] = sample_habit
        mock_manager.habits["Read"] = habit2
        
        results = mock_manager.complete_multiple_habits(["Exercise", "Read"])
        
        assert results == {"Exercise": True, "Read": True}
        assert mock_storage.save_habits.call_count == 2
    
    def test_complete_multiple_habits_mixed(self, mock_manager, sample_habit):
        """Test completing multiple habits with some missing."""
        mock_manager.habits["Exercise"] = sample_habit
        
        results = mock_manager.complete_multiple_habits(["Exercise", "NonExistent"])
        
        assert results == {"Exercise": True, "NonExistent": False}
    
    def test_undo_completion_success(self, mock_manager, mock_storage, sample_habit):
        """Test successful undo of completion."""
        completion_time = datetime(2024, 1, 15, 10, 0, 0)
        sample_habit.completion_history = [completion_time]
        mock_manager.habits["Exercise"] = sample_habit
        
        result = mock_manager.undo_completion("Exercise", completion_time)
        
        assert result is True
        assert completion_time not in sample_habit.completion_history
        mock_storage.save_habits.assert_called_once()
    
    def test_undo_completion_not_found(self, mock_manager):
        """Test undo for non-existent habit."""
        result = mock_manager.undo_completion("NonExistent", datetime.now())
        assert result is False
    
    def test_undo_completion_not_in_history(self, mock_manager, sample_habit):
        """Test undo for completion not in history."""
        mock_manager.habits["Exercise"] = sample_habit
        
        result = mock_manager.undo_completion("Exercise", datetime.now())
        assert result is False

class TestHabitManagerPersistence:
    """Test data persistence methods."""
    
    def test_save_data_success(self, mock_manager, mock_storage):
        """Test successful data save."""
        mock_manager.save_data()
        
        mock_storage.save_habits.assert_called_once_with(mock_manager.habits)
    
    def test_save_data_error(self, mock_manager, mock_storage):
        """Test save data with storage error."""
        mock_storage.save_habits.side_effect = StorageError("Save failed")
        
        with pytest.raises(StorageError, match="Failed to save data"):
            mock_manager.save_data()
    
    def test_load_data_success(self, mock_manager, mock_storage):
        """Test successful data load."""
        test_habits = {"Exercise": Habit("Test", "Test", Periodicity.DAILY)}
        mock_storage.load_habits.return_value = test_habits
        
        mock_manager.load_data()
        
        assert mock_manager.habits == test_habits
    
    def test_backup_data_default_path(self, mock_manager, mock_storage):
        """Test backup with default path."""
        with patch('habitmanager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.strftime.return_value = "20240115_100000"
            
            mock_manager.backup_data()
            
            mock_storage.backup_data.assert_called_once()
            # Check that path includes timestamp
            call_args = mock_storage.backup_data.call_args[0][0]
            assert "20240115_100000" in call_args
    
    def test_backup_data_custom_path(self, mock_manager, mock_storage):
        """Test backup with custom path."""
        custom_path = "/path/to/backup.json"
        
        mock_manager.backup_data(custom_path)
        
        mock_storage.backup_data.assert_called_once_with(custom_path)
    
    def test_restore_data_success(self, mock_manager, mock_storage):
        """Test successful data restore."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            backup_storage = MagicMock()
            backup_habits = {"Exercise": Habit("Test", "Test", Periodicity.DAILY)}
            backup_storage.load_habits.return_value = backup_habits
            mock_factory.return_value = backup_storage
            
            result = mock_manager.restore_data("backup.json")
            
            assert result is True
            assert mock_manager.habits == backup_habits
            mock_storage.save_habits.assert_called_once_with(backup_habits)
    
    def test_restore_data_invalid_data(self, mock_manager):
        """Test restore with invalid data."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            backup_storage = MagicMock()
            backup_storage.load_habits.return_value = {"Invalid": "Not a habit object"}
            mock_factory.return_value = backup_storage
            
            with patch('builtins.print') as mock_print:
                result = mock_manager.restore_data("backup.json")
            
            assert result is False
            mock_print.assert_called_with("Failed to restore backup: Invalid habit data in backup: Invalid")
    
    def test_export_data_json(self, mock_manager, sample_habit):
        """Test exporting data to JSON."""
        mock_manager.habits["Exercise"] = sample_habit
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = mock_manager.export_data("export.json", "json")
        
        assert result is True
        mock_file.assert_called_once_with("export.json", 'w')
        
        # Check written content
        handle = mock_file()
        written_data = json.loads(handle.write.call_args[0][0])
        assert "Exercise" in written_data["habits"]
        assert written_data["export_date"] is not None
    
    def test_export_data_csv(self, mock_manager, sample_habit):
        """Test exporting data to CSV."""
        mock_manager.habits["Exercise"] = sample_habit
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('csv.writer') as mock_csv:
                mock_writer = MagicMock()
                mock_csv.return_value = mock_writer
                
                result = mock_manager.export_data("export.csv", "csv")
        
        assert result is True
        mock_file.assert_called_once_with("export.csv", 'w', newline='')
        mock_writer.writerow.assert_called()
    
    def test_export_data_invalid_format(self, mock_manager):
        """Test export with invalid format."""
        result = mock_manager.export_data("export.txt", "txt")
        assert result is False
    
    def test_get_storage_info(self, mock_manager, mock_storage):
        """Test getting storage information."""
        mock_storage.get_storage_info.return_value = {"type": "json", "size": 1024}
        
        info = mock_manager.get_storage_info()
        
        assert info == {"type": "json", "size": 1024}
        mock_storage.get_storage_info.assert_called_once()

class TestHabitManagerAnalytics:
    """Test analytics integration methods."""
    
    def test_get_all_habits(self, mock_manager):
        """Test getting all habits delegates to analytics."""
        with patch.object(mock_manager.analytics, 'get_all_habits') as mock_analytics:
            mock_analytics.return_value = ["habit1", "habit2"]
            
            result = mock_manager.get_all_habits()
            
            mock_analytics.assert_called_once_with(mock_manager.habits)
            assert result == ["habit1", "habit2"]
    
    def test_get_habits_by_periodicity(self, mock_manager):
        """Test getting habits by periodicity delegates to analytics."""
        with patch.object(mock_manager.analytics, 'get_habits_by_periodicity') as mock_analytics:
            mock_analytics.return_value = ["habit1"]
            
            result = mock_manager.get_habits_by_periodicity(Periodicity.DAILY)
            
            mock_analytics.assert_called_once_with(mock_manager.habits, Periodicity.DAILY)
            assert result == ["habit1"]
    
    def test_get_longest_streak_all(self, mock_manager):
        """Test getting longest streak delegates to analytics."""
        with patch.object(mock_manager.analytics, 'get_longest_streak_all') as mock_analytics:
            mock_analytics.return_value = (10, "Exercise")
            
            result = mock_manager.get_longest_streak_all()
            
            mock_analytics.assert_called_once_with(mock_manager.habits)
            assert result == (10, "Exercise")
    
    def test_get_daily_overview(self, mock_manager):
        """Test getting daily overview delegates to analytics presets."""
        with patch('habitmanager.AnalyticsPresets.daily_overview') as mock_presets:
            mock_presets.return_value = {"total": 5}
            
            result = mock_manager.get_daily_overview()
            
            mock_presets.assert_called_once_with(mock_manager.habits)
            assert result == {"total": 5}
    
    def test_get_habit_analytics(self, mock_manager):
        """Test getting habit analytics delegates to analytics."""
        with patch.object(mock_manager.analytics, 'get_habit_analytics') as mock_analytics:
            mock_analytics.return_value = MagicMock()
            
            result = mock_manager.get_habit_analytics("Exercise")
            
            mock_analytics.assert_called_once_with(mock_manager.habits, "Exercise")
            assert result is not None
    
    def test_get_struggling_habits(self, mock_manager):
        """Test getting struggling habits delegates to analytics."""
        with patch.object(mock_manager.analytics, 'get_struggling_habits') as mock_analytics:
            mock_analytics.return_value = [("Exercise", 30.0)]
            
            result = mock_manager.get_struggling_habits(50.0)
            
            mock_analytics.assert_called_once_with(mock_manager.habits, 50.0)
            assert result == [("Exercise", 30.0)]

class TestHabitManagerPredefinedHabits:
    """Test predefined habits functionality."""
    
    def test_create_predefined_habits_empty(self, mock_manager, mock_storage):
        """Test creating predefined habits when none exist."""
        mock_manager.create_predefined_habits()
        
        assert len(mock_manager.habits) == 5
        assert "Drink Water" in mock_manager.habits
        assert "Exercise" in mock_manager.habits
        assert "Weekly Review" in mock_manager.habits
        # Check save was called
        assert mock_storage.save_habits.call_count >= 5
    
    def test_create_predefined_habits_partial_exists(self, mock_manager):
        """Test creating predefined habits when some already exist."""
        # Create one predefined habit first
        mock_manager.create_habit("Exercise", "Workout", Periodicity.DAILY)
        
        mock_manager.create_predefined_habits()
        
        # Should have 5 total, not 6
        assert len(mock_manager.habits) == 5
        # Exercise should still exist
        assert "Exercise" in mock_manager.habits
        # Others should be added
        assert "Drink Water" in mock_manager.habits
    
    def test_create_predefined_habits_all_exist(self, mock_manager):
        """Test creating predefined habits when all already exist."""
        # Create all predefined habits
        predefined = [
            ("Drink Water", "Water", Periodicity.DAILY),
            ("Exercise", "Workout", Periodicity.DAILY),
            ("Read", "Reading", Periodicity.DAILY),
            ("Weekly Review", "Review", Periodicity.WEEKLY),
            ("Grocery Shopping", "Groceries", Periodicity.WEEKLY)
        ]
        
        for name, desc, period in predefined:
            mock_manager.create_habit(name, desc, period)
        
        initial_count = len(mock_manager.habits)
        
        mock_manager.create_predefined_habits()
        
        # Should not add any new habits
        assert len(mock_manager.habits) == initial_count

class TestHabitManagerUtilities:
    """Test utility methods."""
    
    def test_get_statistics(self, mock_manager):
        """Test getting comprehensive statistics."""
        # Setup mock habits
        daily_habit = MagicMock()
        weekly_habit = MagicMock()
        mock_manager.habits = {
            "Exercise": daily_habit,
            "Review": weekly_habit
        }
        
        # Mock analytics methods
        mock_manager.get_habits_by_periodicity.side_effect = lambda p: (
            [daily_habit] if p == Periodicity.DAILY else [weekly_habit]
        )
        mock_manager.get_total_completions.return_value = 10
        mock_manager.get_broken_habits.return_value = ["Exercise"]
        mock_manager.get_active_streaks.return_value = [("Exercise", 5)]
        mock_manager.get_storage_info.return_value = {"type": "json"}
        
        stats = mock_manager.get_statistics()
        
        assert stats['total_habits'] == 2
        assert stats['daily_habits'] == 1
        assert stats['weekly_habits'] == 1
        assert stats['total_completions'] == 10
        assert stats['broken_habits'] == 1
        assert stats['active_streaks'] == 1
    
    def test_validate_data_integrity_valid(self, mock_manager, sample_habit):
        """Test data integrity validation with valid data."""
        mock_manager.habits = {"Exercise": sample_habit}
        
        result = mock_manager.validate_data_integrity()
        
        assert result['is_valid'] is True
        assert result['issues'] == []
        assert result['warnings'] == []
        assert result['total_habits'] == 1
    
    def test_validate_data_integrity_duplicates(self, mock_manager, sample_habit):
        """Test data integrity validation with duplicate completions."""
        # Add duplicate completion
        duplicate_time = datetime(2024, 1, 15)
        sample_habit.completion_history = [duplicate_time, duplicate_time]
        mock_manager.habits = {"Exercise": sample_habit}
        
        result = mock_manager.validate_data_integrity()
        
        assert result['is_valid'] is False
        assert len(result['issues']) == 1
        assert "duplicate completions" in result['issues'][0]
    
    def test_validate_data_integrity_future_dates(self, mock_manager, sample_habit):
        """Test data integrity validation with future dates."""
        future_time = datetime.now() + timedelta(days=1)
        sample_habit.completion_history = [future_time]
        mock_manager.habits = {"Exercise": sample_habit}
        
        result = mock_manager.validate_data_integrity()
        
        assert result['is_valid'] is True  # Still valid, but with warning
        assert len(result['warnings']) == 1
        assert "future completions" in result['warnings'][0]

class TestHabitManagerFactoryFunctions:
    """Test factory functions."""
    
    def test_create_habit_manager_default(self):
        """Test creating habit manager with defaults."""
        with patch('habitmanager.HabitManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            result = create_habit_manager()
            
            mock_manager_class.assert_called_once_with(storage_type='json', storage_path=None)
            assert result == mock_manager
    
    def test_create_habit_manager_with_sample_data(self):
        """Test creating habit manager with sample data."""
        with patch('habitmanager.HabitManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.habits = {}  # Empty to trigger sample data creation
            mock_manager_class.return_value = mock_manager
            
            result = create_habit_manager(create_sample_data=True)
            
            mock_manager.create_predefined_habits.assert_called_once()
            assert result == mock_manager
    
    def test_migrate_storage_success(self):
        """Test successful storage migration."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            source_storage = MagicMock()
            target_storage = MagicMock()
            
            # Setup mocks
            source_habits = {"Exercise": Habit("Test", "Test", Periodicity.DAILY)}
            source_storage.load_habits.return_value = source_habits
            
            mock_factory.side_effect = [source_storage, target_storage]
            
            result = migrate_storage("source.json", "json", "target.db", "sqlite")
            
            assert result is True
            source_storage.load_habits.assert_called_once()
            target_storage.save_habits.assert_called_once_with(source_habits)
    
    def test_migrate_storage_failure(self):
        """Test storage migration failure."""
        with patch('habitmanager.StorageFactory.create_storage_handler') as mock_factory:
            mock_factory.side_effect = Exception("Migration failed")
            
            with patch('builtins.print') as mock_print:
                result = migrate_storage("source.json", "json", "target.db", "sqlite")
            
            assert result is False
            mock_print.assert_called_with("Migration failed: Migration failed")

class TestHabitManagerIntegration:
    """Integration tests with real components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def real_manager(self, temp_dir):
        """Create a real HabitManager with temporary storage."""
        storage_path = temp_dir / "test_habits.json"
        return HabitManager(storage_type='json', storage_path=str(storage_path))
    
    def test_full_workflow_integration(self, real_manager):
        """Test a complete workflow with real components."""
        # Create habits
        habit1 = real_manager.create_habit("Exercise", "Daily workout", Periodicity.DAILY)
        habit2 = real_manager.create_habit("Read", "Read book", Periodicity.DAILY)
        
        # Complete habits
        today = datetime.now()
        real_manager.complete_habit("Exercise", today)
        real_manager.complete_habit("Read", today - timedelta(days=1))
        
        # Verify completions
        assert len(real_manager.get_habit("Exercise").completion_history) == 1
        assert len(real_manager.get_habit("Read").completion_history) == 1
        
        # Test analytics
        all_habits = real_manager.get_all_habits()
        assert len(all_habits) == 2
        
        streaks = real_manager.get_active_streaks()
        assert len(streaks) == 2
        
        # Test backup and restore
        backup_path = real_manager.storage.file_path.parent / "backup.json"
        assert real_manager.backup_data(str(backup_path))
        
        # Delete a habit
        real_manager.delete_habit("Exercise")
        assert len(real_manager.get_all_habits()) == 1
        
        # Restore from backup
        assert real_manager.restore_data(str(backup_path))
        assert len(real_manager.get_all_habits()) == 2
        assert real_manager.get_habit("Exercise") is not None
        
        # Test export
        export_path = real_manager.storage.file_path.parent / "export.csv"
        assert real_manager.export_data(str(export_path), "csv")
        assert export_path.exists()
    
    def test_data_persistence_across_sessions(self, temp_dir):
        """Test that data persists across manager instances."""
        storage_path = temp_dir / "persistent_habits.json"
        
        # First session - create and save
        manager1 = HabitManager(storage_type='json', storage_path=str(storage_path))
        manager1.create_habit("Persistent", "Test habit", Periodicity.DAILY)
        manager1.complete_habit("Persistent")
        
        # Second session - load and verify
        manager2 = HabitManager(storage_type='json', storage_path=str(storage_path))
        
        assert len(manager2.get_all_habits()) == 1
        habit = manager2.get_habit("Persistent")
        assert habit is not None
        assert len(habit.completion_history) == 1
    
    def test_error_handling_integration(self, real_manager):
        """Test error handling in real scenarios."""
        # Test duplicate habit creation
        real_manager.create_habit("Test", "Test", Periodicity.DAILY)
        
        with pytest.raises(ValueError):
            real_manager.create_habit("Test", "Another", Periodicity.WEEKLY)
        
        # Test completing non-existent habit
        result = real_manager.complete_habit("NonExistent")
        assert result is False
        
        # Test deleting non-existent habit
        result = real_manager.delete_habit("NonExistent")
        assert result is False

class TestHabitManagerStringRepresentations:
    """Test string representation methods."""
    
    def test_str_representation(self, mock_manager):
        """Test __str__ method."""
        mock_manager.habits = {"Exercise": MagicMock()}
        mock_storage = MagicMock()
        mock_storage.__class__.__name__ = "JSONStorageHandler"
        mock_manager.storage = mock_storage
        
        str_repr = str(mock_manager)
        
        assert "HabitManager with 1 habits" in str_repr
        assert "JSONStorageHandler" in str_repr
    
    def test_repr_representation(self, mock_manager):
        """Test __repr__ method."""
        mock_manager.habits = {"Exercise": MagicMock()}
        mock_storage = MagicMock()
        mock_storage.__class__.__name__ = "JSONStorageHandler"
        mock_manager.storage = mock_storage
        
        repr_str = repr(mock_manager)
        
        assert "HabitManager(" in repr_str
        assert "habits=1" in repr_str
        assert "storage=JSONStorageHandler" in repr_str

# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "manager: mark test as a manager test")
    config.addinivalue_line("markers", "crud: mark test as a CRUD test")
    config.addinivalue_line("markers", "persistence: mark test as a persistence test")
    config.addinivalue_line("markers", "analytics: mark test as an analytics test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")

if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])