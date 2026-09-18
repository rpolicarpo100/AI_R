"""
P20 — Database Backup, Migration, Encryption — backup automático SQLite
"""
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

class BackupServiceP20:
    def __init__(self, db_path="./ai_provider_os.db", backup_dir="./backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.last_backup = None
        self.backup_count = 0
    
    def backup(self) -> dict:
        """Backup automático SQLite — copia db para backup folder com timestamp"""
        if not self.db_path.exists():
            return {"status": "FAILED", "reason": f"DB not found {self.db_path}"}
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"ai_provider_os_backup_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_file)
            self.last_backup = datetime.now(timezone.utc)
            self.backup_count += 1
            
            # Keep only last 10 backups
            backups = sorted(self.backup_dir.glob("ai_provider_os_backup_*.db"), key=lambda x: x.stat().st_mtime, reverse=True)
            for old_backup in backups[10:]:
                old_backup.unlink()
            
            print(f"[P20 BACKUP] Backup created {backup_file} ({backup_file.stat().st_size} bytes) — total {self.backup_count}")
            return {"status": "SUCCESS", "backup_file": str(backup_file), "size": backup_file.stat().st_size, "timestamp": timestamp}
        except Exception as e:
            print(f"[P20 BACKUP] Backup failed {e}")
            return {"status": "FAILED", "reason": str(e)}
    
    def list_backups(self) -> list:
        backups = sorted(self.backup_dir.glob("ai_provider_os_backup_*.db"), key=lambda x: x.stat().st_mtime, reverse=True)
        return [{"file": str(b), "size": b.stat().st_size, "mtime": datetime.fromtimestamp(b.stat().st_mtime, tz=timezone.utc).isoformat()} for b in backups]

backup_service_p20 = BackupServiceP20()

print("[P20] Backup service loaded — automatic backup SQLite")
