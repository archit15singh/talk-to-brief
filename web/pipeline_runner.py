"""
Pipeline Integration Wrapper for Web Interface

This module provides a comprehensive wrapper around the existing AudioBriefPipeline
to enable web-based processing with real-time progress updates via WebSocket
communication. It handles background job execution, status tracking, and error
management for the web interface.

Key Components:
- WebPipelineRunner: Main wrapper class for pipeline integration
- JobManager: Advanced job management with statistics and lifecycle control
- Background threading: Non-blocking pipeline execution
- WebSocket integration: Real-time progress updates to web clients
- Error handling: Comprehensive error tracking and recovery

Features:
- Asynchronous job processing with unique job IDs
- Real-time progress updates via WebSocket events
- Job status tracking (running, completed, failed)
- Error handling and logging with context
- Job cancellation and retry capabilities
- Resource validation and prerequisite checking
- Statistics and performance monitoring

Integration Points:
- Imports existing AudioBriefPipeline from src/pipeline.py
- Emits WebSocket events for frontend consumption
- Manages job lifecycle from creation to completion
- Provides job management API for web server routes

Thread Safety:
- Uses threading.Thread for background execution
- Thread-safe job status updates
- Proper cleanup of completed threads
- Resource management for concurrent jobs

Error Handling:
- Comprehensive exception catching and logging
- Graceful degradation on pipeline failures
- Error context preservation for debugging
- Client-friendly error messages via WebSocket

Author: Audio Brief Generator Team
Version: 1.0.0
"""

import os
import sys
import threading
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

# Add src to Python path to import existing pipeline
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from pipeline import AudioBriefPipeline

logger = logging.getLogger(__name__)

