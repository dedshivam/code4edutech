import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from text_extractor import process_uploaded_file
from nlp_processor import parse_job_description
from scoring_engine import ResumeScorer
from database import (
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
    elif page == "Analytics":
        render_analytics_page()

def render_main_dashboard():
    """Render main dashboard with overview and recent evaluations"""
    st.header("📊 Dashboard Overview")
    
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
            eval_data.append({
                'Job Title': eval_row[14],  # job_title
                'Company': eval_row[15],    # company
                'Candidate': eval_row[17],  # candidate_name
                'Score': eval_row[3],       # relevance_score
                'Verdict': eval_row[6],     # verdict
                'Date': eval_row[10]        # evaluated_at
            })
        
        df = pd.DataFrame(eval_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No evaluations found. Start by uploading job descriptions and resumes!")

def render_job_upload_page():
    """Render job description upload page"""
    st.header("📝 Upload Job Description")
    
    with st.form("job_upload_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input("Job Title*", placeholder="e.g., Senior Data Scientist")
            company = st.text_input("Company", placeholder="e.g., Tech Corp")
        
        with col2:
            location = st.text_input("Location", placeholder="e.g., Hyderabad, India")
        
        job_description = st.text_area("Job Description*", height=300, 
                                     placeholder="Paste the complete job description here...")
        
        submitted = st.form_submit_button("Parse and Save Job Description")
        
        if submitted:
            if not job_title or not job_description:
                st.error("Please fill in all required fields (marked with *)")
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
                'Job Title': eval_row[14],
                'Company': eval_row[15],
                'Candidate': eval_row[17] or 'Unknown',
                'Email': eval_row[18] or 'Not provided',
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
    fig_bar.update_xaxis(tickangle=45)
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
