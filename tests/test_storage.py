# test_storage_handler.py

"""
Unit tests for the Storage Handler component.

This test suite covers:
- Abstract StorageHandler base class
- JSONStorageHandler implementation
- SQLiteStorageHandler implementation
- StorageFactory pattern
- StorageError exception handling
- Data persistence and retrieval
- Backup and restore functionality
- Error conditions and edge cases
- Integration with real files and databases
"""

import pytest
import json
import sqlite3
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, mock_open, call

from habit_tracker.storage_handler import (
    StorageHandler,
    JSONStorageHandler,
    SQLiteStorageHandler,
    StorageFactory,
    StorageError
)
from habit_tracker.habit import Habit, Periodicity

class TestStorageError:
    """Test the StorageError exception."""
    
    def test_storage_error_creation(self):
        """Test creating StorageError with message."""
        error = StorageError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_storage_error_inheritance(self):
        """Test that StorageError inherits from Exception."""
        assert issubclass(StorageError, Exception)

class TestStorageHandlerAbstract:
    """Test the abstract StorageHandler base class."""
    
    def test_storage_handler_is_abstract(self):
        """Test that StorageHandler cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StorageHandler()
    
    def test_storage_handler_abstract_methods(self):
        """Test that abstract methods are defined."""
        abstract_methods = StorageHandler.__abstractmethods__
        
        assert 'save_habits' in abstract_methods
        assert 'load_habits' in abstract_methods
        assert 'backup_data' in abstract_methods
        assert 'get_storage_info' in abstract_methods

@pytest.fixture
def sample_habits():
    """Create sample habits for testing."""
    habits = {}
    
    # Daily habit
    daily_habit = Habit(
        name="Exercise",
        description="30 min workout",
        periodicity=Periodicity.DAILY,
        creation_date=datetime(2024, 1, 1)
    )
    daily_habit.check_off(datetime(2024, 1, 15))
    daily_habit.check_off(datetime(2024, 1, 14))
    habits["Exercise"] = daily_habit
    
    # Weekly habit
    weekly_habit = Habit(
        name="Weekly Review",
        description="Review weekly progress",
        periodicity=Periodicity.WEEKLY,
        creation_date=datetime(2024, 1, 1)
    )
    weekly_habit.check_off(datetime(2024, 1, 15))
    habits["Weekly Review"] = weekly_habit
    
    return habits

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

class TestJSONStorageHandler:
    """Test the JSONStorageHandler implementation."""
    
    def test_init_creates_file(self, temp_dir):
        """Test that initialization creates the storage file."""
        file_path = temp_dir / "test_habits.json"
        
        handler = JSONStorageHandler(str(file_path))
        
        assert file_path.exists()
        assert handler.file_path == file_path
        assert handler.backup_dir == temp_dir / "backups"
    
    def test_init_existing_file(self, temp_dir):
        """Test initialization with existing file."""
        file_path = temp_dir / "existing.json"
        
        # Create existing file with data
        existing_data = {
            "habits": {},
            "metadata": {"version": "1.0", "created": "2024-01-01"}
        }
        with open(file_path, 'w') as f:
            json.dump(existing_data, f)
        
        handler = JSONStorageHandler(str(file_path))
        
        # Should not overwrite existing data
        with open(file_path, 'r') as f:
            data = json.load(f)
        assert data == existing_data
    
    def test_init_custom_backup_dir(self, temp_dir):
        """Test initialization with custom backup directory."""
        file_path = temp_dir / "test.json"
        backup_dir = temp_dir / "custom_backups"
        
        handler = JSONStorageHandler(str(file_path), str(backup_dir))
        
        assert handler.backup_dir == backup_dir
        assert backup_dir.exists()
    
    def test_save_habits_success(self, temp_dir, sample_habits):
        """Test successful habit saving."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        
        handler.save_habits(sample_habits)
        
        # Verify file was created and contains correct data
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert 'habits' in data
        assert 'metadata' in data
        assert len(data['habits']) == 2
        assert 'Exercise' in data['habits']
        assert 'Weekly Review' in data['habits']
        assert data['metadata']['total_habits'] == 2
        assert data['metadata']['total_completions'] == 3
    
    def test_save_habits_atomic_operation(self, temp_dir, sample_habits):
        """Test that save operation is atomic (uses temp file)."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Create initial data
        handler.save_habits({})
        
        # Mock open to track file operations
        with patch('builtins.open', mock_open()) as mock_file:
            handler.save_habits(sample_habits)
        
        # Should have opened temp file and then renamed
        mock_file.assert_called()
        # Check that temp file was used
        temp_path = file_path.with_suffix('.tmp')
        assert any(str(temp_path) in str(call) for call in mock_file.call_args_list)
    
    def test_save_habits_creates_backup(self, temp_dir, sample_habits):
        """Test that save creates automatic backup."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Save initial data
        handler.save_habits({})
        
        # Save again (should create backup)
        handler.save_habits(sample_habits)
        
        # Check backup was created
        backup_files = list(handler.backup_dir.glob("habits_auto_backup_*.json"))
        assert len(backup_files) >= 1
    
    def test_save_habits_error_handling(self, temp_dir, sample_habits):
        """Test save error handling."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Mock open to raise an error
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(StorageError, match="Failed to save habits"):
                handler.save_habits(sample_habits)
    
    def test_load_habits_success(self, temp_dir, sample_habits):
        """Test successful habit loading."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        
        # First save the data
        handler.save_habits(sample_habits)
        
        # Create new handler and load
        new_handler = JSONStorageHandler(str(file_path))
        loaded_habits = new_handler.load_habits()
        
        assert len(loaded_habits) == 2
        assert "Exercise" in loaded_habits
        assert "Weekly Review" in loaded_habits
        
        # Verify habit properties
        exercise = loaded_habits["Exercise"]
        assert exercise.name == "Exercise"
        assert exercise.periodicity == Periodicity.DAILY
        assert len(exercise.completion_history) == 2
    
    def test_load_habits_file_not_found(self, temp_dir):
        """Test loading when file doesn't exist."""
        file_path = temp_dir / "nonexistent.json"
        handler = JSONStorageHandler(str(file_path))
        
        habits = handler.load_habits()
        
        assert habits == {}
    
    def test_load_habits_invalid_json(self, temp_dir):
        """Test loading with invalid JSON."""
        file_path = temp_dir / "invalid.json"
        
        # Create file with invalid JSON
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        handler = JSONStorageHandler(str(file_path))
        
        with pytest.raises(StorageError, match="Invalid JSON format"):
            handler.load_habits()
    
    def test_load_habits_corrupted_data(self, temp_dir):
        """Test loading with corrupted habit data."""
        file_path = temp_dir / "corrupted.json"
        
        # Create file with invalid habit data
        corrupted_data = {
            "habits": {
                "Invalid": {
                    "name": "Invalid",
                    "periodicity": "invalid_periodicity",
                    "creation_date": "invalid_date",
                    "completion_history": ["not_a_datetime"]
                }
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(corrupted_data, f)
        
        handler = JSONStorageHandler(str(file_path))
        
        # Should load valid habits and skip invalid ones
        with patch('builtins.print') as mock_print:
            habits = handler.load_habits()
        
        assert habits == {}
        mock_print.assert_called()
        assert "Failed to load habit 'Invalid'" in str(mock_print.call_args)
    
    def test_backup_data_success(self, temp_dir, sample_habits):
        """Test successful backup creation."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        handler.save_habits(sample_habits)
        
        backup_path = temp_dir / "backup.json"
        result = handler.backup_data(str(backup_path))
        
        assert result is True
        assert backup_path.exists()
        
        # Verify backup contains same data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        with open(file_path, 'r') as f:
            original_data = json.load(f)
        
        assert backup_data == original_data
    
    def test_backup_data_creates_directory(self, temp_dir, sample_habits):
        """Test backup creates directory if it doesn't exist."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        handler.save_habits(sample_habits)
        
        backup_path = temp_dir / "new_dir" / "backup.json"
        result = handler.backup_data(str(backup_path))
        
        assert result is True
        assert backup_path.exists()
        assert backup_path.parent.exists()
    
    def test_backup_data_error(self, temp_dir):
        """Test backup error handling."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Try to backup to invalid location
        invalid_path = "/invalid/path/backup.json"
        
        with patch('builtins.print') as mock_print:
            result = handler.backup_data(invalid_path)
        
        assert result is False
        mock_print.assert_called()
        assert "Backup failed" in str(mock_print.call_args)
    
    def test_get_storage_info(self, temp_dir, sample_habits):
        """Test getting storage information."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        handler.save_habits(sample_habits)
        
        info = handler.get_storage_info()
        
        assert info['type'] == 'JSON'
        assert info['file_path'] == str(file_path)
        assert info['file_size_bytes'] > 0
        assert info['file_size_human'] is not None
        assert info['backup_dir'] == str(handler.backup_dir)
        assert 'metadata' in info
    
    def test_cleanup_old_backups(self, temp_dir, sample_habits):
        """Test cleanup of old backup files."""
        file_path = temp_dir / "test.json"
        handler = JSONStorageHandler(str(file_path))
        handler.save_habits(sample_habits)
        
        # Create multiple backups
        for i in range(15):
            handler.save_habits(sample_habits)
        
        backup_files = list(handler.backup_dir.glob("habits_auto_backup_*.json"))
        initial_count = len(backup_files)
        
        # Manually trigger cleanup (keep only 5)
        handler._cleanup_old_backups(5)
        
        backup_files = list(handler.backup_dir.glob("habits_auto_backup_*.json"))
        final_count = len(backup_files)
        
        assert final_count <= 5
        assert final_count < initial_count
    
    def test_format_file_size(self, temp_dir):
        """Test file size formatting."""
        handler = JSONStorageHandler(str(temp_dir / "test.json"))
        
        assert handler._format_file_size(0) == "0.0 B"
        assert handler._format_file_size(1023) == "1023.0 B"
        assert handler._format_file_size(1024) == "1.0 KB"
        assert handler._format_file_size(1024 * 1024) == "1.0 MB"
        assert handler._format_file_size(1024 * 1024 * 1024) == "1.0 GB"

class TestSQLiteStorageHandler:
    """Test the SQLiteStorageHandler implementation."""
    
    def test_init_creates_database(self, temp_dir):
        """Test that initialization creates the database."""
        db_path = temp_dir / "test.db"
        
        handler = SQLiteStorageHandler(str(db_path))
        
        assert db_path.exists()
        assert handler.db_path == db_path
        
        # Verify tables were created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check habits table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habits'")
        assert cursor.fetchone() is not None
        
        # Check completions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completions'")
        assert cursor.fetchone() is not None
        
        # Check metadata table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_init_custom_backup_dir(self, temp_dir):
        """Test initialization with custom backup directory."""
        db_path = temp_dir / "test.db"
        backup_dir = temp_dir / "custom_backups"
        
        handler = SQLiteStorageHandler(str(db_path), str(backup_dir))
        
        assert handler.backup_dir == backup_dir
        assert backup_dir.exists()
    
    def test_save_habits_success(self, temp_dir, sample_habits):
        """Test successful habit saving to SQLite."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        handler.save_habits(sample_habits)
        
        # Verify data was saved
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check habits
        cursor.execute("SELECT name, description, periodicity FROM habits")
        habits_rows = cursor.fetchall()
        assert len(habits_rows) == 2
        
        habit_names = [row[0] for row in habits_rows]
        assert "Exercise" in habit_names
        assert "Weekly Review" in habit_names
        
        # Check completions
        cursor.execute("SELECT COUNT(*) FROM completions")
        completion_count = cursor.fetchone()[0]
        assert completion_count == 3
        
        # Check metadata
        cursor.execute("SELECT value FROM metadata WHERE key='total_habits'")
        total_habits = cursor.fetchone()[0]
        assert total_habits == "2"
        
        conn.close()
    
    def test_save_habits_transaction(self, temp_dir, sample_habits):
        """Test that save operation uses transactions."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Mock sqlite3.connect to raise an error during save
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Make execute raise an error
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            
            with pytest.raises(StorageError, match="Failed to save habits to database"):
                handler.save_habits(sample_habits)
            
            # Verify transaction was started
            mock_conn.execute.assert_called_with('BEGIN TRANSACTION')
    
    def test_save_habits_clears_existing_data(self, temp_dir, sample_habits):
        """Test that save clears existing data before saving."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Save initial data
        initial_habits = {"Initial": Habit("Test", "Test", Periodicity.DAILY)}
        handler.save_habits(initial_habits)
        
        # Save new data
        handler.save_habits(sample_habits)
        
        # Verify only new data exists
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM habits")
        habit_names = [row[0] for row in cursor.fetchall()]
        
        assert "Initial" not in habit_names
        assert "Exercise" in habit_names
        assert "Weekly Review" in habit_names
        
        conn.close()
    
    def test_load_habits_success(self, temp_dir, sample_habits):
        """Test successful habit loading from SQLite."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # First save the data
        handler.save_habits(sample_habits)
        
        # Create new handler and load
        new_handler = SQLiteStorageHandler(str(db_path))
        loaded_habits = new_handler.load_habits()
        
        assert len(loaded_habits) == 2
        assert "Exercise" in loaded_habits
        assert "Weekly Review" in loaded_habits
        
        # Verify habit properties
        exercise = loaded_habits["Exercise"]
        assert exercise.name == "Exercise"
        assert exercise.periodicity == Periodicity.DAILY
        assert len(exercise.completion_history) == 2
    
    def test_load_habits_empty_database(self, temp_dir):
        """Test loading from empty database."""
        db_path = temp_dir / "empty.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        habits = handler.load_habits()
        
        assert habits == {}
    
    def test_load_habits_corrupted_database(self, temp_dir):
        """Test loading from corrupted database."""
        db_path = temp_dir / "corrupted.db"
        
        # Create invalid database file
        with open(db_path, 'w') as f:
            f.write("not a valid database")
        
        handler = SQLiteStorageHandler(str(db_path))
        
        with pytest.raises(StorageError, match="Failed to load habits from database"):
            handler.load_habits()
    
    def test_backup_data_success(self, temp_dir, sample_habits):
        """Test successful database backup."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        handler.save_habits(sample_habits)
        
        backup_path = temp_dir / "backup.db"
        result = handler.backup_data(str(backup_path))
        
        assert result is True
        assert backup_path.exists()
        
        # Verify backup contains same data
        backup_handler = SQLiteStorageHandler(str(backup_path))
        backup_habits = backup_handler.load_habits()
        
        assert len(backup_habits) == 2
        assert "Exercise" in backup_habits
    
    def test_backup_data_error(self, temp_dir):
        """Test backup error handling."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Try to backup to invalid location
        invalid_path = "/invalid/path/backup.db"
        
        with patch('builtins.print') as mock_print:
            result = handler.backup_data(invalid_path)
        
        assert result is False
        mock_print.assert_called()
        assert "Database backup failed" in str(mock_print.call_args)
    
    def test_get_storage_info(self, temp_dir, sample_habits):
        """Test getting storage information for SQLite."""
        db_path = temp_dir / "test.db"
        handler = SQLiteStorageHandler(str(db_path))
        handler.save_habits(sample_habits)
        
        info = handler.get_storage_info()
        
        assert info['type'] == 'SQLite'
        assert info['file_path'] == str(db_path)
        assert info['file_size_bytes'] > 0
        assert info['file_size_human'] is not None
        assert info['habit_count'] == 2
        assert info['completion_count'] == 3
        assert 'created' in info
        assert 'last_modified' in info
    
    def test_format_file_size(self, temp_dir):
        """Test file size formatting for SQLite."""
        handler = SQLiteStorageHandler(str(temp_dir / "test.db"))
        
        assert handler._format_file_size(0) == "0.0 B"
        assert handler._format_file_size(1024) == "1.0 KB"
        assert handler._format_file_size(1024 * 1024) == "1.0 MB"

class TestStorageFactory:
    """Test the StorageFactory class."""
    
    def test_create_json_storage(self, temp_dir):
        """Test creating JSON storage through factory."""
        file_path = temp_dir / "test.json"
        
        storage = StorageFactory.create_storage_handler(
            storage_type='json',
            file_path=str(file_path)
        )
        
        assert isinstance(storage, JSONStorageHandler)
        assert storage.file_path == file_path
    
    def test_create_sqlite_storage(self, temp_dir):
        """Test creating SQLite storage through factory."""
        db_path = temp_dir / "test.db"
        
        storage = StorageFactory.create_storage_handler(
            storage_type='sqlite',
            file_path=str(db_path)
        )
        
        assert isinstance(storage, SQLiteStorageHandler)
        assert storage.db_path == db_path
    
    def test_create_storage_case_insensitive(self, temp_dir):
        """Test that storage type is case insensitive."""
        storage1 = StorageFactory.create_storage_handler(storage_type='JSON')
        storage2 = StorageFactory.create_storage_handler(storage_type='SQLite')
        
        assert isinstance(storage1, JSONStorageHandler)
        assert isinstance(storage2, SQLiteStorageHandler)
    
    def test_create_storage_invalid_type(self):
        """Test creating storage with invalid type."""
        with pytest.raises(ValueError, match="Unknown storage type"):
            StorageFactory.create_storage_handler(storage_type='invalid')
    
    def test_get_available_storage_types(self):
        """Test getting available storage types."""
        types = StorageFactory.get_available_storage_types()
        
        assert 'json' in types
        assert 'sqlite' in types
        assert len(types) == 2
    
    def test_get_storage_help(self):
        """Test getting storage help text."""
        help_text = StorageFactory.get_storage_help()
        
        assert 'JSON Storage' in help_text
        assert 'SQLite Storage' in help_text
        assert 'Simple, portable' in help_text
        assert 'More robust' in help_text

class TestStorageHandlerIntegration:
    """Integration tests for storage handlers."""
    
    def test_json_round_trip(self, temp_dir, sample_habits):
        """Test complete JSON save/load round trip."""
        file_path = temp_dir / "roundtrip.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Save habits
        handler.save_habits(sample_habits)
        
        # Load habits
        loaded_habits = handler.load_habits()
        
        # Verify all data is preserved
        assert len(loaded_habits) == len(sample_habits)
        
        for name, original_habit in sample_habits.items():
            loaded_habit = loaded_habits[name]
            assert loaded_habit.name == original_habit.name
            assert loaded_habit.description == original_habit.description
            assert loaded_habit.periodicity == original_habit.periodicity
            assert loaded_habit.creation_date == original_habit.creation_date
            assert len(loaded_habit.completion_history) == len(original_habit.completion_history)
            
            for original_completion in original_habit.completion_history:
                assert original_completion in loaded_habit.completion_history
    
    def test_sqlite_round_trip(self, temp_dir, sample_habits):
        """Test complete SQLite save/load round trip."""
        db_path = temp_dir / "roundtrip.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Save habits
        handler.save_habits(sample_habits)
        
        # Load habits
        loaded_habits = handler.load_habits()
        
        # Verify all data is preserved
        assert len(loaded_habits) == len(sample_habits)
        
        for name, original_habit in sample_habits.items():
            loaded_habit = loaded_habits[name]
            assert loaded_habit.name == original_habit.name
            assert loaded_habit.description == original_habit.description
            assert loaded_habit.periodicity == original_habit.periodicity
            assert loaded_habit.creation_date == original_habit.creation_date
            assert len(loaded_habit.completion_history) == len(original_habit.completion_history)
    
    def test_migration_json_to_sqlite(self, temp_dir, sample_habits):
        """Test migrating data from JSON to SQLite."""
        # Save to JSON
        json_path = temp_dir / "source.json"
        json_handler = JSONStorageHandler(str(json_path))
        json_handler.save_habits(sample_habits)
        
        # Migrate to SQLite
        sqlite_path = temp_dir / "target.db"
        sqlite_handler = SQLiteStorageHandler(str(sqlite_path))
        
        # Load from JSON and save to SQLite
        habits_from_json = json_handler.load_habits()
        sqlite_handler.save_habits(habits_from_json)
        
        # Verify migration
        habits_from_sqlite = sqlite_handler.load_habits()
        
        assert len(habits_from_sqlite) == len(sample_habits)
        for name in sample_habits:
            assert name in habits_from_sqlite
    
    def test_concurrent_access_json(self, temp_dir, sample_habits):
        """Test concurrent access to JSON storage."""
        file_path = temp_dir / "concurrent.json"
        
        # Create two handlers
        handler1 = JSONStorageHandler(str(file_path))
        handler2 = JSONStorageHandler(str(file_path))
        
        # Save with first handler
        handler1.save_habits(sample_habits)
        
        # Load with second handler
        loaded_habits = handler2.load_habits()
        
        assert len(loaded_habits) == len(sample_habits)
    
    def test_large_dataset_json(self, temp_dir):
        """Test JSON storage with large dataset."""
        file_path = temp_dir / "large.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Create many habits with many completions
        large_habits = {}
        for i in range(100):
            habit = Habit(
                name=f"Habit_{i}",
                description=f"Description {i}",
                periodicity=Periodicity.DAILY
            )
            
            # Add many completions
            for j in range(100):
                habit.check_off(datetime.now() - timedelta(days=j))
            
            large_habits[f"Habit_{i}"] = habit
        
        # Save and load
        handler.save_habits(large_habits)
        loaded_habits = handler.load_habits()
        
        assert len(loaded_habits) == 100
        assert sum(len(h.completion_history) for h in loaded_habits.values()) == 10000
    
    def test_large_dataset_sqlite(self, temp_dir):
        """Test SQLite storage with large dataset."""
        db_path = temp_dir / "large.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Create many habits with many completions
        large_habits = {}
        for i in range(100):
            habit = Habit(
                name=f"Habit_{i}",
                description=f"Description {i}",
                periodicity=Periodicity.DAILY
            )
            
            # Add many completions
            for j in range(100):
                habit.check_off(datetime.now() - timedelta(days=j))
            
            large_habits[f"Habit_{i}"] = habit
        
        # Save and load
        handler.save_habits(large_habits)
        loaded_habits = handler.load_habits()
        
        assert len(loaded_habits) == 100
        assert sum(len(h.completion_history) for h in loaded_habits.values()) == 10000

class TestStorageHandlerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_json_unicode_characters(self, temp_dir):
        """Test JSON storage with Unicode characters."""
        file_path = temp_dir / "unicode.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Create habit with Unicode characters
        habit = Habit(
            name="🏃‍♂️ Exercise",
            description="锻炼 30 分钟",
            periodicity=Periodicity.DAILY
        )
        habits = {"Exercise": habit}
        
        # Save and load
        handler.save_habits(habits)
        loaded_habits = handler.load_habits()
        
        assert "🏃‍♂️ Exercise" in loaded_habits
        assert loaded_habits["🏃‍♂️ Exercise"].description == "锻炼 30 分钟"
    
    def test_sqlite_unicode_characters(self, temp_dir):
        """Test SQLite storage with Unicode characters."""
        db_path = temp_dir / "unicode.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Create habit with Unicode characters
        habit = Habit(
            name="🏃‍♂️ Exercise",
            description="锻炼 30 分钟",
            periodicity=Periodicity.DAILY
        )
        habits = {"Exercise": habit}
        
        # Save and load
        handler.save_habits(habits)
        loaded_habits = handler.load_habits()
        
        assert "🏃‍♂️ Exercise" in loaded_habits
        assert loaded_habits["🏃‍♂️ Exercise"].description == "锻炼 30 分钟"
    
    def test_json_special_characters_in_description(self, temp_dir):
        """Test JSON with special characters in description."""
        file_path = temp_dir / "special.json"
        handler = JSONStorageHandler(str(file_path))
        
        habit = Habit(
            name="Test",
            description="Special chars: \"quotes\", 'apostrophes', \n newlines, \t tabs",
            periodicity=Periodicity.DAILY
        )
        habits = {"Test": habit}
        
        # Save and load
        handler.save_habits(habits)
        loaded_habits = handler.load_habits()
        
        assert loaded_habits["Test"].description == habit.description
    
    def test_json_empty_habits_dictionary(self, temp_dir):
        """Test JSON with empty habits dictionary."""
        file_path = temp_dir / "empty.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Save empty dictionary
        handler.save_habits({})
        
        # Load
        loaded_habits = handler.load_habits()
        
        assert loaded_habits == {}
    
    def test_sqlite_empty_habits_dictionary(self, temp_dir):
        """Test SQLite with empty habits dictionary."""
        db_path = temp_dir / "empty.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Save empty dictionary
        handler.save_habits({})
        
        # Load
        loaded_habits = handler.load_habits()
        
        assert loaded_habits == {}
    
    def test_json_file_permission_error(self, temp_dir):
        """Test JSON with file permission errors."""
        file_path = temp_dir / "readonly.json"
        handler = JSONStorageHandler(str(file_path))
        
        # Create file and make it read-only
        file_path.touch()
        os.chmod(file_path, 0o444)
        
        try:
            with pytest.raises(StorageError):
                handler.save_habits({})
        finally:
            # Restore permissions for cleanup
            os.chmod(file_path, 0o666)
    
    def test_sqlite_database_locked(self, temp_dir):
        """Test SQLite with locked database."""
        db_path = temp_dir / "locked.db"
        handler = SQLiteStorageHandler(str(db_path))
        
        # Open database in another connection to lock it
        conn = sqlite3.connect(str(db_path))
        
        try:
            # Try to save while database is locked
            with pytest.raises(StorageError):
                handler.save_habits({})
        finally:
            conn.close()
    
    def test_json_very_long_habit_name(self, temp_dir):
        """Test JSON with very long habit name."""
        file_path = temp_dir / "long_name.json"
        handler = JSONStorageHandler(str(file_path))
        
        long_name = "A" * 1000
        habit = Habit(name=long_name, description="Test", periodicity=Periodicity.DAILY)
        habits = {"Long": habit}
        
        # Save and load
        handler.save_habits(habits)
        loaded_habits = handler.load_habits()
        
        assert loaded_habits["Long"].name == long_name

# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "storage: mark test as a storage test")
    config.addinivalue_line("markers", "json: mark test as a JSON storage test")
    config.addinivalue_line("markers", "sqlite: mark test as a SQLite storage test")
    config.addinivalue_line("markers", "integration: mark test as a storage integration test")
    config.addinivalue_line("markers", "edge: mark test as an edge case test")

if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])