class WebPipelineRunner:
    """
    Wrapper around AudioBriefPipeline for web integration.
    Provides background job execution with WebSocket progress updates.
    """
    
    def __init__(self, socketio=None):
        """
        Initialize the WebPipelineRunner.
        
        Args:
            socketio: Flask-SocketIO instance for emitting progress updates
        """
        self.socketio = socketio
        self.jobs: Dict[str, Dict] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        
    def create_job(self, audio_file: str, output_name: str = None) -> str:
        """
        Create a new processing job with unique ID.
        
        Args:
            audio_file: Path to the audio file to process
            output_name: Optional output name (defaults to audio filename)
            
        Returns:
            str: Unique job ID
        """
        job_id = str(uuid.uuid4())
        
        # Generate output name from audio file if not provided
        if output_name is None:
            output_name = Path(audio_file).stem
        
        job_data = {
            'job_id': job_id,
            'status': 'created',
            'current_step': None,
            'progress': 0.0,
            'audio_file': audio_file,
            'output_name': output_name,
            'brief_file': None,
            'error_message': None,
            'started_at': datetime.now().isoformat(),
            'completed_at': None
        }
        
        self.jobs[job_id] = job_data
        logger.info(f"Created job {job_id} for audio file: {audio_file}")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get the current status of a job.
        
        Args:
            job_id: The job ID to query
            
        Returns:
            Dict containing job status or None if job not found
        """
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str = None, 
                         current_step: str = None, progress: float = None,
                         error_message: str = None, brief_file: str = None):
        """
        Update job status and emit WebSocket event.
        
        Args:
            job_id: The job ID to update
            status: New status ('created', 'running', 'completed', 'failed')
            current_step: Current pipeline step
            progress: Progress as float between 0.0 and 1.0
            error_message: Error message if failed
            brief_file: Path to generated brief file
        """
        if job_id not in self.jobs:
            logger.error(f"Attempted to update non-existent job: {job_id}")
            return
        
        job = self.jobs[job_id]
        
        # Update job data
        if status:
            job['status'] = status
        if current_step:
            job['current_step'] = current_step
        if progress is not None:
            job['progress'] = progress
        if error_message:
            job['error_message'] = error_message
        if brief_file:
            job['brief_file'] = brief_file
        
        # Set completion time for terminal states
        if status in ['completed', 'failed']:
            job['completed_at'] = datetime.now().isoformat()
        
        # Emit WebSocket events if socketio is available
        if self.socketio:
            if status == 'running':
                self.socketio.emit('pipeline_started', job)
            elif current_step or progress is not None:
                self.socketio.emit('pipeline_progress', job)
            elif status == 'completed':
                self.socketio.emit('pipeline_completed', job)
            elif status == 'failed':
                self.socketio.emit('pipeline_error', job)
        
        logger.info(f"Updated job {job_id}: status={status}, step={current_step}, progress={progress}")
    
    def run_pipeline_async(self, job_id: str) -> threading.Thread:
        """
        Run the pipeline asynchronously in a background thread.
        
        Args:
            job_id: The job ID to process
            
        Returns:
            threading.Thread: The background thread running the pipeline
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        def pipeline_worker():
            """Worker function that runs in the background thread."""
            pipeline = None
            current_step = 'initialization'
            
            try:
                logger.info(f"Starting pipeline for job {job_id}")
                self.update_job_status(job_id, status='running', progress=0.0)
                
                # Step 1: Validate prerequisites (5% progress)
                current_step = 'validation'
                self.update_job_status(job_id, current_step=current_step, progress=0.05)
                
                # Create pipeline instance with error handling
                try:
                    pipeline = AudioBriefPipeline(
                        audio_file=job['audio_file'],
                        output_name=job['output_name']
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize pipeline: {str(e)}")
                
                # Validate prerequisites
                try:
                    pipeline.validate_prerequisites()
                except Exception as e:
                    raise RuntimeError(f"Prerequisites validation failed: {str(e)}")
                
                # Step 2: Transcription (30% progress)
                current_step = 'transcription'
                self.update_job_status(job_id, current_step=current_step, progress=0.1)
                
                try:
                    transcription_result = pipeline.run_transcription()
                    if not transcription_result:
                        raise RuntimeError("Transcription returned False - check audio file format and content")
                except Exception as e:
                    raise RuntimeError(f"Transcription failed: {str(e)}")
                
                self.update_job_status(job_id, progress=0.4)
                
                # Step 3: Analysis (60% progress)
                current_step = 'analysis'
                self.update_job_status(job_id, current_step=current_step, progress=0.4)
                
                try:
                    analysis_result = pipeline.run_analysis()
                    if not analysis_result:
                        raise RuntimeError("Analysis returned False - check transcription output")
                except Exception as e:
                    raise RuntimeError(f"Analysis failed: {str(e)}")
                
                self.update_job_status(job_id, progress=0.8)
                
                # Step 4: Merge (100% progress)
                current_step = 'merge'
                self.update_job_status(job_id, current_step=current_step, progress=0.8)
                
                try:
                    merge_result = pipeline.run_merge()
                    if not merge_result:
                        raise RuntimeError("Merge returned False - check analysis outputs")
                except Exception as e:
                    raise RuntimeError(f"Brief generation failed: {str(e)}")
                
                # Verify output file was created
                if not hasattr(pipeline, 'output_path') or not pipeline.output_path:
                    raise RuntimeError("Pipeline completed but no output path available")
                
                if not os.path.exists(pipeline.output_path):
                    raise RuntimeError(f"Pipeline completed but output file not found: {pipeline.output_path}")
                
                # Check output file is not empty
                if os.path.getsize(pipeline.output_path) == 0:
                    raise RuntimeError("Pipeline completed but output file is empty")
                
                # Pipeline completed successfully
                self.update_job_status(
                    job_id, 
                    status='completed', 
                    current_step='completed',
                    progress=1.0,
                    brief_file=pipeline.output_path
                )
                
                logger.info(f"Pipeline completed successfully for job {job_id}, output: {pipeline.output_path}")
                
            except KeyboardInterrupt:
                logger.info(f"Pipeline job {job_id} was interrupted")
                self.update_job_status(
                    job_id,
                    status='failed',
                    current_step=current_step,
                    error_message="Job was cancelled"
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Pipeline failed for job {job_id} at step {current_step}: {error_msg}")
                
                # Provide more specific error messages based on the step
                step_context = {
                    'initialization': 'Failed to set up the processing pipeline',
                    'validation': 'System prerequisites not met',
                    'transcription': 'Failed to convert audio to text',
                    'analysis': 'Failed to analyze the transcribed content',
                    'merge': 'Failed to generate the final brief'
                }
                
                contextual_error = f"{step_context.get(current_step, 'Processing failed')}: {error_msg}"
                
                self.update_job_status(
                    job_id,
                    status='failed',
                    current_step=current_step,
                    error_message=contextual_error
                )
            finally:
                # Clean up thread reference
                if job_id in self.active_threads:
                    del self.active_threads[job_id]
                
                # Log final status
                final_job = self.jobs.get(job_id, {})
                logger.info(f"Pipeline job {job_id} finished with status: {final_job.get('status', 'unknown')}")
        
        # Start the background thread
        thread = threading.Thread(target=pipeline_worker, name=f"pipeline-{job_id}")
        thread.daemon = True
        self.active_threads[job_id] = thread
        thread.start()
        
        return thread
    
    def start_pipeline(self, audio_file: str, output_name: str = None) -> str:
        """
        Convenience method to create a job and start the pipeline.
        
        Args:
            audio_file: Path to the audio file to process
            output_name: Optional output name (defaults to audio filename)
            
        Returns:
            str: The job ID
        """
        job_id = self.create_job(audio_file, output_name)
        self.run_pipeline_async(job_id)
        return job_id
    
    def is_job_running(self, job_id: str) -> bool:
        """
        Check if a job is currently running.
        
        Args:
            job_id: The job ID to check
            
        Returns:
            bool: True if job is running, False otherwise
        """
        return (job_id in self.active_threads and 
                self.active_threads[job_id].is_alive())
    
    def get_active_jobs(self) -> Dict[str, Dict]:
        """
        Get all jobs that are currently active (not completed or failed).
        
        Returns:
            Dict of active jobs
        """
        return {
            job_id: job_data 
            for job_id, job_data in self.jobs.items()
            if job_data['status'] not in ['completed', 'failed']
        }
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Clean up completed jobs older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed jobs
        """
        current_time = datetime.now()
        jobs_to_remove = []
        
        for job_id, job_data in self.jobs.items():
            if job_data['status'] in ['completed', 'failed'] and job_data['completed_at']:
                completed_time = datetime.fromisoformat(job_data['completed_at'])
                age_hours = (current_time - completed_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            logger.info(f"Cleaned up old job: {job_id}")

class JobManager:
    """
    Enhanced job management with additional tracking and error handling capabilities.
    """
    
    def __init__(self, pipeline_runner: WebPipelineRunner):
        """
        Initialize JobManager with a WebPipelineRunner instance.
        
        Args:
            pipeline_runner: WebPipelineRunner instance to manage
        """
        self.runner = pipeline_runner
        self.job_history = []  # Keep history of all jobs for analytics
        
    def get_job_statistics(self) -> Dict:
        """
        Get statistics about job processing.
        
        Returns:
            Dict containing job statistics
        """
        total_jobs = len(self.runner.jobs)
        completed_jobs = sum(1 for job in self.runner.jobs.values() 
                           if job['status'] == 'completed')
        failed_jobs = sum(1 for job in self.runner.jobs.values() 
                         if job['status'] == 'failed')
        running_jobs = sum(1 for job in self.runner.jobs.values() 
                          if job['status'] == 'running')
        
        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'success_rate': completed_jobs / total_jobs if total_jobs > 0 else 0.0
        }
    
    def get_jobs_by_status(self, status: str) -> Dict[str, Dict]:
        """
        Get all jobs with a specific status.
        
        Args:
            status: Status to filter by ('created', 'running', 'completed', 'failed')
            
        Returns:
            Dict of jobs with the specified status
        """
        return {
            job_id: job_data 
            for job_id, job_data in self.runner.jobs.items()
            if job_data['status'] == status
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Attempt to cancel a running job.
        
        Args:
            job_id: The job ID to cancel
            
        Returns:
            bool: True if job was cancelled, False otherwise
        """
        if job_id not in self.runner.jobs:
            logger.warning(f"Attempted to cancel non-existent job: {job_id}")
            return False
        
        job = self.runner.jobs[job_id]
        
        if job['status'] not in ['created', 'running']:
            logger.warning(f"Cannot cancel job {job_id} with status: {job['status']}")
            return False
        
        # Update job status to cancelled
        self.runner.update_job_status(
            job_id,
            status='failed',
            error_message='Job cancelled by user'
        )
        
        # Note: We can't actually stop the thread safely in Python,
        # but we mark it as cancelled so the UI can reflect this
        logger.info(f"Job {job_id} marked as cancelled")
        return True
    
    def retry_failed_job(self, job_id: str) -> Optional[str]:
        """
        Retry a failed job by creating a new job with the same parameters.
        
        Args:
            job_id: The failed job ID to retry
            
        Returns:
            str: New job ID if retry was started, None if job cannot be retried
        """
        if job_id not in self.runner.jobs:
            logger.warning(f"Attempted to retry non-existent job: {job_id}")
            return None
        
        job = self.runner.jobs[job_id]
        
        if job['status'] != 'failed':
            logger.warning(f"Cannot retry job {job_id} with status: {job['status']}")
            return None
        
        # Create new job with same parameters
        new_job_id = self.runner.start_pipeline(
            audio_file=job['audio_file'],
            output_name=job['output_name']
        )
        
        logger.info(f"Retrying failed job {job_id} as new job {new_job_id}")
        return new_job_id
    
    def get_job_duration(self, job_id: str) -> Optional[float]:
        """
        Get the duration of a job in seconds.
        
        Args:
            job_id: The job ID to query
            
        Returns:
            float: Duration in seconds, or None if job not found or not completed
        """
        if job_id not in self.runner.jobs:
            return None
        
        job = self.runner.jobs[job_id]
        
        if not job['started_at']:
            return None
        
        start_time = datetime.fromisoformat(job['started_at'])
        
        if job['completed_at']:
            end_time = datetime.fromisoformat(job['completed_at'])
            return (end_time - start_time).total_seconds()
        elif job['status'] == 'running':
            # Return current duration for running jobs
            current_time = datetime.now()
            return (current_time - start_time).total_seconds()
        
        return None
    
    def archive_old_jobs(self, max_age_days: int = 7) -> int:
        """
        Archive old jobs to job history and remove from active jobs.
        
        Args:
            max_age_days: Maximum age in days for jobs to keep active
            
        Returns:
            int: Number of jobs archived
        """
        current_time = datetime.now()
        jobs_to_archive = []
        
        for job_id, job_data in self.runner.jobs.items():
            if job_data['status'] in ['completed', 'failed']:
                start_time = datetime.fromisoformat(job_data['started_at'])
                age_days = (current_time - start_time).total_seconds() / (24 * 3600)
                
                if age_days > max_age_days:
                    jobs_to_archive.append((job_id, job_data.copy()))
        
        # Move jobs to history and remove from active jobs
        for job_id, job_data in jobs_to_archive:
            self.job_history.append(job_data)
            del self.runner.jobs[job_id]
        
        logger.info(f"Archived {len(jobs_to_archive)} old jobs")
        return len(jobs_to_archive)
    
    def validate_job_prerequisites(self, audio_file: str) -> Dict[str, bool]:
        """
        Validate prerequisites before starting a job.
        
        Args:
            audio_file: Path to audio file to validate
            
        Returns:
            Dict with validation results
        """
        validation_results = {
            'audio_file_exists': False,
            'audio_file_readable': False,
            'audio_file_valid': False,
            'output_directories_writable': False,
            'pipeline_dependencies_available': False,
            'sufficient_disk_space': False
        }
        
        try:
            # Check if audio file exists and is readable
            audio_path = Path(audio_file)
            validation_results['audio_file_exists'] = audio_path.exists()
            
            if validation_results['audio_file_exists']:
                validation_results['audio_file_readable'] = audio_path.is_file() and os.access(audio_file, os.R_OK)
                
                # Check file size and basic validity
                if validation_results['audio_file_readable']:
                    try:
                        file_size = audio_path.stat().st_size
                        # Check minimum and maximum file sizes
                        min_size = 1024  # 1KB
                        max_size = 100 * 1024 * 1024  # 100MB
                        
                        if min_size <= file_size <= max_size:
                            validation_results['audio_file_valid'] = True
                        else:
                            logger.warning(f"Audio file size out of range: {file_size} bytes")
                    except Exception as e:
                        logger.warning(f"Could not validate audio file size: {e}")
            
            # Check if output directories are writable
            output_dirs = ['data/transcripts', 'data/partials', 'data/outputs']
            all_writable = True
            for dir_path in output_dirs:
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    if not os.access(dir_path, os.W_OK):
                        all_writable = False
                        logger.warning(f"Output directory not writable: {dir_path}")
                        break
                except Exception as e:
                    logger.error(f"Cannot create/access output directory {dir_path}: {e}")
                    all_writable = False
                    break
            validation_results['output_directories_writable'] = all_writable
            
            # Check disk space
            try:
                import shutil
                free_space = shutil.disk_usage('.').free
                required_space = 500 * 1024 * 1024  # 500MB minimum
                validation_results['sufficient_disk_space'] = free_space > required_space
                
                if not validation_results['sufficient_disk_space']:
                    logger.warning(f"Insufficient disk space: {free_space / 1024 / 1024:.1f}MB available")
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")
                validation_results['sufficient_disk_space'] = True  # Assume OK if can't check
            
            # Check pipeline dependencies (basic check)
            try:
                # Try to create a pipeline instance to validate dependencies
                test_pipeline = AudioBriefPipeline(audio_file, "test")
                # Don't call validate_prerequisites as it might fail without proper setup
                # Just check if we can create the instance
                validation_results['pipeline_dependencies_available'] = True
            except ImportError as e:
                logger.error(f"Pipeline import failed: {e}")
                validation_results['pipeline_dependencies_available'] = False
            except Exception as e:
                logger.warning(f"Pipeline dependency validation warning: {e}")
                # Still consider available if we can import, even if there are warnings
                validation_results['pipeline_dependencies_available'] = True
                
        except Exception as e:
            logger.error(f"Error during job prerequisite validation: {e}")
        
        return validation_results
    
    def get_estimated_duration(self, audio_file: str) -> Optional[float]:
        """
        Estimate processing duration based on audio file size and historical data.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            float: Estimated duration in seconds, or None if cannot estimate
        """
        try:
            # Get audio file size
            file_size = os.path.getsize(audio_file)
            
            # Simple estimation: roughly 2-3x the audio duration for processing
            # This is a rough estimate and could be improved with historical data
            
            # For now, estimate based on file size (very rough)
            # Assume ~1MB per minute of audio, and ~3 minutes processing per minute of audio
            estimated_audio_minutes = file_size / (1024 * 1024)  # MB
            estimated_processing_seconds = estimated_audio_minutes * 3 * 60  # 3x audio duration
            
            return max(60, estimated_processing_seconds)  # Minimum 1 minute
            
        except Exception as e:
            logger.warning(f"Could not estimate duration for {audio_file}: {e}")
            return None