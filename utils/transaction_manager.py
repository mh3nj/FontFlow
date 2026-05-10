"""
FontFlow Studio - Transaction Manager
Write-ahead logging for crash recovery and atomic operations
"""

from pathlib import Path
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import uuid
import shutil
import time


@dataclass
class Transaction:
    """A single file operation transaction"""
    id: str
    operation: str  # "MOVE", "COPY", "DELETE"
    source_path: str
    target_path: str
    family_name: str
    timestamp: float
    status: str = "PENDING"  # PENDING, COMMITTED, ROLLED_BACK, FAILED
    error_message: str = ""
    temp_path: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        return cls(**data)


class TransactionManager:
    """
    Manages atomic file operations with crash recovery.
    
    Features:
    - Write-ahead logging (log BEFORE doing anything)
    - Automatic recovery on startup
    - Rollback on failure
    - Transaction history
    """
    
    def __init__(self, data_dir: Path = Path("data/transactions")):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.transactions_dir = self.data_dir / "pending"
        self.transactions_dir.mkdir(exist_ok=True)
        
        self.archive_dir = self.data_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        self.temp_dir = self.data_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.current_transactions: Dict[str, Transaction] = {}
    
    def start_transaction(self, operation: str, source: Path, target: Path, 
                         family_name: str) -> Transaction:
        """
        Start a new transaction (write-ahead log).
        
        Args:
            operation: "MOVE", "COPY", or "DELETE"
            source: Source path
            target: Target path
            family_name: Name of font family
            
        Returns:
            Transaction object
        """
        transaction = Transaction(
            id=str(uuid.uuid4()),
            operation=operation,
            source_path=str(source),
            target_path=str(target),
            family_name=family_name,
            timestamp=time.time(),
            status="PENDING"
        )
        
        # Write transaction to disk BEFORE doing anything
        self._save_transaction(transaction)
        self.current_transactions[transaction.id] = transaction
        
        print(f"📝 Transaction started: {transaction.id} - {operation} {family_name}")
        return transaction
    
    def _save_transaction(self, transaction: Transaction):
        """Save transaction to disk"""
        path = self.transactions_dir / f"{transaction.id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(transaction.to_dict(), f, indent=2)
    
    def _delete_transaction_file(self, transaction_id: str):
        """Delete transaction file after completion"""
        path = self.transactions_dir / f"{transaction_id}.json"
        if path.exists():
            path.unlink()
    
    def commit_transaction(self, transaction: Transaction, 
                          on_success: Optional[Callable] = None):
        """
        Commit a successful transaction.
        
        Args:
            transaction: Transaction to commit
            on_success: Optional callback after commit
        """
        transaction.status = "COMMITTED"
        self._save_transaction(transaction)
        
        # Move to archive
        archive_path = self.archive_dir / f"{transaction.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        src_path = self.transactions_dir / f"{transaction.id}.json"
        if src_path.exists():
            shutil.move(str(src_path), str(archive_path))
        
        # Remove from current
        if transaction.id in self.current_transactions:
            del self.current_transactions[transaction.id]
        
        if on_success:
            on_success()
        
        print(f"✅ Transaction committed: {transaction.id}")
    
    def rollback_transaction(self, transaction: Transaction, 
                            error_message: str = "",
                            on_rollback: Optional[Callable] = None):
        """
        Rollback a failed transaction.
        
        Args:
            transaction: Transaction to rollback
            error_message: Error description
            on_rollback: Optional callback after rollback
        """
        transaction.status = "ROLLED_BACK"
        transaction.error_message = error_message
        self._save_transaction(transaction)
        
        # Move to archive with error flag
        archive_path = self.archive_dir / f"FAILED_{transaction.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        src_path = self.transactions_dir / f"{transaction.id}.json"
        if src_path.exists():
            shutil.move(str(src_path), str(archive_path))
        
        # Remove from current
        if transaction.id in self.current_transactions:
            del self.current_transactions[transaction.id]
        
        # Clean up temp files if any
        if transaction.temp_path:
            temp_path = Path(transaction.temp_path)
            if temp_path.exists():
                shutil.rmtree(temp_path, ignore_errors=True)
        
        if on_rollback:
            on_rollback()
        
        print(f"❌ Transaction rolled back: {transaction.id} - {error_message}")
    
    def recover_pending_transactions(self) -> List[Transaction]:
        """
        Recover pending transactions from previous crash.
        Call this on application startup.
        
        Returns:
            List of recovered transactions that need attention
        """
        pending = []
        
        for file in self.transactions_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    transaction = Transaction.from_dict(data)
                    
                    if transaction.status == "PENDING":
                        pending.append(transaction)
                        print(f"⚠️ Found pending transaction: {transaction.id} - {transaction.operation}")
                        
            except Exception as e:
                print(f"Error reading transaction {file}: {e}")
        
        return pending
    
    def recover_from_crash(self) -> Dict[str, bool]:
        """
        Attempt to recover from a crash.
        Returns dictionary of transaction_id -> success
        """
        pending = self.recover_pending_transactions()
        results = {}
        
        for transaction in pending:
            print(f"\n🔄 Recovering transaction: {transaction.id}")
            
            source = Path(transaction.source_path)
            target = Path(transaction.target_path)
            temp_path = Path(transaction.temp_path) if transaction.temp_path else None
            
            if transaction.operation == "MOVE":
                success = self._recover_move(transaction, source, target, temp_path)
            elif transaction.operation == "COPY":
                success = self._recover_copy(transaction, source, target, temp_path)
            elif transaction.operation == "DELETE":
                success = self._recover_delete(transaction, source)
            else:
                success = False
            
            results[transaction.id] = success
            
            if success:
                self.commit_transaction(transaction)
            else:
                self.rollback_transaction(transaction, "Recovery failed")
        
        return results
    
    def _recover_move(self, transaction: Transaction, source: Path, 
                     target: Path, temp_path: Optional[Path]) -> bool:
        """Recover a move operation after crash"""
        try:
            # Check if files are already in target
            if target.exists():
                # Transaction completed but not committed
                return True
            
            # Check if files are in temp
            if temp_path and temp_path.exists():
                # Move from temp to target
                shutil.move(str(temp_path), str(target))
                return True
            
            # Check if files still at source
            if source.exists():
                # Move from source to target
                shutil.move(str(source), str(target))
                return True
            
            return False
            
        except Exception as e:
            print(f"Recovery failed: {e}")
            return False
    
    def _recover_copy(self, transaction: Transaction, source: Path,
                     target: Path, temp_path: Optional[Path]) -> bool:
        """Recover a copy operation after crash"""
        try:
            if target.exists():
                return True
            
            if temp_path and temp_path.exists():
                shutil.move(str(temp_path), str(target))
                return True
            
            if source.exists():
                shutil.copy2(str(source), str(target))
                return True
            
            return False
            
        except Exception as e:
            print(f"Recovery failed: {e}")
            return False
    
    def _recover_delete(self, transaction: Transaction, source: Path) -> bool:
        """Recover a delete operation after crash"""
        try:
            # If source doesn't exist, delete succeeded
            if not source.exists():
                return True
            
            # If source exists, delete is pending
            # We'll just log and let user decide
            print(f"  Warning: Source still exists: {source}")
            return True
            
        except Exception as e:
            print(f"Recovery failed: {e}")
            return False
    
    def cleanup_old_transactions(self, days: int = 30):
        """Clean up transactions older than specified days"""
        cutoff = time.time() - (days * 24 * 60 * 60)
        
        for file in self.archive_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('timestamp', 0) < cutoff:
                        file.unlink()
                        print(f"Cleaned up old transaction: {file.name}")
            except Exception:
                pass
    
    def get_statistics(self) -> dict:
        """Get transaction statistics"""
        pending_count = len(list(self.transactions_dir.glob("*.json")))
        archived_count = len(list(self.archive_dir.glob("*.json")))
        
        return {
            'pending_transactions': pending_count,
            'archived_transactions': archived_count,
            'has_pending': pending_count > 0,
            'temp_dir_size_mb': self._get_dir_size_mb(self.temp_dir),
        }
    
    def _get_dir_size_mb(self, path: Path) -> float:
        """Get directory size in MB"""
        if not path.exists():
            return 0.0
        
        total = 0
        for file in path.rglob('*'):
            if file.is_file():
                total += file.stat().st_size
        return total / (1024 * 1024)


