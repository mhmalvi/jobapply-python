"""
Glassdoor platform implementation
"""

import os
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from loguru import logger

from .base import BasePlatform

class GlassdoorPlatform(BasePlatform):
    """Glassdoor job search platform implementation."""
    
    def __init__(self, driver, config):
        """Initialize Glassdoor platform."""
        super().__init__(driver, config)
        self.base_url = "https://www.glassdoor.com"
        self.login_executed = False
    
    def login(self) -> None:
        """
        Log in to Glassdoor using credentials from environment variables.
        
        Raises:
            ValueError: If credentials are missing
            Exception: If login fails
        """
        if self.login_executed:
            logger.debug("Already logged in to Glassdoor")
            return
            
        username = os.getenv("GLASSDOOR_USERNAME")
        password = os.getenv("GLASSDOOR_PASSWORD")
        
        if not username or not password:
            raise ValueError("Glassdoor credentials not found in environment variables")
        
        try:
            logger.info("Logging in to Glassdoor")
            self.driver.get(f"{self.base_url}/profile/login_input")
            
            # Handle cookie consent if present
            try:
                cookie_button = self.wait_for_element(
                    (By.ID, "onetrust-accept-btn-handler"),
                    timeout=5
                )
                self.safe_click(cookie_button)
            except TimeoutException:
                logger.debug("No cookie consent dialog found")
            
            # Enter credentials
            username_field = self.wait_for_element(
                (By.ID, "userEmail")
            )
            password_field = self.wait_for_element(
                (By.ID, "userPassword")
            )
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Submit login form
            submit_button = self.wait_for_element(
                (By.CSS_SELECTOR, "button[type='submit']")
            )
            self.safe_click(submit_button)
            
            # Wait for successful login
            self.wait_for_element(
                (By.CSS_SELECTOR, "div[data-test='profile-dropdown']")
            )
            
            self.login_executed = True
            logger.info("Successfully logged in to Glassdoor")
            
        except Exception as e:
            logger.error(f"Failed to log in to Glassdoor: {e}")
            raise
    
    def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Search for jobs on Glassdoor based on configuration.
        
        Returns:
            List[Dict[str, Any]]: List of job listings
        """
        try:
            logger.info("Starting Glassdoor job search")
            
            # Navigate to jobs page
            self.driver.get(f"{self.base_url}/Job/jobs.htm")
            
            # Enter search criteria
            keyword_field = self.wait_for_element(
                (By.CSS_SELECTOR, "input[data-test='search-bar-keyword-input']")
            )
            location_field = self.wait_for_element(
                (By.CSS_SELECTOR, "input[data-test='search-bar-location-input']")
            )
            
            # Clear existing values
            keyword_field.clear()
            location_field.clear()
            
            # Enter search terms
            keyword_field.send_keys(self.config['search']['keywords'])
            self.random_delay()
            location_field.send_keys(self.config['search']['location'])
            location_field.send_keys(Keys.RETURN)
            
            # Wait for results and apply filters
            self._apply_filters()
            
            return self._scrape_job_listings()
            
        except Exception as e:
            logger.error(f"Error during Glassdoor job search: {e}")
            raise
    
    def _apply_filters(self) -> None:
        """Apply job search filters based on configuration."""
        try:
            # Wait for filters to be available
            filter_button = self.wait_for_element(
                (By.CSS_SELECTOR, "button[data-test='filters-button']")
            )
            self.safe_click(filter_button)
            
            # Apply date posted filter
            date_filter = self.wait_for_element(
                (By.CSS_SELECTOR, f"input[value='{self.config['search']['date_posted']}']")
            )
            self.safe_click(date_filter)
            
            # Apply experience level filter if specified
            if self.config['search']['experience_level']:
                exp_filter = self.wait_for_element(
                    (By.CSS_SELECTOR, f"input[value='{self.config['search']['experience_level']}']")
                )
                self.safe_click(exp_filter)
            
            # Apply job type filter
            job_type = self.wait_for_element(
                (By.CSS_SELECTOR, f"input[value='{self.config['search']['job_type']}']")
            )
            self.safe_click(job_type)
            
            # Apply filters
            apply_button = self.wait_for_element(
                (By.CSS_SELECTOR, "button[data-test='apply-filters-button']")
            )
            self.safe_click(apply_button)
            self.random_delay()
            
        except Exception as e:
            logger.warning(f"Error applying filters: {e}")
    
    def _scrape_job_listings(self) -> List[Dict[str, Any]]:
        """
        Scrape job listings from search results.
        
        Returns:
            List[Dict[str, Any]]: List of job listings
        """
        jobs = []
        search_limit = self.config['platforms']['glassdoor']['search_limit']
        
        try:
            # Wait for job list to load
            job_list = self.wait_for_element(
                (By.CSS_SELECTOR, "ul[data-test='jl']")
            )
            
            while len(jobs) < search_limit:
                # Get visible job cards
                job_cards = job_list.find_elements(
                    By.CSS_SELECTOR,
                    "li[data-test='jobListing']"
                )
                
                for card in job_cards:
                    if len(jobs) >= search_limit:
                        break
                        
                    try:
                        # Scroll card into view
                        self.scroll_to_element(card)
                        self.safe_click(card)
                        self.random_delay()
                        
                        job_data = self._extract_job_data(card)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.warning(f"Error extracting job data: {e}")
                        continue
                
                # Try to load more results
                try:
                    show_more = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[data-test='show-more-jobs']"
                    )
                    self.safe_click(show_more)
                    self.random_delay()
                except NoSuchElementException:
                    break
            
            logger.info(f"Found {len(jobs)} jobs on Glassdoor")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping Glassdoor job listings: {e}")
            raise
    
    def _extract_job_data(self, card) -> Dict[str, Any]:
        """
        Extract job data from a job card element.
        
        Args:
            card: Selenium WebElement representing a job card
            
        Returns:
            Dict[str, Any]: Job data dictionary
        """
        try:
            # Extract basic job info
            title = card.find_element(
                By.CSS_SELECTOR,
                "a[data-test='job-link']"
            ).text.strip()
            
            company = card.find_element(
                By.CSS_SELECTOR,
                "div[data-test='employer-name']"
            ).text.strip()
            
            location = card.find_element(
                By.CSS_SELECTOR,
                "div[data-test='location']"
            ).text.strip()
            
            # Get job link
            job_link = card.find_element(
                By.CSS_SELECTOR,
                "a[data-test='job-link']"
            ).get_attribute("href")
            
            # Get job description from side panel
            try:
                description = self.wait_for_element(
                    (By.CSS_SELECTOR, "div[data-test='jobDescriptionContent']")
                ).text.strip()
            except TimeoutException:
                description = "Description not available"
            
            return {
                "platform": "Glassdoor",
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "url": job_link,
                "applied": False
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job data from card: {e}")
            return None
    
    def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Apply to jobs on Glassdoor.
        Note: Glassdoor typically redirects to company websites for applications.
        This implementation focuses on tracking rather than automated application.
        
        Args:
            jobs (List[Dict[str, Any]]): List of jobs to track applications for
        """
        if not self.config['application']['apply_active']:
            logger.info("Auto-apply is disabled in configuration")
            return
            
        logger.info(f"Processing {len(jobs)} Glassdoor jobs")
        
        for job in jobs:
            if job.get("applied"):
                continue
                
            try:
                logger.info(f"Opening application for: {job['title']} at {job['company']}")
                self.driver.get(job["url"])
                
                # Check for Easy Apply button
                try:
                    apply_button = self.wait_for_element(
                        (By.CSS_SELECTOR, "button[data-test='apply-button']"),
                        timeout=5
                    )
                    self.safe_click(apply_button)
                    
                    # Note: Actual application implementation would go here
                    # Most Glassdoor jobs redirect to external sites
                    logger.info(f"Job requires external application: {job['url']}")
                    job["applied"] = False
                    
                except TimeoutException:
                    logger.info(f"No direct apply button found: {job['url']}")
                    job["applied"] = False
                
                self.random_delay()
                
            except Exception as e:
                logger.error(f"Error processing Glassdoor job: {e}")
                continue 