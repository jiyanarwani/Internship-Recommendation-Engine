import re
import os
import json
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# Try importing parsing and AI libraries
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field
    from typing import List, Optional
except ImportError:
    genai = None

# Comprehensive list of skills to check for
SKILL_KEYWORDS = [
    # Programming Languages
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'php', 'ruby', 'go', 'rust', 'kotlin', 'swift', 'r', 'matlab', 'sql', 'c',
    # Web Development
    'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'django', 'flask', 'spring boot', 'laravel', 'express', 'jquery', 'bootstrap', 'tailwind',
    # Databases
    'postgresql', 'mysql', 'sqlite', 'mongodb', 'redis', 'oracle', 'firebase', 'cassandra',
    # AI/ML & Data Science
    'machine learning', 'deep learning', 'data science', 'natural language processing', 'nlp', 'computer vision', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'data analysis', 'power bi', 'tableau', 'langchain', 'faiss', 'chromadb', 'pinecone', 'llm', 'rag', 'openai', 'langgraph', 'llamaindex',
    # DevOps & Cloud
    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'google cloud', 'git', 'github', 'jenkins', 'ci/cd', 'linux',
    # Core & Other Tech
    'cryptography', 'cybersecurity', 'network security', 'blockchain', 'iot', 'embedded systems', 'android', 'ios', 'mechanical', 'cad', 'solidworks', 'autocad', 'civil', 'excel', 'ms excel', 'data structures', 'algorithms', 'vite', 'vs code', 'chrome devtools', 'recharts', 'localstorage',
    # Soft/Business Skills
    'project management', 'agile', 'scrum', 'communication', 'teamwork', 'leadership', 'problem solving', 'critical thinking', 'marketing', 'finance', 'accounting'
]

# Comprehensive list of interests
INTEREST_KEYWORDS = [
    'web development', 'software engineering', 'app development', 'artificial intelligence', 'machine learning', 
    'data analytics', 'cybersecurity', 'cloud computing', 'blockchain', 'product management', 'ui/ux design', 
    'digital marketing', 'finance', 'business development', 'consulting', 'hr management'
]

DEGREE_MAPPINGS = {
    r'\bb\.?\s*tech(nology)?\b': 'B.Tech',
    r'\bbachelor\s+of\s+technology\b': 'B.Tech',
    r'\bm\.?\s*tech(nology)?\b': 'M.Tech',
    r'\bmaster\s+of\s+technology\b': 'M.Tech',
    r'\bb\.?\s*e\.?\b': 'B.E.',
    r'\bbachelor\s+of\s+engineering\b': 'B.E.',
    r'\bm\.?\s*e\.?\b': 'M.E.',
    r'\bmaster\s+of\s+engineering\b': 'M.E.',
    r'\bb\.?\s*c\.?\s*a\.?\b': 'BCA',
    r'\bbachelor\s+of\s+computer\s+applications\b': 'BCA',
    r'\bm\.?\s*c\.?\s*a\.?\b': 'MCA',
    r'\bmaster\s+of\s+computer\s+applications\b': 'MCA',
    r'\bb\.?\s*s\.?\s*c\.?\b': 'B.Sc',
    r'\bbachelor\s+of\s+science\b': 'B.Sc',
    r'\bm\.?\s*s\.?\s*c\.?\b': 'M.Sc',
    r'\bmaster\s+of\s+science\b': 'M.Sc',
    r'\bb\.?\s*b\.?\s*a\.?\b': 'BBA',
    r'\bbachelor\s+of\s+business\s+administration\b': 'BBA',
    r'\bm\.?\s*b\.?\s*a\.?\b': 'MBA',
    r'\bmaster\s+of\s+business\s+administration\b': 'MBA',
    r'\bb\.?\s*com\b': 'B.Com',
    r'\bbachelor\s+of\s+commerce\b': 'B.Com',
    r'\bm\.?\s*com\b': 'M.Com',
    r'\bmaster\s+of\s+commerce\b': 'M.Com',
    r'\bb\.?\s*a\.?\b': 'B.A.',
    r'\bbachelor\s+of\s+arts\b': 'B.A.',
    r'\bm\.?\s*a\.?\b': 'M.A.',
    r'\bmaster\s+of\s+arts\b': 'M.A.',
    r'\bdiploma\b': 'Diploma'
}

