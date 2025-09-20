# Overview

The AI-Powered Resume Evaluation System is an automated solution designed for Innomatics Research Labs to streamline their resume screening process across multiple locations (Hyderabad, Bangalore, Pune, and Delhi NCR). The system evaluates resumes against job descriptions using a hybrid approach that combines rule-based keyword matching with AI-powered semantic analysis to generate relevance scores (0-100) and provide actionable feedback to both placement teams and students.

The application serves two main user groups: placement team members who require authentication to access advanced features, and students who can use a simplified portal without login requirements. The system processes PDF and DOCX resume files, extracts and analyzes text content, and provides comprehensive evaluation reports with missing skills identification and improvement suggestions.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application with responsive design
- **Page Structure**: Multi-page navigation with sidebar menu supporting Student Portal, Dashboard, Job Description Upload, Resume Upload, Batch Evaluation, and Analytics
- **Authentication Flow**: Role-based access with unauthenticated student portal and authenticated staff portal
- **State Management**: Streamlit session state for user authentication and application data persistence

## Backend Architecture
- **Application Layer**: Python-based modular architecture with specialized processors
- **Text Processing Pipeline**: 
  - Text extraction from PDF (PyMuPDF) and DOCX (python-docx) files
  - NLP processing using spaCy for entity recognition and skill extraction
  - Semantic analysis integration with OpenAI GPT models
- **Scoring Engine**: Hybrid evaluation system combining hard keyword matching with soft semantic similarity using TF-IDF vectorization and cosine similarity
- **Batch Processing**: Concurrent resume processing using ThreadPoolExecutor for scalable bulk evaluations

## Data Storage Solutions
- **Primary Database**: PostgreSQL with connection pooling and environment-variable configuration
- **Schema Design**: 
  - User management with bcrypt password hashing and session tokens
  - Job descriptions with structured skill requirements and qualifications
  - Resume storage with extracted text and metadata
  - Evaluation results with detailed scoring breakdowns
- **Fallback Support**: SQLite database implementation for local development

## Authentication and Authorization
- **Password Security**: bcrypt hashing with salt for secure password storage
- **Session Management**: Token-based sessions with configurable expiration (24-hour default)
- **Role-based Access**: Placement team authentication required for administrative features
- **Student Access**: Open access portal for resume submission and basic evaluation features

## Processing Architecture
- **Skill Extraction**: Comprehensive technical skills database with fuzzy matching capabilities
- **Experience Analysis**: Pattern recognition for extracting years of experience and education levels
- **Scoring Algorithm**: Weighted combination of required skills (70%), preferred skills (20%), and experience matching (10%)
- **Analytics Engine**: Statistical analysis and visualization using Plotly for evaluation trends and insights

# External Dependencies

## AI and Machine Learning Services
- **OpenAI API**: GPT model integration for semantic resume analysis and improvement suggestions
- **spaCy**: Natural language processing library for entity recognition and text analysis
- **scikit-learn**: Machine learning utilities for TF-IDF vectorization and similarity calculations
- **FuzzyWuzzy**: Fuzzy string matching for flexible skill and keyword matching

## Database and Storage
- **PostgreSQL**: Primary production database with full ACID compliance
- **psycopg2**: PostgreSQL adapter for Python database connectivity
- **SQLite**: Alternative database option for development and testing environments

## Document Processing
- **PyMuPDF (fitz)**: PDF text extraction and processing capabilities
- **python-docx**: Microsoft Word document text extraction
- **Streamlit**: Web application framework for user interface and file upload handling

## Data Analysis and Visualization
- **pandas**: Data manipulation and analysis for evaluation results
- **numpy**: Numerical computing support for scoring algorithms
- **Plotly**: Interactive data visualization for analytics dashboard
- **matplotlib/seaborn**: Statistical plotting and chart generation

## Security and Utilities
- **bcrypt**: Password hashing and verification for user authentication
- **secrets**: Cryptographically secure token generation for sessions
- **concurrent.futures**: Thread pool execution for batch processing optimization

## Environment Configuration
- **Environment Variables**: Database connection strings, API keys, and configuration parameters
- **Streamlit Secrets**: Secure credential management for deployed applications