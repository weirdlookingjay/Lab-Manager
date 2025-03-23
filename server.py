import os
import sys
import json
import time
import uuid
import shutil
import re
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Optional
import logging
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy import MetaData, Table, Column, String, LargeBinary, DateTime

from werkzeug.security import generate_password_hash
from pydantic import BaseModel
from UserMigrations import User

import requests
from urllib.parse import urljoin

# Add Django settings import
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UsersProject.settings')
django.setup()

from notifications.utils import store_scanned_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurations from environment
CSV_FILE = os.getenv('CSV_FILE', 'Lab-Computers.csv')
DESTINATION_ROOT = os.getenv('DESTINATION_ROOT', r"D:\Client_Files")
LOG_FILE = os.getenv('LOG_FILE', 'copy_log.txt')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'infotech')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'gidget003')
USER_PROFILES = ["Client"]

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

logger.info(f"Connecting to database...")

# Create SQLAlchemy engine with SSL configuration
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require"
        },
        pool_pre_ping=True,  # Add connection health check
        pool_recycle=3600,   # Recycle connections every hour
    )
    
    # Test the connection with proper SQL query
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).scalar()
        logger.info("Successfully connected to database")
except Exception as e:
    logger.error(f"Failed to connect to database: {str(e)}")
    raise

# Create APScheduler jobs table if it doesn't exist
metadata = MetaData()
apscheduler_jobs = Table(
    'apscheduler_jobs', metadata,
    Column('id', String(191), primary_key=True),
    Column('next_run_time', DateTime(timezone=True), index=True),
    Column('job_state', LargeBinary, nullable=False)
)

# Create tables
try:
    logger.info("Creating database tables if they don't exist...")
    metadata.create_all(engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating tables: {str(e)}")
    raise

# Configure job stores for APScheduler
jobstores = {
    'default': SQLAlchemyJobStore(
        url=DATABASE_URL,
        engine=engine,  # Pass the existing engine
        tablename='apscheduler_jobs'  # Explicitly set table name
    )
}

# Configure thread pool
executors = {
    'default': ThreadPoolExecutor(20)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

# Initialize scheduler with PostgreSQL job store
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='America/New_York'  # Set default timezone
)

try:
    logger.info("Starting APScheduler...")
    scheduler.start()
    
    # Verify scheduler is running
    if scheduler.running:
        logger.info("APScheduler started successfully")
        
        # List any existing jobs
        jobs = scheduler.get_jobs()
        if jobs:
            logger.info("Current scheduled jobs:")
            for job in jobs:
                logger.info(f"- {job.id}: Next run at {job.next_run_time}")
        else:
            logger.info("No jobs currently scheduled")
    else:
        raise RuntimeError("Scheduler did not start properly")
        
except Exception as e:
    logger.error(f"Error starting scheduler: {str(e)}")
    raise

def log_message(message):
    """Write log message to log file and print it."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    with open(LOG_FILE, "a") as log:
        log.write(formatted_message + "\n")

def sanitize_filename(filename):
    """Remove only square brackets [ ] from filenames while keeping the extension."""
    name, ext = os.path.splitext(filename)
    clean_name = re.sub(r'[\[\]]', '', name)  # Remove only square brackets
    return clean_name + ext

def authenticate_remote(computer_ip):
    """Authenticate to the remote computer using net use."""
    command = f'net use \\\\{computer_ip}\\C$ /user:{ADMIN_USERNAME} {ADMIN_PASSWORD}'
    result = os.system(command)
    if result == 0:
        log_message(f"[{computer_ip}] Authentication successful")
    else:
        log_message(f"[{computer_ip}] Authentication failed")

def copy_files(computer_ip, computer_label):
    """Copy PDF files from remote computer's Desktop, Documents, and Downloads folders to web storage."""
    folders_to_copy = ["Desktop", "Documents", "Downloads"]
    base_path = f"\\\\{computer_ip}\\C$\\Users"
    
    # Create a temporary directory for staging files
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'pdf_staging', computer_label)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        for user in USER_PROFILES:
            for folder in folders_to_copy:
                source_folder = os.path.join(base_path, user, folder)
                if not os.path.exists(source_folder):
                    log_message(f"[{computer_label}] Skipping {source_folder} (not found)")
                    continue

                try:
                    for file in os.listdir(source_folder):
                        if file.lower().endswith(".pdf"):
                            source_file = os.path.join(source_folder, file)
                            sanitized_name = sanitize_filename(file)
                            temp_file = os.path.join(temp_dir, sanitized_name)

                            # First copy to temp directory
                            shutil.copy2(source_file, temp_file)
                            
                            # Then store in web storage using the notifications.utils function
                            attachment = store_scanned_pdf(temp_file, computer_label)
                            if attachment:
                                log_message(f"[{computer_label}] Successfully stored {file} in web storage")
                            else:
                                log_message(f"[{computer_label}] Failed to store {file} in web storage")

                except Exception as e:
                    log_message(f"[{computer_label}] Error copying from {source_folder}: {str(e)}")
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            log_message(f"Error cleaning up temp directory: {str(e)}")

