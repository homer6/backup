import os
import json
import datetime

class CheckpointManager:
    def __init__(self, checkpoint_file=None, auto_save=True):
        self.checkpoint_file = checkpoint_file
        self.auto_save = auto_save
        self.checkpoint_data = {
            "backup_id": None,
            "timestamp": None,
            "config": {},
            "progress": {
                "download_complete": False,
                "downloaded_files": [],
                "archive_complete": False,
                "archive_volumes": [],
                "upload_complete": False,
                "uploaded_files": []
            }
        }
        
        if checkpoint_file and os.path.exists(checkpoint_file):
            self.load()
    
    def initialize(self, backup_config):
        """Initialize a new checkpoint with backup configuration."""
        backup_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.checkpoint_data = {
            "backup_id": backup_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "config": backup_config,
            "progress": {
                "download_complete": False,
                "downloaded_files": [],
                "archive_complete": False,
                "archive_volumes": [],
                "upload_complete": False,
                "uploaded_files": []
            }
        }
        
        if self.auto_save:
            self.save()
        
        return backup_id
    
    def mark_download_complete(self, downloaded_files=None):
        """Mark the download phase as complete and optionally track downloaded files."""
        self.checkpoint_data["progress"]["download_complete"] = True
        if downloaded_files:
            self.checkpoint_data["progress"]["downloaded_files"] = downloaded_files
        
        if self.auto_save:
            self.save()
    
    def mark_archive_complete(self, archive_volumes=None):
        """Mark the archive creation phase as complete and track archive volumes."""
        self.checkpoint_data["progress"]["archive_complete"] = True
        if archive_volumes:
            self.checkpoint_data["progress"]["archive_volumes"] = archive_volumes
        
        if self.auto_save:
            self.save()
    
    def mark_upload_complete(self, uploaded_files=None):
        """Mark the upload phase as complete and optionally track uploaded files."""
        self.checkpoint_data["progress"]["upload_complete"] = True
        if uploaded_files:
            self.checkpoint_data["progress"]["uploaded_files"] = uploaded_files
        
        if self.auto_save:
            self.save()
    
    def is_download_complete(self):
        """Check if download phase is marked as complete."""
        return self.checkpoint_data["progress"]["download_complete"]
    
    def is_archive_complete(self):
        """Check if archive creation phase is marked as complete."""
        return self.checkpoint_data["progress"]["archive_complete"]
    
    def is_upload_complete(self):
        """Check if upload phase is marked as complete."""
        return self.checkpoint_data["progress"]["upload_complete"]
    
    def get_config(self):
        """Get the backup configuration from the checkpoint."""
        return self.checkpoint_data["config"]
    
    def get_backup_id(self):
        """Get the backup ID from the checkpoint."""
        return self.checkpoint_data["backup_id"]
    
    def save(self):
        """Save the checkpoint data to file."""
        if not self.checkpoint_file:
            return False
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoint_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving checkpoint file: {e}")
            return False
    
    def load(self):
        """Load the checkpoint data from file."""
        if not self.checkpoint_file or not os.path.exists(self.checkpoint_file):
            return False
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                self.checkpoint_data = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading checkpoint file: {e}")
            return False
    
    def validate_config(self, current_config):
        """Validate that the current config matches the checkpointed config."""
        saved_config = self.get_config()
        
        # Check essential parameters
        for key in ["source_profile", "dest_profile", "source_bucket", "dest_bucket",
                   "folder_to_backup", "dest_bucket_base_path"]:
            if key in current_config and key in saved_config:
                if current_config[key] != saved_config[key]:
                    return False
        
        return True