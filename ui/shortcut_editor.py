"""
FontFlow Studio - Keyboard Shortcut Editor
Allows users to customize all keyboard shortcuts
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QScrollArea, QFrame, QMessageBox,
                              QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt6.QtGui import QKeyEvent, QKeySequence, QFont
from typing import Dict, Optional
import yaml
from pathlib import Path

from ui.theme import COLORS, FONT_SIZES

class KeyCaptureDialog(QDialog):
    """Dialog for capturing a key press"""
    
    key_captured = pyqtSignal(str)  # Emits the key sequence as string
    
    def __init__(self, action_name: str, current_key: str, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self.current_key = current_key
        self.captured_key = None
        
        self.setWindowTitle(f"Set Shortcut - {action_name}")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
        """)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Instruction
        instruction = QLabel(f"Press new key for: {self.action_name}")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet(f"font-weight: bold; font-size: 16px;")
        layout.addWidget(instruction)
        
        # Current key display
        self.current_label = QLabel(f"Current: {self.current_key}")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(self.current_label)
        
        # Captured key display
        self.capture_label = QLabel("Press any key...")
        self.capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capture_label.setStyleSheet(f"""
            background-color: {COLORS['bg_panel']};
            padding: 20px;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid {COLORS['accent_primary']};
            border-radius: 8px;
        """)
        layout.addWidget(self.capture_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['bg_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dim']};
            }}
        """)
        save_btn.clicked.connect(self.save)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['accent_danger']};
                border: 1px solid {COLORS['accent_danger']};
                border-radius: 6px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_danger']};
                color: {COLORS['bg_primary']};
            }}
        """)
        clear_btn.clicked.connect(self.clear)
        
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Capture key press"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Build key sequence string
        parts = []
        
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        
        # Get key name
        if key == Qt.Key.Key_Space:
            key_name = "Space"
        elif key == Qt.Key.Key_Left:
            key_name = "Left"
        elif key == Qt.Key.Key_Right:
            key_name = "Right"
        elif key == Qt.Key.Key_Up:
            key_name = "Up"
        elif key == Qt.Key.Key_Down:
            key_name = "Down"
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            key_name = "+"
        elif key == Qt.Key.Key_Minus:
            key_name = "-"
        elif key == Qt.Key.Key_BracketLeft:
            key_name = "["
        elif key == Qt.Key.Key_BracketRight:
            key_name = "]"
        elif key == Qt.Key.Key_Slash:
            key_name = "/"
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            key_name = chr(key - Qt.Key.Key_1 + ord('1'))
        elif key == Qt.Key.Key_0:
            key_name = "0"
        else:
            key_name = event.text().upper() if event.text() else ""
        
        if key_name:
            parts.append(key_name)
        
        if parts:
            self.captured_key = '+'.join(parts)
            self.capture_label.setText(self.captured_key)
            self.capture_label.setStyleSheet(f"""
                background-color: {COLORS['bg_panel']};
                padding: 20px;
                font-size: 24px;
                font-weight: bold;
                border: 2px solid {COLORS['accent_primary']};
                border-radius: 8px;
                color: {COLORS['accent_primary']};
            """)
    
    def save(self):
        """Save captured key"""
        if self.captured_key:
            self.key_captured.emit(self.captured_key)
            self.accept()
        else:
            QMessageBox.warning(self, "No Key", "Please press a key first")
    
    def clear(self):
        """Clear the shortcut"""
        self.key_captured.emit("")
        self.accept()


