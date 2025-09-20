import spacy
import re
import json
import os
from collections import Counter
from openai import OpenAI

# Initialize spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Common skills database
TECHNICAL_SKILLS = [
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin',
    'swift', 'typescript', 'scala', 'r', 'matlab', 'sql', 'nosql', 'mongodb', 'postgresql',
    'mysql', 'oracle', 'redis', 'elasticsearch', 'docker', 'kubernetes', 'aws', 'azure',
    'gcp', 'terraform', 'jenkins', 'git', 'github', 'gitlab', 'jira', 'confluence',
    'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring',
    'laravel', 'rails', 'asp.net', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas',
    'numpy', 'matplotlib', 'seaborn', 'tableau', 'power bi', 'excel', 'spark', 'hadoop',
    'kafka', 'rabbitmq', 'microservices', 'restful', 'graphql', 'soap', 'api', 'agile',
    'scrum', 'devops', 'ci/cd', 'machine learning', 'deep learning', 'ai', 'nlp',
    'computer vision', 'data science', 'data analysis', 'statistics', 'blockchain',
    'cybersecurity', 'linux', 'windows', 'macos', 'bash', 'powershell', 'html', 'css',
    'bootstrap', 'sass', 'less', 'webpack', 'npm', 'yarn', 'junit', 'selenium', 'pytest'
]

def extract_skills_from_text(text):
    """Extract technical skills from text"""
    text_lower = text.lower()
    found_skills = []
    
    # Direct skill matching
    for skill in TECHNICAL_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    # Entity recognition for additional skills
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT'] and len(ent.text) > 2:
            potential_skill = ent.text.lower().strip()
            if potential_skill not in [s.lower() for s in found_skills]:
                found_skills.append(ent.text.strip())
    
    return list(set(found_skills))

def extract_experience_years(text):
    """Extract years of experience from text"""
    experience_patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\+?\s*yrs?\s+(?:of\s+)?experience',
        r'experience\s*:\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+in',
        r'over\s+(\d+)\s+years?',
        r'more\s+than\s+(\d+)\s+years?'
    ]
    
    text_lower = text.lower()
    years = []
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        years.extend([int(match) for match in matches])
    
    return max(years) if years else 0

def extract_education_level(text):
    """Extract education level from text"""
    education_levels = {
        'phd': ['ph.d', 'phd', 'doctorate', 'doctoral'],
        'masters': ['master', 'msc', 'ma', 'mba', 'ms', 'm.sc', 'm.a', 'm.s'],
        'bachelors': ['bachelor', 'bsc', 'ba', 'be', 'btech', 'b.sc', 'b.a', 'b.e', 'b.tech'],
        'diploma': ['diploma', 'certificate'],
        'high_school': ['high school', 'secondary', '12th', 'intermediate']
    }
    
    text_lower = text.lower()
    detected_levels = []
    
    for level, keywords in education_levels.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected_levels.append(level)
                break
    
    # Return highest level found
    level_hierarchy = ['phd', 'masters', 'bachelors', 'diploma', 'high_school']
    for level in level_hierarchy:
        if level in detected_levels:
            return level
    
    return 'unknown'

