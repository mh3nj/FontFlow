"""
FontFlow Studio - Core Engine
Main application controller with keyboard handling and auto-cycling
"""

from pathlib import Path
from typing import Optional, Callable
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import time
import shutil

from models.font_family import FontFamily
from models.classification import Stage, Category, CommandStack, ClassificationAction
from core.font_library import FontLibrary
from core.fast_library import FastFontLibrary, FamilyPointer
from core.session import SessionState
from utils.file_ops import FileOperations
from utils.logger import EventLogger
from utils.duplicate_detector import SafeDuplicateDetector, DuplicateReviewUI


class FontFlowEngine(QObject):
    """
    Core application logic controller.
    Manages state, auto-cycling, and keyboard commands.
    """
    
    # Signals for UI updates
    family_changed = pyqtSignal(object)  # Can be FontFamily or FamilyPointer
    style_changed = pyqtSignal()
    speed_changed = pyqtSignal(int)
    stage_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int)
    mode_changed = pyqtSignal(str, bool)
    
    def __init__(self, library, session: SessionState, config: dict):
        super().__init__()
        
        self.library = library
        self.session = session
        self.config = config
        
        # Detect if using lazy loading
        self.use_lazy_loading = isinstance(library, FastFontLibrary)
        
        # Command stack for undo/redo
        self.command_stack = CommandStack(max_history=config.get('advanced', {}).get('max_undo_history', 100))
        
        # Event logger
        library_name = Path(session.library_root).name
        self.logger = EventLogger(Path("data/logs"), library_name)
        
        # File operations handler
        self.file_ops = FileOperations()
        
        # Session start time (for statistics)
        self.session_start_time = time.time()
        
        # Parse categories from config
        self.categories = self._parse_categories(config.get('categories', {}))
        self.subcategories = self._parse_categories(config.get('subcategories', {}))
        
        # Auto-cycle timer
        self.cycle_timer = QTimer()
        self.cycle_timer.timeout.connect(self._cycle_style)
        self.is_cycling = False
        
        # Store current family pointer/index
        self.current_family_index = session.current_family_index
        self._current_family_object = None  # Parsed FontFamily cache
        
        # Ensure we don't start past the end
        if self.current_family_index >= len(library.families):
            self.current_family_index = 0
    
    def _parse_categories(self, cat_dict: dict) -> dict:
        """Parse categories from config into Category objects"""
        categories = {}
        for key, data in cat_dict.items():
            categories[key] = Category(
                key=key,
                name=data.get('name', f'Category {key}'),
                folder=data.get('folder', f'category_{key}'),
                color=data.get('color', '#00ff88')
            )
        return categories
    
    @property
    def current_family(self):
        """
        Get the currently active family.
        Handles lazy loading automatically.
        """
        if self.use_lazy_loading:
            # Get the family pointer
            if 0 <= self.current_family_index < len(self.library.families):
                family_ptr = self.library.families[self.current_family_index]
                
                # If it's already parsed and cached, return it
                if not family_ptr.needs_parsing and family_ptr.parsed_family:
                    return family_ptr.parsed_family
                
                # Parse on demand
                try:
                    parsed_family = self.library.parse_family(family_ptr)
                    return parsed_family
                except Exception as e:
                    print(f"Error parsing family {family_ptr.name}: {e}")
                    return None
            return None
        else:
            # Legacy mode
            if 0 <= self.current_family_index < len(self.library.families):
                return self.library.families[self.current_family_index]
            return None
    
    @property
    def total_families(self) -> int:
        """Total number of families in library"""
        return len(self.library.families)
    
    @property
    def cycle_speed_ms(self) -> int:
        """Current cycle speed in milliseconds"""
        return self.session.cycle_speed_ms
    
    def check_duplicates(self):
        """Check for duplicates (non-destructive)"""
        print("\n🔍 Checking for duplicates...")
        
        detector = SafeDuplicateDetector(Path(self.session.library_root))
        
        # Get all families (lazy loading handles parsing)
        families = []
        for i in range(len(self.library.families)):
            family = self.library.get_family(i, parse=True)
            if family:
                families.append(family)
        
        # Detect duplicates (auto_mode=False means no auto-delete)
        duplicate_groups = detector.detect_duplicates(families, auto_mode=False)
        
        if duplicate_groups:
            print(f"\n⚠️ Found {len(duplicate_groups)} potential duplicate groups")
            print("   These require manual review (safe mode)")
            
            # In real UI, show dialog
            # For now, print report
            for group in duplicate_groups:
                print(f"\n   Group confidence: {group.confidence:.1%}")
                for evidence in group.evidence:
                    print(f"     • {evidence}")
            
            return duplicate_groups
        else:
            print("✅ No duplicates found!")
            return []

    # ═══════════════════════════════════════════════════════════════
    # AUTO-CYCLING CONTROL
    # ═══════════════════════════════════════════════════════════════
    
    def start_cycling(self):
        """Start auto-cycling through styles"""
        if not self.is_cycling:
            self.is_cycling = True
            self.cycle_timer.start(self.session.cycle_speed_ms)
            print(f"Auto-cycling started at {self.session.cycle_speed_ms}ms")
    
    def stop_cycling(self):
        """Stop auto-cycling"""
        if self.is_cycling:
            self.is_cycling = False
            self.cycle_timer.stop()
            print("Auto-cycling stopped")
    
    def _cycle_style(self):
        """Internal: Cycle to next style in current family"""
        family = self.current_family
        if family:
            old_index = family.current_style_index
            family.next_style()
            print(f"🔄 Cycling style: {old_index} → {family.current_style_index} ({family.current_style.style_name})")
            self.style_changed.emit()
    
    def speed_up(self):
        """Increase cycling speed (decrease interval)"""
        min_speed = self.config.get('ui', {}).get('min_cycle_speed', 200)
        speed_step = self.config.get('ui', {}).get('speed_step', 200)
        
        new_speed = max(min_speed, self.session.cycle_speed_ms - speed_step)
        self.set_speed(new_speed)
    
    def slow_down(self):
        """Decrease cycling speed (increase interval)"""
        max_speed = self.config.get('ui', {}).get('max_cycle_speed', 5000)
        speed_step = self.config.get('ui', {}).get('speed_step', 200)
        
        new_speed = min(max_speed, self.session.cycle_speed_ms + speed_step)
        self.set_speed(new_speed)
    
    def set_speed(self, speed_ms: int):
        """Set cycling speed in milliseconds"""
        self.session.cycle_speed_ms = speed_ms
        
        if self.is_cycling:
            self.cycle_timer.setInterval(speed_ms)
        
        self.speed_changed.emit(speed_ms)
        print(f"Cycle speed: {speed_ms}ms")
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def next_family(self):
        """Move to next family"""
        if self.current_family_index < len(self.library.families) - 1:
            self.current_family_index += 1
            self.session.current_family_index = self.current_family_index
            # Clear cached family object so it re-parses if needed
            self._current_family_object = None
            self._notify_family_changed()
    
    def prev_family(self):
        """Move to previous family"""
        if self.current_family_index > 0:
            self.current_family_index -= 1
            self.session.current_family_index = self.current_family_index
            self._current_family_object = None
            self._notify_family_changed()
    
    def jump_to_family(self, index: int):
        """Jump to specific family by index"""
        if 0 <= index < len(self.library.families):
            self.current_family_index = index
            self.session.current_family_index = index
            self._current_family_object = None
            self._notify_family_changed()
    
    def _notify_family_changed(self):
        """Notify UI that family has changed"""
        family = self.current_family  # This triggers lazy loading if needed
        
        if family:
            # Make sure we have a FontFamily object, not a pointer
            if isinstance(family, FontFamily):
                self.family_changed.emit(family)
                self.progress_updated.emit(self.current_family_index, self.total_families)
                print(f"📁 Family loaded: {family.family_name} ({family.style_count} styles)")
            else:
                print(f"Error: Expected FontFamily, got {type(family)}")
        else:
            print(f"Warning: Could not load family at index {self.current_family_index}")
    
    def next_style(self):
        """Manually cycle to next style"""
        family = self.current_family
        if family:
            family.next_style()
            self.style_changed.emit()
    
    def prev_style(self):
        """Manually cycle to previous style"""
        family = self.current_family
        if family:
            family.prev_style()
            self.style_changed.emit()
    
    # ═══════════════════════════════════════════════════════════════
    # CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def classify(self, category_key: str):
        """
        Classify current family with a category.
        Handles both Stage A and Stage B with REAL file operations.
        """
        family = self.current_family
        
        if not family:
            print("⚠ No current family to classify")
            return
        
        print(f"\n🎯 CLASSIFY: Key={category_key}, Stage={self.session.current_stage}")
        print(f"   Family: {family.family_name}")
        
        # Determine which stage we're in
        if self.session.current_stage == "A":
            # Stage A: Primary classification
            if category_key not in self.categories:
                print(f"❌ Invalid category key: {category_key}")
                print(f"   Available: {list(self.categories.keys())}")
                return
            
            category = self.categories[category_key]
            target_path = Path(self.session.library_root) / category.folder
            
            print(f"📁 Stage A: Classifying '{family.family_name}' → {category.name}")
            print(f"   Target path: {target_path}")
            
            # Log the action
            self.logger.log_classification(
                family_name=family.family_name,
                from_path=str(family.source_folder),
                to_path=str(target_path),
                stage="A",
                category=category_key
            )
            
            # Move to Stage B (don't move files yet)
            self.session.current_stage = "B"
            self.stage_changed.emit("B")
            
            # Store the selected category for Stage B
            self.session.temp_stage_a_category = category.folder
            
            print(f"✅ Stage A complete. Now in Stage B. Press 1-5 to choose subcategory.")
            
        else:
            # Stage B: Subcategory refinement + ACTUAL FILE MOVE
            if category_key not in self.subcategories:
                print(f"❌ Invalid subcategory key: {category_key}")
                print(f"   Available: {list(self.subcategories.keys())}")
                return
            
            subcategory = self.subcategories[category_key]
            
            # Build target path: library_root / category_folder / subcategory_folder
            parent_folder = getattr(self.session, 'temp_stage_a_category', None)
            
            if not parent_folder:
                print("❌ No category selected in Stage A. Something went wrong.")
                self.session.current_stage = "A"
                self.stage_changed.emit("A")
                return
            
            target_path = Path(self.session.library_root) / parent_folder / subcategory.folder
            
            print(f"📁 Stage B: Moving '{family.family_name}'")
            print(f"   From: {family.source_folder}")
            print(f"   To: {target_path}")
            
            # Ensure target directory exists
            target_path.mkdir(parents=True, exist_ok=True)
            
            # COLLECT ALL FONT FILES FOR THIS FAMILY
            font_files = []
            for style in family.styles:
                if style.path.exists():
                    font_files.append(style.path)
                else:
                    print(f"   ⚠ Missing file: {style.path}")
            
            if not font_files:
                print("❌ No font files found to move")
                self.session.current_stage = "A"
                self.stage_changed.emit("A")
                return
            
            print(f"   Moving {len(font_files)} file(s)...")
            
            # MOVE EACH FILE
            moved_files = []
            failed_files = []
            
            for source_path in font_files:
                dest_path = target_path / source_path.name
                
                # Check for conflicts
                if dest_path.exists():
                    print(f"   ⚠ Conflict: {dest_path.name} already exists")
                    failed_files.append(source_path.name)
                    continue
                
                try:
                    shutil.move(str(source_path), str(dest_path))
                    moved_files.append((source_path, dest_path))
                    print(f"   ✓ Moved: {source_path.name}")
                except Exception as e:
                    print(f"   ✗ Failed: {source_path.name} - {e}")
                    failed_files.append(source_path.name)
            
            if failed_files:
                print(f"❌ Failed to move {len(failed_files)} files. Rolling back...")
                # Rollback moved files
                for source, dest in moved_files:
                    try:
                        shutil.move(str(dest), str(source))
                        print(f"   ↩ Rolled back: {dest.name}")
                    except Exception as e:
                        print(f"   ✗ Rollback failed: {dest.name} - {e}")
                
                self.logger.log_error(
                    error_type="file_operation",
                    message=f"Failed to move {len(failed_files)} files",
                    context={'family': family.family_name, 'failed': failed_files}
                )
                
                self.session.current_stage = "A"
                self.stage_changed.emit("A")
                return
            
            # SUCCESS - Update family metadata
            print(f"✅ Successfully moved {len(moved_files)} files")
            
            # Update family source folder
            family.source_folder = target_path
            for i, style in enumerate(family.styles):
                style.path = target_path / style.path.name
            
            # Log the action
            self.logger.log_classification(
                family_name=family.family_name,
                from_path=str(family.source_folder),
                to_path=str(target_path),
                stage="B",
                category=parent_folder,
                subcategory=category_key
            )
            
            # Mark as completed
            self.session.completed_families.add(family.family_name)
            
            # Create action for undo
            action = ClassificationAction(
                timestamp=time.time(),
                family_name=family.family_name,
                from_path=family.source_folder,
                to_path=target_path,
                stage=Stage.B,
                category_key=category_key,
            )
            self.command_stack.commands.append(action)
            self.command_stack.current_index += 1
            
            # Clean up temp data
            if hasattr(self.session, 'temp_stage_a_category'):
                delattr(self.session, 'temp_stage_a_category')
            
            # Move to Stage A for next family
            self.session.current_stage = "A"
            self.stage_changed.emit("A")
            
            # Advance to next family
            self.next_family()
    
    def skip_family(self):
        """Skip current family without classification"""
        family = self.current_family
        if family:
            print(f"Skipping: {family.family_name}")
            self.logger.log_skip(family.family_name)
        self.next_family()
    
    def mark_uncertain(self):
        """Mark current family as uncertain for later review"""
        family = self.current_family
        if family:
            self.session.uncertain_families.add(family.family_name)
            
            # Move to REVIEW_LATER folder
            uncertain_folder = self.config.get('special_folders', {}).get('uncertain', 'REVIEW_LATER')
            target_path = Path(self.session.library_root) / uncertain_folder
            
            print(f"Marking uncertain: {family.family_name}")
            
            # ACTUAL FILE OPERATION
            success, message = self.file_ops.move_family(
                family=family,
                target_dir=target_path
            )
            
            if success:
                print(f"✓ {message}")
                self.logger.log_uncertain(family.family_name, target_path)
            else:
                print(f"✗ {message}")
                self.logger.log_error(
                    error_type="uncertain_move",
                    message=message,
                    context={'family': family.family_name}
                )
            
            self.next_family()
    
    # ═══════════════════════════════════════════════════════════════
    # UNDO/REDO
    # ═══════════════════════════════════════════════════════════════
    
    def undo(self):
        """Undo last classification"""
        action = self.command_stack.undo()
        if action:
            print(f"Undone: {action}")
            self.logger.log_undo(action.family_name, "classification")
            # Remove from completed
            self.session.completed_families.discard(action.family_name)
        else:
            print("Nothing to undo")
    
    def redo(self):
        """Redo last undone classification"""
        action = self.command_stack.redo()
        if action:
            print(f"Redone: {action}")
            self.logger.log_redo(action.family_name, "classification")
            # Add back to completed
            self.session.completed_families.add(action.family_name)
        else:
            print("Nothing to redo")
    
    @property
    def can_undo(self) -> bool:
        return self.command_stack.can_undo
    
    @property
    def can_redo(self) -> bool:
        return self.command_stack.can_redo
    
    # ═══════════════════════════════════════════════════════════════
    # MODE TOGGLES
    # ═══════════════════════════════════════════════════════════════
    
    def toggle_weight_test_mode(self):
        """Toggle weight stress test mode"""
        self.session.weight_test_mode = not self.session.weight_test_mode
        print(f"Weight test mode: {'ON' if self.session.weight_test_mode else 'OFF'}")
        self.mode_changed.emit("weight", self.session.weight_test_mode)
    
    def toggle_logo_test_mode(self):
        """Toggle logo test mode"""
        self.session.logo_test_mode = not self.session.logo_test_mode
        print(f"Logo test mode: {'ON' if self.session.logo_test_mode else 'OFF'}")
        self.mode_changed.emit("logo", self.session.logo_test_mode)
    
    def toggle_persian_stress_mode(self):
        """Toggle Persian shaping stress mode"""
        self.session.persian_stress_mode = not self.session.persian_stress_mode
        print(f"Persian stress mode: {'ON' if self.session.persian_stress_mode else 'OFF'}")
        self.mode_changed.emit("persian", self.session.persian_stress_mode)
    
    def toggle_comparison_mode(self):
        """Toggle comparison panel"""
        self.session.comparison_mode_enabled = not self.session.comparison_mode_enabled
        print(f"Comparison mode: {'ON' if self.session.comparison_mode_enabled else 'OFF'}")
        self.mode_changed.emit("comparison", self.session.comparison_mode_enabled)
    
    # ═══════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════════════════════════
    
    def initialize(self):
        """Initialize the engine with crash recovery and start auto-cycling"""
        
        # Check for crash recovery
        from utils.transaction_manager import TransactionManager, CrashRecoveryWizard
        
        tx_manager = TransactionManager()
        recovery = CrashRecoveryWizard(tx_manager)
        
        if not recovery.check_and_recover():
            print("⚠️ Some transactions could not be recovered")
            print("   Continuing anyway - check logs for details")
        
        # Clean up old transactions
        tx_manager.cleanup_old_transactions(days=30)
        
        # Rotate logs
        from utils.log_rotator import LogRotator
        log_rotator = LogRotator(Path("data/logs"))
        log_rotator.rotate_all_logs()
        
        # Log session start
        self.logger.log_session_start(
            total_families=self.total_families,
            current_index=self.current_family_index
        )
        
        self._notify_family_changed()
        self.start_cycling()
    
    def shutdown(self):
        """Shutdown the engine (called on app close)"""
        # Log session end
        duration = time.time() - self.session_start_time
        completed = len(self.session.completed_families)
        self.logger.log_session_end(
            families_processed=completed,
            duration_seconds=duration
        )
        
        self.stop_cycling()