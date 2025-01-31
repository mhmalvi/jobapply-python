# AutoJobFinder

An automated job search and application tool built with Python and Selenium.

## ⚠️ Legal & Ethical Considerations

This tool is for **educational purposes only**. Before using it:
- Check each platform's Terms of Service regarding automation
- Use responsibly and ethically
- Do not abuse or overload job platforms
- Respect rate limits and platform guidelines

## 🚀 Features

- Search jobs across multiple platforms (LinkedIn, Indeed, Glassdoor)
- Filter by keywords, location, and experience level
- Save job listings to CSV
- Optional automated job application (LinkedIn Easy Apply)
- Anti-detection measures and rate limiting
- Detailed logging and error handling

## 🏗️ Architecture

### High-Level Architecture Diagram
```
          +-------------------+     +-------------------+
          |    User Config     |     |     Credentials   |
          | (keywords, filters)|     | (env, API keys)   |
          +-------------------+     +-------------------+
                     |                         |
                     v                         v
          +-------------------+     +-------------------+
          |   Config Loader   |<----|  Environment Vars |
          +-------------------+     +-------------------+
                     |
                     v
          +-------------------+
          |   Core Engine     |<-------+
          +-------------------+        |
              |           |            |
              v           v            |
+---------------+   +---------------+  |
|  Job Search   |   | Auto-Apply    |  |
|  (Scrapers)   |   | (Form Filler) |  |
+---------------+   +---------------+  |
    |  |  |               |            |
    |  |  +---------------+            |
    |  |                     |          |
    v  v                     v          |
+---------------+   +----------------+  |
| Job Platforms |   | Data Storage   |  |
| (LinkedIn,    |   | (CSV, Excel)   |  |
|  Indeed...)   |   +----------------+  |
+---------------+                       |
           |                            |
           +----------------------------+
           |
           v
+---------------------+
| Anti-Detection      |
| (Delays, Proxies,   |
|  User Agent Rotation)|
+---------------------+
```

### Component Breakdown

#### 1. Configuration Management
- **Purpose**: Centralize user inputs and secrets
- **Components**:
  - `config.yaml`: Stores job search preferences
  - `.env`: Securely stores credentials
- **Key Interaction**: Configuration loader injects settings into core engine

#### 2. Core Engine
- **Purpose**: Orchestrate job search, application, and data flow
- **Components**:
  - `main.py`: Initializes drivers and loads configs
  - `platforms/`: Platform-specific modules
    - Login authentication
    - Search functionality
    - Application automation

#### 3. Job Search & Scraping
- **Dynamic Sites** (LinkedIn/Glassdoor):
  - Uses Selenium for JavaScript-heavy pages
  - Handles scrolling and dynamic content loading
- **Static Sites** (Indeed):
  - Uses Requests + BeautifulSoup for faster parsing
  - Direct HTML extraction

#### 4. Auto-Apply Module
- **Workflow**:
  1. Detect and click apply buttons
  2. Fill forms with resume/cover letter
  3. Handle multi-page applications
- **Tools**:
  - Selenium for form interaction
  - PyAutoGUI for system dialogs

#### 5. Data Storage
- CSV-based job tracking
- Duplicate detection
- Application status monitoring

#### 6. Anti-Detection Layer
- Randomized delays
- User agent rotation
- Proxy support
- Rate limiting

## 🛠️ Prerequisites

- Python 3.8+
- Chrome/Firefox browser
- Windows 10/11
- Platform accounts (LinkedIn, Indeed, Glassdoor)

## 📦 Installation

1. Clone the repository:
```powershell
git clone https://github.com/yourusername/autojobfinder.git
cd autojobfinder
```

