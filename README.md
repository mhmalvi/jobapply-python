# LinkedIn Job Search Automation

An automated tool for searching and tracking remote job opportunities on LinkedIn.

## Features

- Automated LinkedIn login
- Remote job search with customizable filters
- Job data extraction including:
  - Job title
  - Company name
  - Location
  - Job description
  - Application link
  - Remote status
- CSV export of job listings
- Configurable search parameters
- Automatic retry mechanisms
- Detailed logging

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd jobapply-python
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your LinkedIn credentials:
```
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

5. Configure search parameters in `config/config.yaml`

## Usage

Run the job search:
```bash
python -m src.main
```

The script will:
1. Log in to LinkedIn
2. Search for remote jobs matching your criteria
3. Extract job details
4. Save results to a CSV file

## Configuration

Edit `config/config.yaml` to customize:
- Search keywords
- Location preferences
- Experience level
- Job type
- Search limits
- Browser settings
- Logging preferences

## Project Structure

```
jobapply-python/
├── config/
│   └── config.yaml
├── src/
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── linkedin.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   └── logger.py
│   └── main.py
├── logs/
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## Requirements

- Python 3.8+
- Chrome browser
- Required Python packages listed in requirements.txt

## License

MIT License 