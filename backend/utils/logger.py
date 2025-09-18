#!/usr/bin/env python3
"""
Enhanced logging utilities with colors and formatting
"""

import time

class Logger:
    """Enhanced logging with colors and formatting"""
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'GRAY': '\033[90m'
    }
    
    @classmethod
    def _colorize(cls, text, color):
        """Add color to text"""
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['RESET']}"
    
    @classmethod
    def header(cls, text, width=80):
        """Print a styled header"""
        border = "═" * width
        print(f"\n{cls._colorize(border, 'CYAN')}")
        print(f"{cls._colorize(text.center(width), 'CYAN')}")
        print(f"{cls._colorize(border, 'CYAN')}")
    
    @classmethod
    def subheader(cls, text, width=60):
        """Print a styled subheader"""
        border = "─" * width
        print(f"\n{cls._colorize(border, 'BLUE')}")
        print(f"{cls._colorize(text.center(width), 'BLUE')}")
        print(f"{cls._colorize(border, 'BLUE')}")
    
    @classmethod
    def success(cls, message, indent=0):
        """Print success message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('✓', 'GREEN')} {message}")
    
    @classmethod
    def error(cls, message, indent=0):
        """Print error message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('✗', 'RED')} {cls._colorize(message, 'RED')}")
    
    @classmethod
    def warning(cls, message, indent=0):
        """Print warning message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('⚠', 'YELLOW')} {cls._colorize(message, 'YELLOW')}")
    
    @classmethod
    def info(cls, message, indent=0):
        """Print info message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('ℹ', 'BLUE')} {message}")
    
    @classmethod
    def step(cls, step_num, title, description=""):
        """Print step header"""
        step_text = f"STEP {step_num}: {title}"
        print(f"\n{cls._colorize('🔄', 'MAGENTA')} {cls._colorize(step_text, 'BOLD')}")
        if description:
            print(f"   {cls._colorize(description, 'DIM')}")
    
    @classmethod
    def progress(cls, current, total, item_name="item"):
        """Print progress indicator"""
        percentage = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r{cls._colorize('📊', 'CYAN')} Progress: [{bar}] {percentage:.1f}% ({current}/{total} {item_name}s)", end='', flush=True)
        if current == total:
            print()  # New line when complete
    
    @classmethod
    def metric(cls, label, value, unit="", color='WHITE'):
        """Print a metric"""
        print(f"   {cls._colorize('•', 'GRAY')} {label}: {cls._colorize(f'{value}{unit}', color)}")
    
    @classmethod
    def file_saved(cls, filepath, description=""):
        """Print file saved message"""
        print(f"   {cls._colorize('💾', 'GREEN')} Saved: {cls._colorize(str(filepath), 'CYAN')}")
        if description:
            print(f"      {cls._colorize(description, 'DIM')}")
    
    @classmethod
    def processing_time(cls, start_time, operation="Operation"):
        """Print processing time"""
        elapsed = time.time() - start_time
        if elapsed < 60:
            time_str = f"{elapsed:.2f}s"
        else:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            time_str = f"{minutes}m {seconds:.1f}s"
        
        print(f"   {cls._colorize('⏱', 'YELLOW')} {operation} completed in {cls._colorize(time_str, 'BOLD')}")
    
    @classmethod
    def question_preview(cls, rank, question, reason, max_length=80):
        """Print a formatted question preview"""
        # Truncate question if too long
        if len(question) > max_length:
            question = question[:max_length-3] + "..."
        
        print(f"\n{cls._colorize(f'{rank}.', 'BOLD')} {cls._colorize(question, 'WHITE')}")
        print(f"   {cls._colorize('💡', 'YELLOW')} {cls._colorize(reason, 'DIM')}")
    
    @classmethod
    def directory_tree(cls, base_path, items):
        """Print a directory tree structure"""
        print(f"\n{cls._colorize('📁', 'CYAN')} {cls._colorize('Output Structure:', 'BOLD')}")
        print(f"{cls._colorize(str(base_path), 'CYAN')}")
        
        for i, (name, description) in enumerate(items):
            is_last = i == len(items) - 1
            prefix = "└── " if is_last else "├── "
            print(f"{prefix}{cls._colorize(name, 'WHITE')} - {cls._colorize(description, 'DIM')}")