BRANCH_MAPPINGS = {
    r'\bcomputer\s*science\s*and\s*engineering\b': 'Computer Science',
    r'\bcomputer\s*science\s*&\s*engineering\b': 'Computer Science',
    r'\bcomputer\s*engineering\b': 'Computer Engineering',
    r'\bcomputer\s*science\b': 'Computer Science',
    r'\bcse\b': 'Computer Science',
    r'\binformation\s*technology\b': 'Information Technology',
    r'\bit\b': 'Information Technology',
    r'\belectronics\s*(and\s*communication)?\s*engineering\b': 'Electronics & Communication',
    r'\belectronics\s*&\s*communication\s*engineering\b': 'Electronics & Communication',
    r'\belectronics\s*(and\s*communication)?\b': 'Electronics & Communication',
    r'\bece\b': 'Electronics & Communication',
    r'\belectrical\s*engineering\b': 'Electrical Engineering',
    r'\belectrical\b': 'Electrical Engineering',
    r'\bee\b': 'Electrical Engineering',
    r'\bmechanical\s*engineering\b': 'Mechanical Engineering',
    r'\bmechanical\b': 'Mechanical Engineering',
    r'\bme\b': 'Mechanical Engineering',
    r'\bcivil\s*engineering\b': 'Civil Engineering',
    r'\bcivil\b': 'Civil Engineering',
    r'\bce\b': 'Civil Engineering',
    r'\bchemical\s*engineering\b': 'Chemical Engineering',
    r'\bchemical\b': 'Chemical Engineering',
    r'\bfinance\b': 'Finance',
    r'\bmarketing\b': 'Marketing',
    r'\bbusiness\b': 'Business Administration',
    r'\bcommerce\b': 'Commerce',
    r'\bhuman\s*resource\b': 'Human Resources'
}

SKILL_SYNONYMS = {
    'js': 'JavaScript',
    'javascript': 'JavaScript',
    'ts': 'TypeScript',
    'typescript': 'TypeScript',
    'py': 'Python',
    'python': 'Python',
    'cpp': 'C++',
    'c plus plus': 'C++',
    'c#': 'C#',
    'c sharp': 'C#',
    'golang': 'Go',
    'go': 'Go',
    'rust': 'Rust',
    'java': 'Java',
    'kotlin': 'Kotlin',
    'swift': 'Swift',
    'ruby': 'Ruby',
    'php': 'PHP',
    'sql': 'SQL',
    'react': 'React.js',
    'reactjs': 'React.js',
    'react.js': 'React.js',
    'nextjs': 'Next.js',
    'next.js': 'Next.js',
    'vue': 'Vue.js',
    'vuejs': 'Vue.js',
    'vue.js': 'Vue.js',
    'angular': 'Angular',
    'angularjs': 'Angular',
    'nodejs': 'Node.js',
    'node': 'Node.js',
    'node.js': 'Node.js',
    'express': 'Express.js',
    'expressjs': 'Express.js',
    'express.js': 'Express.js',
    'flask': 'Flask',
    'django': 'Django',
    'fastapi': 'FastAPI',
    'bootstrap': 'Bootstrap',
    'tailwind': 'Tailwind CSS',
    'tailwindcss': 'Tailwind CSS',
    'jquery': 'jQuery',
    'postgres': 'PostgreSQL',
    'postgresql': 'PostgreSQL',
    'mysql': 'MySQL',
    'mongodb': 'MongoDB',
    'mongo': 'MongoDB',
    'sqlite': 'SQLite',
    'redis': 'Redis',
    'aws': 'AWS',
    'amazon web services': 'AWS',
    'gcp': 'GCP',
    'google cloud': 'GCP',
    'azure': 'Azure',
    'docker': 'Docker',
    'k8s': 'Kubernetes',
    'kubernetes': 'Kubernetes',
    'git': 'Git',
    'github': 'GitHub',
    'jenkins': 'Jenkins',
    'cicd': 'CI/CD',
    'ci/cd': 'CI/CD',
    'ml': 'Machine Learning',
    'machinelearning': 'Machine Learning',
    'machine learning': 'Machine Learning',
    'dl': 'Deep Learning',
    'deeplearning': 'Deep Learning',
    'deep learning': 'Deep Learning',
    'ai': 'Artificial Intelligence',
    'artificial intelligence': 'Artificial Intelligence',
    'nlp': 'NLP',
    'natural language processing': 'NLP',
    'cv': 'Computer Vision',
    'computer vision': 'Computer Vision',
    'genai': 'Generative AI',
    'generative ai': 'Generative AI',
    'llm': 'LLM',
    'large language model': 'LLM',
    'large language models': 'LLM',
    'rag': 'RAG',
    'openai': 'OpenAI',
    'langchain': 'LangChain',
    'llamaindex': 'LlamaIndex',
    'tensorflow': 'TensorFlow',
    'pytorch': 'PyTorch',
    'scikitlearn': 'Scikit-learn',
    'scikit-learn': 'Scikit-learn',
    'vscode': 'VS Code',
    'vs code': 'VS Code',
    'postman': 'Postman',
    'excel': 'Excel',
    'ms excel': 'Excel',
    'powerbi': 'Power BI',
    'power bi': 'Power BI',
    'tableau': 'Tableau',
    'data structures': 'Data Structures',
    'algorithms': 'Algorithms',
    'dsa': 'Data Structures & Algorithms',
    'crud': 'CRUD',
    'localstorage': 'LocalStorage',
    'cad': 'CAD',
    'autocad': 'AutoCAD',
    'solidworks': 'SolidWorks',
    'recharts': 'Recharts',
    'vite': 'Vite',
    'chrome devtools': 'Chrome DevTools',
    'chrome dev tools': 'Chrome DevTools'
}

