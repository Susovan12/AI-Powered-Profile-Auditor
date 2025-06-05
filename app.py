import streamlit as st
import openai
from openai import OpenAI
import os
import language_tool_python
from dotenv import load_dotenv
import PyPDF2
import io
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from fake_useragent import UserAgent
import json
import urllib.parse
from streamlit_lottie import st_lottie
# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)

# Initialize language tool for grammar checking
language_tool = language_tool_python.LanguageToolPublicAPI('en-US')


# Set page configuration
st.set_page_config(page_title="LinkedIn Profile Auditor", page_icon="🔍", layout="wide")

# You can try adding a theme or custom CSS here if desired
# Example (basic custom CSS - you would typically put this in a separate .css file and load it):
# st.markdown("""<style>
# body { color: #fff; background-color: #1e1e1e; }
# .stApp { background-color: #1e1e1e; }
# .stTabs [data-baseweb="tab-list"] button { padding: 10px; }
# </style>""", unsafe_allow_html=True)

# App title and description
st.title("🔍 AI-Powered LinkedIn Profile Auditor")
st.markdown("""
This tool analyzes your LinkedIn profile or resume and provides feedback to make it more effective.
It checks for grammar, professional tone, keyword relevance, and gives you actionable suggestions.
""")

# Add the resume generation function
def generate_resume(profile_sections_text, job_description=None, api_key=None):
    if api_key:
        client = OpenAI(api_key=api_key)
    elif openai_api_key:
        client = OpenAI(api_key=openai_api_key)
    else:
        return "Error: No OpenAI API key provided. Please enter your API key in the sidebar."

    prompt = f"""Create a professional resume based on the following profile information:

{profile_sections_text}

"""
    if job_description:
        prompt += f"""Tailor the resume for the following job description:

Job Description:
{job_description}

"""

    prompt += """Format the resume as a professional document using markdown, closely following a standard resume structure.

Include the following sections in this approximate order:
- Name
- Contact Information
- Professional Summary / About Me
- Technical Skills
- Work Experience
- Education
- Projects
- Awards, Honors, Certifications

Use markdown headings (## for main sections) and bullet points (*) for lists within sections (e.g., job responsibilities, project details).
Use markdown horizontal rules (---) to clearly separate each main section.

For the Name, use a level 1 markdown heading (#) with the full name, but do NOT make the name text bold yourself (no ** stars).
For Contact Information, place Phone, Email, LinkedIn, and GitHub on a single line separated by ' | '. Place this line immediately below the Name with minimal vertical space.

Ensure the language is concise, uses action verbs and highlights achievements.
Do not include placeholder text like '[Your Name]' - use the provided information directly.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Consider gpt-4 for better quality if available
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Create a well-formatted, professional resume from the provided sections."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500 # Adjust as needed for resume length
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating resume: {str(e)}. Ensure your API key is correct and you have sufficient credits."

# Add the cover letter generation function
def generate_cover_letter(profile_text, company_name, job_posting, api_key=None):
    if api_key:
        client = OpenAI(api_key=api_key)
    elif openai_api_key:
        client = OpenAI(api_key=openai_api_key)
    else:
        return "Error: No OpenAI API key provided. Please enter your API key in the sidebar."

    prompt = f"""Write a professional cover letter for a job application.

Use the following profile information:
{profile_text}

Use the following company name and job posting to tailor the letter:
Company Name: {company_name}
Job Posting:
{job_posting}

Address the letter to the hiring manager (use a general title like 'Hiring Manager' if no name is provided). Highlight relevant skills and experience from the profile that match the job posting. Explain why you are interested in this specific role and company. Keep the letter concise and professional.

Include a professional closing.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Consider gpt-4 for better quality
            messages=[
                {"role": "system", "content": "You are an expert cover letter writer. Create a compelling and tailored cover letter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500 # Adjust as needed for cover letter length
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating cover letter: {str(e)}. Ensure your API key is correct and you have sufficient credits."

def get_random_user_agent():
    try:
        ua = UserAgent()
        return ua.random
    except:
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def create_session():
    session = requests.Session()
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    })
    return session

