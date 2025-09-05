"""
Utilities for safely saving files.
"""
import os
import json
import tempfile
import shutil
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("safe_save")

def safe_save_json(data, output_path):
    """
    Safely save JSON data to a file using a temporary file and multiple fallback paths.
    
    Args:
        data: The data to save
        output_path: The target output path
        
    Returns:
        The actual path where the file was saved, or None if saving failed
    """
    # Generate timestamp for unique filenames if needed
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get base filename and directory
    base_dir = os.path.dirname(output_path)
    filename = os.path.basename(output_path)
    
    # Define potential save locations
    potential_paths = [
        output_path,  # Original path
        os.path.join(f"backend/{base_dir}" if not base_dir.startswith("backend/") else base_dir, filename),  # With/without backend/ prefix
        os.path.join("data/generated", filename),  # In data/generated
        os.path.join("backend/data/generated", filename),  # In backend/data/generated
        os.path.join(tempfile.gettempdir(), f"{filename}.{timestamp}")  # Fallback to temp directory
    ]
    
    logger.info(f"Attempting to save {filename} with multiple fallback paths")
    
    # Try each path until one works
    for path in potential_paths:
        directory = os.path.dirname(path)
        
        try:
            # Ensure the directory exists
            os.makedirs(directory, exist_ok=True)
            
            # Create a temporary file in the same directory
            temp_fd, temp_path = tempfile.mkstemp(suffix='.json', dir=directory)
            logger.info(f"Trying to save to {path} (via temp file {temp_path})")
            
            try:
                # Write to the temporary file
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Move the temporary file to the final location
                shutil.move(temp_path, path)
                
                # Verify the file was created
                if os.path.exists(path):
                    file_size = os.path.getsize(path)
                    logger.info(f"Successfully saved file to {path} ({file_size} bytes)")
                    
                    # Copy to other key locations for redundancy
                    try:
                        redundant_paths = []
                        if not path.startswith("data/generated"):
                            redundant_paths.append("data/generated")
                        if not path.startswith("backend/data/generated"):
                            redundant_paths.append("backend/data/generated")
                        
                        for redundant_dir in redundant_paths:
                            os.makedirs(redundant_dir, exist_ok=True)
                            redundant_path = os.path.join(redundant_dir, filename)
                            
                            if not os.path.exists(redundant_path):
                                shutil.copy2(path, redundant_path)
                                logger.info(f"Created redundant copy at {redundant_path}")
                    except Exception as e:
                        logger.warning(f"Failed to create redundant copies: {str(e)}")
                    
                    return path
                else:
                    logger.warning(f"File not found at {path} after moving from temp file")
            except Exception as e:
                logger.warning(f"Failed to save to {path}: {str(e)}")
                # Clean up temp file if it still exists
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"Failed to prepare directory {directory}: {str(e)}")
    
    # If we get here, all attempts failed
    logger.error(f"Failed to save file {filename} to any location")
    return None