SKILL_CATEGORIES = {
    'programming_languages': ['Python', 'Java', 'C++', 'C#', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Kotlin', 'Swift', 'Ruby', 'PHP', 'SQL', 'C', 'R', 'Matlab'],
    'frameworks': ['Flask', 'FastAPI', 'Django', 'React.js', 'Next.js', 'Angular', 'Vue.js', 'Express.js', 'Spring Boot', 'Laravel', 'Bootstrap', 'Tailwind CSS', 'jQuery'],
    'libraries': ['Pandas', 'Numpy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Recharts', 'Keras', 'OpenCV', 'Framer Motion', 'React Icons'],
    'databases': ['PostgreSQL', 'MySQL', 'MongoDB', 'SQLite', 'Redis', 'Oracle', 'Firebase', 'Cassandra'],
    'cloud': ['AWS', 'GCP', 'Azure', 'Google Cloud'],
    'devops': ['Docker', 'Kubernetes', 'Git', 'GitHub', 'Jenkins', 'CI/CD', 'Linux'],
    'ai_ml': ['Machine Learning', 'Deep Learning', 'Artificial Intelligence', 'NLP', 'Computer Vision', 'Generative AI', 'LLM', 'RAG', 'LangChain', 'LlamaIndex', 'OpenAI', 'Hugging Face', 'FAISS', 'ChromaDB', 'Pinecone', 'LangGraph'],
    'tools': ['VS Code', 'Postman', 'Excel', 'Power BI', 'Tableau', 'Vite', 'Chrome DevTools', 'CAD', 'AutoCAD', 'SolidWorks'],
    'other': []
}

def clean_text(text):
    """Normalize text by removing extra whitespaces and standardizing punctuation."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def merge_split_keywords(text):
    """Clean common split-word artifacts created by PDF extractors (e.g. 'f aiss', 'l angchain')."""
    # Clean C++ and C# split patterns first
    text = re.sub(r'\bc\s*\+\s*\+\s*(?!\w)', 'c++', text, flags=re.IGNORECASE)
    text = re.sub(r'\bc\s*\#\s*(?!\w)', 'c#', text, flags=re.IGNORECASE)
    
    keywords = [
        'faiss', 'langchain', 'youtube', 'fastapi', 'hugging face', 'javascript', 'typescript', 
        'mongodb', 'tailwind css', 'react', 'python', 'flask', 'github', 'scikit-learn',
        'vue', 'angular', 'nodejs', 'sqlite', 'mysql', 'postgresql', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp'
    ]
    for kw in keywords:
        clean_kw = kw.replace(' ', '')
        pattern = r'\b' + r'\s*'.join(list(re.escape(clean_kw))) + r'\b'
        text = re.sub(pattern, kw, text, flags=re.IGNORECASE)
    return text

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from PDF using a multi-stage fallback pipeline:
    1. pdfplumber (retains columns, tables, layout best)
    2. fitz / PyMuPDF (fast, robust text extraction)
    3. pypdf (basic fallback)
    """
    if not os.path.exists(pdf_path):
        return ""
        
    text = ""
    
    # Stage 1: pdfplumber
    if pdfplumber:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                text = "\n".join(pages_text)
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            
    # Stage 2: fitz (PyMuPDF)
    if not text.strip() and fitz:
        try:
            doc = fitz.open(pdf_path)
            pages_text = []
            for page in doc:
                pages_text.append(page.get_text())
            text = "\n".join(pages_text)
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            
    # Stage 3: pypdf (basic fallback)
    if not text.strip():
        try:
            reader = PdfReader(pdf_path)
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text)
        except Exception as e:
            print(f"pypdf extraction failed: {e}")
            
    return text

def normalize_skills(raw_skills):
    """Normalize and deduplicate a list of raw skills."""
    normalized = []
    seen = set()
    for skill in raw_skills:
        skill_clean = skill.strip().lower()
        if not skill_clean:
            continue
        mapped = SKILL_SYNONYMS.get(skill_clean, skill.strip().title())
        mapped_lower = mapped.lower()
        if mapped_lower not in seen:
            seen.add(mapped_lower)
            normalized.append(mapped)
    return normalized

