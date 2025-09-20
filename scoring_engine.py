import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from nlp_processor import extract_skills_from_text, extract_experience_years, extract_education_level, analyze_resume_semantic, generate_improvement_suggestions
from fuzzywuzzy import fuzz
import json

class ResumeScorer:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
    def calculate_hard_match_score(self, resume_data, job_requirements):
        """Calculate hard match score based on exact keyword and skill matching"""
        scores = {}
        
        # Skills matching
        resume_skills = extract_skills_from_text(resume_data['extracted_text'])
        required_skills = job_requirements.get('required_skills', [])
        preferred_skills = job_requirements.get('preferred_skills', [])
        
        # Exact skill matches
        exact_required_matches = len(set([s.lower() for s in resume_skills]) & set([s.lower() for s in required_skills]))
        exact_preferred_matches = len(set([s.lower() for s in resume_skills]) & set([s.lower() for s in preferred_skills]))
        
        # Fuzzy skill matches (for handling variations)
        fuzzy_required_matches = 0
        fuzzy_preferred_matches = 0
        
        for resume_skill in resume_skills:
            for required_skill in required_skills:
                if fuzz.ratio(resume_skill.lower(), required_skill.lower()) > 80:
                    fuzzy_required_matches += 1
                    break
                    
        for resume_skill in resume_skills:
            for preferred_skill in preferred_skills:
                if fuzz.ratio(resume_skill.lower(), preferred_skill.lower()) > 80:
                    fuzzy_preferred_matches += 1
                    break
        
        # Calculate skill scores
        total_required_skills = len(required_skills) if required_skills else 1
        total_preferred_skills = len(preferred_skills) if preferred_skills else 1
        
        required_skill_score = min(100, ((exact_required_matches + fuzzy_required_matches) / total_required_skills) * 100)
        preferred_skill_score = min(100, ((exact_preferred_matches + fuzzy_preferred_matches) / total_preferred_skills) * 100)
        
        scores['skills'] = {
            'required_score': required_skill_score,
            'preferred_score': preferred_skill_score,
            'matched_required': exact_required_matches + fuzzy_required_matches,
            'matched_preferred': exact_preferred_matches + fuzzy_preferred_matches,
            'total_required': total_required_skills,
            'total_preferred': total_preferred_skills
        }
        
        # Experience matching
        resume_experience = extract_experience_years(resume_data['extracted_text'])
        required_experience = job_requirements.get('experience_required', 0)
        
        if required_experience == 0:
            experience_score = 100
        else:
            experience_ratio = min(1.0, resume_experience / required_experience)
            experience_score = experience_ratio * 100
        
        scores['experience'] = {
            'score': experience_score,
            'resume_years': resume_experience,
            'required_years': required_experience
        }
        
        # Education matching
        resume_education = extract_education_level(resume_data['extracted_text'])
        required_education = job_requirements.get('education_required', 'unknown')
        
        education_hierarchy = {
            'high_school': 1,
            'diploma': 2,
            'bachelors': 3,
            'masters': 4,
            'phd': 5,
            'unknown': 0
        }
        
        resume_edu_level = education_hierarchy.get(resume_education, 0)
        required_edu_level = education_hierarchy.get(required_education, 0)
        
        if required_edu_level == 0:
            education_score = 100
        elif resume_edu_level >= required_edu_level:
            education_score = 100
        else:
            education_score = max(0, (resume_edu_level / required_edu_level) * 100)
        
        scores['education'] = {
            'score': education_score,
            'resume_level': resume_education,
            'required_level': required_education
        }
        
        # Calculate weighted hard match score
        weights = {
            'required_skills': 0.5,
            'preferred_skills': 0.2,
            'experience': 0.2,
            'education': 0.1
        }
        
        total_hard_score = (
            required_skill_score * weights['required_skills'] +
            preferred_skill_score * weights['preferred_skills'] +
            experience_score * weights['experience'] +
            education_score * weights['education']
        )
        
        return total_hard_score, scores
    
    def calculate_semantic_match_score(self, resume_data, job_description_text):
        """Calculate semantic match score using TF-IDF and cosine similarity"""
        try:
            # Prepare texts
            resume_text = resume_data['extracted_text']
            
            # Create TF-IDF vectors
            documents = [resume_text, job_description_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            semantic_score = similarity_matrix[0][1] * 100
            
            return semantic_score
            
        except Exception as e:
            print(f"Error in semantic scoring: {e}")
            return 50  # Default neutral score
    
    def identify_missing_skills(self, resume_data, job_requirements):
        """Identify missing skills and qualifications"""
        resume_skills = [s.lower() for s in extract_skills_from_text(resume_data['extracted_text'])]
        required_skills = [s.lower() for s in job_requirements.get('required_skills', [])]
        preferred_skills = [s.lower() for s in job_requirements.get('preferred_skills', [])]
        
        missing_required = []
        missing_preferred = []
        
        # Check for missing required skills
        for skill in required_skills:
            if not any(fuzz.ratio(skill, resume_skill) > 80 for resume_skill in resume_skills):
                missing_required.append(skill)
        
        # Check for missing preferred skills
        for skill in preferred_skills:
            if not any(fuzz.ratio(skill, resume_skill) > 80 for resume_skill in resume_skills):
                missing_preferred.append(skill)
        
        # Check experience gap
        resume_experience = extract_experience_years(resume_data['extracted_text'])
        required_experience = job_requirements.get('experience_required', 0)
        experience_gap = max(0, required_experience - resume_experience)
        
        # Check education gap
        resume_education = extract_education_level(resume_data['extracted_text'])
        required_education = job_requirements.get('education_required', 'unknown')
        
        education_hierarchy = {
            'high_school': 1, 'diploma': 2, 'bachelors': 3, 'masters': 4, 'phd': 5, 'unknown': 0
        }
        
        resume_edu_level = education_hierarchy.get(resume_education, 0)
        required_edu_level = education_hierarchy.get(required_education, 0)
        education_gap = required_edu_level > resume_edu_level
        
        return {
            'missing_required_skills': missing_required,
            'missing_preferred_skills': missing_preferred,
            'experience_gap_years': experience_gap,
            'education_gap': education_gap,
            'current_education': resume_education,
            'required_education': required_education
        }
    
    def determine_verdict(self, relevance_score):
        """Determine fit verdict based on relevance score"""
        if relevance_score >= 75:
            return "High"
        elif relevance_score >= 50:
            return "Medium"
        else:
            return "Low"
    
    def evaluate_resume(self, resume_data, job_description_text, job_requirements):
        """Complete resume evaluation pipeline"""
        try:
            # Calculate hard match score
            hard_match_score, hard_match_details = self.calculate_hard_match_score(resume_data, job_requirements)
            
            # Calculate semantic match score using TF-IDF
            tfidf_semantic_score = self.calculate_semantic_match_score(resume_data, job_description_text)
            
            # Get AI-powered semantic analysis
            ai_semantic_analysis = analyze_resume_semantic(resume_data['extracted_text'], job_requirements)
            ai_semantic_score = ai_semantic_analysis.get('semantic_score', 50)
            
            # Combine semantic scores (weighted average)
            combined_semantic_score = (tfidf_semantic_score * 0.4) + (ai_semantic_score * 0.6)
            
            # Calculate final relevance score
            weights = {
                'hard_match': 0.6,
                'semantic_match': 0.4
            }
            
            relevance_score = (
                hard_match_score * weights['hard_match'] +
                combined_semantic_score * weights['semantic_match']
            )
            
            # Identify missing skills and gaps
            missing_elements = self.identify_missing_skills(resume_data, job_requirements)
            
            # Determine verdict
            verdict = self.determine_verdict(relevance_score)
            
            # Generate improvement suggestions
            improvement_suggestions = generate_improvement_suggestions(
                ai_semantic_analysis, job_requirements, missing_elements
            )
            
            # Compile evaluation details
            evaluation_details = {
                'hard_match_details': hard_match_details,
                'tfidf_semantic_score': tfidf_semantic_score,
                'ai_semantic_analysis': ai_semantic_analysis,
                'combined_semantic_score': combined_semantic_score,
                'scoring_weights': weights,
                'missing_elements': missing_elements
            }
            
            return {
                'relevance_score': round(relevance_score, 2),
                'hard_match_score': round(hard_match_score, 2),
                'semantic_match_score': round(combined_semantic_score, 2),
                'verdict': verdict,
                'missing_skills': missing_elements['missing_required_skills'] + missing_elements['missing_preferred_skills'],
                'improvement_suggestions': improvement_suggestions,
                'evaluation_details': evaluation_details
            }
            
        except Exception as e:
            print(f"Error in resume evaluation: {e}")
            return {
                'relevance_score': 0,
                'hard_match_score': 0,
                'semantic_match_score': 0,
                'verdict': 'Low',
                'missing_skills': [],
                'improvement_suggestions': ['Error occurred during evaluation'],
                'evaluation_details': {'error': str(e)}
            }
