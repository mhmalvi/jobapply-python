"""
Base platform class for job search platforms
"""

from abc import ABC, abstractmethod
import random
import time
from typing import List, Dict, Any
import pandas as pd
from loguru import logger
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BasePlatform(ABC):
    """Base class for job search platform implementations."""
    
    def __init__(self, driver: webdriver.Chrome, config: dict):
        """
        Initialize the platform.
        
        Args:
            driver (webdriver.Chrome): Selenium WebDriver instance
            config (dict): Application configuration
        """
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(
            driver,
            config['delays']['page_load_timeout']
        )
    
    @abstractmethod
    def login(self) -> None:
        """
        Log in to the platform.
        
        Raises:
            NotImplementedError: Must be implemented by platform classes
        """
        pass
    
    @abstractmethod
    def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Search for jobs based on configuration.
        
        Returns:
            List[Dict[str, Any]]: List of job listings
            
        Raises:
            NotImplementedError: Must be implemented by platform classes
        """
        pass
    
    @abstractmethod
    def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Apply to the given jobs.
        
        Args:
            jobs (List[Dict[str, Any]]): List of job listings to apply to
            
        Raises:
            NotImplementedError: Must be implemented by platform classes
        """
        pass
    
    def save_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Save job listings to CSV file.
        
        Args:
            jobs (List[Dict[str, Any]]): List of job listings to save
        """
        if not jobs:
            logger.warning("No jobs to save")
            return
            
        try:
            df = pd.DataFrame(jobs)
            filename = f"jobs_{self.__class__.__name__.lower()}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(jobs)} jobs to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving jobs to CSV: {e}")
            raise
    
    def random_delay(self, min_delay: float = None, max_delay: float = None) -> None:
        """
        Add random delay between actions to avoid detection.
        
        Args:
            min_delay (float, optional): Minimum delay in seconds
            max_delay (float, optional): Maximum delay in seconds
        """
        if min_delay is None:
            min_delay = self.config['delays']['min_delay']
        if max_delay is None:
            max_delay = self.config['delays']['max_delay']
            
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def wait_for_element(self, locator: tuple, timeout: int = None) -> Any:
        """
        Wait for element to be present and visible.
        
        Args:
            locator (tuple): Selenium locator tuple (By.*, "selector")
            timeout (int, optional): Custom timeout in seconds
            
        Returns:
            WebElement: The found element
            
        Raises:
            TimeoutException: If element not found within timeout
        """
        if timeout is None:
            timeout = self.config['delays']['page_load_timeout']
            
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located(locator)
            )
            return element
            
        except TimeoutException:
            logger.error(f"Element not found: {locator}")
            raise
    
    def safe_click(self, element) -> None:
        """
        Safely click an element with retry logic.
        
        Args:
            element: Selenium WebElement to click
            
        Raises:
            Exception: If click fails after retries
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                element.click()
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to click element after {max_retries} attempts: {e}")
                    raise
                self.random_delay()
    
    def scroll_to_element(self, element) -> None:
        """
        Scroll element into view.
        
        Args:
            element: Selenium WebElement to scroll to
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true);",
            element
        )
        self.random_delay() 