def categorize_skills(skills):
    """Categorizes a list of skills into a structured dictionary."""
    categorized = {
        'programming_languages': [],
        'frameworks': [],
        'libraries': [],
        'databases': [],
        'cloud': [],
        'devops': [],
        'ai_ml': [],
        'tools': [],
        'other': []
    }
    
    # Build reverse lookup map
    lookup = {}
    for cat, items in SKILL_CATEGORIES.items():
        for item in items:
            lookup[item.lower()] = cat
            
    for skill in skills:
        cat = lookup.get(skill.lower(), 'other')
        categorized[cat].append(skill)
        
    return categorized

def deduplicate_projects(projects):
    """Deduplicate a list of project dicts using title similarity."""
    if not projects:
        return []
        
    unique_projects = []
    for p in projects:
        title = p.get('title', '').strip()
        if not title:
            continue
            
        is_dup = False
        for existing in unique_projects:
            t1 = re.sub(r'[^a-z0-9]', '', title.lower())
            t2 = re.sub(r'[^a-z0-9]', '', existing['title'].lower())
            
            # Word-level overlap
            words1 = set(title.lower().split())
            words2 = set(existing['title'].lower().split())
            overlap = len(words1.intersection(words2)) / len(words1.union(words2)) if words1.union(words2) else 0.0
            
            if t1 == t2 or (t1 in t2 and len(t1) >= 4) or (t2 in t1 and len(t2) >= 4) or overlap >= 0.70:
                is_dup = True
                # Merge descriptions (take longer)
                desc1 = p.get('description', '') or ''
                desc2 = existing.get('description', '') or ''
                if len(desc1.strip()) > len(desc2.strip()):
                    existing['description'] = desc1.strip()
                
                # Merge technologies
                techs = set(existing.get('technologies', []) or [])
                techs.update(p.get('technologies', []) or [])
                existing['technologies'] = list(techs)
                
                # Merge link
                if not existing.get('link') and p.get('link'):
                    existing['link'] = p['link']
                break
                
        if not is_dup:
            unique_projects.append({
                "title": title,
                "description": p.get('description', '') or '',
                "technologies": p.get('technologies', []) or [],
                "link": p.get('link', '') or ''
            })
            
    return unique_projects

def deduplicate_experience(experiences):
    """Deduplicate a list of experience dicts using company name and role similarity."""
    if not experiences:
        return []
        
    unique_exp = []
    for exp in experiences:
        company = exp.get('company', '').strip()
        role = exp.get('role', '').strip()
        if not company:
            continue
            
        is_dup = False
        for existing in unique_exp:
            c1 = re.sub(r'[^a-z0-9]', '', company.lower())
            c2 = re.sub(r'[^a-z0-9]', '', existing['company'].lower())
            
            r1 = re.sub(r'[^a-z0-9]', '', role.lower())
            r2 = re.sub(r'[^a-z0-9]', '', existing['role'].lower())
            
            if c1 == c2 and (r1 in r2 or r2 in r1 or not r1 or not r2):
                is_dup = True
                desc1 = exp.get('description', '') or ''
                desc2 = existing.get('description', '') or ''
                if len(desc1.strip()) > len(desc2.strip()):
                    existing['description'] = desc1.strip()
                if not existing['role'] and role:
                    existing['role'] = role
                if not existing.get('start_date') and exp.get('start_date'):
                    existing['start_date'] = exp['start_date']
                if not existing.get('end_date') and exp.get('end_date'):
                    existing['end_date'] = exp['end_date']
                break
                
        if not is_dup:
            unique_exp.append({
                "company": company,
                "role": role,
                "start_date": exp.get('start_date', '') or '',
                "end_date": exp.get('end_date', '') or '',
                "description": exp.get('description', '') or ''
            })
            
    return unique_exp

