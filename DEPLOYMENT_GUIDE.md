# 🚀 Streamlit Cloud Deployment Guide

## Required Dependencies (create requirements.txt)

Create a `requirements.txt` file in your project root with these dependencies:

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
scikit-learn>=1.3.0
bcrypt>=4.0.0
psycopg2-binary>=2.9.0
pymupdf>=1.23.0
python-docx>=0.8.11
fuzzywuzzy>=0.18.0
python-levenshtein>=0.20.0
google-generativeai>=0.3.0
spacy>=3.7.0
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

## Project Structure for Deployment

Your repository should have this structure:
```
resume-evaluation-system/
├── app.py                  (main Streamlit app)
├── requirements.txt        (dependencies)
├── .streamlit/
│   └── config.toml        (configuration)
├── dashboard.py           (dashboard functions)
├── text_extractor.py      (PDF/DOCX processing)
├── nlp_processor.py       (NLP functions)
├── database_postgres.py   (database operations)
├── scoring_engine.py      (evaluation logic)
├── auth.py                (authentication)
├── batch_processor.py     (batch operations)
└── README.md              (project description)
```

## Environment Secrets Configuration

The app requires these secrets:
- `GEMINI_API_KEY`: Your Google Gemini API key
- Database connection settings (PostgreSQL or SQLite fallback)

## Deployment Steps

### 1. Create GitHub Repository
- Create new repository on GitHub
- Push all project files
- Ensure `app.py` is your main Streamlit file

### 2. Setup Streamlit Cloud Account
- Go to https://share.streamlit.io
- Sign up with your GitHub account
- Authorize repository access

### 3. Deploy Application
- Click "Create app"
- Select "Yup, I have an app"
- Choose your GitHub repository
- Set main file path: `app.py`
- Choose custom subdomain
- Click "Deploy"

### 4. Configure Secrets
In Streamlit Cloud app settings, add:
```
[secrets]
GEMINI_API_KEY = "your_actual_gemini_api_key"
```

## Database Configuration for Cloud

The app supports both PostgreSQL and SQLite. For Streamlit Cloud:
- Uses SQLite by default (no additional setup needed)
- PostgreSQL requires cloud database service (like Neon, Supabase)

## Post-Deployment Notes

- App URL: `https://your-subdomain.streamlit.app`
- Auto-updates when you push to GitHub
- Apps sleep after 12 hours of inactivity
- Free tier has resource limitations

## Troubleshooting

Common issues:
1. **Import errors**: Check all dependencies in requirements.txt
2. **Secrets not found**: Verify secrets configuration in app settings
3. **Memory issues**: Optimize large data processing
4. **Slow loading**: spaCy model download takes time on first deploy