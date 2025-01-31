#!/usr/bin/env python3
"""
AutoJobFinder - Automated Job Search and Application Tool
Author: AutoJobFinder Team
License: MIT
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import yaml
from loguru import logger
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger
from src.platforms.linkedin import LinkedInPlatform
from src.platforms.indeed import IndeedPlatform
from src.platforms.glassdoor import GlassdoorPlatform
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class AutoJobFinder:
    def __init__(self):
        """Initialize AutoJobFinder with configuration and logging."""
        self.config = self._load_config()
        self.setup_logging()
        self.driver = None
        self.platforms = {}
        
    def _load_config(self):
        """Load configuration from YAML and environment variables."""
        config_path = project_root / "config" / "config.yaml"
        env_path = project_root / ".env"
        
        # Load environment variables
        load_dotenv(env_path)
        
        # Load YAML config
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_logging(self):
        """Configure logging settings."""
        log_config = self.config['logging']
        log_path = project_root / log_config['file_path']
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        setup_logger(
            log_path,
            level=log_config['level'],
            rotation=f"{log_config['max_file_size']} MB",
            retention=log_config['backup_count']
        )
    
    def setup_webdriver(self):
        """Initialize and configure the Chrome WebDriver."""
        chrome_options = uc.ChromeOptions()
        if self.config['browser']['headless']:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(
            options=chrome_options,
            driver_executable_path=None,  # Will be downloaded automatically
            browser_executable_path=None,  # Will use default Chrome installation
            suppress_welcome=True,
            headless=False  # Set to True for headless mode
        )
        self.driver.implicitly_wait(self.config['delays']['page_load_timeout'])
        
        logger.info("WebDriver initialized successfully")
    
    def initialize_platforms(self):
        """Initialize job search platforms based on configuration."""
        if self.config['platforms']['linkedin']['enabled']:
            self.platforms['linkedin'] = LinkedInPlatform(self.driver, self.config)
        
        if self.config['platforms']['indeed']['enabled']:
            self.platforms['indeed'] = IndeedPlatform(self.driver, self.config)
            
        if self.config['platforms']['glassdoor']['enabled']:
            self.platforms['glassdoor'] = GlassdoorPlatform(self.driver, self.config)
    
    def run(self):
        """Main execution method for job search and application."""
        try:
            logger.info("Starting AutoJobFinder")
            self.setup_webdriver()
            self.initialize_platforms()
            
            for platform_name, platform in self.platforms.items():
                logger.info(f"Starting job search on {platform_name}")
                platform.login()
                jobs = platform.search_jobs()
                
                if self.config['application']['apply_active']:
                    platform.apply_to_jobs(jobs)
                else:
                    platform.save_jobs(jobs)
                
                logger.info(f"Completed job search on {platform_name}")
        
        except Exception as e:
            logger.error(f"Error during execution: {str(e)}")
            raise
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")

def setup_driver():
    """Set up and configure the undetected ChromeDriver."""
    try:
        # Configure Chrome options
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        
        # Create undetected ChromeDriver instance
        driver = uc.Chrome(
            options=options,
            driver_executable_path=None,  # Will be downloaded automatically
            browser_executable_path=None,  # Will use default Chrome installation
            suppress_welcome=True,
            headless=False  # Set to True for headless mode
        )
        
        # Set timeouts
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        
        return driver
        
    except Exception as e:
        logger.error(f"Error setting up ChromeDriver: {e}")
        raise

def main():
    """Main function to run the job search."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Configure logging
        os.makedirs("logs", exist_ok=True)
        logger.add(
            "logs/job_search_{time}.log",
            rotation="1 day",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
        )
        
        # Load configuration from YAML
        config_path = os.path.join("config", "config.yaml")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
        
        driver = None
        try:
            # Initialize WebDriver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver = setup_driver()
                    logger.info("WebDriver initialized successfully")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to initialize WebDriver after {max_retries} attempts")
                        raise
                    logger.warning(f"WebDriver initialization attempt {attempt + 1} failed: {e}")
                    time.sleep(5)
            
            # Initialize LinkedIn platform
            linkedin = LinkedInPlatform(driver, config)
            logger.info("LinkedIn platform initialized")
            
            # Login to LinkedIn with retry logic
            max_login_retries = 3
            for attempt in range(max_login_retries):
                try:
                    linkedin.login()
                    logger.info("Successfully logged in to LinkedIn")
                    break
                except Exception as e:
                    if attempt == max_login_retries - 1:
                        logger.error(f"Failed to log in to LinkedIn after {max_login_retries} attempts")
                        raise
                    logger.warning(f"LinkedIn login attempt {attempt + 1} failed: {e}")
                    time.sleep(5)
            
            # Search for jobs
            try:
                jobs = linkedin.search_jobs()
                logger.info(f"Found {len(jobs)} jobs on LinkedIn")
                
                if jobs:
                    # Save jobs to CSV
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_path = f"jobs_linkedin_{timestamp}.csv"
                    
                    try:
                        import pandas as pd
                        df = pd.DataFrame(jobs)
                        df.to_csv(csv_path, index=False)
                        logger.info(f"Saved {len(jobs)} jobs to {csv_path}")
                    except Exception as e:
                        logger.error(f"Error saving jobs to CSV: {e}")
                    
                    # Log job details
                    for job in jobs:
                        logger.info("---")
                        logger.info(f"Title: {job.get('title', 'N/A')}")
                        logger.info(f"Company: {job.get('company', 'N/A')}")
                        logger.info(f"Location: {job.get('location', 'N/A')}")
                        logger.info(f"Link: {job.get('link', 'N/A')}")
                    
                    # Apply to jobs if enabled
                    if config['application']['apply_active']:
                        try:
                            linkedin.apply_to_jobs(jobs)
                        except Exception as e:
                            logger.error(f"Error during job application: {e}")
                
            except Exception as e:
                logger.error(f"Error during job search: {e}")
                raise
        
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
            
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("WebDriver closed")
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {e}")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 