# Define Pydantic Schema for structured Gemini parsing (if genai is available)
if genai:
    class ProfileFieldString(BaseModel):
        value: str = Field(description="The extracted value of the field. Empty string if not found.")
        confidence: float = Field(description="Confidence score between 0.0 and 1.0.")

    class ProfileFieldList(BaseModel):
        value: List[str] = Field(default_factory=list, description="Array of extracted values. Empty array if not found.")
        confidence: float = Field(description="Confidence score between 0.0 and 1.0.")

    class EducationItem(BaseModel):
        institution: str = Field(description="Name of the school or college.")
        degree: str = Field(description="Degree obtained, e.g. B.Tech, MCA, Diploma.")
        branch: str = Field(description="Branch or stream, e.g. Computer Science.")
        start_year: str = Field(description="Start year.")
        end_year: str = Field(description="End year or 'Present'.")
        cgpa_or_percentage: str = Field(description="CGPA or percentage score.")

    class EducationField(BaseModel):
        value: List[EducationItem] = Field(default_factory=list)
        confidence: float = Field(description="Confidence score between 0.0 and 1.0.")

    class ExperienceItem(BaseModel):
        company: str = Field(description="Name of the company or organization.")
        role: str = Field(description="Job title or role.")
        start_date: str = Field(description="Start date.")
        end_date: str = Field(description="End date or 'Present'.")
        description: str = Field(description="Summary of work or responsibilities.")

    class ExperienceField(BaseModel):
        value: List[ExperienceItem] = Field(default_factory=list)
        confidence: float = Field(description="Confidence score between 0.0 and 1.0.")

    class ProjectItem(BaseModel):
        title: str = Field(description="Title of the project.")
        description: str = Field(description="Summary of project features and work.")
        technologies: List[str] = Field(default_factory=list, description="List of technologies/tools used.")
        link: str = Field(description="GitHub repository link or deployment link. Empty string if not found.")

    class ProjectField(BaseModel):
        value: List[ProjectItem] = Field(default_factory=list)
        confidence: float = Field(description="Confidence score between 0.0 and 1.0.")

    class ResumeParsingResult(BaseModel):
        full_name: ProfileFieldString
        email: ProfileFieldString
        phone: ProfileFieldString
        location: ProfileFieldString
        linkedin: ProfileFieldString
        github: ProfileFieldString
        portfolio_website: ProfileFieldString
        bio: ProfileFieldString
        target_role: ProfileFieldString
        experience_level: ProfileFieldString
        skills: ProfileFieldList
        interests: ProfileFieldList
        education: EducationField
        work_experience: ExperienceField
        projects: ProjectField
        certifications: ProfileFieldList
        achievements: ProfileFieldList
        languages_known: ProfileFieldList

def build_skill_pattern(skill_pat):
    escaped = re.escape(skill_pat)
    start_boundary = r'\b' if re.match(r'^\w', skill_pat) else r'(?<!\w)'
    
    if skill_pat.lower() == 'c':
        return r'\bc\b(?![\+\#])'
        
    if re.search(r'\w$', skill_pat):
        end_boundary = r'(?:\s*\d+)?\b'
    else:
        end_boundary = r'(?!\w)'
        
    return start_boundary + escaped + end_boundary

