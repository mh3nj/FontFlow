"""
FontFlow Studio - Log Rotator
Automatic log file rotation and archiving
"""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import gzip
import shutil
import yaml


class LogRotator:
    """
    Manages log file rotation to prevent disk filling.
    
    Features:
    - Size-based rotation (default 10MB)
    - Age-based archiving (default 30 days)
    - Gzip compression for old logs
    - Configurable limits
    """
    
    # Default settings
    DEFAULT_MAX_SIZE_MB = 10
    DEFAULT_MAX_AGE_DAYS = 30
    DEFAULT_MAX_FILES = 10
    
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.archive_dir = self.log_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load rotation config from settings"""
        try:
            config_path = Path("config.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('logging', {})
        except Exception:
            pass
        
        return {
            'max_size_mb': self.DEFAULT_MAX_SIZE_MB,
            'max_age_days': self.DEFAULT_MAX_AGE_DAYS,
            'max_files': self.DEFAULT_MAX_FILES,
            'compress': True,
        }
    
    def rotate_log(self, log_path: Path) -> bool:
        """
        Rotate a log file if needed.
        
        Args:
            log_path: Path to the log file
            
        Returns:
            True if rotation occurred, False otherwise
        """
        if not log_path.exists():
            return False
        
        # Check size
        size_mb = log_path.stat().st_size / (1024 * 1024)
        if size_mb <= self.config.get('max_size_mb', self.DEFAULT_MAX_SIZE_MB):
            return False
        
        print(f"📋 Rotating log: {log_path.name} ({size_mb:.1f}MB)")
        
        # Generate rotated filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated_name = f"{log_path.stem}_{timestamp}.log"
        rotated_path = self.archive_dir / rotated_name
        
        # Move current log to archive
        shutil.move(str(log_path), str(rotated_path))
        
        # Compress if enabled
        if self.config.get('compress', True):
            self._compress_log(rotated_path)
        
        # Create new empty log file
        log_path.touch()
        
        # Clean up old logs
        self._cleanup_old_logs()
        
        return True
    
    def _compress_log(self, log_path: Path):
        """Compress a log file with gzip"""
        try:
            compressed_path = log_path.with_suffix('.log.gz')
            with open(log_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original after compression
            log_path.unlink()
            print(f"  Compressed: {compressed_path.name}")
            
        except Exception as e:
            print(f"  Failed to compress: {e}")
    
    def _cleanup_old_logs(self):
        """Remove old archived logs based on age and count"""
        max_age_days = self.config.get('max_age_days', self.DEFAULT_MAX_AGE_DAYS)
        max_files = self.config.get('max_files', self.DEFAULT_MAX_FILES)
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # Get all archived logs
        all_logs = []
        for pattern in ['*.log', '*.log.gz']:
            all_logs.extend(self.archive_dir.glob(pattern))
        
        # Sort by modification time (oldest first)
        all_logs.sort(key=lambda p: p.stat().st_mtime)
        
        # Delete old files beyond max count
        if len(all_logs) > max_files:
            to_delete = all_logs[:-max_files]
            for log_file in to_delete:
                log_file.unlink()
                print(f"  Deleted old log: {log_file.name}")
        
        # Delete files older than max age
        for log_file in all_logs:
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mod_time < cutoff_date:
                log_file.unlink()
                print(f"  Deleted aged log: {log_file.name}")
    
    def rotate_all_logs(self) -> Dict[str, List[str]]:
        """Rotate all logs in the directory"""
        results = {'rotated': [], 'failed': []}
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.name != "archive":  # Skip archive dir
                try:
                    if self.rotate_log(log_file):
                        results['rotated'].append(log_file.name)
                except Exception as e:
                    results['failed'].append((log_file.name, str(e)))
        
        return results
    
    def get_statistics(self) -> dict:
        """Get log rotation statistics"""
        # Get main log sizes
        main_logs = []
        for log_file in self.log_dir.glob("*.log"):
            if log_file.is_file():
                main_logs.append({
                    'name': log_file.name,
                    'size_mb': log_file.stat().st_size / (1024 * 1024),
                })
        
        # Get archived logs
        archived_logs = []
        for pattern in ['*.log', '*.log.gz']:
            for log_file in self.archive_dir.glob(pattern):
                archived_logs.append({
                    'name': log_file.name,
                    'size_mb': log_file.stat().st_size / (1024 * 1024),
                    'age_days': (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)).days,
                })
        
        # Calculate total size
        total_size_mb = sum(l['size_mb'] for l in main_logs) + sum(l['size_mb'] for l in archived_logs)
        
        return {
            'main_logs': main_logs,
            'archived_logs_count': len(archived_logs),
            'total_size_mb': total_size_mb,
            'config': self.config,
        }
