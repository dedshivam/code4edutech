import sqlite3
import json
from datetime import datetime
import streamlit as st

DATABASE_PATH = "resume_evaluation.db"

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

def init_database():
    """Initialize database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Job descriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT NOT NULL,
            required_skills TEXT,
            preferred_skills TEXT,
            qualifications TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Resumes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            candidate_name TEXT,
            candidate_email TEXT,
            extracted_text TEXT NOT NULL,
            skills TEXT,
            experience TEXT,
            education TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Evaluations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            resume_id INTEGER NOT NULL,
            relevance_score REAL NOT NULL,
            hard_match_score REAL NOT NULL,
            semantic_match_score REAL NOT NULL,
            verdict TEXT NOT NULL,
            missing_skills TEXT,
            improvement_suggestions TEXT,
            evaluation_details TEXT,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_descriptions (id),
            FOREIGN KEY (resume_id) REFERENCES resumes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_job_description(title, company, location, description, required_skills, preferred_skills, qualifications):
    """Save job description to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO job_descriptions (title, company, location, description, required_skills, preferred_skills, qualifications)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, company, location, description, json.dumps(required_skills), json.dumps(preferred_skills), json.dumps(qualifications)))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def save_resume(filename, candidate_name, candidate_email, extracted_text, skills, experience, education):
    """Save resume to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO resumes (filename, candidate_name, candidate_email, extracted_text, skills, experience, education)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (filename, candidate_name, candidate_email, extracted_text, json.dumps(skills), json.dumps(experience), json.dumps(education)))
    
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id

def save_evaluation(job_id, resume_id, relevance_score, hard_match_score, semantic_match_score, verdict, missing_skills, improvement_suggestions, evaluation_details):
    """Save evaluation results to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO evaluations (job_id, resume_id, relevance_score, hard_match_score, semantic_match_score, verdict, missing_skills, improvement_suggestions, evaluation_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (job_id, resume_id, relevance_score, hard_match_score, semantic_match_score, verdict, json.dumps(missing_skills), json.dumps(improvement_suggestions), json.dumps(evaluation_details)))
    
    evaluation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return evaluation_id

def get_job_descriptions():
    """Get all job descriptions"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM job_descriptions ORDER BY created_at DESC')
    jobs = cursor.fetchall()
    conn.close()
    
    return jobs

def get_resumes():
    """Get all resumes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM resumes ORDER BY uploaded_at DESC')
    resumes = cursor.fetchall()
    conn.close()
    
    return resumes

def get_evaluations(job_id=None, min_score=None, verdict=None):
    """Get evaluations with optional filters"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT e.*, j.title as job_title, j.company, r.filename, r.candidate_name, r.candidate_email
        FROM evaluations e
        JOIN job_descriptions j ON e.job_id = j.id
        JOIN resumes r ON e.resume_id = r.id
        WHERE 1=1
    '''
    params = []
    
    if job_id:
        query += ' AND e.job_id = ?'
        params.append(job_id)
    
    if min_score:
        query += ' AND e.relevance_score >= ?'
        params.append(min_score)
    
    if verdict:
        query += ' AND e.verdict = ?'
        params.append(verdict)
    
    query += ' ORDER BY e.relevance_score DESC, e.evaluated_at DESC'
    
    cursor.execute(query, params)
    evaluations = cursor.fetchall()
    conn.close()
    
    return evaluations

def get_job_by_id(job_id):
    """Get job description by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM job_descriptions WHERE id = ?', (job_id,))
    job = cursor.fetchone()
    conn.close()
    
    return job

def get_resume_by_id(resume_id):
    """Get resume by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM resumes WHERE id = ?', (resume_id,))
    resume = cursor.fetchone()
    conn.close()
    
    return resume

def get_evaluation_stats():
    """Get evaluation statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
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
    avg_score = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'total_resumes': total_resumes,
        'total_evaluations': total_evaluations,
        'verdict_distribution': dict(verdict_dist),
        'average_score': avg_score
    }
