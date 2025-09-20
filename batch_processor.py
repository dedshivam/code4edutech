import streamlit as st
import pandas as pd
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from text_extractor import process_uploaded_file
from nlp_processor import parse_job_description
from scoring_engine import ResumeScorer
from database_postgres import save_resume, save_evaluation, get_job_by_id

class BatchProcessor:
    def __init__(self, max_workers=4):
        """Initialize batch processor with configurable concurrency"""
        self.max_workers = max_workers
        self.scorer = ResumeScorer()
    
    def process_resume_batch(self, uploaded_files, job_id, progress_callback=None):
        """Process multiple resume files in batch with concurrent processing"""
        total_files = len(uploaded_files)
        results = []
        
        # Get job details once
        job_details = get_job_by_id(job_id)
        if not job_details:
            return {"error": "Job not found"}
        
        # Handle both string and already parsed data
        required_skills = job_details[5] if job_details[5] else []
        if isinstance(required_skills, str):
            required_skills = json.loads(required_skills)
        
        preferred_skills = job_details[6] if job_details[6] else []
        if isinstance(preferred_skills, str):
            preferred_skills = json.loads(preferred_skills)
        
        qualifications = job_details[7] if job_details[7] else {}
        if isinstance(qualifications, str):
            qualifications = json.loads(qualifications)
        
        job_requirements = {
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'experience_required': qualifications.get('experience_required', 0) if isinstance(qualifications, dict) else 0,
            'education_required': qualifications.get('education_required', 'unknown') if isinstance(qualifications, dict) else 'unknown'
        }
        
        # Process resumes concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {}
            for i, uploaded_file in enumerate(uploaded_files):
                future = executor.submit(
                    self._process_single_resume, 
                    uploaded_file, job_id, job_details, job_requirements
                )
                future_to_file[future] = (i, uploaded_file.name)
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_file):
                file_index, filename = future_to_file[future]
                
                try:
                    result = future.result()
                    results.append({
                        'index': file_index,
                        'filename': filename,
                        'status': 'success',
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'index': file_index,
                        'filename': filename,
                        'status': 'error',
                        'error': str(e)
                    })
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_files, filename)
        
        # Sort results by original index
        results.sort(key=lambda x: x['index'])
        
        return {
            'total_processed': total_files,
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'results': results
        }
    
    def _process_single_resume(self, uploaded_file, job_id, job_details, job_requirements):
        """Process a single resume file"""
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Extract text and information from resume
        resume_data = process_uploaded_file(uploaded_file)
        if not resume_data:
            raise Exception("Failed to extract text from resume")
        
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
        
        if not resume_id:
            raise Exception("Failed to save resume to database")
        
        # Evaluate resume
        evaluation_result = self.scorer.evaluate_resume(
            resume_data, job_details[3], job_requirements
        )
        
        # Save evaluation
        evaluation_id = save_evaluation(
            job_id, resume_id,
            evaluation_result['relevance_score'],
            evaluation_result['hard_match_score'],
            evaluation_result['semantic_match_score'],
            evaluation_result['verdict'],
            evaluation_result['missing_skills'],
            evaluation_result['improvement_suggestions'],
            evaluation_result['evaluation_details']
        )
        
        if not evaluation_id:
            raise Exception("Failed to save evaluation to database")
        
        return {
            'resume_id': resume_id,
            'evaluation_id': evaluation_id,
            'score': evaluation_result['relevance_score'],
            'verdict': evaluation_result['verdict'],
            'candidate_name': resume_data['contact_info'].get('name', 'Unknown'),
            'candidate_email': resume_data['contact_info'].get('email', '')
        }
    
    def generate_batch_report(self, batch_results, job_title):
        """Generate a comprehensive batch processing report"""
        if 'results' not in batch_results:
            return None
        
        successful_results = [r for r in batch_results['results'] if r['status'] == 'success']
        
        if not successful_results:
            return None
        
        # Create DataFrame for analysis
        data = []
        for result in successful_results:
            if 'result' in result:
                data.append({
                    'Filename': result['filename'],
                    'Candidate': result['result'].get('candidate_name', 'Unknown'),
                    'Email': result['result'].get('candidate_email', ''),
                    'Score': result['result'].get('score', 0),
                    'Verdict': result['result'].get('verdict', 'Unknown')
                })
        
        df = pd.DataFrame(data)
        
        # Generate summary statistics
        summary = {
            'total_processed': batch_results['total_processed'],
            'successful': batch_results['successful'],
            'failed': batch_results['failed'],
            'average_score': df['Score'].mean() if not df.empty else 0,
            'high_potential': len(df[df['Verdict'] == 'High']) if not df.empty else 0,
            'medium_potential': len(df[df['Verdict'] == 'Medium']) if not df.empty else 0,
            'low_potential': len(df[df['Verdict'] == 'Low']) if not df.empty else 0,
            'top_candidates': df.nlargest(5, 'Score').to_dict('records') if not df.empty else []
        }
        
        return {
            'summary': summary,
            'dataframe': df,
            'job_title': job_title
        }

