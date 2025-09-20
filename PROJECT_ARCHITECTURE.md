# InnoVantage - AI-Powered Resume Evaluation System

## Architecture & Functionality Documentation

### Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow & Processing Pipeline](#data-flow--processing-pipeline)
4. [Feature Breakdown](#feature-breakdown)
5. [Security & Authentication](#security--authentication)
6. [AI & Machine Learning Integration](#ai--machine-learning-integration)
7. [Database Schema](#database-schema)
8. [API Endpoints & Functions](#api-endpoints--functions)

---

## System Overview

InnoVantage is a comprehensive AI-powered resume evaluation system designed for Innomatics Research Labs to automate and standardize their recruitment process across multiple locations (Hyderabad, Bangalore, Pune, and Delhi NCR).

### Key Capabilities
- **Automated Resume Parsing**: Extracts text and structured data from PDF/DOCX files
- **AI-Powered Evaluation**: Uses hybrid scoring combining rule-based matching with semantic analysis
- **Batch Processing**: Concurrent processing of multiple resumes with real-time progress tracking
- **Role-Based Access**: Separate portals for students and placement teams
- **Advanced Analytics**: Comprehensive insights and performance metrics
- **Modern UI**: Streamlit-based interface with responsive design and modern styling

---

## Architecture Components

### Frontend Layer
```
┌─────────────────────────────────────┐
│           Streamlit Web App         │
├─────────────────────────────────────┤
│  • Modern UI with gradient styling  │
│  • Responsive multi-page navigation │
│  • Real-time progress tracking      │
│  • Interactive charts & analytics   │
│  • File upload & batch processing   │
└─────────────────────────────────────┘
```

### Application Layer
```
┌─────────────────────────────────────┐
│         Core Application            │
├─────────────────────────────────────┤
│  app.py          │ Main entry point │
│  dashboard.py    │ UI components    │
│  auth.py         │ Authentication   │
│  batch_processor.py │ Bulk processing│
└─────────────────────────────────────┘
```

### Processing Layer
```
┌─────────────────────────────────────┐
│        Processing Engines           │
├─────────────────────────────────────┤
│  text_extractor.py   │ File parsing │
│  nlp_processor.py    │ NLP analysis │
│  scoring_engine.py   │ Evaluation   │
│  utils.py           │ Utilities    │
└─────────────────────────────────────┘
```

### Data Layer
```
┌─────────────────────────────────────┐
│         Database Layer              │
├─────────────────────────────────────┤
│  database_postgres.py │ Main DB ops │
│  database.py         │ SQLite backup│
│  PostgreSQL Database │ Primary store│
└─────────────────────────────────────┘
```

---

## Data Flow & Processing Pipeline

### 1. Resume Upload & Processing
```
User Upload → File Validation → Text Extraction → NLP Processing → Database Storage
     ↓              ↓               ↓              ↓               ↓
   PDF/DOCX    Size/Type Check   PyMuPDF/docx   spaCy/OpenAI   PostgreSQL
```

### 2. Job Description Processing
```
Job Text Input → NLP Analysis → Skill Extraction → Requirements Parsing → Database Storage
      ↓              ↓             ↓                 ↓                ↓
   Raw Text      OpenAI/spaCy   Pattern Matching   JSON Structure   PostgreSQL
```

### 3. Evaluation Pipeline
```
Resume + Job → Feature Extraction → Scoring Algorithm → Verdict Generation → Results Storage
     ↓              ↓                    ↓                  ↓              ↓
   Text Data    Skills/Experience   Hybrid Scoring     High/Med/Low    Database
```

### 4. Batch Processing Flow
```
Multiple Files → ThreadPoolExecutor → Parallel Processing → Results Aggregation → Report Generation
      ↓                ↓                     ↓                    ↓                ↓
   File Queue      Concurrent Tasks      Individual Results      Summary Stats     CSV/JSON Export
```

---

## Feature Breakdown

### 1. Student Portal (Unauthenticated)
- **Purpose**: Allow students to evaluate their resumes without login
- **Features**:
  - Simple resume upload interface
  - Basic evaluation results
  - Improvement suggestions
  - No data persistence (privacy-focused)

### 2. Dashboard (Authenticated)
- **Purpose**: Executive overview for placement teams
- **Components**:
  - Real-time metrics display
  - Verdict distribution charts
  - Recent evaluations table
  - Quick navigation to other features

### 3. Job Description Management
- **Upload Interface**: Structured form for job details
- **NLP Processing**: Automatic skill and requirement extraction
- **Storage**: Parsed requirements saved for future evaluations

### 4. Resume Upload & Evaluation
- **File Processing**: Support for PDF and DOCX formats
- **Text Extraction**: Advanced parsing with error handling
- **Evaluation Engine**: Multi-factor scoring algorithm
- **Results Display**: Comprehensive feedback and suggestions

### 5. Batch Processing System
- **Concurrent Processing**: ThreadPoolExecutor for parallel operations
- **Progress Tracking**: Real-time status updates
- **Error Handling**: Individual file error tracking
- **Reporting**: Comprehensive batch analysis reports

### 6. Advanced Analytics
- **Performance Metrics**: Score distributions and trends
- **Job Analysis**: Position-wise candidate quality
- **Skills Gap Analysis**: Missing skills identification
- **Recommendation Engine**: AI-powered insights

---

## Security & Authentication

### Authentication System
```python
bcrypt Password Hashing → Session Token Generation → Database Session Storage → Middleware Validation
        ↓                        ↓                         ↓                      ↓
   Secure Storage          32-byte URL-safe token      24-hour expiry        Route Protection
```

### Security Features
- **Password Security**: bcrypt hashing with salt
- **Session Management**: Secure token-based sessions
- **Role-Based Access**: Different permissions for users
- **Input Validation**: File type and size restrictions
- **Error Handling**: Safe error messages without data exposure

### User Roles
- **Student**: Open access to evaluation features
- **Placement Team**: Full access to management features
- **Admin**: Complete system access
- **Mentor**: Educational features access

---

## AI & Machine Learning Integration

### NLP Processing Pipeline
```
Text Input → spaCy Processing → Entity Recognition → Skill Extraction → Semantic Analysis
    ↓             ↓                  ↓                ↓                ↓
Raw Resume    Tokenization      Named Entities    Technical Skills   OpenAI Integration
```

### Scoring Algorithm
```python
# Hybrid Scoring Model
final_score = (
    hard_match_score * 0.7 +      # Exact keyword matching
    semantic_score * 0.2 +        # AI semantic similarity
    experience_score * 0.1        # Experience matching
)
```

### AI Integration Points
1. **Job Description Parsing**: OpenAI GPT for requirement extraction
2. **Semantic Matching**: Embeddings-based similarity scoring
3. **Improvement Suggestions**: AI-generated feedback
4. **Skills Analysis**: Pattern recognition for skill identification

---

## Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    location VARCHAR(50),
    role VARCHAR(20) DEFAULT 'placement_team',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### job_descriptions
```sql
CREATE TABLE job_descriptions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(100),
    location VARCHAR(100),
    description TEXT NOT NULL,
    required_skills JSONB,
    preferred_skills JSONB,
    other_requirements JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### resumes
```sql
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    candidate_name VARCHAR(100),
    candidate_email VARCHAR(100),
    extracted_text TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### evaluations
```sql
CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_descriptions(id),
    resume_id INTEGER REFERENCES resumes(id),
    relevance_score DECIMAL(5,2),
    hard_match_score DECIMAL(5,2),
    semantic_match_score DECIMAL(5,2),
    verdict VARCHAR(20),
    missing_skills JSONB,
    improvement_suggestions TEXT,
    evaluation_details JSONB,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints & Functions

### Core Functions

#### Database Operations
- `init_database()`: Initialize database connection and tables
- `save_user()`: Create new user accounts
- `save_job_description()`: Store job requirements
- `save_resume()`: Store resume data
- `save_evaluation()`: Store evaluation results
- `get_evaluations()`: Retrieve evaluation history

#### Processing Functions
- `process_uploaded_file()`: Extract text from PDF/DOCX
- `parse_job_description()`: NLP analysis of job requirements
- `evaluate_resume()`: Core evaluation algorithm
- `process_resume_batch()`: Batch processing coordinator

#### Authentication Functions
- `login_user()`: User authentication
- `register_user()`: Account creation
- `check_authentication()`: Session validation
- `logout_user()`: Session termination

### System Configuration

#### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/dbname

# AI Integration
OPENAI_API_KEY=your_openai_api_key

# Application Settings
FLASK_ENV=production
DEBUG=False
```

#### Streamlit Configuration
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"

[server]
port = 5000
address = "0.0.0.0"
maxUploadSize = 50
```

---

## Performance & Scalability

### Optimization Features
- **Concurrent Processing**: ThreadPoolExecutor for batch operations
- **Database Connection Pooling**: Efficient database connections
- **Caching**: Session state management for UI performance
- **File Validation**: Early rejection of invalid files
- **Error Recovery**: Graceful handling of processing failures

### Scalability Considerations
- **Horizontal Scaling**: Stateless application design
- **Database Optimization**: Indexed queries and efficient schema
- **Memory Management**: Streaming file processing
- **Background Processing**: Async task handling capability

---

## Monitoring & Maintenance

### Logging & Error Tracking
- **Application Logs**: Structured logging with severity levels
- **Error Boundaries**: Safe error handling with user-friendly messages
- **Performance Metrics**: Processing time and throughput monitoring
- **Database Monitoring**: Query performance and connection health

### Backup & Recovery
- **Database Backups**: Automated PostgreSQL backups
- **Configuration Management**: Version-controlled settings
- **Disaster Recovery**: Multi-environment deployment capability

---

## Future Enhancement Opportunities

### Technical Improvements
- **API Layer**: RESTful API for external integrations
- **Mobile App**: React Native mobile application
- **Advanced ML**: Custom ML models for resume scoring
- **Real-time Features**: WebSocket-based live updates

### Business Features
- **Interview Scheduling**: Integrated calendar management
- **Candidate Tracking**: Complete recruitment pipeline
- **Report Templates**: Customizable report generation
- **Multi-tenant**: Support for multiple organizations

---

*This documentation serves as a comprehensive guide to understanding the InnoVantage system architecture and functionality. For technical support or questions, contact the development team.*