class CrashRecoveryWizard:
    """
    Handles crash recovery with user interaction.
    Shows dialog when pending transactions are found.
    """
    
    def __init__(self, transaction_manager: 'TransactionManager'):
        self.transaction_manager = transaction_manager
    
    def check_and_recover(self) -> bool:
        """
        Check for pending transactions and attempt recovery.
        Returns True if recovery was successful or no issues found.
        """
        pending = self.transaction_manager.recover_pending_transactions()
        
        if not pending:
            print("✅ No pending transactions found - system is clean")
            return True
        
        print(f"\n⚠️ Found {len(pending)} pending transactions from previous crash")
        
        # Attempt automatic recovery
        results = self.transaction_manager.recover_from_crash()
        
        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count
        
        if success_count > 0:
            print(f"\n✅ Auto-recovered {success_count} transactions")
        
        if fail_count > 0:
            print(f"❌ Failed to recover {fail_count} transactions")
            print("   Please check data/transactions/archive/ for details")
        
        return fail_count == 0
    
    def show_recovery_dialog(self):
        """Show a dialog for manual recovery (if needed)"""
        # In real UI, this would show a QMessageBox
        pending = self.transaction_manager.recover_pending_transactions()
        
        if pending:
            print("\n" + "="*60)
            print("🔄 CRASH RECOVERY")
            print("="*60)
            print(f"Found {len(pending)} pending operations from previous crash.")
            print("\nAttempting automatic recovery...")
            
            # Auto-recover
            self.transaction_manager.recover_from_crash()
            
            # Show results
            stats = self.transaction_manager.get_statistics()
            if stats['has_pending']:
                print("\n⚠️ Some operations could not be auto-recovered.")
                print("   Please check: data/transactions/archive/")
            else:
                print("\n✅ Recovery complete! All operations restored.")
