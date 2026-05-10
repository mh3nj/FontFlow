"""
FontFlow Studio - Classification System
Category definitions and classification actions (for undo/redo)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from enum import Enum
import time
import shutil
from send2trash import send2trash


class Stage(Enum):
    """Classification stage"""
    A = "primary"      # Initial categorization (1-9, 0)
    B = "secondary"    # Refinement within category


@dataclass
class Category:
    """User-defined classification folder"""
    
    key: str                   # "1", "2", etc.
    name: str                  # "Sans Serif - Modern"
    folder: str               # "01_Sans_Modern"
    color: str = "#00ff88"     # Neon green default
    subcategories: List['Category'] = field(default_factory=list)
    
    def get_path(self, root: Path) -> Path:
        """Get absolute path for this category"""
        return root / self.folder
    
    def __str__(self):
        return f"[{self.key}] {self.name}"


@dataclass
class ClassificationAction:
    """
    Reversible move operation for undo/redo system.
    This represents a single atomic action of moving a font family.
    """
    
    timestamp: float
    family_name: str           # Store name instead of reference (for serialization)
    from_path: Optional[Path]  # None if this is initial classification
    to_path: Path
    stage: Stage
    category_key: str
    subcategory_key: Optional[str] = None
    
    # For tracking moved files
    moved_files: List[tuple[Path, Path]] = field(default_factory=list)  # (source, dest) pairs
    
    def execute(self) -> bool:
        """
        Execute this action (move files from from_path to to_path).
        Returns True if successful.
        """
        try:
            if not self.from_path or not self.from_path.exists():
                print(f"Warning: Source path doesn't exist: {self.from_path}")
                return False
            
            # Ensure target directory exists
            self.to_path.mkdir(parents=True, exist_ok=True)
            
            # Find all font files in the source directory that belong to this family
            font_extensions = {'.ttf', '.otf', '.woff2', '.ttc'}
            font_files = []
            
            for ext in font_extensions:
                font_files.extend(self.from_path.glob(f"*{ext}"))
            
            # Move each file
            self.moved_files = []
            for source_file in font_files:
                dest_file = self.to_path / source_file.name
                
                # Check for conflicts
                if dest_file.exists():
                    print(f"Warning: File already exists: {dest_file}")
                    continue
                
                # Move the file
                shutil.move(str(source_file), str(dest_file))
                self.moved_files.append((source_file, dest_file))
            
            return True
            
        except Exception as e:
            print(f"Error executing classification action: {e}")
            # Attempt rollback
            self.undo()
            return False
    
    def undo(self) -> bool:
        """
        Reverse this action (move files back to from_path).
        Returns True if successful.
        """
        try:
            if not self.from_path:
                print("Cannot undo: no source path")
                return False
            
            # Ensure source directory exists
            self.from_path.mkdir(parents=True, exist_ok=True)
            
            # Move files back
            for source_file, dest_file in reversed(self.moved_files):
                if dest_file.exists():
                    shutil.move(str(dest_file), str(source_file))
            
            return True
            
        except Exception as e:
            print(f"Error undoing classification action: {e}")
            return False
    
    def redo(self) -> bool:
        """
        Re-apply this action (move files from from_path to to_path).
        Same as execute() but uses cached moved_files.
        """
        try:
            # Move files forward again
            for source_file, dest_file in self.moved_files:
                if source_file.exists():
                    # Ensure target directory exists
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_file), str(dest_file))
            
            return True
            
        except Exception as e:
            print(f"Error redoing classification action: {e}")
            return False
    
    def __str__(self):
        stage_name = "Stage A" if self.stage == Stage.A else "Stage B"
        return f"{stage_name}: {self.family_name} → {self.to_path.name}"


class CommandStack:
    """
    Manages undo/redo history using the Command Pattern.
    Maintains a stack of ClassificationAction objects.
    """
    
    def __init__(self, max_history: int = 100):
        self.commands: List[ClassificationAction] = []
        self.current_index: int = -1
        self.max_history = max_history
    
    def execute(self, command: ClassificationAction) -> bool:
        """
        Execute a new command and add it to history.
        Discards any redo branch if we're in the middle of history.
        """
        # Truncate any redo branch
        if self.current_index < len(self.commands) - 1:
            self.commands = self.commands[:self.current_index + 1]
        
        # Execute the command
        success = command.execute()
        
        if success:
            # Add to history
            self.commands.append(command)
            self.current_index += 1
            
            # Limit history size (remove oldest)
            if len(self.commands) > self.max_history:
                self.commands.pop(0)
                self.current_index -= 1
        
        return success
    
    def undo(self) -> Optional[ClassificationAction]:
        """
        Undo the last command.
        Returns the undone command, or None if nothing to undo.
        """
        if self.current_index >= 0:
            command = self.commands[self.current_index]
            success = command.undo()
            
            if success:
                self.current_index -= 1
                return command
        
        return None
    
    def redo(self) -> Optional[ClassificationAction]:
        """
        Redo the next command.
        Returns the redone command, or None if nothing to redo.
        """
        if self.current_index < len(self.commands) - 1:
            self.current_index += 1
            command = self.commands[self.current_index]
            success = command.redo()
            
            if success:
                return command
            else:
                self.current_index -= 1
        
        return None
    
    @property
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self.current_index >= 0
    
    @property
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self.current_index < len(self.commands) - 1
    
    def clear(self):
        """Clear all history"""
        self.commands = []
        self.current_index = -1
    
    def get_history(self, count: int = 10) -> List[ClassificationAction]:
        """Get recent history (most recent first)"""
        if not self.commands:
            return []
        
        end_idx = self.current_index + 1
        start_idx = max(0, end_idx - count)
        return list(reversed(self.commands[start_idx:end_idx]))
