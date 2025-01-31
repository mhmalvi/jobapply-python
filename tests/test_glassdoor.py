"""
Test Glassdoor platform functionality
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.platforms.glassdoor import GlassdoorPlatform

@pytest.fixture
def mock_config():
    """Fixture to provide mock configuration."""
    return {
        'search': {
            'keywords': 'Python Developer',
            'location': 'New York',
            'job_type': 'fulltime',
            'date_posted': '7',
            'experience_level': 'entry_level'
        },
        'platforms': {
            'glassdoor': {
                'enabled': True,
                'search_limit': 10
            }
        },
        'application': {
            'apply_active': False
        },
        'delays': {
            'min_delay': 1,
            'max_delay': 3,
            'page_load_timeout': 10
        }
    }

@pytest.fixture
def mock_driver():
    """Fixture to provide a mock Selenium WebDriver."""
    driver = Mock()
    # Mock common WebDriver methods
    driver.find_element.return_value = Mock()
    driver.find_elements.return_value = []
    return driver

@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables."""
    with patch.dict('os.environ', {
        'GLASSDOOR_USERNAME': 'test@example.com',
        'GLASSDOOR_PASSWORD': 'test_password'
    }):
        yield

@pytest.fixture
def glassdoor_platform(mock_driver, mock_config):
    """Fixture to provide a Glassdoor platform instance."""
    return GlassdoorPlatform(mock_driver, mock_config)

def test_glassdoor_initialization(glassdoor_platform):
    """Test Glassdoor platform initialization."""
    assert glassdoor_platform.base_url == "https://www.glassdoor.com"
    assert glassdoor_platform.driver is not None
    assert glassdoor_platform.config is not None
    assert not glassdoor_platform.login_executed

def test_glassdoor_login_missing_credentials(glassdoor_platform):
    """Test login behavior with missing credentials."""
    with pytest.raises(ValueError, match="Glassdoor credentials not found"):
        glassdoor_platform.login()

def test_glassdoor_login_success(glassdoor_platform, mock_env_vars):
    """Test successful login process."""
    # Mock successful element finds
    glassdoor_platform.wait_for_element = Mock()
    glassdoor_platform.safe_click = Mock()
    
    glassdoor_platform.login()
    
    assert glassdoor_platform.login_executed
    assert glassdoor_platform.driver.get.called
    assert glassdoor_platform.driver.get.call_args[0][0] == f"{glassdoor_platform.base_url}/profile/login_input"

def test_glassdoor_login_failure(glassdoor_platform, mock_env_vars):
    """Test login failure handling."""
    glassdoor_platform.wait_for_element = Mock(side_effect=TimeoutException)
    
    with pytest.raises(Exception):
        glassdoor_platform.login()
    
    assert not glassdoor_platform.login_executed

def test_glassdoor_search_jobs(glassdoor_platform):
    """Test job search functionality."""
    # Mock successful element interactions
    glassdoor_platform.wait_for_element = Mock()
    glassdoor_platform.safe_click = Mock()
    glassdoor_platform._apply_filters = Mock()
    glassdoor_platform._scrape_job_listings = Mock(return_value=[
        {
            'title': 'Python Developer',
            'company': 'Test Company',
            'location': 'New York',
            'description': 'Test description',
            'url': 'https://test.com/job',
            'applied': False
        }
    ])
    
    jobs = glassdoor_platform.search_jobs()
    
    assert len(jobs) == 1
    assert jobs[0]['title'] == 'Python Developer'
    assert glassdoor_platform.driver.get.called

def test_glassdoor_apply_filters(glassdoor_platform):
    """Test filter application functionality."""
    glassdoor_platform.wait_for_element = Mock()
    glassdoor_platform.safe_click = Mock()
    
    glassdoor_platform._apply_filters()
    
    # Verify filter interactions
    assert glassdoor_platform.wait_for_element.call_count >= 4
    assert glassdoor_platform.safe_click.call_count >= 4

def test_glassdoor_scrape_job_listings(glassdoor_platform):
    """Test job listing scraping functionality."""
    # Mock job card elements
    mock_card = Mock()
    mock_card.find_element.side_effect = lambda by, selector: Mock(
        text='Test value',
        get_attribute=lambda x: 'https://test.com/job'
    )
    
    glassdoor_platform.wait_for_element = Mock(return_value=Mock(
        find_elements=Mock(return_value=[mock_card])
    ))
    glassdoor_platform.scroll_to_element = Mock()
    glassdoor_platform.safe_click = Mock()
    
    jobs = glassdoor_platform._scrape_job_listings()
    
    assert len(jobs) > 0
    assert all(isinstance(job, dict) for job in jobs)

def test_glassdoor_extract_job_data(glassdoor_platform):
    """Test job data extraction from card."""
    mock_card = Mock()
    mock_card.find_element.side_effect = lambda by, selector: Mock(
        text='Test value',
        get_attribute=lambda x: 'https://test.com/job'
    )
    
    job_data = glassdoor_platform._extract_job_data(mock_card)
    
    assert job_data is not None
    assert job_data['platform'] == 'Glassdoor'
    assert not job_data['applied']

def test_glassdoor_apply_to_jobs_disabled(glassdoor_platform):
    """Test job application when auto-apply is disabled."""
    jobs = [{
        'title': 'Python Dev',
        'company': 'Test Co',
        'url': 'https://glassdoor.com/job/123',
        'applied': False
    }]
    
    glassdoor_platform.apply_to_jobs(jobs)
    assert not jobs[0]['applied']

def test_glassdoor_apply_to_jobs_error_handling(glassdoor_platform):
    """Test error handling during job application."""
    glassdoor_platform.config['application']['apply_active'] = True
    jobs = [{
        'title': 'Python Dev',
        'company': 'Test Co',
        'url': 'https://glassdoor.com/job/123',
        'applied': False
    }]
    
    # Mock driver to raise exception
    glassdoor_platform.driver.get.side_effect = Exception("Network error")
    
    # Should not raise exception but log error
    glassdoor_platform.apply_to_jobs(jobs)
    assert not jobs[0]['applied']

def test_glassdoor_handle_cookie_consent(glassdoor_platform, mock_env_vars):
    """Test handling of cookie consent dialog."""
    glassdoor_platform.wait_for_element = Mock(side_effect=TimeoutException)
    
    # Should not raise exception when cookie dialog is not found
    glassdoor_platform.login() 