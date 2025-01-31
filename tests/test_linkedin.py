"""
Test LinkedIn platform functionality
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.platforms.linkedin import LinkedInPlatform

@pytest.fixture
def mock_config():
    """Fixture to provide mock configuration."""
    return {
        'search': {
            'keywords': 'Python Developer',
            'location': 'New York',
            'job_type': 'F',  # Full-time
            'date_posted': '7',
            'experience_level': 'ENTRY_LEVEL'
        },
        'platforms': {
            'linkedin': {
                'enabled': True,
                'search_limit': 10
            }
        },
        'application': {
            'apply_active': False,
            'resume_path': 'resumes/resume.pdf'
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
    driver.current_url = "https://www.linkedin.com/jobs"
    return driver

@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables."""
    with patch.dict('os.environ', {
        'LINKEDIN_USERNAME': 'test@example.com',
        'LINKEDIN_PASSWORD': 'test_password'
    }):
        yield

@pytest.fixture
def linkedin_platform(mock_driver, mock_config):
    """Fixture to provide a LinkedIn platform instance."""
    return LinkedInPlatform(mock_driver, mock_config)

def test_linkedin_initialization(linkedin_platform):
    """Test LinkedIn platform initialization."""
    assert linkedin_platform.base_url == "https://www.linkedin.com"
    assert linkedin_platform.driver is not None
    assert linkedin_platform.config is not None
    assert not linkedin_platform.login_executed

def test_linkedin_login_missing_credentials(linkedin_platform):
    """Test login behavior with missing credentials."""
    with pytest.raises(ValueError, match="LinkedIn credentials not found"):
        linkedin_platform.login()

def test_linkedin_login_success(linkedin_platform, mock_env_vars):
    """Test successful login process."""
    # Mock successful element finds
    linkedin_platform.wait_for_element = Mock()
    linkedin_platform.safe_click = Mock()
    
    linkedin_platform.login()
    
    assert linkedin_platform.login_executed
    assert linkedin_platform.driver.get.called_with(f"{linkedin_platform.base_url}/login")

def test_linkedin_login_failure(linkedin_platform, mock_env_vars):
    """Test login failure handling."""
    linkedin_platform.wait_for_element = Mock(side_effect=TimeoutException)
    
    with pytest.raises(Exception):
        linkedin_platform.login()
    
    assert not linkedin_platform.login_executed

def test_linkedin_search_jobs(linkedin_platform):
    """Test job search functionality."""
    # Mock successful element interactions
    linkedin_platform.wait_for_element = Mock()
    linkedin_platform.safe_click = Mock()
    linkedin_platform._apply_filters = Mock()
    linkedin_platform._scrape_job_listings = Mock(return_value=[
        {
            'title': 'Python Developer',
            'company': 'Test Company',
            'location': 'New York',
            'description': 'Test description',
            'url': 'https://linkedin.com/jobs/view/123',
            'applied': False
        }
    ])
    
    jobs = linkedin_platform.search_jobs()
    
    assert len(jobs) == 1
    assert jobs[0]['title'] == 'Python Developer'
    assert linkedin_platform.driver.get.called

def test_linkedin_apply_filters(linkedin_platform):
    """Test filter application functionality."""
    linkedin_platform.wait_for_element = Mock()
    linkedin_platform.safe_click = Mock()
    
    linkedin_platform._apply_filters()
    
    # Verify filter interactions
    assert linkedin_platform.wait_for_element.call_count >= 3
    assert linkedin_platform.safe_click.call_count >= 3

def test_linkedin_scrape_job_listings(linkedin_platform):
    """Test job listing scraping functionality."""
    # Mock job card elements
    mock_card = Mock()
    mock_card.find_element.side_effect = lambda by, selector: Mock(
        text='Test value',
        get_attribute=lambda x: 'https://linkedin.com/jobs/view/123'
    )
    
    linkedin_platform.wait_for_element = Mock(return_value=Mock(
        find_elements=Mock(return_value=[mock_card])
    ))
    linkedin_platform.scroll_to_element = Mock()
    linkedin_platform.safe_click = Mock()
    
    jobs = linkedin_platform._scrape_job_listings()
    
    assert len(jobs) > 0
    assert all(isinstance(job, dict) for job in jobs)

def test_linkedin_extract_job_data(linkedin_platform):
    """Test job data extraction from card."""
    mock_card = Mock()
    mock_card.find_element.side_effect = lambda by, selector: Mock(
        text='Test value',
        get_attribute=lambda x: 'https://linkedin.com/jobs/view/123'
    )
    
    job_data = linkedin_platform._extract_job_data(mock_card)
    
    assert job_data is not None
    assert job_data['platform'] == 'LinkedIn'
    assert not job_data['applied']

def test_linkedin_apply_to_jobs_disabled(linkedin_platform):
    """Test job application when auto-apply is disabled."""
    jobs = [{
        'title': 'Python Dev',
        'company': 'Test Co',
        'url': 'https://linkedin.com/jobs/view/123',
        'applied': False
    }]
    
    linkedin_platform.apply_to_jobs(jobs)
    assert not jobs[0]['applied']

def test_linkedin_easy_apply_flow(linkedin_platform):
    """Test LinkedIn Easy Apply workflow."""
    linkedin_platform.config['application']['apply_active'] = True
    jobs = [{
        'title': 'Python Dev',
        'company': 'Test Co',
        'url': 'https://linkedin.com/jobs/view/123',
        'applied': False
    }]
    
    # Mock Easy Apply button found
    linkedin_platform.wait_for_element = Mock()
    linkedin_platform.safe_click = Mock()
    
    # Mock successful application submission
    linkedin_platform._submit_easy_apply = Mock(return_value=True)
    
    linkedin_platform.apply_to_jobs(jobs)
    assert jobs[0]['applied']

def test_linkedin_submit_easy_apply(linkedin_platform):
    """Test Easy Apply submission process."""
    linkedin_platform.wait_for_element = Mock()
    linkedin_platform.safe_click = Mock()
    
    result = linkedin_platform._submit_easy_apply()
    assert result

def test_linkedin_handle_application_questions(linkedin_platform):
    """Test handling of application questions."""
    # Mock question elements
    mock_question = Mock()
    mock_question.get_attribute.return_value = "text"
    linkedin_platform.driver.find_elements.return_value = [mock_question]
    
    linkedin_platform._handle_application_questions()
    assert linkedin_platform.driver.find_elements.called

def test_linkedin_error_handling(linkedin_platform):
    """Test error handling during job operations."""
    linkedin_platform.driver.get.side_effect = Exception("Network error")
    
    with pytest.raises(Exception):
        linkedin_platform.search_jobs()

def test_linkedin_pagination(linkedin_platform):
    """Test job search pagination."""
    linkedin_platform.wait_for_element = Mock()
    linkedin_platform.safe_click = Mock()
    linkedin_platform._scrape_job_listings = Mock(side_effect=[
        [{'title': 'Job 1'}],
        [{'title': 'Job 2'}],
        []
    ])
    
    jobs = linkedin_platform.search_jobs()
    assert len(jobs) > 0 