def render_enhanced_batch_processing():
    """Render enhanced batch processing interface"""
    st.header("🚀 Enhanced Batch Processing")
    st.markdown("Process thousands of resumes efficiently with parallel processing")
    
    # Job selection
    from database_postgres import get_job_descriptions
    jobs = get_job_descriptions()
    if not jobs:
        st.warning("Please upload at least one job description first!")
        return
    
    job_options = {f"{job[1]} - {job[2] or 'Company Not Specified'}": job[0] for job in jobs}
    selected_job = st.selectbox("Select Job Position for Batch Evaluation", options=list(job_options.keys()))
    
    if not selected_job:
        return
    
    job_id = job_options[selected_job]
    job_title = selected_job.split(' - ')[0]
    
    # Batch processing configuration
    st.subheader("⚙️ Processing Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        max_workers = st.slider("Concurrent Workers", min_value=1, max_value=8, value=4, 
                               help="Higher values process faster but use more resources")
    
    with col2:
        chunk_size = st.slider("Batch Chunk Size", min_value=10, max_value=100, value=25,
                              help="Number of resumes to process in each batch")
    
    # File upload
    st.subheader("📄 Upload Resume Files")
    uploaded_files = st.file_uploader(
        "Upload Multiple Resume Files", 
        type=['pdf', 'docx', 'doc'],
        accept_multiple_files=True,
        help="Upload multiple PDF or DOCX files for batch processing"
    )
    
    if uploaded_files:
        st.success(f"📁 {len(uploaded_files)} files selected for processing")
        
        # File validation
        valid_files = []
        invalid_files = []
        
        for file in uploaded_files:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                invalid_files.append(f"{file.name} (too large: {file.size/1024/1024:.1f}MB)")
            else:
                valid_files.append(file)
        
        if invalid_files:
            st.error(f"❌ Invalid files: {', '.join(invalid_files)}")
        
        if valid_files:
            st.info(f"✅ {len(valid_files)} valid files ready for processing")
            
            # Processing options
            st.subheader("🎯 Processing Options")
            
            col1, col2 = st.columns(2)
            with col1:
                save_intermediate = st.checkbox("Save intermediate results", value=True,
                                              help="Save progress even if processing is interrupted")
            
            with col2:
                generate_report = st.checkbox("Generate detailed report", value=True,
                                            help="Create comprehensive analysis report after processing")
            
            # Start processing button
            if st.button("🚀 Start Batch Processing", type="primary"):
                processor = BatchProcessor(max_workers=max_workers)
                
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.empty()
                
                start_time = time.time()
                
                def update_progress(completed, total, current_file):
                    progress = completed / total
                    progress_bar.progress(progress)
                    elapsed = time.time() - start_time
                    remaining = (elapsed / completed * (total - completed)) if completed > 0 else 0
                    
                    status_text.text(
                        f"Processing {completed}/{total} files | "
                        f"Current: {current_file} | "
                        f"Elapsed: {elapsed:.1f}s | "
                        f"ETA: {remaining:.1f}s"
                    )
                
                try:
                    # Process files in chunks if there are many
                    if len(valid_files) > chunk_size:
                        st.info(f"Processing {len(valid_files)} files in chunks of {chunk_size}")
                        
                        all_results = []
                        for i in range(0, len(valid_files), chunk_size):
                            chunk = valid_files[i:i + chunk_size]
                            st.write(f"Processing chunk {i//chunk_size + 1}/{(len(valid_files)-1)//chunk_size + 1}")
                            
                            chunk_results = processor.process_resume_batch(
                                chunk, job_id, update_progress
                            )
                            all_results.extend(chunk_results.get('results', []))
                        
                        # Combine chunk results
                        batch_results = {
                            'total_processed': len(valid_files),
                            'successful': len([r for r in all_results if r['status'] == 'success']),
                            'failed': len([r for r in all_results if r['status'] == 'error']),
                            'results': all_results
                        }
                    else:
                        # Process all files at once
                        batch_results = processor.process_resume_batch(
                            valid_files, job_id, update_progress
                        )
                    
                    # Processing completed
                    total_time = time.time() - start_time
                    status_text.text(f"✅ Processing completed in {total_time:.1f} seconds")
                    
                    # Display results
                    st.success(f"🎉 Batch processing completed!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Processed", batch_results['total_processed'])
                    with col2:
                        st.metric("Successful", batch_results['successful'])
                    with col3:
                        st.metric("Failed", batch_results['failed'])
                    
                    # Generate and display report
                    if generate_report and int(batch_results.get('successful', 0)) > 0:
                        st.subheader("📊 Batch Processing Report")
                        
                        report = processor.generate_batch_report(batch_results, job_title)
                        if report:
                            # Summary metrics
                            summary = report['summary']
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Average Score", f"{summary['average_score']:.1f}")
                            with col2:
                                st.metric("High Potential", summary['high_potential'])
                            with col3:
                                st.metric("Medium Potential", summary['medium_potential'])
                            with col4:
                                st.metric("Low Potential", summary['low_potential'])
                            
                            # Top candidates
                            if summary['top_candidates']:
                                st.subheader("🏆 Top Candidates")
                                top_df = pd.DataFrame(summary['top_candidates'])
                                st.dataframe(top_df, use_container_width=True)
                            
                            # Full results
                            st.subheader("📋 All Results")
                            st.dataframe(report['dataframe'], use_container_width=True)
                            
                            # Download report
                            csv = report['dataframe'].to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results CSV",
                                data=csv,
                                file_name=f"batch_evaluation_{job_title}_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    
                    # Error details
                    failed_results = [r for r in batch_results.get('results', []) if isinstance(r, dict) and r.get('status') == 'error']
                    if failed_results:
                        with st.expander(f"❌ Failed Files ({len(failed_results)})"):
                            for failed in failed_results:
                                st.error(f"**{failed.get('filename', 'Unknown')}**: {failed.get('error', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"❌ Batch processing failed: {str(e)}")
                    status_text.text("Processing failed")
    
    # Usage tips
    st.markdown("---")
    st.subheader("💡 Performance Tips")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **Optimization:**
        - Use 4-6 concurrent workers for best performance
        - Process files in chunks of 25-50 for large batches
        - Ensure stable internet connection for AI features
        - Use smaller file sizes when possible
        """)
    
    with tips_col2:
        st.markdown("""
        **Best Practices:**
        - Process during off-peak hours for large batches
        - Validate file formats before uploading
        - Keep backup of original files
        - Monitor system resources during processing
        """)