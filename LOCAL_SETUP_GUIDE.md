# InnoVantage - Local Development Setup Guide

## Quick Start Guide for Running the Project Locally

This guide will help you set up and run the InnoVantage Resume Evaluation System on your local machine.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Environment Setup](#environment-setup)
4. [Database Configuration](#database-configuration)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Development Workflow](#development-workflow)

---

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space
- **Network**: Internet connection for AI features and package installation

### Required Software
- **Python 3.11+**: Download from [python.org](https://python.org/downloads/)
- **Git**: Download from [git-scm.com](https://git-scm.com/downloads)
- **PostgreSQL** (Optional): Download from [postgresql.org](https://postgresql.org/download/)

---

## Installation Methods

### Method 1: Using UV (Recommended)

UV is a fast Python package manager that's already configured for this project.

#### Step 1: Install UV
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Using pip
pip install uv
```

#### Step 2: Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd innomatics-resume-evaluator

# Install dependencies using UV
uv sync

# Download spaCy language model
uv run python -m spacy download en_core_web_sm
```

### Method 2: Using Traditional pip + venv

#### Step 1: Create Virtual Environment
```bash
# Clone the repository
git clone <repository-url>
cd innomatics-resume-evaluator

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

#### Step 2: Install Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Alternative: Install from pyproject.toml
pip install -e .

# Download spaCy language model
python -m spacy download en_core_web_sm
```

---

## Environment Setup

### Step 1: Create Environment File
Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env
```

### Step 2: Configure Environment Variables
Edit the `.env` file with your settings:

```bash
# Database Configuration (Optional - defaults to SQLite)
DATABASE_URL=postgresql://username:password@localhost:5432/resume_evaluation

# OpenAI API Configuration (Optional - enables AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
FLASK_ENV=development
DEBUG=True

# Streamlit Configuration
STREAMLIT_SERVER_PORT=5000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Step 3: API Key Setup (Optional)

#### OpenAI API Key
1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create an account or sign in
3. Generate a new API key
4. Add it to your `.env` file

**Note**: The application works without OpenAI API key but with limited AI features.

---

## Database Configuration

### Option 1: SQLite (Default - No Setup Required)
The application automatically creates a SQLite database file. No additional setup needed.

```bash
# SQLite database will be created automatically as:
# resume_evaluation.db
```

### Option 2: PostgreSQL (Recommended for Production)

#### Install PostgreSQL
```bash
# On macOS using Homebrew
brew install postgresql
brew services start postgresql

# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# On Windows
# Download and install from postgresql.org
```

#### Create Database
```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE resume_evaluation;
CREATE USER resume_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE resume_evaluation TO resume_user;
\q
```

#### Update Environment
```bash
# Add to .env file
DATABASE_URL=postgresql://resume_user:your_password@localhost:5432/resume_evaluation
```

---

## Running the Application

### Method 1: Using UV (Recommended)
```bash
# Navigate to project directory
cd innomatics-resume-evaluator

# Run the application
uv run streamlit run app.py

# Alternative: Run with specific configuration
uv run streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

### Method 2: Using Traditional Python
```bash
# Activate virtual environment (if using venv)
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Run the application
streamlit run app.py

# Alternative: Run with specific configuration
streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

### Access the Application
Once running, the application will be available at:
- **Local**: http://localhost:5000
- **Network**: http://0.0.0.0:5000

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # On macOS/Linux
netstat -ano | findstr :5000  # On Windows

# Kill the process or use different port
streamlit run app.py --server.port 8501
```

#### 2. Package Installation Errors
```bash
# Clear pip cache
pip cache purge

# Upgrade pip
pip install --upgrade pip

# Install packages one by one
pip install streamlit pandas numpy
```

#### 3. Database Connection Issues
```bash
# Check PostgreSQL service
sudo systemctl status postgresql  # On Linux
brew services list | grep postgresql  # On macOS

# Test database connection
psql postgresql://username:password@localhost:5432/database_name
```

#### 4. spaCy Model Download Issues
```bash
# Manual download
python -m spacy download en_core_web_sm

# Alternative download method
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.tar.gz
```

#### 5. Memory Issues
```bash
# Increase virtual memory (if needed)
# On Linux: Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Performance Optimization

#### 1. Python Optimization
```bash
# Use Python 3.11+ for better performance
python --version

# Enable bytecode optimization
export PYTHONOPTIMIZE=2
```

#### 2. Memory Management
```bash
# Monitor memory usage
pip install memory-profiler
python -m memory_profiler app.py
```

#### 3. Database Optimization
```bash
# For PostgreSQL: Tune configuration
# Edit postgresql.conf:
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
```

---

## Development Workflow

### Project Structure
```
innomatics-resume-evaluator/
├── app.py                 # Main application entry point
├── dashboard.py           # UI components and pages
├── auth.py               # Authentication system
├── database_postgres.py  # Database operations
├── text_extractor.py     # File processing
├── nlp_processor.py      # NLP and AI processing
├── scoring_engine.py     # Evaluation algorithms
├── batch_processor.py    # Batch processing system
├── utils.py              # Utility functions
├── pyproject.toml        # Project dependencies
├── .streamlit/           # Streamlit configuration
│   └── config.toml
├── test_files/           # Sample files for testing
├── attached_assets/      # Generated assets
└── .env                  # Environment variables
```

### Development Commands
```bash
# Install development dependencies
uv add --dev pytest black flake8 mypy

# Run tests
uv run pytest

# Format code
uv run black .

# Check code quality
uv run flake8 .
uv run mypy .

# Update dependencies
uv lock --upgrade
```

### Testing the Application

#### 1. Basic Functionality Test
1. Access the application at http://localhost:5000
2. Navigate to "Student Portal"
3. Upload a sample resume (use files in `test_files/`)
4. Verify evaluation results are displayed

#### 2. Authentication Test
1. Navigate to "Dashboard" (requires login)
2. Register a new account
3. Login with created credentials
4. Verify access to authenticated features

#### 3. Job Description Test
1. Login to the system
2. Navigate to "Job Descriptions"
3. Upload a sample job description
4. Verify parsing and storage

#### 4. Batch Processing Test
1. Navigate to "Batch Processing"
2. Upload multiple resume files
3. Monitor progress and results
4. Download generated reports

---

## Production Deployment

### Environment Preparation
```bash
# Set production environment
export FLASK_ENV=production
export DEBUG=False

# Use production database
export DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/prod_db
```

### Security Considerations
- Use strong passwords for database users
- Enable SSL/TLS for database connections
- Set up proper firewall rules
- Regular security updates
- Monitor access logs

### Performance Tuning
- Use connection pooling for database
- Enable gzip compression
- Set up caching layers
- Monitor resource usage
- Scale horizontally as needed

---

## Getting Help

### Support Resources
- **Documentation**: This guide and PROJECT_ARCHITECTURE.md
- **Issues**: Check existing issues or create new ones
- **Community**: Join development discussions
- **Contact**: reach out to development team

### Log Files and Debugging
```bash
# Application logs
tail -f logs/application.log

# Database logs (PostgreSQL)
tail -f /var/log/postgresql/postgresql-*.log

# Streamlit logs
streamlit run app.py --logger.level debug
```

---

## FAQ

**Q: Can I run this without an OpenAI API key?**
A: Yes, the system will fall back to rule-based evaluation methods.

**Q: What file formats are supported for resumes?**
A: PDF and DOCX formats are fully supported.

**Q: How much memory does the application use?**
A: Typically 500MB-1GB depending on batch processing load.

**Q: Can I use a different database?**
A: The system is designed for PostgreSQL but includes SQLite fallback.

**Q: Is this suitable for production use?**
A: Yes, with proper configuration and security measures.

---

*For additional support or questions, please refer to the project documentation or contact the development team.*