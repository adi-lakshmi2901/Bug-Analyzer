"""Configuration and logging setup for Bug Analysis Agent."""

import logging
import sys
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Configure logging for the Bug Analysis Agent."""
    
    @staticmethod
    def setup_logging(
        level: str = "INFO",
        log_file: Optional[str] = None,
        format_string: Optional[str] = None
    ):
        """Setup logging configuration."""
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Convert string level to logging level
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')
        
        # Create formatter
        formatter = logging.Formatter(format_string)
        
        # Setup handlers
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format=format_string,
            handlers=handlers,
            force=True
        )
        
        # Set specific loggers
        logging.getLogger("pydantic_ai").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured at {level} level")


class Config:
    """Configuration settings for Bug Analysis Agent."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.requirements_folder = "product-requirements-specs"
        self.model_name = "openai:gpt-4o-mini"
        self.create_backup = True
        self.log_level = "INFO"
        self.log_file = "analysis.log"
        
    def update_from_env(self):
        """Update configuration from environment variables."""
        import os
        
        # Update from environment if available
        self.requirements_folder = os.getenv("REQUIREMENTS_FOLDER", self.requirements_folder)
        self.model_name = os.getenv("AI_MODEL_NAME", self.model_name)
        self.create_backup = os.getenv("CREATE_BACKUP", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.log_file = os.getenv("LOG_FILE", self.log_file)
        
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "requirements_folder": self.requirements_folder,
            "model_name": self.model_name,
            "create_backup": self.create_backup,
            "log_level": self.log_level,
            "log_file": self.log_file
        }
    
    def validate(self) -> list:
        """Validate configuration and return any error messages."""
        errors = []
        
        # Check requirements folder
        req_path = Path(self.requirements_folder)
        if not req_path.exists():
            errors.append(f"Requirements folder does not exist: {self.requirements_folder}")
        
        # Check log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {self.log_level}")
        
        return errors