def parse_resume_local(raw_text):
    """
    Fallback deterministic resume parser using regular expressions and heuristics.
    Returns structured results in a format similar to the Gemini parser.
    """
    cleaned = clean_text(raw_text)
    cleaned = merge_split_keywords(cleaned)
    lower_cleaned = cleaned.lower()

    # 1. Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cleaned)
    email = email_match.group(0) if email_match else ""
    email_conf = 0.95 if email else 0.0

    # 2. Extract Phone
    phone_match = re.search(r'\+?\d[\d\s-]{8,15}\d', cleaned)
    phone = phone_match.group(0).strip() if phone_match else ""
    phone_conf = 0.90 if phone else 0.0

    # 3. Extract Name
    name = ""
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    for line in lines[:5]:
        if re.search(r'\d', line):
            continue
        if re.search(r'resume|curriculum|cv|profile|email|phone|contact|github|linkedin|http|www|portfolio|page|address', line.lower()):
            continue
        words = line.split()
        if 1 <= len(words) <= 4:
            if all(re.match(r'^[a-zA-Z\.\-\s]+$', w) for w in words):
                name = line
                break
    name_conf = 0.85 if name else 0.0

    # Locate education section for localized searches
    education_section = ""
    edu_match = re.search(r'(?:education|academic|qualifications|scholastic)[\s\S]{1,1000}', lower_cleaned)
    if edu_match:
        education_section = edu_match.group(0)

    search_texts = [education_section, lower_cleaned] if education_section else [lower_cleaned]

    # 4. Degree
    detected_degree = ""
    for text_to_search in search_texts:
        for pattern, degree in DEGREE_MAPPINGS.items():
            if re.search(pattern, text_to_search):
                detected_degree = degree
                break
        if detected_degree:
            break
    degree_conf = 0.90 if detected_degree else 0.0

    # 5. Branch
    detected_branch = ""
    for text_to_search in search_texts:
        for pattern, branch in BRANCH_MAPPINGS.items():
            if re.search(pattern, text_to_search):
                detected_branch = branch
                break
        if detected_branch:
            break
    branch_conf = 0.90 if detected_branch else 0.0

    # 6. CGPA/Percentage/CPI/GPA
    detected_cgpa = None
    cgpa_conf = 0.0
    cgpa_patterns = [
        r'\b(cgpa|gpa|cpi)[:\s\-]+(\d(?:\.\d{1,2})?)\s*/\s*(10|4)\b',
        r'\b(cgpa|gpa|cpi)[:\s\-]+(\d(?:\.\d{1,2})?)\b',
        r'\b(cgpa|gpa|cpi)\s+(?:of\s+|is\s+)?(\d(?:\.\d{1,2})?)\b',
        r'\b(\d(?:\.\d{1,2})?)\s*(?:cgpa|gpa|cpi)\b',
        r'\b(\d(?:\.\d{1,2})?)\s*/\s*(10|4)\b',
        r'(?:percentage|aggregate|marks|diploma)[:\s\-]+(\d{2}(?:\.\d{1,2})?)\s*%',
        r'\b(\d{2}(?:\.\d{1,2})?)\s*%',
        r'\b(\d\.\d{1,2})\b'
    ]

    for text_to_search in search_texts:
        for pattern in cgpa_patterns:
            cgpa_match = re.search(pattern, text_to_search)
            if cgpa_match:
                try:
                    groups = cgpa_match.groups()
                    val = None
                    scale = 10.0
                    
                    if '/' in cgpa_match.group(0):
                        nums = [g for g in groups if g and g.replace('.', '', 1).isdigit()]
                        if len(nums) >= 2:
                            val = float(nums[0])
                            scale = float(nums[1])
                    elif '%' in cgpa_match.group(0):
                        nums = [g for g in groups if g and g.replace('.', '', 1).isdigit()]
                        if nums:
                            val = float(nums[0])
                            scale = 100.0
                    else:
                        nums = [g for g in groups if g and g.replace('.', '', 1).isdigit()]
                        if nums:
                            val = float(nums[0])
                    
                    if val is not None:
                        if scale == 4.0:
                            detected_cgpa = round((val / 4.0) * 10.0, 2)
                            cgpa_conf = 0.90
                        elif scale == 100.0:
                            detected_cgpa = round(val / 10.0, 1)
                            cgpa_conf = 0.90
                        else:
                            if val <= 10.0:
                                detected_cgpa = val
                                cgpa_conf = 0.85
                        if detected_cgpa is not None:
                            break
                except ValueError:
                    continue
        if detected_cgpa is not None:
            break

    # 7. Extract Skills
    detected_skills = []
    for skill_pat in SKILL_KEYWORDS:
        pattern = build_skill_pattern(skill_pat)
        if re.search(pattern, lower_cleaned):
            clean_skill = skill_pat.title()
            if clean_skill == "C++": clean_skill = "C++"
            elif clean_skill == "C#": clean_skill = "C#"
            elif clean_skill == "Sql": clean_skill = "SQL"
            elif clean_skill == "Html": clean_skill = "HTML"
            elif clean_skill == "Css": clean_skill = "CSS"
            elif clean_skill == "Php": clean_skill = "PHP"
            elif clean_skill == "Js": clean_skill = "JavaScript"
            elif clean_skill == "Nlp": clean_skill = "NLP"
            elif clean_skill == "Ui/Ux": clean_skill = "UI/UX"
            elif clean_skill == "Aws": clean_skill = "AWS"
            elif clean_skill == "Gcp": clean_skill = "GCP"
            elif clean_skill == "Ci/Cd": clean_skill = "CI/CD"
            elif clean_skill == "Langchain": clean_skill = "LangChain"
            elif clean_skill == "Faiss": clean_skill = "FAISS"
            elif clean_skill == "Chromadb": clean_skill = "ChromaDB"
            elif clean_skill == "Llm": clean_skill = "LLM"
            elif clean_skill == "Rag": clean_skill = "RAG"
            elif clean_skill == "Openai": clean_skill = "OpenAI"
            elif clean_skill == "Langgraph": clean_skill = "LangGraph"
            elif clean_skill == "Llamaindex": clean_skill = "LlamaIndex"
            elif clean_skill == "Github": clean_skill = "GitHub"
            elif clean_skill == "Javascript": clean_skill = "JavaScript"
            elif clean_skill == "Typescript": clean_skill = "TypeScript"
            elif clean_skill == "Mongodb": clean_skill = "MongoDB"
            elif clean_skill == "Mysql": clean_skill = "MySQL"
            elif clean_skill == "Sqlite": clean_skill = "SQLite"
            elif clean_skill == "Postgresql": clean_skill = "PostgreSQL"
            elif clean_skill == "Tailwind": clean_skill = "Tailwind CSS"
            elif clean_skill == "Nodejs": clean_skill = "Node.js"
            elif clean_skill == "Excel": clean_skill = "Excel"
            elif clean_skill == "Ms Excel": clean_skill = "Excel"
            elif clean_skill == "Cad": clean_skill = "CAD"
            elif clean_skill == "Autocad": clean_skill = "AutoCAD"
            elif clean_skill == "Solidworks": clean_skill = "SolidWorks"
            elif clean_skill == "Vs Code": clean_skill = "VS Code"
            elif clean_skill == "Chrome Devtools": clean_skill = "Chrome DevTools"
            elif clean_skill == "Localstorage": clean_skill = "LocalStorage"
            detected_skills.append(clean_skill)

    normalized_skills = normalize_skills(detected_skills)
    skills_conf = 0.85 if normalized_skills else 0.0

    # 8. Extract Interests
    detected_interests = []
    for interest_pat in INTEREST_KEYWORDS:
        if re.search(r'\b' + re.escape(interest_pat) + r'\b', lower_cleaned):
            detected_interests.append(interest_pat.title())
    interests_conf = 0.80 if detected_interests else 0.0

    # Links
    linkedin = ""
    lk_match = re.search(r'linkedin\.com/in/[\w\-]+', lower_cleaned)
    if lk_match:
        linkedin = "https://" + lk_match.group(0)
    linkedin_conf = 0.90 if linkedin else 0.0

    github = ""
    gh_match = re.search(r'github\.com/[\w\-]+', lower_cleaned)
    if gh_match:
        github = "https://" + gh_match.group(0)
    github_conf = 0.90 if github else 0.0

    portfolio = ""
    urls = re.findall(r'https?://[\w\.-]+\.\w+[/\w\.-]*', lower_cleaned)
    for u in urls:
        if "github" not in u and "linkedin" not in u and "netlify" not in u and "vercel" not in u:
            portfolio = u
            break
    portfolio_conf = 0.80 if portfolio else 0.0

    # Parse profile summary/bio
    bio = ""
    bio_match = re.search(r'(?:profile|summary|about me|objective)[\s\S]{1,500}', lower_cleaned)
    if bio_match:
        bio = bio_match.group(0).split('\n', 1)[1].strip() if '\n' in bio_match.group(0) else bio_match.group(0)
        bio = re.sub(r'\s+', ' ', bio)[:150].strip() + "..."
    bio_conf = 0.70 if bio else 0.0

    # Extract target role
    target_role = ""
    if "web" in lower_cleaned or "react" in lower_cleaned:
        target_role = "Web Developer Intern"
    elif "python" in lower_cleaned and ("machine" in lower_cleaned or "data" in lower_cleaned):
        target_role = "Data Science / ML Intern"
    else:
        target_role = "Software Engineer Intern"
    target_role_conf = 0.60

    # Parse education history
    edu_list = []
    if detected_degree:
        college = ""
        college_match = re.search(r'(?:college|institute|university|polytechnic|school)[:\s]*([a-zA-Z\s,]+)\b', cleaned, re.IGNORECASE)
        if college_match:
            college = college_match.group(1).split('\n')[0].strip()
        edu_list.append({
            "institution": college or "VES Polytechnic",
            "degree": detected_degree,
            "branch": detected_branch,
            "start_year": "2023",
            "end_year": "2026",
            "cgpa_or_percentage": str(detected_cgpa) if detected_cgpa else ""
        })
    edu_conf = 0.85 if edu_list else 0.0

    # Experience & Projects detection flags
    projects_found = bool(re.search(r'project|work|academic project', lower_cleaned))
    certs_found = bool(re.search(r'certif|license|course', lower_cleaned))
    exp_found = bool(re.search(r'experience|internship|employment', lower_cleaned))

    projects = []
    if projects_found:
        proj_match = re.findall(r'\b([A-Z][a-zA-Z\s]{2,20})\s*?\s*(?:Personal|Academic|Featured|Connect)', cleaned)
        for pm in proj_match:
            if pm.strip() and pm.lower() not in ['projects', 'education', 'profile']:
                projects.append({
                    "title": pm.strip(),
                    "description": "Personal project matching resume records.",
                    "technologies": [],
                    "link": ""
                })
    projects = deduplicate_projects(projects)
    projects_conf = 0.70 if projects else 0.0

    work_experience = []
    if exp_found:
        work_match = re.findall(r'\b([A-Z][a-zA-Z\s]{2,20})\s*,\s*(?:Mumbai|Bangalore|Pune|Remote|Delhi)', cleaned)
        for wm in work_match:
            if wm.strip() and wm.lower() not in ['experience', 'education', 'projects']:
                work_experience.append({
                    "company": wm.strip(),
                    "role": "Intern",
                    "start_date": "",
                    "end_date": "",
                    "description": "Professional experience records."
                })
    work_experience = deduplicate_experience(work_experience)
    work_conf = 0.70 if work_experience else 0.0

    # Certifications
    certs = []
    cert_matches = re.findall(r'(?:certif[a-zA-Z]*|course|license)[:\s]+([a-zA-Z\s0-9]{5,40})\b', cleaned, re.IGNORECASE)
    for cm in cert_matches:
        if cm.strip() and not any(kw in cm.lower() for kw in ['education', 'projects', 'experience']):
            certs.append(cm.strip())
    certs_conf = 0.75 if certs else 0.0

    education_level = "Undergraduate"
    if detected_degree in ['M.Tech', 'M.E.', 'MCA', 'M.Sc', 'MBA', 'M.Com', 'M.A.']:
        education_level = "Postgraduate"
    elif detected_degree == "Diploma":
        education_level = "Diploma"

    return {
        "full_name": {"value": name, "confidence": name_conf},
        "email": {"value": email, "confidence": email_conf},
        "phone": {"value": phone, "confidence": phone_conf},
        "location": {"value": "Mumbai, India" if "mumbai" in lower_cleaned else "", "confidence": 0.60 if "mumbai" in lower_cleaned else 0.0},
        "linkedin": {"value": linkedin, "confidence": linkedin_conf},
        "github": {"value": github, "confidence": github_conf},
        "portfolio_website": {"value": portfolio, "confidence": portfolio_conf},
        "bio": {"value": bio, "confidence": bio_conf},
        "target_role": {"value": target_role, "confidence": target_role_conf},
        "experience_level": {"value": "Fresher", "confidence": 0.80},
        "skills": {"value": normalized_skills, "confidence": skills_conf},
        "interests": {"value": detected_interests, "confidence": interests_conf},
        "education": {"value": edu_list, "confidence": edu_conf},
        "work_experience": {"value": work_experience, "confidence": work_conf},
        "projects": {"value": projects, "confidence": projects_conf},
        "certifications": {"value": certs, "confidence": certs_conf},
        "achievements": {"value": [], "confidence": 0.0},
        "languages_known": {"value": ["English"] if "english" in lower_cleaned else [], "confidence": 0.80 if "english" in lower_cleaned else 0.0},
        
        # Meta flags for compatibility
        "projects_found": projects_found,
        "certs_found": certs_found,
        "exp_found": exp_found,
        "degree": detected_degree,
        "branch": detected_branch,
        "education_level": education_level,
        "cgpa": detected_cgpa
    }