def parse_job_description(job_text):
    """Parse job description to extract requirements"""
    if not openai_client:
        return parse_job_description_rule_based(job_text)
    
    try:
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert HR analyst. Parse the job description and extract key information. Respond with JSON in this exact format: {'required_skills': ['skill1', 'skill2'], 'preferred_skills': ['skill1', 'skill2'], 'experience_required': number, 'education_required': 'level', 'key_responsibilities': ['resp1', 'resp2']}"
                },
                {
                    "role": "user",
                    "content": f"Parse this job description:\n\n{job_text}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
        else:
            result = {}
        return result
    
    except Exception as e:
        print(f"Error parsing job description with AI: {e}")
        return parse_job_description_rule_based(job_text)

def parse_job_description_rule_based(job_text):
    """Rule-based job description parsing as fallback"""
    text_lower = job_text.lower()
    
    # Extract skills
    skills = extract_skills_from_text(job_text)
    
    # Separate required vs preferred
    required_skills = []
    preferred_skills = []
    
    # Look for required/must-have sections
    required_indicators = ['required', 'must have', 'essential', 'mandatory']
    preferred_indicators = ['preferred', 'nice to have', 'plus', 'bonus', 'desirable']
    
    lines = job_text.split('\n')
    current_section = 'unknown'
    
    for line in lines:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in required_indicators):
            current_section = 'required'
        elif any(indicator in line_lower for indicator in preferred_indicators):
            current_section = 'preferred'
        
        # Extract skills from current line
        line_skills = [skill for skill in skills if skill.lower() in line_lower]
        
        if current_section == 'required':
            required_skills.extend(line_skills)
        elif current_section == 'preferred':
            preferred_skills.extend(line_skills)
    
    # If no clear separation, assume all skills are required
    if not required_skills and not preferred_skills:
        required_skills = skills[:len(skills)//2] if len(skills) > 5 else skills
        preferred_skills = skills[len(skills)//2:] if len(skills) > 5 else []
    
    return {
        'required_skills': list(set(required_skills)),
        'preferred_skills': list(set(preferred_skills)),
        'experience_required': extract_experience_years(job_text),
        'education_required': extract_education_level(job_text),
        'key_responsibilities': extract_responsibilities(job_text)
    }

def extract_responsibilities(text):
    """Extract key responsibilities from job description"""
    lines = text.split('\n')
    responsibilities = []
    
    responsibility_indicators = ['responsible for', 'duties', 'responsibilities', 'role includes', 'you will']
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(indicator in line_lower for indicator in responsibility_indicators):
            # Look at next few lines for bullet points
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].strip()
                if next_line and (next_line.startswith('-') or next_line.startswith('•') or next_line.startswith('*')):
                    responsibilities.append(next_line.lstrip('-•* '))
                elif not next_line:
                    break
    
    return responsibilities[:5]  # Return top 5 responsibilities

def analyze_resume_semantic(resume_text, job_requirements):
    """Perform semantic analysis of resume against job requirements using AI"""
    if not openai_client:
        return {
            'semantic_score': 50,  # Default neutral score
            'analysis': 'AI analysis not available - API key not configured',
            'strengths': [],
            'gaps': []
        }
    
    try:
        prompt = f"""
        Analyze this resume against the job requirements and provide a semantic match score.
        
        Job Requirements:
        - Required Skills: {job_requirements.get('required_skills', [])}
        - Preferred Skills: {job_requirements.get('preferred_skills', [])}
        - Experience Required: {job_requirements.get('experience_required', 0)} years
        - Education Required: {job_requirements.get('education_required', 'unknown')}
        
        Resume Text:
        {resume_text[:2000]}
        
        Provide a JSON response with:
        {{
            "semantic_score": number (0-100),
            "analysis": "detailed analysis text",
            "strengths": ["strength1", "strength2"],
            "gaps": ["gap1", "gap2"]
        }}
        """
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume analyzer. Provide detailed semantic analysis comparing resumes to job requirements."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
        else:
            result = {}
        return result
    
    except Exception as e:
        print(f"Error in semantic analysis: {e}")
        return {
            'semantic_score': 50,
            'analysis': f'Error in AI analysis: {str(e)}',
            'strengths': [],
            'gaps': []
        }

def generate_improvement_suggestions(resume_analysis, job_requirements, missing_skills):
    """Generate personalized improvement suggestions for candidates"""
    if not openai_client:
        return [
            "Consider acquiring the missing technical skills identified in the analysis",
            "Highlight relevant project experience more prominently",
            "Add specific metrics and achievements to demonstrate impact"
        ]
    
    try:
        prompt = f"""
        Based on this resume analysis and job requirements, provide 3-5 specific, actionable improvement suggestions for the candidate.
        
        Job Requirements:
        {job_requirements}
        
        Resume Analysis:
        {resume_analysis}
        
        Missing Skills:
        {missing_skills}
        
        Provide suggestions as a JSON array of strings:
        {{"suggestions": ["suggestion1", "suggestion2", "suggestion3"]}}
        """
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a career counselor providing specific, actionable advice to job candidates."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
        else:
            result = {}
        return result.get('suggestions', [])
    
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return [
            "Consider acquiring the missing technical skills",
            "Add more specific project details and achievements",
            "Improve resume format and structure for better readability"
        ]