2. Create and activate a virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Download WebDriver:
- Chrome: The script will automatically download ChromeDriver
- Firefox: Download [GeckoDriver](https://github.com/mozilla/geckodriver/releases)

## ⚙️ Configuration

1. Create `.env` file in the project root:
```env
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
INDEED_API_KEY=your_api_key  # Optional
```

2. Modify `config/config.yaml` with your preferences:
```yaml
search:
  keywords: "Python Developer"
  location: "New York"
  experience_level: "Entry Level"
```

3. Place your resume and cover letter in the `resumes/` directory:
- `resume.pdf`
- `cover_letter.pdf`

## 🚀 Usage

1. Basic job search (no auto-apply):
```powershell
python src/main.py
```

2. Enable auto-apply (modify config.yaml):
```yaml
application:
  apply_active: true
```

## 📁 Project Structure

```
AutoJobFinder/
├── config/
│   ├── config.yaml           # Search preferences
│   └── .env                  # Credentials
├── logs/                     # Application logs
├── resumes/                  # Resume files
├── src/
│   ├── platforms/
│   │   ├── base.py
│   │   ├── linkedin.py
│   │   ├── indeed.py
│   │   └── glassdoor.py
│   ├── utils/
│   │   ├── config_loader.py
│   │   └── logger.py
│   └── main.py
└── tests/                    # Unit tests
```

## 📝 Logging

Logs are stored in `logs/autojobfinder.log` with the following information:
- Job search results
- Application attempts
- Errors and warnings
- Platform-specific messages

## 🔒 Security

- Credentials are stored in `.env` (never commit this file)
- Session data is not persisted
- Proxy support available for additional privacy
- Rate limiting to avoid detection

## 🐛 Troubleshooting

1. **Login Issues**
   - Verify credentials in `.env`
   - Check for CAPTCHA/2FA requirements
   - Ensure stable internet connection

2. **WebDriver Errors**
   - Update Chrome/Firefox to latest version
   - Clear browser cache/cookies
   - Check WebDriver compatibility

3. **Application Errors**
   - Review log files for details
   - Verify resume/cover letter paths
   - Check platform-specific requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For support, please open an issue in the GitHub repository.

## 🙏 Acknowledgments

- Selenium WebDriver team
- Python community
- Job platform developers

## 📊 Roadmap

- [ ] Add support for more job platforms
- [ ] Implement AI-powered job matching
- [ ] Add resume tailoring features
- [ ] Develop browser extension interface
- [ ] Add email notifications
- [ ] Implement job analytics

## 🔍 Design Decisions

1. **Modular Platform-Specific Code**:
   - Separate logic for each platform enables easy scaling
   - New platforms can be added without affecting existing code

2. **Browser Modes**:
   - Headless mode for speed
   - GUI mode for debugging
   - Configurable through settings

3. **Config-Driven Behavior**:
   - All major settings in config files
   - Easy to modify without code changes

4. **Ethical Safeguards**:
   - Built-in delays
   - Rate limiting
   - Proxy rotation
   - User agent randomization

## 🔄 Flow of Control

1. **Initialization**:
   - Load configurations
   - Initialize WebDriver
   - Authenticate with platforms

2. **Job Search**:
   - Generate search URLs
   - Scrape job listings
   - Filter duplicates

3. **Auto-Apply** (if enabled):
   - Process each job
   - Fill application forms
   - Track status

4. **Cleanup**:
   - Save results
   - Close connections
   - Generate reports

Remember to star ⭐ the repository if you find it helpful!

## 💻 Technical Details

### Core Class Diagram
```python
class AutoJobFinder:
    - config: dict               # Loaded from config.yaml
    - driver: WebDriver          # Selenium instance
    - jobs: List[Job]           # List of Job objects
    - logger: Logger            # Logging instance

    + run()                     # Main entry point
    + shutdown()               # Cleanup resources

class JobPlatform(ABC):
    - platform_name: str
    - driver: WebDriver
    - logger: Logger

    @abstractmethod
    def search_jobs() -> List[Job]
    @abstractmethod
    def apply_to_job(job: Job)

class LinkedIn(JobPlatform):
    - login_executed: bool = False

    + search_jobs()             # LinkedIn-specific search logic
    + apply_to_job()           # LinkedIn EasyApply handler

class Indeed(JobPlatform):
    + search_jobs()             # Indeed scraping via Requests/BS4
    + apply_to_job()           # Indeed application logic

class Job:
    - id: str                   # Unique job identifier (hash of title + company)
    - title: str
    - company: str
    - link: str
    - applied: bool = False
    - platform: str
```

### Implementation Details

#### 1. LinkedIn Job Search Implementation
```python
def linkedin_login():
    try:
        driver.get("https://linkedin.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        username_field = driver.find_element(By.ID, "username")
        username_field.send_keys(env.USERNAME)
        # ... (similar for password and submit)
    except TimeoutException:
        logger.error("Login page elements not found")
        raise
```

#### 2. Job Data Model (Pydantic)
```python
from pydantic import BaseModel

class Job(BaseModel):
    id: str                    # SHA-256 hash of title + company + link
    title: str
    company: str
    link: str
    platform: str
    applied: bool = False

def generate_job_id(title: str, company: str, link: str) -> str:
    unique_str = f"{title}{company}{link}".encode("utf-8")
    return hashlib.sha256(unique_str).hexdigest()
```

#### 3. Anti-Detection Mechanisms
```python
def create_stealth_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={UserAgent().random}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver
```

#### 4. Error Handling & Retries
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def search_jobs_with_retry(platform: JobPlatform) -> List[Job]:
    return platform.search_jobs()
```

### Sequence Diagram (Job Application Flow)
```
User -> main.py: Run Script
main.py -> ConfigLoader: Load config.yaml and .env
ConfigLoader -> LinkedIn: Initialize driver
LinkedIn -> LinkedIn: Login
LinkedIn -> LinkedIn: Search jobs
LinkedIn -> DataStorage: Filter duplicates
DataStorage -> LinkedIn: Return new jobs
LinkedIn -> LinkedIn: Apply to each job
loop For each job:
    LinkedIn -> LinkedIn: Navigate to job link
    LinkedIn -> LinkedIn: Click Easy Apply
    LinkedIn -> FormFiller: Populate fields
    FormFiller -> LinkedIn: Submit application
    LinkedIn -> DataStorage: Mark as applied
end
main.py -> LinkedIn: Shutdown driver
```

### Performance Optimizations

#### 1. Concurrent Job Search
```python
import asyncio

async def search_all_platforms():
    linkedin_task = asyncio.create_task(LinkedIn.search_jobs())
    indeed_task = asyncio.create_task(Indeed.search_jobs())
    await asyncio.gather(linkedin_task, indeed_task)
```

#### 2. Smart Caching
- Cache job search results to minimize API calls
- Store session cookies for faster re-authentication
- Cache form field mappings for repeated applications

### Edge Case Handling

1. **CAPTCHA Detection**:
   - Automatic detection and pause
   - Optional manual intervention
   - Proxy rotation on detection

2. **Rate Limiting**:
   - Exponential backoff
   - Session cool-down periods
   - Request queue management

3. **Form Variations**:
   - Dynamic field detection
   - Optional field skipping
   - Custom field mappings

### Testing Strategy

1. **Unit Tests**:
```python
def test_job_id_generation():
    job = Job(title="Python Dev", company="ABC Corp", link="https://...", platform="LinkedIn")
    assert job.id == generate_job_id(job.title, job.company, job.link)
```

2. **Integration Tests**:
- Platform login verification
- Search result validation
- Form field mapping tests

3. **Mock Tests**:
- Simulated platform responses
- Network condition testing
- Error scenario validation

Remember to star ⭐ the repository if you find it helpful! 