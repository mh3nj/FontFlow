"""
FontFlow Studio - Event Logger
Append-only event logging for audit trail and recovery
"""

from pathlib import Path
from typing import Optional, List, Dict
import json
import time
import threading
from datetime import datetime


class EventLogger:
    """
    Append-only event logger for all font operations.
    
    Features:
    - Thread-safe logging
    - JSONL format (one JSON object per line)
    - Never overwrites (append-only)
    - Includes timestamps and metadata
    - Supports querying history
    """
    
    def __init__(self, log_dir: Path, library_name: str):
        """
        Initialize logger.
        
        Args:
            log_dir: Directory for log files
            library_name: Name of the library (used in filename)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file name based on library
        safe_name = library_name.replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime('%Y%m%d')
        self.log_file = self.log_dir / f"fontflow_{safe_name}_{timestamp}.jsonl"
        
        # Thread lock for safe concurrent writes
        self._lock = threading.Lock()
        
        # Write header if new file
        if not self.log_file.exists():
            self._write_header()
    
    def _write_header(self):
        """Write log file header"""
        header = {
            'event': 'log_started',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'library': str(self.log_file.stem),
            'version': '1.0',
        }
        self._append_entry(header)
    
    def _append_entry(self, entry: dict):
        """Append an entry to the log file (thread-safe)"""
        with self._lock:
            try:
                with self.log_file.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(entry) + '\n')
            except Exception as e:
                print(f"Error writing to log: {e}")
    
    def log_classification(self, family_name: str, from_path: str, to_path: str, 
                          stage: str, category: str, subcategory: Optional[str] = None):
        """
        Log a font classification action.
        
        Args:
            family_name: Name of the font family
            from_path: Source directory
            to_path: Destination directory
            stage: Classification stage ("A" or "B")
            category: Category key
            subcategory: Subcategory key (optional)
        """
        entry = {
            'event': 'classification',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'family_name': family_name,
            'from_path': str(from_path),
            'to_path': str(to_path),
            'stage': stage,
            'category': category,
            'subcategory': subcategory,
        }
        self._append_entry(entry)
    
    def log_skip(self, family_name: str):
        """Log a skipped family"""
        entry = {
            'event': 'skip',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'family_name': family_name,
        }
        self._append_entry(entry)
    
    def log_uncertain(self, family_name: str, to_path: str):
        """Log a family marked as uncertain"""
        entry = {
            'event': 'uncertain',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'family_name': family_name,
            'to_path': str(to_path),
        }
        self._append_entry(entry)
    
    def log_undo(self, family_name: str, action_type: str):
        """Log an undo operation"""
        entry = {
            'event': 'undo',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'family_name': family_name,
            'undone_action': action_type,
        }
        self._append_entry(entry)
    
    def log_redo(self, family_name: str, action_type: str):
        """Log a redo operation"""
        entry = {
            'event': 'redo',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'family_name': family_name,
            'redone_action': action_type,
        }
        self._append_entry(entry)
    
    def log_error(self, error_type: str, message: str, context: Optional[dict] = None):
        """Log an error"""
        entry = {
            'event': 'error',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'context': context or {},
        }
        self._append_entry(entry)
    
    def log_session_start(self, total_families: int, current_index: int):
        """Log session start"""
        entry = {
            'event': 'session_start',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'total_families': total_families,
            'starting_index': current_index,
        }
        self._append_entry(entry)
    
    def log_session_end(self, families_processed: int, duration_seconds: float):
        """Log session end"""
        entry = {
            'event': 'session_end',
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'families_processed': families_processed,
            'duration_seconds': duration_seconds,
        }
        self._append_entry(entry)
    
    def get_history(self, family_name: Optional[str] = None, 
                   event_type: Optional[str] = None,
                   limit: int = 100) -> List[Dict]:
        """
        Query log history.
        
        Args:
            family_name: Filter by family name (optional)
            event_type: Filter by event type (optional)
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries (most recent first)
        """
        if not self.log_file.exists():
            return []
        
        entries = []
        
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if family_name and entry.get('family_name') != family_name:
                            continue
                        
                        if event_type and entry.get('event') != event_type:
                            continue
                        
                        entries.append(entry)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent first
            entries.reverse()
            return entries[:limit]
            
        except Exception as e:
            print(f"Error reading log: {e}")
            return []
    
    def get_family_history(self, family_name: str) -> List[Dict]:
        """Get complete history for a specific family"""
        return self.get_history(family_name=family_name, limit=1000)
    
    def get_statistics(self) -> Dict:
        """
        Get statistics from log file.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_events': 0,
            'classifications': 0,
            'skips': 0,
            'uncertain': 0,
            'undos': 0,
            'redos': 0,
            'errors': 0,
        }
        
        if not self.log_file.exists():
            return stats
        
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        event = entry.get('event', '')
                        
                        stats['total_events'] += 1
                        
                        if event == 'classification':
                            stats['classifications'] += 1
                        elif event == 'skip':
                            stats['skips'] += 1
                        elif event == 'uncertain':
                            stats['uncertain'] += 1
                        elif event == 'undo':
                            stats['undos'] += 1
                        elif event == 'redo':
                            stats['redos'] += 1
                        elif event == 'error':
                            stats['errors'] += 1
                            
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"Error calculating statistics: {e}")
        
        return stats
    
    def export_report(self, output_path: Path):
        """
        Export a human-readable report.
        
        Args:
            output_path: Path for the report file
        """
        stats = self.get_statistics()
        recent = self.get_history(limit=50)
        
        try:
            with output_path.open('w', encoding='utf-8') as f:
                f.write("FontFlow Session Report\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("Statistics:\n")
                f.write(f"  Total Events: {stats['total_events']}\n")
                f.write(f"  Classifications: {stats['classifications']}\n")
                f.write(f"  Skips: {stats['skips']}\n")
                f.write(f"  Uncertain: {stats['uncertain']}\n")
                f.write(f"  Undos: {stats['undos']}\n")
                f.write(f"  Redos: {stats['redos']}\n")
                f.write(f"  Errors: {stats['errors']}\n\n")
                
                f.write("Recent Activity (last 50 events):\n")
                f.write("-" * 50 + "\n")
                
                for entry in recent:
                    event = entry.get('event', 'unknown')
                    dt = entry.get('datetime', '')
                    family = entry.get('family_name', 'N/A')
                    
                    f.write(f"{dt} | {event:15s} | {family}\n")
            
            print(f"Report exported to: {output_path}")
            
        except Exception as e:
            print(f"Error exporting report: {e}")