def get_public_profile_url(url):
    """Convert LinkedIn URL to public profile format"""
    try:
        # Extract username from URL
        if 'linkedin.com/in/' in url:
            username = url.split('linkedin.com/in/')[-1].split('/')[0].split('?')[0]
            return f"https://www.linkedin.com/in/{username}/"
        return url
    except:
        return url

def scrape_linkedin_profile(url):
    try:
        # Display comprehensive warning about LinkedIn scraping limitations
        st.warning("""
⚠️ **LinkedIn Profile Access Limitations:**
- LinkedIn actively prevents automated scraping
- Most profiles require authentication
- Some profiles may be private or restricted
- For best results, please manually copy and paste your profile sections
        """)
        
        # Convert to public profile URL
        public_url = get_public_profile_url(url)
        
        # Create a session with proper headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # First try to get the public profile page
        response = session.get(public_url, timeout=10)
        
        if response.status_code == 999 or response.status_code == 403:
            st.error("LinkedIn is blocking access. Trying alternative method...")
            
            # Try with mobile user agent
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
            
            time.sleep(2)  # Add delay
            response = session.get(public_url, timeout=10)
        
        if response.status_code != 200:
            return f"Error: Could not access the LinkedIn profile. Status code: {response.status_code}. Please try copying and pasting your profile sections manually."
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Initialize profile sections
        profile_sections = {
            'about': '',
            'experience': '',
            'skills': ''
        }
        
        # Try to find profile sections using multiple methods
        # About/Summary section
        about_selectors = [
            'section.summary',
            'section.about',
            'div[data-section="summary"]',
            'div[data-section="about"]',
            'div[class*="summary"]',
            'div[class*="about"]'
        ]
        
        for selector in about_selectors:
            section = soup.select_one(selector)
            if section:
                profile_sections['about'] = section.get_text(strip=True)
                break
        
        # Experience section
        exp_selectors = [
            'section#experience',
            'section.experience',
            'div[data-section="experience"]',
            'div[class*="experience"]'
        ]
        
        for selector in exp_selectors:
            section = soup.select_one(selector)
            if section:
                profile_sections['experience'] = section.get_text(strip=True)
                break
        
        # Skills section
        skills_selectors = [
            'section#skills',
            'section.skills',
            'div[data-section="skills"]',
            'div[class*="skills"]'
        ]
        
        for selector in skills_selectors:
            section = soup.select_one(selector)
            if section:
                profile_sections['skills'] = section.get_text(strip=True)
                break
        
        # Format the profile text
        profile_text = ""
        if profile_sections['about']:
            profile_text += "# ABOUT ME\n" + profile_sections['about'] + "\n\n"
        if profile_sections['experience']:
            profile_text += "# EXPERIENCE\n" + profile_sections['experience'] + "\n\n"
        if profile_sections['skills']:
            profile_text += "# SKILLS\n" + profile_sections['skills']
        
        if not profile_text.strip():
            return """Error: Could not extract profile information. This is likely because:
1. The profile requires authentication
2. LinkedIn's structure has changed
3. The profile is private or restricted

Please copy and paste your profile sections manually for the best results."""
        
        return profile_text
    except requests.exceptions.RequestException as e:
        return f"Network Error: {str(e)}. Please check your internet connection and try again."
    except Exception as e:
        return f"Error scraping LinkedIn profile: {str(e)}. Please copy and paste your profile sections manually."

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

