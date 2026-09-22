#!/usr/bin/env python3
# utils/error_handler.py - Comprehensive error handling framework

import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from functools import wraps
import json


class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self, log_dir="logs"):
        """Initialize error handler with logging"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Error statistics
        self.error_count = 0
        self.error_types = {}
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.log_dir / f"ai_assistent_{datetime.now().strftime('%Y%m%d')}.log"
        error_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Main logger
        self.logger = logging.getLogger('ai_assistent')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # File handler for errors only
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 60)
        self.logger.info("AI Assistent Voice Assistant Started")
        self.logger.info("=" * 60)
    
    def log_error(self, error, context="", severity="ERROR"):
        """Log an error with context"""
        self.error_count += 1
        error_type = type(error).__name__
        
        # Track error types
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        # Log the error
        error_msg = f"{context}: {error_type} - {str(error)}"
        
        if severity == "CRITICAL":
            self.logger.critical(error_msg)
        elif severity == "ERROR":
            self.logger.error(error_msg)
        elif severity == "WARNING":
            self.logger.warning(error_msg)
        
        # Log traceback for debugging
        self.logger.debug(traceback.format_exc())
        
        # Save error details
        self._save_error_details(error, context, error_type)
    
    def _save_error_details(self, error, context, error_type):
        """Save detailed error information"""
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        error_file = self.log_dir / f"error_details_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Load existing errors
            if error_file.exists():
                with open(error_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            # Add new error
            errors.append(error_details)
            
            # Save
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save error details: {e}")
    
    def get_user_friendly_message(self, error, context=""):
        """Convert technical error to user-friendly message"""
        error_type = type(error).__name__
        
        # Map errors to user-friendly messages
        error_messages = {
            'ImportError': "A required component is missing. Please check your installation.",
            'ModuleNotFoundError': "A required module is not installed. Run: pip install -r requirements.txt",
            'FileNotFoundError': "Could not find a required file. Please check your installation.",
            'PermissionError': "Permission denied. Try running as administrator.",
            'ConnectionError': "Network connection failed. Check your internet connection.",
            'TimeoutError': "Operation timed out. Please try again.",
            'ValueError': "Invalid input provided. Please check your command.",
            'KeyError': "Configuration error. Please check your settings.",
            'AttributeError': "Internal error. Please report this issue.",
            'OSError': "System error occurred. Please check system resources.",
            'MemoryError': "Out of memory. Please close some applications.",
            'KeyboardInterrupt': "Operation cancelled by user.",
        }
        
        user_msg = error_messages.get(error_type, "An unexpected error occurred.")
        
        if context:
            user_msg = f"{context}: {user_msg}"
        
        return user_msg
    
    def get_error_stats(self):
        """Get error statistics"""
        return {
            'total_errors': self.error_count,
            'error_types': self.error_types,
            'log_directory': str(self.log_dir)
        }


# Global error handler instance
_error_handler = None

def get_error_handler():
    """Get or create global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_errors(context="", user_friendly=True, default_return=None):
    """Decorator for error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                handler.logger.info("Operation cancelled by user")
                raise
            except Exception as e:
                # Log the error
                func_context = context or f"{func.__name__}"
                handler.log_error(e, func_context)
                
                # Return user-friendly message or default
                if user_friendly:
                    return handler.get_user_friendly_message(e, func_context)
                elif default_return is not None:
                    return default_return
                else:
                    raise
        return wrapper
    return decorator


def safe_execute(func, *args, default=None, context="", **kwargs):
    """Safely execute a function with error handling"""
    handler = get_error_handler()
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handler.log_error(e, context or func.__name__)
        return default


# Test the error handler
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ERROR HANDLER")
    print("=" * 60)
    
    handler = ErrorHandler()
    
    # Test 1: Log different severity levels
    print("\n1. Testing log levels...")
    handler.logger.info("This is an info message")
    handler.logger.warning("This is a warning message")
    handler.logger.error("This is an error message")
    
    # Test 2: Log an exception
    print("\n2. Testing exception logging...")
    try:
        result = 1 / 0
    except Exception as e:
        handler.log_error(e, "Division test")
        print(f"User message: {handler.get_user_friendly_message(e, 'Math operation')}")
    
    # Test 3: Test decorator
    print("\n3. Testing decorator...")
    
    @handle_errors(context="Test function", user_friendly=True)
    def test_function():
        raise ValueError("Test error")
    
    result = test_function()
    print(f"Result: {result}")
    
    # Test 4: Test safe_execute
    print("\n4. Testing safe_execute...")
    
    def risky_function():
        raise RuntimeError("Risky operation failed")
    
    result = safe_execute(risky_function, default="Safe default", context="Risky test")
    print(f"Result: {result}")
    
    # Test 5: Get statistics
    print("\n5. Error statistics...")
    stats = handler.get_error_stats()
    print(f"Total errors: {stats['total_errors']}")
    print(f"Error types: {stats['error_types']}")
    print(f"Log directory: {stats['log_directory']}")
    
    print("\n✅ Error handler test complete!")
    print(f"Check logs in: {handler.log_dir}")