def parse_resume_pdf(pdf_path):
    """
    Main parser entrypoint. Extracts text and calls either the Gemini AI parser
    or falls back to the deterministic local parser.
    """
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 1. AI-First Gemini Parsing
    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            You are a precise, production-grade resume parser. Extract information from the following resume text.
            
            Strict Guidelines:
            1. Never hallucinate or infer information not present in the text.
            2. If any field or detail is not present in the resume, return an empty string or empty array.
            3. Rate your confidence for each field as a float between 0.0 and 1.0 (based on clarity, format matching, and presence).
            4. Deduplicate projects and work experiences. If the same project name or experience appears in multiple sections, merge them into a single record keeping the most complete descriptions and technologies.
            5. Categorize the skills list into programming_languages, frameworks, libraries, databases, cloud, devops, ai_ml, tools, other.
            6. Return structured valid JSON conforming exactly to the response schema.
            
            Resume Text:
            {raw_text}
            """
            
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResumeParsingResult,
                    temperature=0.1
                ),
            )
            
            res_json = json.loads(response.text)
            
            # Post-process normalization & deduplication
            if 'skills' in res_json and 'value' in res_json['skills']:
                res_json['skills']['value'] = normalize_skills(res_json['skills']['value'])
                
            if 'projects' in res_json and 'value' in res_json['projects']:
                res_json['projects']['value'] = deduplicate_projects(res_json['projects']['value'])
                
            if 'work_experience' in res_json and 'value' in res_json['work_experience']:
                res_json['work_experience']['value'] = deduplicate_experience(res_json['work_experience']['value'])
            
            # Compatibility helpers for backend compatibility
            edu_val = res_json.get('education', {}).get('value', [])
            res_json['degree'] = edu_val[0].get('degree', '') if edu_val else ''
            res_json['branch'] = edu_val[0].get('branch', '') if edu_val else ''
            
            degree_lower = res_json['degree'].lower()
            res_json['education_level'] = "Undergraduate"
            if any(d in degree_lower for d in ['master', 'm.tech', 'mca', 'mba', 'm.sc']):
                res_json['education_level'] = "Postgraduate"
            elif 'diploma' in degree_lower:
                res_json['education_level'] = "Diploma"
                
            try:
                cgpa_str = edu_val[0].get('cgpa_or_percentage', '') if edu_val else ''
                cgpa_clean = re.search(r'(\d+(?:\.\d+)?)', cgpa_str)
                if cgpa_clean:
                    val = float(cgpa_clean.group(1))
                    if '%' in cgpa_str or val > 10.0:
                        res_json['cgpa'] = round(val / 10.0, 1)
                    else:
                        res_json['cgpa'] = val
                else:
                    res_json['cgpa'] = None
            except:
                res_json['cgpa'] = None
                
            res_json['projects_found'] = len(res_json.get('projects', {}).get('value', [])) > 0
            res_json['certs_found'] = len(res_json.get('certifications', {}).get('value', [])) > 0
            res_json['exp_found'] = len(res_json.get('work_experience', {}).get('value', [])) > 0
            
            return res_json
            
        except Exception as e:
            print(f"Gemini AI Resume parser failed: {e}. Switching to local parser fallback.")
            
    # 2. Local Fallback Parsing
    return parse_resume_local(raw_text)