class ShortcutEditor(QDialog):
    """Main shortcut editor dialog"""
    
    shortcuts_changed = pyqtSignal(dict)  # Emits when shortcuts are saved
    
    # Default shortcuts
    DEFAULT_SHORTCUTS = {
        # Classification
        "classify_1": "1",
        "classify_2": "2", 
        "classify_3": "3",
        "classify_4": "4",
        "classify_5": "5",
        "classify_6": "6",
        "classify_7": "7",
        "classify_8": "8",
        "classify_9": "9",
        "classify_0": "0",
        # Flow control
        "skip_family": "Space",
        "mark_uncertain": "/",
        # Navigation
        "next_family": "Right",
        "prev_family": "Left",
        "next_style": "Down",
        "prev_style": "Up",
        # Undo/Redo
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        # Speed
        "speed_up": "]",
        "slow_down": "[",
        # Zoom
        "zoom_in": "Ctrl++",
        "zoom_out": "Ctrl+-",
        "zoom_reset": "Ctrl+0",
        # Modes
        "weight_test": "W",
        "logo_test": "L", 
        "persian_stress": "P",
        "comparison": "C",
        "language_settings": "Ctrl+L",
        "duplicate_check": "Ctrl+D",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.shortcuts = self.load_shortcuts()
        self.setWindowTitle("Keyboard Shortcut Editor")
        self.setMinimumSize(600, 500)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
            }}
            QTableWidget {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border']};
                selection-background-color: {COLORS['bg_hover']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['accent_primary']};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        self.init_ui()
    
    def load_shortcuts(self) -> Dict[str, str]:
        """Load shortcuts from config file"""
        config_path = Path("config.yaml")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('keyboard', self.DEFAULT_SHORTCUTS.copy())
            except:
                pass
        return self.DEFAULT_SHORTCUTS.copy()
    
    def save_shortcuts(self):
        """Save shortcuts to config file"""
        config_path = Path("config.yaml")
        
        # Load existing config
        config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            except:
                pass
        
        # Update keyboard section
        config['keyboard'] = self.shortcuts
        
        # Save back
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print("✅ Shortcuts saved to config.yaml")
        self.shortcuts_changed.emit(self.shortcuts)
    
    def reset_to_defaults(self):
        """Reset all shortcuts to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Reset all keyboard shortcuts to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
            self.refresh_table()
            QMessageBox.information(self, "Reset Complete", "Shortcuts reset to defaults. Click Save to apply.")
    
    def refresh_table(self):
        """Refresh the table widget with current shortcuts"""
        self.table.setRowCount(len(self.actions))
        for row, (action_id, action_name, description) in enumerate(self.actions):
            # Action name
            name_item = QTableWidgetItem(action_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setToolTip(description)
            self.table.setItem(row, 0, name_item)
            
            # Current shortcut
            shortcut = self.shortcuts.get(action_id, "")
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setFlags(shortcut_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            shortcut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, shortcut_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_primary']};
                    color: {COLORS['bg_primary']};
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_dim']};
                }}
            """)
            edit_btn.clicked.connect(lambda checked, aid=action_id: self.edit_shortcut(aid))
            self.table.setCellWidget(row, 2, edit_btn)
    
    def edit_shortcut(self, action_id: str):
        """Open dialog to edit a specific shortcut"""
        action_name = next((a[1] for a in self.actions if a[0] == action_id), action_id)
        current_key = self.shortcuts.get(action_id, "")
        
        dialog = KeyCaptureDialog(action_name, current_key, self)
        dialog.key_captured.connect(lambda new_key: self.update_shortcut(action_id, new_key))
        dialog.exec()
    
    def update_shortcut(self, action_id: str, new_key: str):
        """Update a shortcut value"""
        if new_key:
            self.shortcuts[action_id] = new_key
        else:
            # Clear shortcut
            self.shortcuts[action_id] = ""
        
        self.refresh_table()
        print(f"Updated {action_id}: {new_key if new_key else 'Cleared'}")
    
    def init_ui(self):
        """Initialize the editor UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("⌨️ Keyboard Shortcut Editor")
        title.setFont(QFont("Segoe UI", FONT_SIZES['h2'], QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_primary']};")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Click 'Edit' to change any shortcut. Press 'Clear' in the dialog to remove a shortcut.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 120)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Define all actions
        self.actions = [
            ("classify_1", "Classify 1", "Category 1"),
            ("classify_2", "Classify 2", "Category 2"),
            ("classify_3", "Classify 3", "Category 3"),
            ("classify_4", "Classify 4", "Category 4"),
            ("classify_5", "Classify 5", "Category 5"),
            ("classify_6", "Classify 6", "Category 6"),
            ("classify_7", "Classify 7", "Category 7"),
            ("classify_8", "Classify 8", "Category 8"),
            ("classify_9", "Classify 9", "Category 9"),
            ("classify_0", "Classify 0", "Category 0"),
            ("---", "──────────", ""),
            ("skip_family", "Skip Family", "Skip without classifying"),
            ("mark_uncertain", "Mark Uncertain", "Move to review later"),
            ("---", "──────────", ""),
            ("next_family", "Next Family", "Go to next font family"),
            ("prev_family", "Previous Family", "Go to previous font family"),
            ("next_style", "Next Style", "Manual style cycle"),
            ("prev_style", "Previous Style", "Manual style cycle backward"),
            ("---", "──────────", ""),
            ("undo", "Undo", "Undo last classification"),
            ("redo", "Redo", "Redo last undone action"),
            ("---", "──────────", ""),
            ("speed_up", "Speed Up", "Increase cycle speed"),
            ("slow_down", "Slow Down", "Decrease cycle speed"),
            ("---", "──────────", ""),
            ("zoom_in", "Zoom In", "Increase font size"),
            ("zoom_out", "Zoom Out", "Decrease font size"),
            ("zoom_reset", "Reset Zoom", "Reset to 100%"),
            ("---", "──────────", ""),
            ("weight_test", "Weight Test Mode", "Toggle weight stress test"),
            ("logo_test", "Logo Test Mode", "Toggle logo test"),
            ("persian_stress", "Persian Stress Mode", "Toggle Persian shaping test"),
            ("comparison", "Comparison Mode", "Toggle comparison panel"),
            ("language_settings", "Language Settings", "Open language selector"),
            ("duplicate_check", "Check Duplicates", "Run duplicate detection"),
        ]
        
        self.refresh_table()
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['bg_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dim']};
            }}
        """)
        save_btn.clicked.connect(lambda: [self.save_shortcuts(), self.accept()])
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