# Function to analyze profile with OpenAI
def analyze_profile(profile_text, job_description=None, api_key=None):
    # Create OpenAI client with the appropriate API key
    if api_key:
        client = OpenAI(api_key=api_key)
    elif openai_api_key:
        client = OpenAI(api_key=openai_api_key)
    else:
        return "Error: No OpenAI API key provided. Please enter your API key in the sidebar."
    
    # Prepare prompt for GPT with expanded analysis requests
    # Request ATS analysis to be clearly separated for later parsing
    prompt = f"""Analyze this LinkedIn profile or resume content and provide professional feedback. Focus on the following aspects:

{profile_text}

"""
    
    if job_description:
        prompt += f"""Compare this profile content with the following job description and analyze keyword relevance and job fit:

Job Description:
{job_description}

"""
    
    prompt += """Provide a detailed analysis covering:

1.  **Overall Impression:** Clarity, conciseness, and professional tone.
2.  **Tone Analysis:** Evaluate the overall tone of the profile/resume.
3.  **Grammar and Language Quality:** Assessment of writing mechanics.
4.  **Action Verbs and Achievements:** Effective use of action verbs and quantifiable achievements.
5.  **Red Flags/Weak Points:** Passive language, vague phrases, areas needing improvement.
6.  **Buzzword Identification:** List any buzzwords or overused phrases.
7.  **Professional Vocabulary:** Assess the use of industry-specific and professional language.
8.  **Specific Improvement Suggestions:** Actionable recommendations for each section.

---
## ATS ASSESSMENT START

Provide an evaluation of the content's suitability for Applicant Tracking Systems, focusing on keywords, formatting, and structure. Be detailed in this section.

## ATS ASSESSMENT END
---

Include numerical scores as percentages (0-100%) for:

-   Clarity Score:
-   Impact Score:
-   (If job description provided) Keyword Match Score:
-   ATS Score:: [ATS_SCORE_PERCENTAGE]  <-- Provide the ATS score on this line using this format.

Format the response with clear markdown headings (e.g., ## Overall Impression) and bullet points where appropriate. Place the scores at the very end of the analysis in a clear list as requested.

"""

    try:
        # Using the new OpenAI API format
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Or a more capable model like gpt-4 if available and desired
            messages=[
                {"role": "system", "content": "You are an expert LinkedIn profile and resume reviewer with years of experience in HR and recruitment. Provide comprehensive, structured, and actionable feedback based on the user's input. Ensure the ATS section and score are formatted exactly as requested for parsing."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500 # Increased max_tokens slightly to accommodate more detailed ATS feedback
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}. Ensure your API key is correct and you have sufficient credits."

# Sidebar for API key input
with st.sidebar:
    st.header("⚙️ Settings")
    user_api_key = st.text_input("OpenAI API Key (optional if using .env)", type="password", help="Your API key will not be stored")
    
    st.markdown("""---
### 📋 Instructions
1. Enter your OpenAI API key
2. Paste your LinkedIn profile sections, URL, or upload a resume
3. Optionally add a job description for keyword matching
4. Click 'Analyze Profile' to get feedback
    """)
    
    st.markdown("""---
### 🔑 About API Keys
Your OpenAI API key is used only for this analysis and is never stored.
You can also add it to a .env file as OPENAI_API_KEY=your-key-here
    """)

# Main content area
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Profile Input", "📊 General Analysis", "🤖 ATS Analysis", "📄 Cover Letter", "✍️ Resume Builder", "❓ How to Use This Tool"])

# Initialize session state variables
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'scores' not in st.session_state:
    st.session_state['scores'] = {'Clarity': 'N/A', 'Impact': 'N/A', 'ATS': 'N/A', 'Keyword Match': 'N/A'}
if 'ats_analysis' not in st.session_state:
    st.session_state['ats_analysis'] = ""
if 'other_analysis' not in st.session_state:
    st.session_state['other_analysis'] = ""
if 'generated_resume' not in st.session_state:
    st.session_state['generated_resume'] = ""
if 'generated_cover_letter' not in st.session_state:
    st.session_state['generated_cover_letter'] = ""
if 'profile_for_cl' not in st.session_state:
    st.session_state['profile_for_cl'] = "" # To store profile content for Cover Letter tab

with tab1:
    st.header("Enter Your Profile or Upload Resume")
    st.markdown("Provide your profile details below or upload a resume for analysis.")
    
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Manual Profile Input")
        # Only manual entry fields remain
        profile_about = st.text_area("About Me / Summary", height=150,
                                   placeholder="Paste your LinkedIn 'About' section here...")
        profile_experience = st.text_area("Experience", height=200,
                                        placeholder="Paste your work experience here...")
        profile_skills = st.text_area("Skills", height=100,
                                    placeholder="List your skills here...")

        # Initialize full_profile variable for analysis tab
        full_profile_analysis = f"""# ABOUT ME\n{profile_about}\n\n# EXPERIENCE\n{profile_experience}\n\n# SKILLS\n{profile_skills}"""

    with col2:
        st.subheader("Job Description (Optional) or Upload Resume")
        job_description = st.text_area("Job Description for Keyword Matching", height=300,
                                     placeholder="Paste a job description to compare your profile against...")

        st.markdown("--- \n **Or**") # Added separator
        st.subheader("Upload Resume")
        uploaded_file = st.file_uploader("Upload a PDF resume", type="pdf")

        resume_text = ""
        if uploaded_file is not None:
            with st.spinner("Extracting text from PDF..."):
                resume_text = extract_text_from_pdf(uploaded_file)
                if resume_text.startswith("Error"):
                    st.error(resume_text)
                else:
                    st.success("PDF successfully processed!")
                    with st.expander("Preview Extracted Text"):
                        st.text(resume_text)
                    # If manual fields are empty, use the resume text for analysis
                    if not profile_about.strip() and not profile_experience.strip() and not profile_skills.strip():
                        full_profile_analysis = resume_text

    analyze_button = st.button("🔍 Analyze Profile", type="primary", use_container_width=True)

    # Perform analysis when button is clicked and profile content exists
    if analyze_button and full_profile_analysis.strip(): # Use full_profile_analysis here
        with st.spinner("AI is analyzing your profile... This may take a moment."):
            analysis_result = analyze_profile(full_profile_analysis, job_description, user_api_key)
            st.session_state['analysis_result'] = analysis_result # Store full result
            
            # --- Parse analysis_result to separate ATS and others, and extract scores ---
            ats_start_marker = "## ATS ASSESSMENT START"
            ats_end_marker = "## ATS ASSESSMENT END"
            
            ats_content = ""
            other_content = analysis_result
            
            # Extract ATS section
            if ats_start_marker in analysis_result and ats_end_marker in analysis_result:
                start_index = analysis_result.find(ats_start_marker)
                end_index = analysis_result.find(ats_end_marker)
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    # Extract the content between markers, including the start marker
                    ats_content = analysis_result[start_index : end_index + len(ats_end_marker)]
                    
                    # Remove ATS content from the original analysis_result for 'other_content'
                    other_content = analysis_result[:start_index] + analysis_result[end_index + len(ats_end_marker):]
            
            # Extract all scores using regex on the *full* analysis result before removing scores from other_content
            scores = {}
            score_patterns = {
                'Clarity': r"Clarity Score:\s*(\d+%)",
                'Impact': r"Impact Score:\s*(\d+%)",
                'ATS': r"ATS Score:\s*(\d+%)", # Corrected regex to use a single colon
                'Keyword Match': r"Keyword Match Score:\s*(\d+%)"
            }
            
            for label, pattern in score_patterns.items():
                match = re.search(pattern, analysis_result, re.MULTILINE)
                if match:
                    scores[label] = match.group(1) # Keep as percentage string for display
                else:
                    scores[label] = 'N/A'
                    
            # Remove score lines from other_content so they only appear in the ATS tab progress bars
            # Use re.sub with flags=re.MULTILINE to handle lines correctly
            for label, pattern in score_patterns.items():
                 # Escape potential regex special characters in the pattern and match the start of a line
                 safe_pattern = re.escape(pattern).replace("\\(", "(").replace("\\)", ")").replace("\\d+", "\\d+").replace("\\%", "%") # Keep intended regex parts
                 other_content = re.sub(f"^{safe_pattern}$", "", other_content, flags=re.MULTILINE).strip()
            
            st.session_state['ats_analysis'] = ats_content
            st.session_state['other_analysis'] = other_content
            st.session_state['scores'] = scores
            
            # Store the profile text in session state for use in other tabs (like Cover Letter)
            st.session_state['profile_for_cl'] = full_profile_analysis
            
            # Provide feedback to the user that analysis is complete and they can view results
            st.success("Analysis complete! Go to the 'General Analysis' or 'ATS Analysis' tabs to view the feedback.")
            st.session_state['analysis_complete'] = True # Use session state to indicate completion
            

with tab2:
    # Display non-ATS analysis results
    st.header("📊 General Analysis Results")
    st.markdown("Here is the comprehensive AI feedback on your profile or resume:")
    
    if st.session_state['analysis_result'] is not None:
        if st.session_state['other_analysis'].strip():
            # Use st.markdown to render the AI's markdown formatting
            st.markdown(st.session_state['other_analysis'])
        else:
             st.info("No general analysis results available. Run the analysis first.")

        # Scores are now only displayed in the ATS tab with progress bars.

    else:
        st.info("Enter your profile details or upload a resume, then click 'Analyze Profile' to see results here.")

with tab3:
    # Display ATS-specific analysis and scores with progress bars
    st.header("🤖 ATS Analysis Results")

    if st.session_state['analysis_result'] is not None:

        # Display scores with progress bars
        st.subheader("Compatibility Scores")
        
        # Removed Lottie animation loading and display code
        # The following lines were responsible for the Lottie animation and the warning.
#        try:
#            # Make sure you have downloaded a .json animation file and placed it in the same directory as app.py
#            with open("ats_animation.json", "r") as f:
#                lottie_json = json.load(f)
#            st_lottie(lottie_json, height=100, key="ats_animation") # Reduced height slightly
#        except FileNotFoundError:
#            st.warning("Lottie animation file 'ats_animation.json' not found. Please download one and place it in the app directory.")
#        except Exception as e:
#            st.error(f"Could not load animation: {e}")
        
        score_order = ['Clarity', 'Impact', 'ATS', 'Keyword Match'] # Define the order of scores
        for label in score_order:
            score_value_str = st.session_state['scores'].get(label, 'N/A')
            
            # If the score is N/A, just display the text
            if score_value_str == 'N/A':
                st.text(f"{label} Score: {score_value_str}")
            else:
                # Otherwise, try to process and display the progress bar
                try:
                    # Extract numerical value and convert to float 0-1
                    score_percentage = int(score_value_str.replace('%', ''))
                    
                    # Ensure percentage is within 0-100 range before converting to float 0-1
                    if 0 <= score_percentage <= 100:
                        score_float = score_percentage / 100.0
                        # Display score label and progress bar
                        st.markdown(f"**{label} Score:** {score_value_str}")
                        st.progress(score_float)
                    else:
                         # Handle cases where parsed percentage is out of expected range
                         st.text(f"{label} Score: {score_value_str} (Error: Invalid percentage value)")
                except ValueError:
                    # Handle cases where parsing to int fails (should not happen if format is consistent)
                    st.text(f"{label} Score: {score_value_str} (Error displaying progress - parsing failed)")
            
        st.markdown("---") # Add a separator

        # Add helpful tips about ATS (Keep or remove as desired)
        with st.expander("ℹ️ About ATS Optimization Tips"):
            st.markdown("""
            **What is ATS?**
            - Applicant Tracking System (ATS) is software used by employers to manage job applications
            - It scans resumes for keywords and formatting before human review
            
            **Tips for ATS Optimization:**
            - Use standard section headings
            - Include relevant keywords from job descriptions
            - Avoid complex formatting and tables
            - Use standard fonts and bullet points
            - Submit in PDF or Word format
            """)

    else:
        st.info("Run the analysis first to see ATS feedback here.")

with tab4:
    st.header("📄 Cover Letter")
    st.markdown("Generate a tailored cover letter based on your profile and a job description.")

    # Input fields for cover letter generation
    company_name = st.text_input("Company Name")
    job_posting = st.text_area("Job Posting (for tailoring the cover letter)", height=300,
                               placeholder="Paste the job description here...")

    generate_cl_button = st.button("✨ Generate Cover Letter", type="primary")

    # Logic to generate cover letter when button is clicked
    if generate_cl_button:
        # Get profile content from session state (populated by the Analyze Profile button)
        profile_text_for_cl = st.session_state.get('profile_for_cl', '')
        
        if not profile_text_for_cl.strip():
            st.warning("Please analyze your profile first in the 'Profile Input' tab.")
        elif not company_name.strip() or not job_posting.strip():
             st.warning("Please enter both Company Name and Job Posting to generate a cover letter.")
        else:
            with st.spinner("AI is generating your cover letter..."):
                 generated_cl = generate_cover_letter(profile_text_for_cl, company_name, job_posting, user_api_key)
                 st.session_state['generated_cover_letter'] = generated_cl

    # Output area will go here
    if st.session_state['generated_cover_letter'].strip():
        st.subheader("Generated Cover Letter")
        st.text_area("", st.session_state['generated_cover_letter'], height=400)

        # Add download button
        st.download_button(
            label="Download Cover Letter",
            data=st.session_state['generated_cover_letter'],
            file_name="generated_cover_letter.txt",
            mime="text/plain"
        )

with tab5:
    st.header("✍️ AI Powered Resume Builder")
    st.markdown("Generate a resume based on your profile information and additional details.")

    # New Input fields for comprehensive CV content
    resume_name = st.text_input("Full Name")
    resume_contact = st.text_area("Contact Information (Phone, Email, LinkedIn URL, etc.)", height=100,
                                 placeholder="Enter your phone number, email, LinkedIn URL, etc.")
    resume_education = st.text_area("Education", height=150,
                                   placeholder="List your degrees, universities, dates, GPA (optional)..")

    # Existing input fields
    resume_about = st.text_area("About Me / Summary for Resume", height=150,
                               placeholder="Paste your About Me or Summary here...")
    resume_experience = st.text_area("Experience for Resume", height=200,
                                     placeholder="Paste your work experience here...")
    resume_skills = st.text_area("Skills for Resume", height=100,
                                 placeholder="List your skills here...")

    # Additional fields
    resume_projects = st.text_area("Projects (Optional)", height=150,
                                  placeholder="List significant projects, roles, and outcomes...")
    resume_awards = st.text_area("Awards, Honors, Certifications (Optional)", height=100,
                                placeholder="List any relevant awards, honors, or certifications...")

    # Optional Job Description for tailoring
    resume_job_description = st.text_area("Job Description (Optional) for Resume Tailoring", height=200,
                                          placeholder="Paste a job description here to tailor the resume...")

    generate_button = st.button("✨ Generate Resume", type="primary")

    if generate_button and (resume_name.strip() or resume_contact.strip() or resume_education.strip() or resume_about.strip() or resume_experience.strip() or resume_skills.strip() or resume_projects.strip() or resume_awards.strip()):
        with st.spinner("Generating resume..."):
            # Combine input for the AI
            resume_input_text = f"""# NAME\n{resume_name}\n\n# CONTACT INFORMATION\n{resume_contact}\n\n# EDUCATION\n{resume_education}\n\n# ABOUT ME\n{resume_about}\n\n# EXPERIENCE\n{resume_experience}\n\n# SKILLS\n{resume_skills}\n\n# PROJECTS\n{resume_projects}\n\n# AWARDS, HONORS, CERTIFICATIONS\n{resume_awards}"""

            # Use the generate_resume function (defined above)
            st.session_state['generated_resume'] = generate_resume(resume_input_text, resume_job_description, user_api_key)

    # Display the generated resume
    if st.session_state['generated_resume'].strip():
        st.subheader("Generated Resume")
        
        # Display the generated resume using st.text (reverting to previous behavior)
        st.text(st.session_state['generated_resume'])

        # Add download button
        st.download_button(
            label="Download Resume",
            data=st.session_state['generated_resume'],
            file_name="generated_resume.txt",
            mime="text/plain"
        )
    elif generate_button:
         st.warning("Please provide content for at least one section to generate a resume.")

with tab6:
    st.header("❓ How to Use This Tool")
    st.markdown("""
    1. **Enter Your Profile Content**
       - Paste your LinkedIn profile sections, or
       - Upload a PDF resume, or
       - Enter profile information manually
    
    2. **Add Job Description (Optional)**
       - Include a job posting for keyword matching
       - This helps analyze profile relevance
    
    3. **View Results**
       - General Analysis: Overall feedback and scores
       - ATS Analysis: Compatibility with tracking systems
       - Specific recommendations for improvement
    
    4. **Make Improvements**
       - Follow the suggestions provided
       - Update your profile/resume accordingly
       - Re-analyze to check improvements
    """)

# Footer
st.markdown("---")
st.markdown("""<div style='text-align: center'>
<p>Built with Streamlit and OpenAI GPT-3.5 Turbo</p>
</div>""", unsafe_allow_html=True)
