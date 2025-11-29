from pathlib import Path

class ConfigManager:
    """
    Manages application configuration directory and files.
    Ensures ~/.config/risi exists and provides utilities for config access.
    """
    
    CONFIG_DIR_NAME = "risi"
    CONFIG_FOLDER = Path.home() / ".config" / CONFIG_DIR_NAME
    
    @classmethod
    def initialize(cls) -> Path:
        """
        Ensure the config directory exists. Create it if missing.
        Should be called on application startup.
        
        Returns:
            Path to the config directory
        """
        try:
            cls.CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
            print(f"✓ Config directory ready: {cls.CONFIG_FOLDER}")
            return cls.CONFIG_FOLDER
        except Exception as e:
            print(f"✗ Failed to create config directory: {e}")
            raise
    
    @classmethod
    def get_config_path(cls) -> Path:
        """Get the config directory path."""
        return cls.CONFIG_FOLDER
    
    @classmethod
    def get_file_path(cls, filename: str) -> Path:
        """
        Get the full path to a config file.
        
        Args:
            filename: Name of the config file (e.g., "settings.json")
        
        Returns:
            Full path to the file in the config directory
        """
        return cls.CONFIG_FOLDER / filename
    
    @classmethod
    def config_file_exists(cls, filename: str) -> bool:
        """Check if a config file exists."""
        return cls.get_file_path(filename).exists()
    
    @classmethod
    def read_config_file(cls, filename: str) -> str:
        """
        Read a config file and return its contents.
        
        Args:
            filename: Name of the config file
        
        Returns:
            File contents as string
        """
        file_path = cls.get_file_path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return f.read()
    
    @classmethod
    def write_config_file(cls, filename: str, content: str) -> None:
        """
        Write content to a config file.
        
        Args:
            filename: Name of the config file
            content: Content to write
        """
        file_path = cls.get_file_path(filename)
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Config file saved: {file_path}")
