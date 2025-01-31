"""
LinkedIn platform implementation
"""

import os
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from loguru import logger

from .base import BasePlatform

class LinkedInPlatform(BasePlatform):
    """LinkedIn job search platform implementation."""
    
    def __init__(self, driver, config):
        """Initialize LinkedIn platform."""
        super().__init__(driver, config)
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = f"{self.base_url}/jobs"
        self.login_executed = False
    
    def _check_if_logged_in(self) -> bool:
        """Check if already logged in to LinkedIn."""
        try:
            # Navigate to LinkedIn homepage
            self.driver.get(self.base_url)
            self.random_delay(2, 3)
            
            # Check for elements that indicate logged-in state
            try:
                self.wait_for_element(
                    (By.CSS_SELECTOR, "nav.global-nav"),
                    timeout=5
                )
                return True
            except TimeoutException:
                try:
                    self.wait_for_element(
                        (By.CSS_SELECTOR, ".feed-identity-module"),
                        timeout=5
                    )
                    return True
                except TimeoutException:
                    try:
                        self.wait_for_element(
                            (By.CSS_SELECTOR, ".search-global-typeahead"),
                            timeout=5
                        )
                        return True
                    except TimeoutException:
                        return False
                        
        except Exception as e:
            logger.warning(f"Error checking login status: {e}")
            return False
    
    def login(self) -> None:
        """
        Log in to LinkedIn using credentials from environment variables.
        
        Raises:
            ValueError: If credentials are missing
            Exception: If login fails
        """
        # First check if already logged in
        if self._check_if_logged_in():
            logger.info("Already logged in to LinkedIn")
            self.login_executed = True
            return
            
        logger.info("Logging in to LinkedIn")
        
        username = os.getenv("LINKEDIN_USERNAME")
        password = os.getenv("LINKEDIN_PASSWORD")
        
        if not username or not password:
            raise ValueError("LinkedIn credentials not found in environment variables")
        
        try:
            # Go directly to the sign-in page
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for page to load completely
            self.random_delay(2, 4)
            
            # Enter username
            username_field = self.wait_for_element(
                (By.ID, "username"),
                timeout=10
            )
            username_field.clear()
            username_field.send_keys(username)
            self.random_delay(1, 2)
            
            # Enter password
            password_field = self.wait_for_element(
                (By.ID, "password"),
                timeout=10
            )
            password_field.clear()
            password_field.send_keys(password)
            self.random_delay(1, 2)
            
            # Submit login form
            submit_button = self.wait_for_element(
                (By.CSS_SELECTOR, "button[type='submit']"),
                timeout=10
            )
            self.safe_click(submit_button)
            
            # Wait for successful login - check multiple possible elements
            try:
                self.wait_for_element(
                    (By.CSS_SELECTOR, "nav.global-nav"),
                    timeout=10
                )
            except TimeoutException:
                # Try alternative elements that indicate successful login
                try:
                    self.wait_for_element(
                        (By.CSS_SELECTOR, ".feed-identity-module"),
                        timeout=10
                    )
                except TimeoutException:
                    self.wait_for_element(
                        (By.CSS_SELECTOR, ".search-global-typeahead"),
                        timeout=10
                    )
            
            self.login_executed = True
            logger.info("Successfully logged in to LinkedIn")
            
        except Exception as e:
            logger.error(f"Failed to log in to LinkedIn: {e}")
            raise
    
    def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn based on configuration.
        
        Returns:
            List[Dict[str, Any]]: List of job listings
        """
        try:
            logger.info("Starting LinkedIn job search")
            
            # Construct the search URL with parameters
            keywords = self.config['search']['keywords'].replace(' ', '%20')
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location=Remote&f_WT=2"
            
            # Navigate to the search URL
            self.driver.get(search_url)
            self.random_delay(5, 7)  # Give more time for the page to load
            
            # Wait for any sign that the page has loaded
            page_loaded = False
            load_indicators = [
                ".jobs-search-results-list",
                "div[data-results-list-top-scroll-sentinel]",
                ".scaffold-layout__list-container",
                ".jobs-search-no-results",
                ".jobs-search-results__list"
            ]
            
            for indicator in load_indicators:
                try:
                    self.wait_for_element(
                        (By.CSS_SELECTOR, indicator),
                        timeout=10
                    )
                    page_loaded = True
                    break
                except TimeoutException:
                    continue
            
            if not page_loaded:
                logger.warning("Could not confirm if page loaded, but continuing")
            
            # Try to apply additional filters if needed
            try:
                self._apply_filters(remote_only=True)
            except Exception as e:
                logger.warning(f"Could not apply additional filters: {e}")
            
            # Scroll the page a few times to load more results
            for _ in range(3):
                try:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    self.random_delay(2, 3)
                except Exception:
                    break
            
            # Try to find job listings with multiple approaches
            jobs = []
            
            # First try: Look for job cards using the exact structure
            try:
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "li.ember-view.occludable-update.p0.relative.scaffold-layout__list-item"
                )
                
                if job_cards:
                    for card in job_cards[:self.config['platforms']['linkedin']['search_limit']]:
                        try:
                            self.scroll_to_element(card)
                            self.random_delay(1, 2)
                            
                            # Get job ID for tracking
                            job_id = card.get_attribute("data-occludable-job-id")
                            
                            # Try to click the card
                            try:
                                # Find the clickable container
                                clickable = card.find_element(
                                    By.CSS_SELECTOR,
                                    "div.job-card-container--clickable"
                                )
                                self.safe_click(clickable)
                            except Exception:
                                # Fallback to direct card click
                                self.safe_click(card)
                            
                            self.random_delay(2, 3)
                            
                            job_data = self._extract_job_data()
                            if job_data and job_data not in jobs:
                                job_data['job_id'] = job_id
                                jobs.append(job_data)
                                logger.debug(f"Extracted job: {job_data['title']} at {job_data['company']}")
                        
                        except Exception as e:
                            logger.warning(f"Error processing job card: {e}")
                            continue
            
            except Exception as e:
                logger.warning(f"Error finding job cards: {e}")
            
            # Second try: Look for job links directly
            if not jobs:
                try:
                    job_links = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "div.job-card-container--clickable a[href*='/jobs/view/']"
                    )
                    
                    if job_links:
                        for link in job_links[:self.config['platforms']['linkedin']['search_limit']]:
                            try:
                                job_url = link.get_attribute("href")
                                if job_url:
                                    self.driver.get(job_url)
                                    self.random_delay(2, 3)
                                    
                                    job_data = self._extract_job_data()
                                    if job_data and job_data not in jobs:
                                        # Extract job ID from URL
                                        job_id = job_url.split('/view/')[-1].split('?')[0]
                                        job_data['job_id'] = job_id
                                        jobs.append(job_data)
                                        logger.debug(f"Extracted job: {job_data['title']} at {job_data['company']}")
                            
                            except Exception as e:
                                logger.warning(f"Error processing job link: {e}")
                                continue
                
                except Exception as e:
                    logger.warning(f"Error finding job links: {e}")
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"Error during LinkedIn job search: {e}")
            return []
    
    def _apply_filters(self, remote_only: bool = False) -> None:
        """
        Apply job search filters based on configuration.
        
        Args:
            remote_only (bool): Whether to filter for remote jobs only
        """
        try:
            # Try different selectors for the filter button
            filter_selectors = [
                "button.search-reusables__filters-show-modal-button",
                "button[aria-label='Filter results']",
                "[aria-label='Show all filters']",
                "button.filter-button"
            ]
            
            filter_button = None
            for selector in filter_selectors:
                try:
                    filter_button = self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    )
                    break
                except TimeoutException:
                    continue
            
            if not filter_button:
                logger.warning("Could not find filter button")
                return
            
            self.safe_click(filter_button)
            self.random_delay(2, 3)
            
            if remote_only:
                # Try different approaches to set remote filter
                remote_selectors = [
                    "//button[contains(@aria-label, 'Remote filter')]",
                    "//button[contains(@aria-label, 'Workplace type')]",
                    "//*[contains(text(), 'Remote')]/ancestor::button",
                    "//span[text()='Remote']/ancestor::button"
                ]
                
                remote_section = None
                for selector in remote_selectors:
                    try:
                        remote_section = self.wait_for_element(
                            (By.XPATH, selector),
                            timeout=5
                        )
                        break
                    except TimeoutException:
                        continue
                
                if remote_section:
                    self.safe_click(remote_section)
                    self.random_delay(1, 2)
                    
                    # Try to find and click remote checkboxes
                    remote_options = self.driver.find_elements(
                        By.XPATH,
                        "//label[contains(translate(., 'REMOTE', 'remote'), 'remote')]//input[@type='checkbox']"
                    )
                    
                    for option in remote_options:
                        if not option.is_selected():
                            try:
                                self.safe_click(option)
                                self.random_delay(1, 2)
                            except Exception:
                                continue
            
            # Try to find and click the "Show results" button
            show_results_selectors = [
                "button.reusable-search-filters-buttons",
                "button[aria-label='Apply current filters']",
                "button.search-reusables__secondary-filters-show-results-button",
                "button[data-test='reusables-filters-show-results-button']"
            ]
            
            for selector in show_results_selectors:
                try:
                    show_results = self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    )
                    self.safe_click(show_results)
                    break
                except TimeoutException:
                    continue
            
            self.random_delay(3, 5)
            
        except Exception as e:
            logger.warning(f"Error applying filters: {e}")
    
    def _scrape_job_listings(self) -> List[Dict[str, Any]]:
        """
        Scrape job listings from search results.
        
        Returns:
            List[Dict[str, Any]]: List of job listings
        """
        jobs = []
        search_limit = self.config['platforms']['linkedin']['search_limit']
        
        try:
            # Try modern job list selector first
            try:
                job_list = self.wait_for_element(
                    (By.CSS_SELECTOR, ".jobs-search-results-list"),
                    timeout=5
                )
            except TimeoutException:
                # Fall back to classic selector
                job_list = self.wait_for_element(
                    (By.CSS_SELECTOR, ".jobs-search__results-list"),
                    timeout=10
                )
            
            self.random_delay(2, 3)
            
            scroll_attempts = 0
            max_scroll_attempts = 5
            
            while len(jobs) < search_limit and scroll_attempts < max_scroll_attempts:
                # Get visible job cards
                try:
                    # Try modern card selector
                    job_cards = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".jobs-search-results__list-item"
                    )
                except NoSuchElementException:
                    # Fall back to classic card selector
                    job_cards = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".job-card-container"
                    )
                
                if not job_cards:
                    logger.warning("No job cards found")
                    break
                
                # Process visible cards
                for card in job_cards:
                    if len(jobs) >= search_limit:
                        break
                    
                    try:
                        # Scroll card into view and click
                        self.scroll_to_element(card)
                        self.random_delay(1, 2)
                        
                        # Try to click the card
                        try:
                            self.safe_click(card)
                        except Exception:
                            # If clicking the card fails, try to find and click the title link
                            title_link = card.find_element(
                                By.CSS_SELECTOR,
                                "a.job-card-list__title, a.job-card-container__link"
                            )
                            self.safe_click(title_link)
                        
                        self.random_delay(2, 3)
                        
                        # Extract job data
                        job_data = self._extract_job_data()
                        if job_data and job_data not in jobs:  # Avoid duplicates
                            jobs.append(job_data)
                            logger.debug(f"Extracted job: {job_data['title']} at {job_data['company']}")
                    
                    except Exception as e:
                        logger.warning(f"Error processing job card: {e}")
                        continue
                
                if len(jobs) < search_limit:
                    # Scroll to load more results
                    last_card = job_cards[-1]
                    self.scroll_to_element(last_card)
                    self.random_delay(2, 3)
                    
                    # Try to click "Show more" button if present
                    try:
                        show_more = self.driver.find_element(
                            By.CSS_SELECTOR,
                            "button.infinite-scroller__show-more-button, button.see-more-jobs"
                        )
                        self.safe_click(show_more)
                        self.random_delay(2, 3)
                    except NoSuchElementException:
                        scroll_attempts += 1
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn job listings: {e}")
            return []
    
    def _extract_job_data(self) -> Dict[str, Any]:
        """
        Extract job data from the currently selected job card.
        
        Returns:
            Dict[str, Any]: Job data dictionary
        """
        try:
            # Wait for job details with multiple possible selectors
            details_loaded = False
            for selector in [
                ".jobs-unified-top-card",
                ".jobs-details",
                ".jobs-search-results__job-details"
            ]:
                try:
                    self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    )
                    details_loaded = True
                    break
                except TimeoutException:
                    continue
            
            if not details_loaded:
                return None
            
            # Extract job title
            title = None
            title_selectors = [
                ".jobs-unified-top-card__job-title",
                ".jobs-details-top-card__job-title",
                "h2.t-24"
            ]
            
            for selector in title_selectors:
                try:
                    title = self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    ).text.strip()
                    break
                except TimeoutException:
                    continue
            
            if not title:
                return None
            
            # Extract company name
            company = "Unknown Company"
            company_selectors = [
                ".jobs-unified-top-card__company-name",
                ".jobs-details-top-card__company-info",
                "a.ember-view.t-black.t-normal"
            ]
            
            for selector in company_selectors:
                try:
                    company = self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    ).text.strip()
                    break
                except TimeoutException:
                    continue
            
            # Extract location
            location = "Remote"
            location_selectors = [
                ".jobs-unified-top-card__bullet",
                ".jobs-details-top-card__bullet",
                ".jobs-unified-top-card__workplace-type"
            ]
            
            for selector in location_selectors:
                try:
                    location = self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    ).text.strip()
                    break
                except TimeoutException:
                    continue
            
            # Get job link
            job_link = self.driver.current_url
            
            # Get job description
            description = "Description not available"
            description_selectors = [
                ".jobs-description__content",
                ".jobs-description-content",
                "#job-details"
            ]
            
            for selector in description_selectors:
                try:
                    description = self.wait_for_element(
                        (By.CSS_SELECTOR, selector),
                        timeout=5
                    ).text.strip()
                    break
                except TimeoutException:
                    continue
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'link': job_link,
                'description': description,
                'platform': 'LinkedIn',
                'applied': False,
                'remote': True
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job details: {e}")
            return None
    
    def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Apply to jobs on LinkedIn.
        
        Args:
            jobs (List[Dict[str, Any]]): List of jobs to apply to
        """
        if not self.config['application']['apply_active']:
            logger.info("Auto-apply is disabled in configuration")
            return
            
        logger.info(f"Processing {len(jobs)} LinkedIn jobs")
        
        for job in jobs:
            if job.get("applied"):
                continue
                
            try:
                logger.info(f"Opening application for: {job['title']} at {job['company']}")
                self.driver.get(job["url"])
                
                # Look for Easy Apply button
                try:
                    apply_button = self.wait_for_element(
                        (By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']"),
                        timeout=5
                    )
                    
                    if "Easy Apply" in apply_button.text:
                        self.safe_click(apply_button)
                        
                        if self._submit_easy_apply():
                            job["applied"] = True
                            logger.info(f"Successfully applied to job: {job['title']}")
                        else:
                            logger.info(f"Could not complete application: {job['title']}")
                            
                except TimeoutException:
                    logger.info(f"No Easy Apply button found: {job['url']}")
                    job["applied"] = False
                
                self.random_delay()
                
            except Exception as e:
                logger.error(f"Error processing LinkedIn job: {e}")
                continue
    
    def _submit_easy_apply(self) -> bool:
        """
        Submit an Easy Apply application.
        
        Returns:
            bool: True if application was submitted successfully
        """
        try:
            while True:
                # Handle any application questions
                self._handle_application_questions()
                
                # Look for next or submit button
                try:
                    next_button = self.wait_for_element(
                        (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
                        timeout=5
                    )
                    self.safe_click(next_button)
                    self.random_delay()
                    
                except TimeoutException:
                    # Try to find submit button
                    try:
                        submit_button = self.wait_for_element(
                            (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
                            timeout=5
                        )
                        self.safe_click(submit_button)
                        return True
                        
                    except TimeoutException:
                        logger.warning("Could not find next or submit button")
                        return False
            
        except Exception as e:
            logger.error(f"Error during Easy Apply submission: {e}")
            return False
    
    def _handle_application_questions(self) -> None:
        """Handle any application questions in the Easy Apply flow."""
        try:
            # Find all question fields
            questions = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.jobs-easy-apply-form-section__input"
            )
            
            for question in questions:
                try:
                    # Get question type
                    input_type = question.get_attribute("type")
                    
                    if input_type == "text":
                        # Text input
                        question.send_keys("Yes")
                    elif input_type == "radio":
                        # Radio button
                        self.safe_click(question)
                    elif input_type == "checkbox":
                        # Checkbox
                        if not question.is_selected():
                            self.safe_click(question)
                            
                except Exception as e:
                    logger.warning(f"Error handling application question: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error finding application questions: {e}") 