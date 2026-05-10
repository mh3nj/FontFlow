# FontFlow Studio - Utilities Package

from .file_ops import FileOperations, FileOperationError
from .logger import EventLogger
from .color_generator import ColorGenerator
from .text_samples import TextSamples
from .persian_text import PersianTextHandler, TextSampleProvider, PERSIAN_SUPPORT
from .font_loader import FontLoader
from .duplicate_detector import SafeDuplicateDetector, DuplicateEvidence, DuplicateGroup, DuplicateReviewUI
from .transaction_manager import TransactionManager, CrashRecoveryWizard
from .log_rotator import LogRotator
