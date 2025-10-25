from typing import Dict, Any
from cryptography.fernet import Fernet
from pathlib import Path
import json
import os

class PrivacyManager:
    """Manages privacy settings and handles sensitive data encryption."""
    
    def __init__(self, key_file: str = "privacy.key"):
        """Initialize privacy manager with encryption key."""
        self.key_file = Path(key_file)
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)
        self.settings = self._load_settings()
        
    def _load_or_create_key(self) -> bytes:
        """Load existing key or create a new one."""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            return key
            
    def _load_settings(self) -> Dict[str, Any]:
        """Load privacy settings from file."""
        settings_file = Path("privacy_settings.json")
        if settings_file.exists():
            return json.loads(settings_file.read_text())
        else:
            default_settings = {
                "encrypt_emails": True,
                "encrypt_calendar": True,
                "encrypt_documents": True,
                "data_retention_days": 30,
                "ask_permission_before_sharing": True,
            }
            settings_file.write_text(json.dumps(default_settings, indent=4))
            return default_settings
            
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data."""
        return self.fernet.encrypt(data.encode())
        
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data."""
        return self.fernet.decrypt(encrypted_data).decode()
        
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update privacy settings."""
        self.settings.update(settings)
        Path("privacy_settings.json").write_text(json.dumps(self.settings, indent=4))
        
    def is_sensitive_data(self, data_type: str) -> bool:
        """Check if a given data type should be treated as sensitive."""
        return self.settings.get(f"encrypt_{data_type}", False)
        
    def clear_sensitive_data(self, older_than_days: int = None) -> None:
        """Clear sensitive data older than specified days."""
        if older_than_days is None:
            older_than_days = self.settings["data_retention_days"]
        
        # TODO: Implement logic to clear old sensitive data
        pass

    def ask_permission(self, action: str, data_type: str) -> bool:
        """Ask user permission before performing sensitive actions."""
        if not self.settings["ask_permission_before_sharing"]:
            return True
            
        response = input(f"Allow {action} for {data_type}? (yes/no): ").lower()
        return response in ["yes", "y"]