import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
import streamlit as st

# Get PostgreSQL connection details from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")

def get_connection():
    """Get PostgreSQL database connection"""
    try:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)
        else:
            return psycopg2.connect(
                host=PGHOST,
                port=PGPORT,
                user=PGUSER,
                password=PGPASSWORD,
                database=PGDATABASE
            )
    except Exception as e:
        # Log the detailed error server-side but show generic message to users
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize PostgreSQL database with required tables"""
    conn = get_connection()
    if not conn:
        return False
        
    cursor = conn.cursor()
    
    try:
        # Job descriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT NOT NULL,
                required_skills JSONB,
                preferred_skills JSONB,
                qualifications JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Resumes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                candidate_name TEXT,
                candidate_email TEXT,
                extracted_text TEXT NOT NULL,
                skills JSONB,
                experience TEXT,
                education TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Evaluations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id SERIAL PRIMARY KEY,
                job_id INTEGER NOT NULL,
                resume_id INTEGER NOT NULL,
                relevance_score REAL NOT NULL,
                hard_match_score REAL NOT NULL,
                semantic_match_score REAL NOT NULL,
                verdict TEXT NOT NULL,
                missing_skills JSONB,
                improvement_suggestions JSONB,
                evaluation_details JSONB,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_descriptions (id),
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
        ''')
        
        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                location TEXT,
                role TEXT DEFAULT 'placement_team',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        return True
        
    except Exception as e:
        # Log the detailed error server-side but show generic message to users
        print(f"Database initialization error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def save_job_description(title, company, location, description, required_skills, preferred_skills, qualifications):
    """Save job description to PostgreSQL database"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO job_descriptions (title, company, location, description, required_skills, preferred_skills, qualifications)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        ''', (title, company, location, description, json.dumps(required_skills), json.dumps(preferred_skills), json.dumps(qualifications)))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        return job_id
        
    except Exception as e:
        print(f"Error saving job description: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def save_resume(filename, candidate_name, candidate_email, extracted_text, skills, experience, education):
    """Save resume to PostgreSQL database"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO resumes (filename, candidate_name, candidate_email, extracted_text, skills, experience, education)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        ''', (filename, candidate_name, candidate_email, extracted_text, json.dumps(skills), json.dumps(experience), json.dumps(education)))
        
        resume_id = cursor.fetchone()[0]
        conn.commit()
        return resume_id
        
    except Exception as e:
        print(f"Error saving resume: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def save_evaluation(job_id, resume_id, relevance_score, hard_match_score, semantic_match_score, verdict, missing_skills, improvement_suggestions, evaluation_details):
    """Save evaluation results to PostgreSQL database"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO evaluations (job_id, resume_id, relevance_score, hard_match_score, semantic_match_score, verdict, missing_skills, improvement_suggestions, evaluation_details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        ''', (job_id, resume_id, relevance_score, hard_match_score, semantic_match_score, verdict, json.dumps(missing_skills), json.dumps(improvement_suggestions), json.dumps(evaluation_details)))
        
        evaluation_id = cursor.fetchone()[0]
        conn.commit()
        return evaluation_id
        
    except Exception as e:
        print(f"Error saving evaluation: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_job_descriptions():
    """Get all job descriptions"""
    conn = get_connection()
    if not conn:
        return []
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM job_descriptions ORDER BY created_at DESC')
        jobs = cursor.fetchall()
        return jobs
        
    except Exception as e:
        print(f"Error fetching job descriptions: {e}")
        st.error("Unable to load job descriptions. Please refresh the page.")
        return []
    finally:
        cursor.close()
        conn.close()

def get_resumes():
    """Get all resumes"""
    conn = get_connection()
    if not conn:
        return []
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM resumes ORDER BY uploaded_at DESC')
        resumes = cursor.fetchall()
        return resumes
        
    except Exception as e:
        print(f"Error fetching resumes: {e}")
        st.error("Unable to load resumes. Please refresh the page.")
        return []
    finally:
        cursor.close()
        conn.close()

def get_evaluations(job_id=None, min_score=None, verdict=None):
    """Get evaluations with optional filters"""
    conn = get_connection()
    if not conn:
        return []
        
    cursor = conn.cursor()
    
    try:
        query = '''
            SELECT e.*, j.title as job_title, j.company, r.filename, r.candidate_name, r.candidate_email
            FROM evaluations e
            JOIN job_descriptions j ON e.job_id = j.id
            JOIN resumes r ON e.resume_id = r.id
            WHERE 1=1
        '''
        params = []
        
        if job_id:
            query += ' AND e.job_id = %s'
            params.append(job_id)
        
        if min_score:
            query += ' AND e.relevance_score >= %s'
            params.append(min_score)
        
        if verdict:
            query += ' AND e.verdict = %s'
            params.append(verdict)
        
        query += ' ORDER BY e.relevance_score DESC, e.evaluated_at DESC'
        
        cursor.execute(query, params)
        evaluations = cursor.fetchall()
        return evaluations
        
    except Exception as e:
        print(f"Error fetching evaluations: {e}")
        st.error("Unable to load evaluations. Please refresh the page.")
        return []
    finally:
        cursor.close()
        conn.close()

def get_job_by_id(job_id):
    """Get job description by ID"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM job_descriptions WHERE id = %s', (job_id,))
        job = cursor.fetchone()
        return job
        
    except Exception as e:
        print(f"Error fetching job: {e}")
        st.error("Unable to load job information. Please try again.")
        return None
    finally:
        cursor.close()
        conn.close()

def get_resume_by_id(resume_id):
    """Get resume by ID"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM resumes WHERE id = %s', (resume_id,))
        resume = cursor.fetchone()
        return resume
        
    except Exception as e:
        print(f"Error fetching resume: {e}")
        st.error("Unable to load resume information. Please try again.")
        return None
    finally:
        cursor.close()
        conn.close()

def get_evaluation_stats():
    """Get evaluation statistics"""
    conn = get_connection()
    if not conn:
        return {'total_jobs': 0, 'total_resumes': 0, 'total_evaluations': 0, 'verdict_distribution': {}, 'average_score': 0}
        
    cursor = conn.cursor()
    
    try:
        # Total counts
        cursor.execute('SELECT COUNT(*) FROM job_descriptions')
        total_jobs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM resumes')
        total_resumes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM evaluations')
        total_evaluations = cursor.fetchone()[0]
        
        # Verdict distribution
        cursor.execute('SELECT verdict, COUNT(*) FROM evaluations GROUP BY verdict')
        verdict_dist = cursor.fetchall()
        
        # Average scores
        cursor.execute('SELECT AVG(relevance_score) FROM evaluations')
        avg_score_result = cursor.fetchone()[0]
        avg_score = float(avg_score_result) if avg_score_result else 0
        
        return {
            'total_jobs': total_jobs,
            'total_resumes': total_resumes,
            'total_evaluations': total_evaluations,
            'verdict_distribution': dict(verdict_dist),
            'average_score': avg_score
        }
        
    except Exception as e:
        print(f"Error fetching evaluation stats: {e}")
        st.error("Unable to load statistics. Please refresh the page.")
        return {'total_jobs': 0, 'total_resumes': 0, 'total_evaluations': 0, 'verdict_distribution': {}, 'average_score': 0}
    finally:
        cursor.close()
        conn.close()

# User authentication functions
def save_user(username, email, password_hash, location, role='placement_team'):
    """Save user to database"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, location, role)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        ''', (username, email, password_hash, location, role))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
        
    except Exception as e:
        print(f"Error saving user: {e}")
        st.error("Registration failed. Please try again.")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username):
    """Get user by username"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE username = %s AND is_active = TRUE', (username,))
        user = cursor.fetchone()
        return user
        
    except Exception as e:
        print(f"Error fetching user: {e}")
        st.error("Login failed. Please check your credentials.")
        return None
    finally:
        cursor.close()
        conn.close()

def save_session(user_id, session_token, expires_at):
    """Save user session"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s) RETURNING id
        ''', (user_id, session_token, expires_at))
        
        session_id = cursor.fetchone()[0]
        conn.commit()
        return session_id
        
    except Exception as e:
        print(f"Error saving session: {e}")
        st.error("Session creation failed. Please try logging in again.")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_session(session_token):
    """Get session by token"""
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT s.*, u.username, u.email, u.location, u.role 
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = TRUE
        ''', (session_token,))
        session = cursor.fetchone()
        return session
        
    except Exception as e:
        print(f"Error fetching session: {e}")
        st.error("Session verification failed. Please log in again.")
        return None
    finally:
        cursor.close()
        conn.close()