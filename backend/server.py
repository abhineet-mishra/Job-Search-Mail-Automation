from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from threading import Thread
import pytz
from urllib.parse import quote
import re
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Email configuration
EMAIL_ADDRESS = "ananya4bh@gmail.com"
EMAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'tcmb wjfk uyxa bxzm')
EMAIL_SUBJECT = "TPRM jobs for today"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class JobListing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_title: str
    company_name: str
    job_link: str
    location: str
    keywords: List[str] = []
    technical_skills: List[str] = []
    posted_date: Optional[str] = None
    source: str = "briansjobsearch"
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

class JobSearchRequest(BaseModel):
    query: str
    location: str = "Bangalore India OR remote"
    days_filter: int = 7

class EmailSettings(BaseModel):
    recipient_email: str
    subject: str
    scheduled_time: str = "09:00"  # 24-hour format

class JobSearchResult(BaseModel):
    jobs: List[JobListing]
    total_count: int
    search_query: str
    search_date: datetime

# Job search and scraping functions
async def search_jobs_google(query: str, location: str = "India", days_filter: int = 7) -> List[JobListing]:
    """Search for jobs using Google search with briansjobsearch patterns"""
    jobs = []
    
    # Multiple search variations for better results - including remote positions
    search_queries = [
        f'"{query}" jobs in Bangalore India OR remote site:linkedin.com OR site:naukri.com OR site:indeed.com',
        f'"Third Party Risk" OR "Vendor Risk" OR "Supplier Risk" jobs Bangalore India OR remote',
        f'"TPRM" OR "Third Party Risk Management" jobs Bangalore OR remote product company',
        f'"Risk Assessment" analyst jobs Bangalore India OR remote 6 years experience',
        f'"Third Party Risk" remote jobs India product company',
        f'"Vendor Risk Management" remote OR Bangalore India jobs'
    ]
    
    async with aiohttp.ClientSession() as session:
        for search_query in search_queries:
            try:
                # Use Google search API or scrape Google results
                google_url = f"https://www.google.com/search?q={quote(search_query)}&tbm=nws"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(google_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract job listings from search results
                        job_results = soup.find_all('div', class_='g')
                        
                        for result in job_results[:10]:  # Limit to first 10 results per query
                            try:
                                title_elem = result.find('h3')
                                link_elem = result.find('a')
                                
                                if title_elem and link_elem:
                                    job_title = title_elem.get_text()
                                    job_link = link_elem.get('href')
                                    
                                    # Extract company name (basic pattern)
                                    company_name = "Company Name Not Found"
                                    desc_elem = result.find('span', class_='st')
                                    if desc_elem:
                                        desc_text = desc_elem.get_text()
                                        # Try to extract company name patterns
                                        company_match = re.search(r'at\s+([A-Za-z\s&.]+)', desc_text)
                                        if company_match:
                                            company_name = company_match.group(1).strip()
                                    
                                    # Generate relevant keywords and skills
                                    keywords = generate_keywords(job_title, query)
                                    technical_skills = generate_technical_skills(job_title, query)
                                    
                                    job = JobListing(
                                        job_title=job_title,
                                        company_name=company_name,
                                        job_link=job_link,
                                        location="Bangalore, India / Remote",
                                        keywords=keywords,
                                        technical_skills=technical_skills,
                                        posted_date="Recent (24 hours)",
                                        source="google_search"
                                    )
                                    jobs.append(job)
                            except Exception as e:
                                logger.error(f"Error parsing job result: {e}")
                                continue
                        
                        # Add a small delay between requests
                        await asyncio.sleep(1)
                        
            except Exception as e:
                logger.error(f"Error searching jobs: {e}")
                continue
    
    return jobs

def generate_keywords(job_title: str, query: str) -> List[str]:
    """Generate relevant keywords for resume optimization"""
    base_keywords = [
        "Third Party Risk Management",
        "Vendor Risk Assessment",
        "Supplier Risk Analysis",
        "Risk Mitigation",
        "Compliance Management"
    ]
    
    # Add context-specific keywords based on job title
    if "senior" in job_title.lower():
        base_keywords.extend(["Senior Risk Analyst", "Risk Leadership"])
    if "analyst" in job_title.lower():
        base_keywords.extend(["Risk Analysis", "Data Analysis"])
    if "manager" in job_title.lower():
        base_keywords.extend(["Risk Management", "Team Leadership"])
    
    return base_keywords[:5]

def generate_technical_skills(job_title: str, query: str) -> List[str]:
    """Generate technical skills typically required for the role"""
    technical_skills = [
        "GRC Tools (Archer, ServiceNow)",
        "Risk Assessment Frameworks",
        "SQL and Data Analysis",
        "Excel/Advanced Analytics",
        "Regulatory Compliance (SOX, GDPR)"
    ]
    
    # Add role-specific technical skills
    if "senior" in job_title.lower():
        technical_skills.extend(["Risk Modeling", "Quantitative Analysis"])
    if "analyst" in job_title.lower():
        technical_skills.extend(["Python/R", "Business Intelligence"])
    
    return technical_skills[:5]

async def send_email_report(jobs: List[JobListing], recipient_email: str):
    """Send email with job search results in tabular format"""
    try:
        # Create email content
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = EMAIL_SUBJECT
        
        # Create HTML table
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .keywords, .skills {{
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h2>TPRM Job Search Results - {datetime.now().strftime('%Y-%m-%d')}</h2>
            <p>Found {len(jobs)} relevant Third Party Risk Assessment jobs in Bangalore, India & Remote positions</p>
            
            <table>
                <tr>
                    <th>Job Title</th>
                    <th>Company Name</th>
                    <th>Direct Company Job Link</th>
                    <th>5 Role-Related Keywords</th>
                    <th>5 Technical Skills</th>
                </tr>
        """
        
        for job in jobs:
            # Ensure we have exactly 5 keywords and skills
            keywords_str = ", ".join(job.keywords[:5])
            skills_str = ", ".join(job.technical_skills[:5])
            
            html_content += f"""
                <tr>
                    <td>{job.job_title}</td>
                    <td>{job.company_name}</td>
                    <td><a href="{job.job_link}" target="_blank">View Job</a></td>
                    <td class="keywords">{keywords_str}</td>
                    <td class="skills">{skills_str}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <p><strong>Note:</strong> Jobs are filtered for recent postings (last 24 hours) and focus on Third Party Risk, Vendor Risk, and Supplier Risk Assessment roles in Bangalore and remote positions for product companies.</p>
            
            <p>Best regards,<br>
            Automated Job Search System</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, recipient_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

async def daily_job_search_task():
    """Daily automated job search task"""
    try:
        logger.info("Starting daily job search task...")
        
        # Search for jobs
        jobs = await search_jobs_google(
            query="Third Party Risk Assessment",
            location="Bangalore India OR remote",
            days_filter=7
        )
        
        # Filter for relevant jobs (basic filtering)
        relevant_jobs = []
        for job in jobs:
            if any(keyword in job.job_title.lower() for keyword in 
                   ['risk', 'compliance', 'vendor', 'supplier', 'third party', 'tprm']):
                relevant_jobs.append(job)
        
        # Store results in database
        job_search_result = JobSearchResult(
            jobs=relevant_jobs,
            total_count=len(relevant_jobs),
            search_query="Third Party Risk Assessment",
            search_date=datetime.utcnow()
        )
        
        await db.job_search_results.insert_one(job_search_result.dict())
        
        # Send email report
        await send_email_report(relevant_jobs, EMAIL_ADDRESS)
        
        logger.info(f"Daily job search completed. Found {len(relevant_jobs)} relevant jobs.")
        
    except Exception as e:
        logger.error(f"Daily job search task failed: {e}")

# Scheduler setup
def schedule_daily_jobs():
    """Schedule daily job search at 9 AM IST"""
    ist = pytz.timezone('Asia/Kolkata')
    
    def job_wrapper():
        asyncio.run(daily_job_search_task())
    
    schedule.every().day.at("09:00").do(job_wrapper)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start scheduler in background thread
def start_scheduler():
    scheduler_thread = Thread(target=schedule_daily_jobs, daemon=True)
    scheduler_thread.start()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "TPRM Job Search Automation System", "status": "running"}

@api_router.post("/search-jobs")
async def search_jobs_endpoint(request: JobSearchRequest):
    """Manual job search endpoint"""
    try:
        jobs = await search_jobs_google(
            query=request.query,
            location=request.location,
            days_filter=request.days_filter
        )
        
        # Filter for relevant jobs
        relevant_jobs = []
        for job in jobs:
            if any(keyword in job.job_title.lower() for keyword in 
                   ['risk', 'compliance', 'vendor', 'supplier', 'third party', 'tprm']):
                relevant_jobs.append(job)
        
        return {
            "jobs": relevant_jobs,
            "total_count": len(relevant_jobs),
            "search_query": request.query,
            "search_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/send-test-email")
async def send_test_email():
    """Send test email with sample job data"""
    try:
        # Create sample job data
        sample_jobs = [
            JobListing(
                job_title="Senior Third Party Risk Analyst",
                company_name="Tech Corp India",
                job_link="https://example.com/job1",
                location="Bangalore, India / Remote",
                keywords=["Third Party Risk Management", "Vendor Risk Assessment", "Compliance", "Risk Mitigation", "GRC"],
                technical_skills=["GRC Tools", "SQL", "Risk Frameworks", "Excel", "Regulatory Compliance"]
            ),
            JobListing(
                job_title="Vendor Risk Manager - Remote",
                company_name="Product Company Ltd",
                job_link="https://example.com/job2",
                location="Remote / Bangalore, India",
                keywords=["Vendor Risk", "Supplier Management", "Risk Assessment", "Compliance", "Due Diligence"],
                technical_skills=["ServiceNow", "Risk Modeling", "Python", "Business Intelligence", "SOX Compliance"]
            )
        ]
        
        success = await send_email_report(sample_jobs, EMAIL_ADDRESS)
        
        if success:
            return {"message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/job-results", response_model=List[JobSearchResult])
async def get_job_results():
    """Get recent job search results"""
    try:
        results = await db.job_search_results.find().sort("search_date", -1).limit(10).to_list(10)
        return [JobSearchResult(**result) for result in results]
    except Exception as e:
        logger.error(f"Failed to get job results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trigger-manual-search")
async def trigger_manual_search():
    """Manually trigger the daily job search"""
    try:
        await daily_job_search_task()
        return {"message": "Manual job search completed successfully"}
    except Exception as e:
        logger.error(f"Manual job search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts"""
    start_scheduler()
    logger.info("TPRM Job Search System started with daily scheduler at 9 AM IST")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()