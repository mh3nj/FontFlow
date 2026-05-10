"""
FontFlow Studio - Session Management
Handles saving and loading application state
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Set
import json
from datetime import datetime

from models.classification import Stage


@dataclass
class SessionState:
    """
    Persistent application state that survives across restarts.
    Saved as JSON in data/sessions/
    """
    
    # Library info
    library_root: str  # Store as string for JSON serialization
    last_opened: str   # ISO timestamp
    
    # Progress
    current_family_index: int = 0
    completed_families: Set[str] = field(default_factory=set)      # Family names
    uncertain_families: Set[str] = field(default_factory=set)      # Marked with '/'
    
    # UI state
    cycle_speed_ms: int = 1000
    current_stage: str = "A"  # Store as string: "A" or "B"
    
    # Mode toggles
    comparison_mode_enabled: bool = False
    comparison_folder: Optional[str] = None
    weight_test_mode: bool = False
    logo_test_mode: bool = False
    persian_stress_mode: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert sets to lists for JSON
        data['completed_families'] = list(self.completed_families)
        data['uncertain_families'] = list(self.uncertain_families)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create from dictionary (JSON deserialization)"""
        # Convert lists back to sets
        if 'completed_families' in data:
            data['completed_families'] = set(data['completed_families'])
        if 'uncertain_families' in data:
            data['uncertain_families'] = set(data['uncertain_families'])
        return cls(**data)
    
    def save(self, path: Path):
        """Save session to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'SessionState':
        """Load session from JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def create_new(cls, library_root: Path) -> 'SessionState':
        """Create a new session for a library"""
        return cls(
            library_root=str(library_root),
            last_opened=datetime.now().isoformat(),
        )


class SessionManager:
    """
    Manages session persistence and auto-saving.
    One session per library root.
    """
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionState] = None
    
    def get_session_path(self, library_root: Path) -> Path:
        """Get the session file path for a library"""
        # Use hash of path to avoid filesystem issues
        safe_name = str(abs(hash(str(library_root))))
        return self.session_dir / f"session_{safe_name}.json"
    
    def load_or_create(self, library_root: Path) -> SessionState:
        """Load existing session or create new one"""
        session_path = self.get_session_path(library_root)
        
        if session_path.exists():
            try:
                session = SessionState.load(session_path)
                session.last_opened = datetime.now().isoformat()
                self.current_session = session
                print(f"Loaded session: {len(session.completed_families)} families completed")
                return session
            except Exception as e:
                print(f"Error loading session: {e}")
                # Fall through to create new
        
        # Create new session
        session = SessionState.create_new(library_root)
        self.current_session = session
        print("Created new session")
        return session
    
    def save_current(self):
        """Save the current session"""
        if self.current_session:
            session_path = self.get_session_path(Path(self.current_session.library_root))
            self.current_session.save(session_path)
    
    def list_recent_sessions(self, count: int = 10) -> list:
        """List recent sessions (by last_opened timestamp)"""
        sessions = []
        for session_file in self.session_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    sessions.append({
                        'library_root': data.get('library_root'),
                        'last_opened': data.get('last_opened'),
                        'completed': len(data.get('completed_families', [])),
                    })
            except Exception:
                continue
        
        # Sort by last_opened (most recent first)
        sessions.sort(key=lambda s: s['last_opened'], reverse=True)
        return sessions[:count]
