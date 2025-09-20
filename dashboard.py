import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from text_extractor import process_uploaded_file, extract_text_from_pdf, extract_text_from_docx
from nlp_processor import parse_job_description
from scoring_engine import ResumeScorer
from database_postgres import (
    save_job_description, save_resume, save_evaluation, 
    get_job_descriptions, get_resumes, get_evaluations, 
    get_job_by_id, get_resume_by_id, get_evaluation_stats
)

def render_dashboard(page):
    """Render the selected dashboard page"""
    
    if page == "Dashboard":
        render_main_dashboard()
    elif page == "Upload Job Description":
        render_job_upload_page()
    elif page == "Upload Resume":
        render_resume_upload_page()
    elif page == "Batch Evaluation":
        render_batch_evaluation_page()
        st.markdown("---")
        from batch_processor import render_enhanced_batch_processing
        render_enhanced_batch_processing()
    elif page == "Analytics":
        render_analytics_page()
        st.markdown("---")
        render_advanced_analytics()
    elif page == "Student Portal":
        render_student_portal()

def render_main_dashboard():
    """Render main dashboard with overview and recent evaluations"""
    # Modern dashboard header
    st.markdown("""<div style='background: linear-gradient(90deg, #667eea, #764ba2); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;'>
        <h1 style='color: white; margin: 0; font-size: 2rem;'>📊 Executive Dashboard</h1>
        <p style='color: white; margin: 0.5rem 0 0 0; opacity: 0.9;'>Real-time insights and analytics</p>
    </div>""", unsafe_allow_html=True)
    
    # Get statistics
    stats = get_evaluation_stats()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", stats['total_jobs'])
    
    with col2:
        st.metric("Total Resumes", stats['total_resumes'])
    
    with col3:
        st.metric("Total Evaluations", stats['total_evaluations'])
    
    with col4:
        st.metric("Avg Score", f"{stats['average_score']:.1f}")
    
    # Verdict distribution chart
    if stats['verdict_distribution']:
        st.subheader("Verdict Distribution")
        verdict_df = pd.DataFrame(list(stats['verdict_distribution'].items()), 
                                columns=['Verdict', 'Count'])
        
        fig = px.pie(verdict_df, values='Count', names='Verdict', 
                    color_discrete_map={'High': '#00ff00', 'Medium': '#ffff00', 'Low': '#ff0000'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent evaluations
    st.subheader("Recent Evaluations")
    recent_evaluations = get_evaluations()[:10]  # Get last 10 evaluations
    
    if recent_evaluations:
        eval_data = []
        for eval_row in recent_evaluations:
            # PostgreSQL query returns: e.*, j.title as job_title, j.company, r.filename, r.candidate_name, r.candidate_email
            # So the columns are: evaluation columns (0-10) + job_title (11) + company (12) + filename (13) + candidate_name (14) + candidate_email (15)
            eval_data.append({
                'Job Title': eval_row[11] if len(eval_row) > 11 else 'Unknown',  # job_title
                'Company': eval_row[12] if len(eval_row) > 12 else 'Unknown',    # company
                'Candidate': eval_row[14] if len(eval_row) > 14 else 'Unknown',  # candidate_name
                'Score': eval_row[3],       # relevance_score
                'Verdict': eval_row[6],     # verdict
                'Date': eval_row[10]        # evaluated_at
            })
        
        df = pd.DataFrame(eval_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No evaluations found. Start by uploading job descriptions and resumes!")

def render_job_upload_page():
    """Render job description upload page with PDF/DOCX import support"""
    st.header("📝 Upload Job Description")
    
    # File upload section
    uploaded_file = st.file_uploader(
        "Upload Job Description File",
        type=['pdf', 'docx', 'doc'],
        help="Supported formats: PDF, DOCX, DOC"
    )
    
    # Initialize variables
    extracted_text = ""
    prefilled_title = ""
    prefilled_company = ""
    prefilled_location = ""
    
    # Process uploaded file if present
    if uploaded_file:
        with st.spinner("Extracting text from document..."):
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name
            file_extension = filename.lower().split('.')[-1]
            
            # Extract text based on file type
            if file_extension == 'pdf':
                from text_extractor import extract_text_from_pdf
                extracted_text = extract_text_from_pdf(file_bytes)
            elif file_extension in ['docx', 'doc']:
                from text_extractor import extract_text_from_docx
                extracted_text = extract_text_from_docx(file_bytes)
            
            if not extracted_text:
                st.error("Could not extract text from the file. Please check the file format and try again.")
                return
            
            # Smart prefilling using regex patterns
            import re
            text_lines = extracted_text.split('\n')
            
            # Extract Job Title - look for first non-empty line ≤ 100 chars
            for line in text_lines[:5]:
                line = line.strip()
                if line and len(line) <= 100 and not any(keyword in line.lower() for keyword in ['company', 'location', 'description', 'requirements']):
                    # Remove common prefixes
                    line = re.sub(r'^(job\s*title\s*[:-]\s*|position\s*[:-]\s*|role\s*[:-]\s*)', '', line, flags=re.IGNORECASE).strip()
                    if line:
                        prefilled_title = line
                        break
            
            # Extract Company - look for patterns
            company_pattern = r'(?:company|organization|employer|firm)\s*[:-]\s*(.+?)(?:\n|$)'
            company_match = re.search(company_pattern, extracted_text, re.IGNORECASE | re.MULTILINE)
            if company_match:
                prefilled_company = company_match.group(1).strip()[:50]  # Limit length
            
            # Extract Location - look for patterns
            location_pattern = r'(?:location|place|office|city)\s*[:-]\s*(.+?)(?:\n|$)'
            location_match = re.search(location_pattern, extracted_text, re.IGNORECASE | re.MULTILINE)
            if location_match:
                prefilled_location = location_match.group(1).strip()[:50]  # Limit length
            
            st.success(f"✅ Text extracted successfully! ({len(extracted_text)} characters)")
    
    # Form with extracted/prefilled data
    with st.form("job_upload_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input("Job Title*", value=prefilled_title, placeholder="e.g., Senior Data Scientist")
            company = st.text_input("Company", value=prefilled_company, placeholder="e.g., Tech Corp")
        
        with col2:
            location = st.text_input("Location", value=prefilled_location, placeholder="e.g., Hyderabad, India")
        
        # Show extracted text in editable area
        job_description = st.text_area(
            "Job Description*", 
            value=extracted_text,
            height=300, 
            placeholder="Upload a PDF/DOCX file above or paste the complete job description here..."
        )
        
        submitted = st.form_submit_button("Parse and Save Job Description")
        
        if submitted:
            if not job_title or not job_description:
                st.error("Please fill in all required fields (marked with *). Make sure to upload a file or enter job description text.")
            else:
                with st.spinner("Parsing job description..."):
                    # Parse job description using NLP
                    parsed_requirements = parse_job_description(job_description)
                    
                    # Save to database
                    job_id = save_job_description(
                        job_title, company, location, job_description,
                        parsed_requirements.get('required_skills', []),
                        parsed_requirements.get('preferred_skills', []),
                        {
                            'experience_required': parsed_requirements.get('experience_required', 0),
                            'education_required': parsed_requirements.get('education_required', 'unknown'),
                            'key_responsibilities': parsed_requirements.get('key_responsibilities', [])
                        }
                    )
                
                st.success(f"✅ Job description saved successfully! (ID: {job_id})")
                
                # Display parsed information
                st.subheader("Parsed Job Requirements")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Required Skills:**")
                    for skill in parsed_requirements.get('required_skills', []):
                        st.write(f"• {skill}")
                
                with col2:
                    st.write("**Preferred Skills:**")
                    for skill in parsed_requirements.get('preferred_skills', []):
                        st.write(f"• {skill}")
                
                st.write(f"**Experience Required:** {parsed_requirements.get('experience_required', 0)} years")
                st.write(f"**Education Required:** {parsed_requirements.get('education_required', 'Not specified')}")

def render_resume_upload_page():
    """Render resume upload page"""
    st.header("📄 Upload Resume")
    
    # Job selection
    jobs = get_job_descriptions()
    if not jobs:
        st.warning("Please upload at least one job description first!")
        return
    
    job_options = {f"{job[1]} - {job[2] or 'Company Not Specified'}": job[0] for job in jobs}
    selected_job = st.selectbox("Select Job Position", options=list(job_options.keys()))
    
    if selected_job:
        job_id = job_options[selected_job]
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Resume", 
            type=['pdf', 'docx', 'doc'],
            help="Supported formats: PDF, DOCX, DOC"
        )
        
        if uploaded_file:
            with st.spinner("Processing resume..."):
                # Extract text and information from resume
                resume_data = process_uploaded_file(uploaded_file)
                
                if resume_data:
                    # Display extracted information
                    st.subheader("Extracted Information")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Contact Information:**")
                        st.write(f"Name: {resume_data['contact_info'].get('name', 'Not found')}")
                        st.write(f"Email: {resume_data['contact_info'].get('email', 'Not found')}")
                        st.write(f"Phone: {resume_data['contact_info'].get('phone', 'Not found')}")
                    
                    with col2:
                        st.write("**File Information:**")
                        st.write(f"Filename: {resume_data['filename']}")
                        st.write(f"Text Length: {len(resume_data['extracted_text'])} characters")
                    
                    # Show extracted text preview
                    with st.expander("Preview Extracted Text"):
                        st.text_area("Extracted Text", resume_data['extracted_text'][:1000] + "..." if len(resume_data['extracted_text']) > 1000 else resume_data['extracted_text'], height=200)
                    
                    # Save and evaluate buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Save Resume", type="primary"):
                            # Save resume to database
                            resume_id = save_resume(
                                resume_data['filename'],
                                resume_data['contact_info'].get('name', ''),
                                resume_data['contact_info'].get('email', ''),
                                resume_data['extracted_text'],
                                resume_data['sections'].get('skills', ''),
                                resume_data['sections'].get('experience', ''),
                                resume_data['sections'].get('education', '')
                            )
                            st.success(f"✅ Resume saved successfully! (ID: {resume_id})")
                    
                    with col2:
                        if st.button("Evaluate Resume", type="secondary"):
                            # Get job details
                            job_details = get_job_by_id(job_id)
                            if job_details:
                                with st.spinner("Evaluating resume..."):
                                    # Prepare job requirements
                                    job_requirements = {
                                        'required_skills': json.loads(job_details[5]) if job_details[5] else [],
                                        'preferred_skills': json.loads(job_details[6]) if job_details[6] else [],
                                        'experience_required': json.loads(job_details[7]).get('experience_required', 0) if job_details[7] else 0,
                                        'education_required': json.loads(job_details[7]).get('education_required', 'unknown') if job_details[7] else 'unknown'
                                    }
                                    
                                    # Initialize scorer and evaluate
                                    scorer = ResumeScorer()
                                    evaluation_result = scorer.evaluate_resume(
                                        resume_data, job_details[3], job_requirements
                                    )
                                    
                                    # Display evaluation results
                                    display_evaluation_results(evaluation_result)

def render_batch_evaluation_page():
    """Render batch evaluation page"""
    st.header("🔄 Batch Evaluation")
    
    # Job selection
    jobs = get_job_descriptions()
    if not jobs:
        st.warning("Please upload at least one job description first!")
        return
    
    job_options = {f"{job[1]} - {job[2] or 'Company Not Specified'}": job[0] for job in jobs}
    selected_job = st.selectbox("Select Job Position for Batch Evaluation", options=list(job_options.keys()))
    
    if selected_job:
        job_id = job_options[selected_job]
        
        # Get all resumes
        resumes = get_resumes()
        if not resumes:
            st.warning("No resumes found. Please upload some resumes first!")
            return
        
        st.write(f"Found {len(resumes)} resumes to evaluate")
        
        if st.button("Start Batch Evaluation", type="primary"):
            # Get job details
            job_details = get_job_by_id(job_id)
            if job_details:
                job_requirements = {
                    'required_skills': json.loads(job_details[5]) if job_details[5] else [],
                    'preferred_skills': json.loads(job_details[6]) if job_details[6] else [],
                    'experience_required': json.loads(job_details[7]).get('experience_required', 0) if job_details[7] else 0,
                    'education_required': json.loads(job_details[7]).get('education_required', 'unknown') if job_details[7] else 'unknown'
                }
                
                # Initialize scorer
                scorer = ResumeScorer()
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                evaluated_count = 0
                total_resumes = len(resumes)
                
                for i, resume in enumerate(resumes):
                    status_text.text(f"Evaluating resume {i+1}/{total_resumes}: {resume[1]}")
                    
                    # Prepare resume data
                    resume_data = {
                        'filename': resume[1],
                        'extracted_text': resume[3],
                        'contact_info': {
                            'name': resume[2],
                            'email': resume[3]
                        },
                        'sections': {
                            'skills': json.loads(resume[4]) if resume[4] else '',
                            'experience': json.loads(resume[5]) if resume[5] else '',
                            'education': json.loads(resume[6]) if resume[6] else ''
                        }
                    }
                    
                    # Evaluate resume
                    evaluation_result = scorer.evaluate_resume(
                        resume_data, job_details[3], job_requirements
                    )
                    
                    # Save evaluation
                    save_evaluation(
                        job_id, resume[0],
                        evaluation_result['relevance_score'],
                        evaluation_result['hard_match_score'],
                        evaluation_result['semantic_match_score'],
                        evaluation_result['verdict'],
                        evaluation_result['missing_skills'],
                        evaluation_result['improvement_suggestions'],
                        evaluation_result['evaluation_details']
                    )
                    
                    evaluated_count += 1
                    progress_bar.progress(evaluated_count / total_resumes)
                
                status_text.text("✅ Batch evaluation completed!")
                st.success(f"Successfully evaluated {evaluated_count} resumes!")
    
    # Display existing evaluations
    st.subheader("Evaluation Results")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_filter = st.selectbox("Filter by Job", ["All"] + list(job_options.keys()))
    
    with col2:
        min_score = st.slider("Minimum Score", 0, 100, 0)
    
    with col3:
        verdict_filter = st.selectbox("Filter by Verdict", ["All", "High", "Medium", "Low"])
    
    # Get filtered evaluations
    job_id_filter = job_options.get(job_filter) if job_filter != "All" else None
    verdict_filter = verdict_filter if verdict_filter != "All" else None
    
    evaluations = get_evaluations(job_id_filter, min_score, verdict_filter)
    
    if evaluations:
        # Create DataFrame for display
        eval_data = []
        for eval_row in evaluations:
            eval_data.append({
                'ID': eval_row[0],
                'Job Title': eval_row[11] if len(eval_row) > 11 else 'Unknown',
                'Company': eval_row[12] if len(eval_row) > 12 else 'Unknown',
                'Candidate': eval_row[14] if len(eval_row) > 14 else 'Unknown',
                'Email': eval_row[15] if len(eval_row) > 15 else 'Not provided',
                'Score': eval_row[3],
                'Verdict': eval_row[6],
                'Date': eval_row[10]
            })
        
        df = pd.DataFrame(eval_data)
        
        # Display results
        st.dataframe(df, use_container_width=True)
        
        # Export functionality
        if st.button("Export Results to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No evaluations found with the selected filters.")

def render_analytics_page():
    """Render analytics and insights page"""
    st.header("📈 Analytics & Insights")
    
    # Get all evaluations
    evaluations = get_evaluations()
    
    if not evaluations:
        st.info("No evaluation data available yet. Complete some evaluations to see analytics.")
        return
    
    # Create DataFrame
    eval_data = []
    for eval_row in evaluations:
        eval_data.append({
            'job_title': eval_row[14],
            'company': eval_row[15],
            'candidate_name': eval_row[17],
            'relevance_score': eval_row[3],
            'hard_match_score': eval_row[4],
            'semantic_match_score': eval_row[5],
            'verdict': eval_row[6],
            'evaluated_at': eval_row[10]
        })
    
    df = pd.DataFrame(eval_data)
    
    # Score distribution
    st.subheader("Score Distribution")
    fig_hist = px.histogram(df, x='relevance_score', nbins=20, title="Distribution of Relevance Scores")
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Score comparison by job
    st.subheader("Average Scores by Job Position")
    job_scores = df.groupby('job_title').agg({
        'relevance_score': 'mean',
        'hard_match_score': 'mean',
        'semantic_match_score': 'mean'
    }).round(2).reset_index()
    
    fig_bar = px.bar(job_scores, x='job_title', y='relevance_score', 
                     title="Average Relevance Score by Job Position")
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Verdict distribution over time
    st.subheader("Verdict Trends Over Time")
    df['date'] = pd.to_datetime(df['evaluated_at']).dt.date
    verdict_trends = df.groupby(['date', 'verdict']).size().reset_index(name='count')
    
    fig_line = px.line(verdict_trends, x='date', y='count', color='verdict',
                       title="Verdict Distribution Over Time")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Summary statistics
    st.subheader("Summary Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Average Relevance Score", f"{df['relevance_score'].mean():.1f}")
        st.metric("Highest Score", f"{df['relevance_score'].max():.1f}")
        st.metric("Total Candidates Evaluated", len(df))
    
    with col2:
        st.metric("Average Hard Match Score", f"{df['hard_match_score'].mean():.1f}")
        st.metric("Average Semantic Score", f"{df['semantic_match_score'].mean():.1f}")
        high_potential = len(df[df['verdict'] == 'High'])
        st.metric("High Potential Candidates", high_potential)

def display_evaluation_results(evaluation_result):
    """Display evaluation results in a formatted way"""
    st.subheader("🎯 Evaluation Results")
    
    # Main scores
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Relevance Score", f"{evaluation_result['relevance_score']}/100")
    
    with col2:
        st.metric("Hard Match Score", f"{evaluation_result['hard_match_score']:.1f}/100")
    
    with col3:
        st.metric("Semantic Score", f"{evaluation_result['semantic_match_score']:.1f}/100")
    
    with col4:
        verdict_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
        st.metric("Verdict", f"{verdict_color.get(evaluation_result['verdict'], '⚪')} {evaluation_result['verdict']}")
    
    # Score breakdown chart
    scores_data = {
        'Score Type': ['Hard Match', 'Semantic Match'],
        'Score': [evaluation_result['hard_match_score'], evaluation_result['semantic_match_score']]
    }
    fig = px.bar(scores_data, x='Score Type', y='Score', title="Score Breakdown")
    fig.update_layout(yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig, use_container_width=True)
    
    # Missing skills
    if evaluation_result['missing_skills']:
        st.subheader("❌ Missing Skills")
        missing_skills_text = ", ".join(evaluation_result['missing_skills'])
        st.error(f"Missing: {missing_skills_text}")
    
    # Improvement suggestions
    if evaluation_result['improvement_suggestions']:
        st.subheader("💡 Improvement Suggestions")
        for i, suggestion in enumerate(evaluation_result['improvement_suggestions'], 1):
            st.write(f"{i}. {suggestion}")
    
    # Detailed analysis
    with st.expander("Detailed Analysis"):
        st.json(evaluation_result['evaluation_details'])

def render_student_portal():
    """Render student portal for viewing evaluation feedback"""
    st.header("🎓 Student Portal")
    st.markdown("View your resume evaluation feedback and improvement suggestions")
    
    # Student email input for finding their evaluations
    st.subheader("Find Your Evaluation Results")
    student_email = st.text_input("Enter your email address:", placeholder="your.email@example.com")
    
    if student_email:
        # Get evaluations for this student
        all_evaluations = get_evaluations()
        student_evaluations = []
        
        for eval_row in all_evaluations:
            # Check if email matches (index 15 for candidate_email)
            if len(eval_row) > 15 and eval_row[15] and eval_row[15].lower() == student_email.lower():
                student_evaluations.append(eval_row)
        
        if student_evaluations:
            st.success(f"Found {len(student_evaluations)} evaluation(s) for {student_email}")
            
            for i, eval_row in enumerate(student_evaluations, 1):
                with st.expander(f"Evaluation #{i} - {eval_row[11] if len(eval_row) > 11 else 'Unknown Job'} at {eval_row[12] if len(eval_row) > 12 else 'Unknown Company'}"):
                    
                    # Basic evaluation info
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        score = eval_row[3]
                        verdict = eval_row[6]
                        verdict_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(verdict, "⚪")
                        st.metric("Overall Score", f"{score}/100")
                        st.write(f"**Verdict:** {verdict_color} {verdict}")
                    
                    with col2:
                        st.metric("Technical Match", f"{eval_row[4]:.1f}/100")
                        st.metric("Semantic Match", f"{eval_row[5]:.1f}/100")
                    
                    with col3:
                        st.write(f"**Job:** {eval_row[11] if len(eval_row) > 11 else 'Unknown'}")
                        st.write(f"**Company:** {eval_row[12] if len(eval_row) > 12 else 'Unknown'}")
                        st.write(f"**Evaluated:** {eval_row[10]}")
                    
                    # Missing skills
                    if eval_row[7]:  # missing_skills
                        try:
                            missing_skills = json.loads(eval_row[7])
                            if missing_skills:
                                st.subheader("📋 Skills to Develop")
                                skills_text = ", ".join(missing_skills)
                                st.error(f"Consider learning: {skills_text}")
                        except:
                            pass
                    
                    # Improvement suggestions
                    if eval_row[8]:  # improvement_suggestions
                        try:
                            suggestions = json.loads(eval_row[8])
                            if suggestions:
                                st.subheader("💡 Improvement Suggestions")
                                for j, suggestion in enumerate(suggestions, 1):
                                    st.write(f"{j}. {suggestion}")
                        except:
                            pass
                    
                    # Detailed analysis
                    if eval_row[9]:  # evaluation_details
                        with st.expander("📊 Detailed Analysis"):
                            try:
                                details = json.loads(eval_row[9])
                                
                                # Skills analysis
                                if 'hard_match_details' in details and 'skills' in details['hard_match_details']:
                                    skills_info = details['hard_match_details']['skills']
                                    st.write("**Skills Match Analysis:**")
                                    st.write(f"• Required skills matched: {skills_info.get('matched_required', 0)}/{skills_info.get('total_required', 0)}")
                                    st.write(f"• Preferred skills matched: {skills_info.get('matched_preferred', 0)}/{skills_info.get('total_preferred', 0)}")
                                
                                # Experience analysis
                                if 'hard_match_details' in details and 'experience' in details['hard_match_details']:
                                    exp_info = details['hard_match_details']['experience']
                                    st.write("**Experience Analysis:**")
                                    st.write(f"• Your experience: {exp_info.get('resume_years', 0)} years")
                                    st.write(f"• Required experience: {exp_info.get('required_years', 0)} years")
                                
                                # Education analysis
                                if 'hard_match_details' in details and 'education' in details['hard_match_details']:
                                    edu_info = details['hard_match_details']['education']
                                    st.write("**Education Analysis:**")
                                    st.write(f"• Your education: {edu_info.get('resume_level', 'Unknown').title()}")
                                    st.write(f"• Required education: {edu_info.get('required_level', 'Unknown').title()}")
                                
                            except:
                                st.write("Detailed analysis data not available")
        else:
            st.info("No evaluations found for this email address. Make sure you've submitted your resume for evaluation.")
    
    # General improvement tips
    st.markdown("---")
    st.subheader("💼 General Career Tips")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **Technical Skills:**
        - Keep your technical skills updated with industry trends
        - Add specific project examples that demonstrate your skills
        - Include metrics and achievements in your experience
        - Consider getting relevant certifications
        """)
    
    with tips_col2:
        st.markdown("""
        **Resume Tips:**
        - Use clear, professional formatting
        - Quantify your achievements with numbers
        - Tailor your resume for each job application
        - Keep it concise but comprehensive
        """)
    
    # Contact information
    st.markdown("---")
    st.info("💬 **Need help?** Contact your placement coordinator for personalized guidance on improving your profile.")

def render_advanced_analytics():
    """Render advanced analytics and insights"""
    st.header("📈 Advanced Analytics & Insights")
    st.markdown("Deep insights and reporting for placement team decision making")
    
    # Get all data
    evaluations = get_evaluations()
    jobs = get_job_descriptions()
    resumes = get_resumes()
    
    if not evaluations:
        st.info("No evaluation data available yet. Complete some evaluations to see advanced analytics.")
        return
    
    # Create comprehensive DataFrame
    eval_data = []
    for eval_row in evaluations:
        eval_data.append({
            'evaluation_id': eval_row[0],
            'job_id': eval_row[1],
            'resume_id': eval_row[2],
            'relevance_score': eval_row[3],
            'hard_match_score': eval_row[4],
            'semantic_match_score': eval_row[5],
            'verdict': eval_row[6],
            'job_title': eval_row[11] if len(eval_row) > 11 else 'Unknown',
            'company': eval_row[12] if len(eval_row) > 12 else 'Unknown',
            'candidate_name': eval_row[14] if len(eval_row) > 14 else 'Unknown',
            'candidate_email': eval_row[15] if len(eval_row) > 15 else 'Unknown',
            'evaluated_at': eval_row[10]
        })
    
    df = pd.DataFrame(eval_data)
    
    # Advanced metrics dashboard
    st.subheader("🎯 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        avg_score = df['relevance_score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}", f"{avg_score-70:.1f}" if avg_score > 70 else f"+{70-avg_score:.1f}")
    
    with col2:
        high_quality = len(df[df['relevance_score'] >= 80])
        st.metric("High Quality Candidates", high_quality, f"{(high_quality/len(df)*100):.1f}%")
    
    with col3:
        avg_hard_match = df['hard_match_score'].mean()
        st.metric("Avg Technical Match", f"{avg_hard_match:.1f}")
    
    with col4:
        avg_semantic = df['semantic_match_score'].mean()
        st.metric("Avg Semantic Match", f"{avg_semantic:.1f}")
    
    with col5:
        total_evaluations = len(df)
        st.metric("Total Evaluations", total_evaluations)
    
    # Performance by location analysis
    st.subheader("🌍 Performance by Location")
    if 'location' in df.columns:
        location_stats = df.groupby('location').agg({
            'relevance_score': ['mean', 'count'],
            'verdict': lambda x: (x == 'High').sum()
        }).round(2)
        
        location_stats.columns = ['Avg Score', 'Total Evaluations', 'High Potential']
        st.dataframe(location_stats, use_container_width=True)
    
    # Advanced score distribution analysis
    st.subheader("📊 Score Distribution Analysis")
    
    # Score distribution by verdict
    fig_box = px.box(df, x='verdict', y='relevance_score', 
                     title="Score Distribution by Verdict",
                     color='verdict',
                     color_discrete_map={'High': '#28a745', 'Medium': '#ffc107', 'Low': '#dc3545'})
    st.plotly_chart(fig_box, use_container_width=True)
    
    # Time series analysis
    st.subheader("📅 Evaluation Trends Over Time")
    df['date'] = pd.to_datetime(df['evaluated_at']).dt.date
    
    # Daily evaluation counts and average scores
    daily_stats = df.groupby('date').agg({
        'relevance_score': ['mean', 'count'],
        'verdict': lambda x: (x == 'High').sum()
    }).reset_index()
    
    daily_stats.columns = ['date', 'avg_score', 'total_evals', 'high_potential']
    
    fig_time = px.line(daily_stats, x='date', y='avg_score', 
                       title="Average Scores Over Time",
                       markers=True)
    fig_time.add_scatter(x=daily_stats['date'], y=daily_stats['total_evals'], 
                        mode='lines+markers', name='Daily Evaluations', yaxis='y2')
    
    fig_time.update_layout(yaxis2=dict(title="Number of Evaluations", overlaying='y', side='right'))
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Job performance comparison
    st.subheader("💼 Job Position Analysis")
    
    job_performance = df.groupby('job_title').agg({
        'relevance_score': ['mean', 'std', 'count'],
        'hard_match_score': 'mean',
        'semantic_match_score': 'mean',
        'verdict': lambda x: (x == 'High').sum()
    }).round(2)
    
    job_performance.columns = ['Avg Score', 'Score StdDev', 'Total Candidates', 'Avg Hard Match', 'Avg Semantic', 'High Potential']
    job_performance = job_performance.sort_values(by='Avg Score', ascending=False)
    
    st.dataframe(job_performance, use_container_width=True)
    
    # Candidate quality heatmap
    st.subheader("🔥 Quality Heatmap")
    
    # Create score bins
    df['score_bin'] = pd.cut(df['relevance_score'], bins=[0, 50, 70, 85, 100], 
                            labels=['Poor (0-50)', 'Fair (50-70)', 'Good (70-85)', 'Excellent (85-100)'])
    
    heatmap_data = df.groupby(['job_title', 'score_bin']).size().unstack(fill_value=0)
    
    fig_heatmap = px.imshow(heatmap_data.values, 
                           x=heatmap_data.columns, 
                           y=heatmap_data.index,
                           title="Candidate Quality Distribution by Job Position",
                           aspect="auto")
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Skills gap analysis
    st.subheader("🎯 Skills Gap Analysis")
    
    try:
        # Analyze missing skills from evaluations
        missing_skills_data = []
        for eval_row in evaluations:
            if eval_row[7]:  # missing_skills column
                try:
                    missing_skills = json.loads(eval_row[7])
                    job_title = eval_row[11] if len(eval_row) > 11 else 'Unknown'
                    for skill in missing_skills:
                        missing_skills_data.append({
                            'job_title': job_title,
                            'skill': skill,
                            'evaluation_id': eval_row[0]
                        })
                except:
                    pass
        
        if missing_skills_data:
            skills_df = pd.DataFrame(missing_skills_data)
            
            # Most commonly missing skills
            top_missing = skills_df['skill'].value_counts().head(10)
            
            fig_skills = px.bar(x=top_missing.index, y=top_missing.values,
                               title="Top 10 Most Commonly Missing Skills",
                               labels={'x': 'Skills', 'y': 'Frequency'})
            st.plotly_chart(fig_skills, use_container_width=True)
            
            # Skills gap by job position
            skills_by_job = skills_df.groupby(['job_title', 'skill']).size().reset_index(name='count')
            skills_pivot = skills_by_job.pivot(index='job_title', columns='skill', values='count').fillna(0)
            
            st.subheader("Missing Skills by Job Position")
            st.dataframe(skills_pivot, use_container_width=True)
    
    except Exception as e:
        st.info("Skills gap analysis not available - no sufficient data")
    
    # Recommendations engine
    st.subheader("🤖 AI Recommendations")
    
    recommendations = []
    
    # Score-based recommendations
    if avg_score < 65:
        recommendations.append("📉 **Low Average Score Alert**: Consider revising job requirements or improving candidate screening process.")
    
    if df['hard_match_score'].mean() < df['semantic_match_score'].mean() - 10:
        recommendations.append("🔧 **Skills Mismatch**: Candidates have good overall profiles but lack specific technical skills. Consider skills training programs.")
    
    if len(df[df['verdict'] == 'High']) / len(df) < 0.2:
        recommendations.append("🎯 **Low High-Potential Rate**: Only {:.1%} of candidates are high-potential. Review sourcing strategies.".format(len(df[df['verdict'] == 'High']) / len(df)))
    
    # Time-based recommendations
    if len(daily_stats) > 7:
        recent_avg = daily_stats.tail(3)['avg_score'].mean()
        older_avg = daily_stats.iloc[:-3]['avg_score'].mean()
        
        if recent_avg < older_avg - 5:
            recommendations.append("📉 **Declining Quality Trend**: Recent candidates show lower scores. Review current sourcing channels.")
        elif recent_avg > older_avg + 5:
            recommendations.append("📈 **Improving Quality Trend**: Recent candidates show higher scores. Current sourcing strategy is working well.")
    
    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.success("✅ **Performance is Good**: No major issues detected in current evaluation patterns.")
    
    # Export comprehensive report
    st.subheader("📄 Export Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Analytics Report"):
            report_data = {
                'summary_stats': {
                    'total_evaluations': len(df),
                    'average_score': avg_score,
                    'high_potential_rate': len(df[df['verdict'] == 'High']) / len(df),
                    'avg_hard_match': avg_hard_match,
                    'avg_semantic_match': avg_semantic
                },
                'job_performance': job_performance.to_dict(),
                'daily_trends': daily_stats.to_dict('records'),
                'recommendations': recommendations
            }
            
            report_json = json.dumps(report_data, indent=2, default=str)
            st.download_button(
                label="📥 Download Analytics Report (JSON)",
                data=report_json,
                file_name=f"analytics_report_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📋 Export Evaluation Data"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Raw Data (CSV)",
                data=csv_data,
                file_name=f"evaluation_data_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🎯 Export High Potential List"):
            high_potential = df[df['verdict'] == 'High'][['candidate_name', 'candidate_email', 'job_title', 'company', 'relevance_score']].sort_values(by='relevance_score', ascending=False)
            high_potential_csv = high_potential.to_csv(index=False)
            st.download_button(
                label="📥 Download High Potential (CSV)",
                data=high_potential_csv,
                file_name=f"high_potential_candidates_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
