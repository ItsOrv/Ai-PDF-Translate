"""
File and directory utilities for the application.
"""

import os
import glob
import logging
from pathlib import Path
from typing import List, Optional

from src.config.constants import Constants

logger = logging.getLogger(__name__)

class FileUtils:
    """Utility functions for file operations."""
    
    @staticmethod
    def find_pdf_files(directory: str = None) -> List[str]:
        """
        Find all PDF files in a directory. If no directory is provided, 
        it searches in both the current directory and a 'samples' subdirectory.
        
        Args:
            directory: Directory to search in or None to search in default locations
            
        Returns:
            List of paths to PDF files
        """
        pdf_files = []
        
        # If no directory provided, check default locations
        if directory is None:
            # First check samples directory
            if os.path.exists(Constants.SAMPLES_DIR) and os.path.isdir(Constants.SAMPLES_DIR):
                pdf_files.extend(glob.glob(f"{Constants.SAMPLES_DIR}/*.pdf"))
            
            # Then check current directory
            pdf_files.extend(glob.glob(f"*.{Constants.PDF_EXTENSION}"))
        else:
            # Use the provided directory
            if os.path.exists(directory):
                pdf_files.extend(glob.glob(f"{directory}/*.{Constants.PDF_EXTENSION}"))
            else:
                logger.warning(f"Directory not found: {directory}")
        
        # Log the results
        if pdf_files:
            logger.info(f"Found {len(pdf_files)} PDF file(s)")
            for pdf_file in pdf_files:
                logger.debug(f"PDF file: {pdf_file}")
        else:
            logger.warning("No PDF files found")
            
        return pdf_files
        
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> str:
        """
        Ensure the specified directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Absolute path to the directory
        """
        abs_path = os.path.abspath(directory_path)
        
        if not os.path.exists(abs_path):
            logger.info(f"Creating directory: {abs_path}")
            os.makedirs(abs_path)
        elif not os.path.isdir(abs_path):
            logger.error(f"{abs_path} exists but is not a directory")
            raise ValueError(f"{abs_path} exists but is not a directory")
            
        return abs_path
        
    @staticmethod
    def get_output_path(input_path: str, output_dir: Optional[str] = None, suffix: str = "_translated") -> str:
        """
        Generate an output file path based on the input path.
        
        Args:
            input_path: Path to the input file
            output_dir: Directory for the output file (or None to use input file's directory)
            suffix: Suffix to add to the filename
            
        Returns:
            Path to the output file
        """
        # Get the base filename and directory
        input_dir, input_filename = os.path.split(input_path)
        base_name, ext = os.path.splitext(input_filename)
        
        # Determine output directory
        if output_dir is None:
            output_dir = input_dir
        
        # Ensure output directory exists
        FileUtils.ensure_directory_exists(output_dir)
        
        # Create output path
        output_filename = f"{base_name}{suffix}{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        return output_path
        
    @staticmethod
    def get_project_root() -> Path:
        """
        Get the project root directory based on the location of known files/directories.
        
        Returns:
            Path to the project root directory
        """
        # Start with the current working directory
        current_dir = Path.cwd()
        
        # Check if we're already at the project root
        if (current_dir / 'src').exists() and (current_dir / 'src').is_dir():
            return current_dir
        
        # Try to locate project root by looking for src directory
        parent_dir = current_dir
        for _ in range(3):  # Only check up to 3 levels up
            if (parent_dir / 'src').exists() and (parent_dir / 'src').is_dir():
                return parent_dir
            parent_dir = parent_dir.parent
        
        # If we couldn't find the project root, just return the current directory
        logger.warning("Could not locate project root directory, using current directory")
        return current_dir 