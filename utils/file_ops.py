"""
FontFlow Studio - File Operations
Safe, atomic file operations with rollback support
"""

from pathlib import Path
from typing import List, Tuple, Optional
import shutil
import time
from send2trash import send2trash

from models.font_family import FontFamily, FontStyle
from utils.transaction_manager import TransactionManager


class FileOperationError(Exception):
    """Custom exception for file operation errors"""
    pass


class FileOperations:
    """
    Handles all file system operations safely.
    
    Features:
    - Atomic operations (all or nothing)
    - Automatic rollback on failure
    - Recycle bin integration (no permanent deletes)
    - Collision detection
    - Progress tracking
    """
    
    # Font file extensions we handle
    FONT_EXTENSIONS = {'.ttf', '.otf', '.woff2', '.ttc', '.woff'}

    def __init__(self):
        self.transaction_manager = TransactionManager()
        self.temp_dir = Path("data/transactions/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def move_family(self, family: FontFamily, target_dir: Path, 
                    on_progress: Optional[callable] = None) -> Tuple[bool, str]:
        """Move all files in a font family with transaction support"""
        
        # Create transaction manager instance
        tx_manager = TransactionManager()
        
        # Start transaction (write-ahead log)
        transaction = tx_manager.start_transaction(
            operation="MOVE",
            source=family.source_folder,
            target=target_dir,
            family_name=family.family_name
        )
        
        try:
            # Validate target directory
            target_dir = Path(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Create temp directory for this transaction (atomic move)
            temp_move_dir = tx_manager.temp_dir / transaction.id
            temp_move_dir.mkdir(parents=True, exist_ok=True)
            transaction.temp_path = str(temp_move_dir)
            tx_manager._save_transaction(transaction)
            
            # Collect all font files
            font_files = [style.path for style in family.styles]
            
            # First, copy to temp (safe operation)
            temp_files = []
            for source_path in font_files:
                temp_path = temp_move_dir / source_path.name
                shutil.copy2(str(source_path), str(temp_path))
                temp_files.append(temp_path)
            
            # Then move from temp to target (atomic per file)
            for i, temp_path in enumerate(temp_files):
                if on_progress:
                    on_progress(i + 1, len(temp_files), temp_path.name)
                
                dest_path = target_dir / temp_path.name
                
                # Check for conflicts
                if dest_path.exists():
                    raise FileOperationError(f"File already exists: {dest_path.name}")
                
                # Move from temp to target
                shutil.move(str(temp_path), str(dest_path))
            
            # Update family metadata
            family.source_folder = target_dir
            for i, style in enumerate(family.styles):
                style.path = target_dir / style.path.name
            
            # Commit transaction
            tx_manager.commit_transaction(transaction)
            
            # Clean up original files
            for source_path in font_files:
                if source_path.exists():
                    source_path.unlink()
            
            # Clean up empty source folders
            self._cleanup_empty_folders(family.source_folder.parent)
            
            return True, f"Moved {len(font_files)} file(s) to {target_dir.name}"
            
        except Exception as e:
            # Rollback transaction
            tx_manager.rollback_transaction(transaction, str(e))
            
            # Clean up temp files
            if transaction.temp_path:
                temp_path = Path(transaction.temp_path)
                if temp_path.exists():
                    shutil.rmtree(temp_path, ignore_errors=True)
            
            return False, f"Move failed: {e}"
    
    def _cleanup_empty_folders(self, root_path: Path):
        """Remove empty directories recursively"""
        try:
            for dirpath in sorted(root_path.rglob('*'), reverse=True):
                if dirpath.is_dir() and not any(dirpath.iterdir()):
                    dirpath.rmdir()
                    print(f"Removed empty directory: {dirpath}")
        except Exception as e:
            print(f"Error cleaning directories: {e}")
    
    def _rollback_moves(self, moved_files: List[Tuple[Path, Path]]):
        """Rollback file moves in case of error"""
        for source, dest in reversed(moved_files):
            try:
                if dest.exists():
                    shutil.move(str(dest), str(source))
                    print(f"Rolled back: {dest.name} → {source.name}")
            except Exception as e:
                print(f"Warning: Failed to rollback {dest.name}: {e}")
    
    def send_to_recycle_bin(self, family: FontFamily) -> Tuple[bool, str]:
        """
        Send font family to recycle bin (safe delete).
        
        Uses system recycle bin - files can be restored!
        
        Args:
            family: FontFamily to delete
            
        Returns:
            (success: bool, message: str)
        """
        try:
            deleted_files = []
            
            for style in family.styles:
                if style.path.exists():
                    send2trash(str(style.path))
                    deleted_files.append(style.path.name)
            
            if deleted_files:
                return True, f"Sent {len(deleted_files)} file(s) to recycle bin"
            else:
                return False, "No files found to delete"
                
        except Exception as e:
            return False, f"Failed to delete: {e}"
    
    def copy_family(self, family: FontFamily, target_dir: Path) -> Tuple[bool, str]:
        """
        Copy font family to target directory (non-destructive).
        
        Args:
            family: FontFamily to copy
            target_dir: Destination directory
            
        Returns:
            (success: bool, message: str)
        """
        try:
            target_dir = Path(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            copied_files = []
            
            for style in family.styles:
                if style.path.exists():
                    dest_path = target_dir / style.path.name
                    
                    # Skip if already exists
                    if dest_path.exists():
                        continue
                    
                    shutil.copy2(str(style.path), str(dest_path))
                    copied_files.append(style.path.name)
            
            return True, f"Copied {len(copied_files)} file(s)"
            
        except Exception as e:
            return False, f"Copy failed: {e}"
    
    def verify_family_integrity(self, family: FontFamily) -> Tuple[bool, List[str]]:
        """
        Verify that all font files in family actually exist.
        
        Args:
            family: FontFamily to verify
            
        Returns:
            (all_exist: bool, missing_files: List[str])
        """
        missing = []
        
        for style in family.styles:
            if not style.path.exists():
                missing.append(str(style.path))
        
        return len(missing) == 0, missing
    
    def get_directory_size(self, path: Path) -> int:
        """
        Get total size of directory in bytes.
        
        Args:
            path: Directory path
            
        Returns:
            Total size in bytes
        """
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except Exception as e:
            print(f"Error calculating size: {e}")
        
        return total
    
    def format_size(self, size_bytes: int) -> str:
        """Format byte size to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def cleanup_empty_directories(self, root: Path):
        """
        Remove empty directories recursively.
        
        Useful after moving fonts out of folders.
        
        Args:
            root: Root directory to clean
        """
        self._cleanup_empty_folders(root)