def cleanup_job(event):
    """Remove the job from database after it completes."""
    try:
        job_id = event.job_id
        logger.info(f"Job {job_id} completed, removing from database...")
        scheduler.remove_job(job_id)
        logger.info(f"Job {job_id} removed successfully")
    except Exception as e:
        logger.error(f"Error removing job {event.job_id}: {str(e)}")

# Track current scan operation
current_scan_operation = {
    'is_running': False,
    'start_time': None,
    'processed_computers': 0,
    'total_computers': 0
}

async def run_script():
    """Main function to read CSV and process each computer."""
    global current_scan_operation
    
    log_message("Script execution started")
    current_scan_operation['is_running'] = True
    current_scan_operation['start_time'] = datetime.now()
    
    try:
        computers = pd.read_csv(CSV_FILE)
        current_scan_operation['total_computers'] = len(computers)
        current_scan_operation['processed_computers'] = 0
        
        for _, row in computers.iterrows():
            computer_ip = row["IPAddress"]
            computer_label = row["ComputerLabel"]

            log_message(f"Processing {computer_ip} ({computer_label})...")
            authenticate_remote(computer_ip)  # Authenticate first
            copy_files(computer_ip, computer_label)
            
            current_scan_operation['processed_computers'] += 1

    except Exception as e:
        log_message(f"Critical error: {e}")
    finally:
        current_scan_operation['is_running'] = False
        current_scan_operation['start_time'] = None
        log_message("Script execution completed")

@app.post("/run")
async def run_script_now(background_tasks: BackgroundTasks):
    """Run the script immediately."""
    background_tasks.add_task(run_script)
    return {"message": "Script execution started in background"}

@app.post("/schedule")
async def schedule_script(hour: int, minute: int, name: Optional[str] = "daily_backup"):
    """Schedule script execution at a specific time (24-hour format)."""
    logger.info(f"Received schedule request - hour: {hour}, minute: {minute}, name: {name}")

    # Validate input
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        error_msg = f"Invalid time values: hour={hour}, minute={minute}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=400, 
            detail=error_msg
        )

    try:
        # Verify scheduler is running
        if not scheduler.running:
            error_msg = "Scheduler is not running"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # Verify database connection
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1")).scalar()
                logger.info("Database connection verified")
        except Exception as db_error:
            error_msg = f"Database connection error: {str(db_error)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # Check if job exists
        existing_job = scheduler.get_job(name)
        if existing_job:
            logger.info(f"Found existing job '{name}', removing it")
            scheduler.remove_job(name)

        logger.info(f"Creating new job '{name}' for {hour:02d}:{minute:02d}")
        
        # Add new job with timezone-aware scheduling and cleanup listener
        job = scheduler.add_job(
            run_script,
            'cron',
            hour=hour,
            minute=minute,
            id=name,
            name=f"Backup at {hour:02d}:{minute:02d}",
            replace_existing=True,
            misfire_grace_time=None,  # Always run, even if misfired
            timezone='America/New_York'  # Explicitly set to Eastern Time
        )
        
        # Add listener for job completion
        scheduler.add_listener(cleanup_job, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Verify job was added
        added_job = scheduler.get_job(name)
        if not added_job:
            error_msg = f"Job '{name}' was not added successfully"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        next_run = added_job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z") if added_job.next_run_time else "Not scheduled"
        logger.info(f"Job '{name}' scheduled successfully. Next run at: {next_run}")
        
        # List all current jobs for verification
        all_jobs = scheduler.get_jobs()
        logger.info("Current scheduled jobs:")
        for j in all_jobs:
            logger.info(f"- {j.id}: Next run at {j.next_run_time}")
        
        return {
            "message": "Job scheduled successfully",
            "job_id": name,
            "next_run": next_run,
            "schedule": {
                "hour": hour,
                "minute": minute,
                "timezone": "America/New_York"
            }
        }
        
    except Exception as e:
        error_msg = f"Error scheduling job: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/schedules")
async def get_schedules():
    """Get all scheduled jobs."""
    try:
        logger.info("Fetching all scheduled jobs...")
        jobs = scheduler.get_jobs()
        
        schedules = [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
            }
            for job in jobs
        ]
        
        logger.info(f"Found {len(schedules)} scheduled jobs")
        return {
            "schedules": schedules
        }
    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch schedules: {str(e)}"
        )

@app.delete("/schedule/{job_id}")
async def delete_schedule(job_id: str):
    """Delete a scheduled job."""
    logger.info(f"Attempting to delete job: {job_id}")
    try:
        job = scheduler.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Schedule '{job_id}' not found"
            )
            
        scheduler.remove_job(job_id)
        logger.info(f"Successfully deleted job: {job_id}")
        return {
            "message": f"Schedule '{job_id}' deleted successfully",
            "job_id": job_id
        }
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete schedule: {str(e)}"
        )

@app.get("/logs")
async def get_logs():
    """Retrieve log contents."""
    if not os.path.exists(LOG_FILE):
        return {"logs": "No logs found"}
    with open(LOG_FILE, "r") as log:
        return {"logs": log.read()}

# Add startup verification endpoint
@app.get("/status")
async def get_status():
    """Get the current status of the scheduler and any scheduled jobs."""
    try:
        jobs = scheduler.get_jobs()
        return {
            "scheduler_running": scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z") if job.next_run_time else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_scan_status():
    """Get the current status of the scan operation."""
    try:
        # Get scheduler status
        scheduler_status = scheduler.state if scheduler else 'stopped'
        
        # Get latest job if any
        jobs = scheduler.get_jobs() if scheduler else []
        next_run = None
        if jobs:
            next_job = min(jobs, key=lambda x: x.next_run_time if x.next_run_time else datetime.max)
            next_run = next_job.next_run_time

        # Get current operation status
        if current_scan_operation['is_running']:
            status = 'running'
            message = f"Scanning in progress. Processed {current_scan_operation['processed_computers']} of {current_scan_operation['total_computers']} computers."
        elif next_run:
            status = 'scheduled'
            message = f"Next scan scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            status = 'idle'
            message = "No scan in progress or scheduled"

        # Get the schedule information
        schedule_info = {'type': 'none', 'minutes': 0, 'seconds': 0}
        if jobs:
            # Get the schedule from the job
            job = next_job
            if hasattr(job.trigger, 'interval'):
                schedule_info = {
                    'type': 'interval',
                    'minutes': job.trigger.interval.total_seconds() // 60,
                    'seconds': job.trigger.interval.total_seconds() % 60
                }
            elif hasattr(job.trigger, 'hour'):
                # For cron jobs, calculate time until next run
                if next_run:
                    time_until = next_run - datetime.now()
                    schedule_info = {
                        'type': 'daily',
                        'minutes': time_until.total_seconds() // 60,
                        'seconds': time_until.total_seconds() % 60
                    }

        return {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'schedule': schedule_info
        }
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        return {
            'status': 'error',
            'message': f"Error getting scan status: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'schedule': {'type': 'none', 'minutes': 0, 'seconds': 0}
        }

@app.get("/api/scan/status")
async def get_scan_status_endpoint():
    return await get_scan_status()

# Computer models for your existing table structure
class Computer(BaseModel):
    ip_address: str
    label: str
    last_seen: Optional[datetime]
    is_online: bool = False
    model: Optional[str] = None
    last_transfer: Optional[datetime] = None
    total_transfers: int = 0
    successful_transfers: int = 0
    failed_transfers: int = 0
    total_bytes_transferred: int = 0
    os_version: Optional[str] = None
    user_profile: Optional[str] = None

# Computer routes
@app.get("/api/computers")
async def get_computers():
    """Get all computers from the database."""
    try:
        query = text("""
            SELECT 
                ip_address,
                label,
                last_seen,
                is_online,
                model,
                last_transfer,
                total_transfers,
                successful_transfers,
                failed_transfers,
                total_bytes_transferred,
                os_version,
                user_profile
            FROM user_management_computer 
            ORDER BY label ASC
        """)
        with engine.connect() as conn:
            result = conn.execute(query)
            computer_list = []
            for row in result:
                computer = dict(row._mapping)
                # Convert datetime objects to ISO format strings
                if computer['last_seen']:
                    computer['last_seen'] = computer['last_seen'].isoformat()
                if computer['last_transfer']:
                    computer['last_transfer'] = computer['last_transfer'].isoformat()
                # Ensure numeric fields are integers
                computer['total_transfers'] = int(computer.get('total_transfers', 0) or 0)
                computer['successful_transfers'] = int(computer.get('successful_transfers', 0) or 0)
                computer['failed_transfers'] = int(computer.get('failed_transfers', 0) or 0)
                computer['total_bytes_transferred'] = int(computer.get('total_bytes_transferred', 0) or 0)
                # Ensure boolean fields are proper booleans
                computer['is_online'] = bool(computer.get('is_online', False))
                computer_list.append(computer)
            return computer_list
    except Exception as e:
        logger.error(f"Error fetching computers: {str(e)}")
        return {"error": str(e)}

@app.get("/api/computers/{ip_address}")
async def get_computer(ip_address: str):
    """Get a specific computer by IP address."""
    try:
        query = text("""
            SELECT * FROM user_management_computer 
            WHERE ip_address = :ip_address
        """)
        with engine.connect() as conn:
            result = conn.execute(query, {"ip_address": ip_address})
            computer = result.fetchone()
            if not computer:
                raise HTTPException(status_code=404, detail="Computer not found")
            return dict(computer)
    except Exception as e:
        logger.error(f"Error fetching computer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/computers/{ip_address}")
async def update_computer_status(ip_address: str):
    """Update computer's online status and last seen time."""
    try:
        query = text("""
            UPDATE user_management_computer 
            SET last_seen = NOW(), is_online = TRUE
            WHERE ip_address = :ip_address
            RETURNING *
        """)
        with engine.connect() as conn:
            result = conn.execute(query, {"ip_address": ip_address})
            conn.commit()
            updated = result.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Computer not found")
            return dict(updated)
    except Exception as e:
        logger.error(f"Error updating computer status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/computers/{ip_address}/transfer")
async def update_transfer_stats(
    ip_address: str,
    successful: bool,
    bytes_transferred: int
):
    """Update computer's file transfer statistics."""
    try:
        query = text("""
            UPDATE user_management_computer 
            SET 
                last_transfer = NOW(),
                total_transfers = total_transfers + 1,
                successful_transfers = successful_transfers + :success,
                failed_transfers = failed_transfers + :failed,
                total_bytes_transferred = total_bytes_transferred + :bytes
            WHERE ip_address = :ip_address
            RETURNING *
        """)
        with engine.connect() as conn:
            result = conn.execute(query, {
                "ip_address": ip_address,
                "success": 1 if successful else 0,
                "failed": 0 if successful else 1,
                "bytes": bytes_transferred
            })
            conn.commit()
            updated = result.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Computer not found")
            return dict(updated)
    except Exception as e:
        logger.error(f"Error updating transfer stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str


@app.post("/api/users")
async def create_user(user: UserCreate):
    """Create a new user."""
    hashed_password = generate_password_hash(user.password)

    new_user = User(username=user.username, password=hashed_password, email=user.email, role=user.role)

    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, password, email, role) VALUES (:username, :password, :email, :role)"),
                {"username": new_user.username, "password": new_user.password, "email": new_user.email, "role": new_user.role}
            )
            conn.commit()
        return {"message": "User created successfully"}
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=400, detail="User creation failed")


@app.get("/api/users/id/{user_id}")
async def get_user(user_id: int):
    """Retrieve a user by ID."""
    logger.info(f"Attempting to retrieve user with ID: {user_id}")
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT username, email, role FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            user = result.fetchone()
            logger.info(f"Query result: {user}")
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return {
                "username": user['username'],
                "email": user['email'],
                "role": user['role']
            }
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user")


@app.put("/api/users/{username}/role")
async def update_user_role(username: str, role: str):
    """Update a user's role."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET role = :role WHERE username = :username"),
                {"role": role, "username": username}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            conn.commit()
            return {"message": "User role updated successfully"}
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user role")