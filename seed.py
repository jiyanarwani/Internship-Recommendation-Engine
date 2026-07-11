from models import db, User, Profile, Internship
from datetime import datetime

def seed_database():
    from app import create_app
    app = create_app()
    with app.app_context():
        # Drop all and recreate tables
        db.drop_all()
        db.create_all()
        perform_seed()

def perform_seed():
    print("Database tables initialized. Seeding records...")
    
    # 1. Create Admin User
    admin = User(email="admin@pm-internship.gov.in", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    
    # 2. Create Student User
    student = User(email="student@pm-internship.gov.in", role="candidate")
    student.set_password("student123")
    db.session.add(student)
    db.session.commit()  # commit to get student.id
    
    # Create Student Profile
    student_profile = Profile(
        user_id=student.id,
        full_name="Aarav Sharma",
        phone="+91-98765-43210",
        college="Indian Institute of Technology, Bombay",
        degree="B.Tech",
        branch="Computer Science",
        graduation_year=2027,
        cgpa=8.9,
        skills=["Python", "Flask", "SQL", "JavaScript", "HTML", "CSS", "Git"],
        interests=["Web Development", "Artificial Intelligence", "Software Engineering"],
        preferred_industry="IT",
        preferred_job_role="Software Developer",
        preferred_location="Mumbai"
    )
    db.session.add(student_profile)
    
    # 3. Seed Internships
    internships_data = [
        {
            "company_name": "Infosys",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/9/95/Infosys_logo.svg",
            "title": "Systems Engineer Intern",
            "description": "Collaborate with our operations and engineering team to maintain, scale, and optimize enterprise systems. Work on writing test plans, automating deployment pipelines, and scripting utility tools.",
            "responsibilities": "Support network administrators in diagnosing errors, write shell scripts for task automation, configure systems settings, test software builds for sanity checkpoints.",
            "required_skills": ["Java", "Linux", "Git", "SQL"],
            "eligibility_criteria": "Pursuing B.Tech or BCA with no active backlogs. Minimum CGPA of 6.0.",
            "degree_requirement": "B.Tech",
            "branch_requirement": ["Computer Science", "Information Technology", "Electronics & Communication"],
            "location": "Bangalore",
            "mode": "Remote",
            "duration": 6,
            "stipend": 15000,
            "industry": "IT",
            "category": "Software Engineering",
            "application_deadline": "2026-09-30"
        },
        {
            "company_name": "TCS",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg",
            "title": "Junior Web Developer",
            "description": "Join our digital solutions unit to build front-facing user dashboards, optimize website responsiveness, and link backend web APIs to client screens.",
            "responsibilities": "Translate Figma designs into HTML/CSS code, script interactive front-end components, integrate APIs, perform cross-browser usability tests.",
            "required_skills": ["HTML", "CSS", "JavaScript", "React"],
            "eligibility_criteria": "Undergraduates in B.Sc, BCA, or B.Tech with functional knowledge of modern DOM structure.",
            "degree_requirement": "Any",
            "branch_requirement": ["Computer Science", "Information Technology", "Electronics & Communication", "Science"],
            "location": "Mumbai",
            "mode": "Hybrid",
            "duration": 3,
            "stipend": 18000,
            "industry": "IT",
            "category": "Web Development",
            "application_deadline": "2026-10-15"
        },
        {
            "company_name": "Reliance Jio",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Jio_Logo.svg",
            "title": "Networks Engineering Associate",
            "description": "Engage in managing and diagnosing issues inside core mobile connectivity protocols. Understand cloud networking patterns and virtual hardware controllers.",
            "responsibilities": "Audit network configurations, assist core architects in monitoring server latency, log system telemetry, map physical cable pathways.",
            "required_skills": ["Linux", "Python", "SQL", "Docker"],
            "eligibility_criteria": "Pursuing B.Tech in Electronics/Electrical branches. Min CGPA 7.0 required.",
            "degree_requirement": "B.Tech",
            "branch_requirement": ["Electrical Engineering", "Electronics & Communication", "Computer Science"],
            "location": "Navi Mumbai",
            "mode": "Onsite",
            "duration": 6,
            "stipend": 20000,
            "industry": "IT",
            "category": "Network Engineering",
            "application_deadline": "2026-09-20"
        },
        {
            "company_name": "Wipro",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Wipro_Logo.svg",
            "title": "Cloud Operations Analyst",
            "description": "Work with our Cloud Deployment wing to audit server configurations, manage backup routines, and optimize system access structures.",
            "responsibilities": "Track AWS console usage metrics, script custom backup policies in Python, update Linux server parameters, monitor access permissions.",
            "required_skills": ["AWS", "Linux", "Python", "Git"],
            "eligibility_criteria": "Students in BCA, MCA, or B.Tech. Understanding of basic cloud computing concepts is a plus.",
            "degree_requirement": "Any",
            "branch_requirement": ["Computer Science", "Information Technology"],
            "location": "Pune",
            "mode": "Remote",
            "duration": 6,
            "stipend": 16000,
            "industry": "IT",
            "category": "Cloud Computing",
            "application_deadline": "2026-11-01"
        },
        {
            "company_name": "Google",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_\"G\"_logo.svg",
            "title": "Software Engineering Intern (STEP)",
            "description": "An introductory internship program designed for undergraduate computer science students. Work on writing client-facing features or optimization scripts for global software.",
            "responsibilities": "Write clean C++ or Python code, participate in code reviews, design algorithms for optimization tasks, present final project to engineers.",
            "required_skills": ["Python", "Java", "C++", "Git"],
            "eligibility_criteria": "Second-year B.Tech students pursuing Computer Science. Strong foundation in Data Structures and Algorithms is required. Minimum CGPA of 8.0.",
            "degree_requirement": "B.Tech",
            "branch_requirement": ["Computer Science", "Information Technology"],
            "location": "Hyderabad",
            "mode": "Onsite",
            "duration": 3,
            "stipend": 50000,
            "industry": "IT",
            "category": "Software Engineering",
            "application_deadline": "2026-08-30"
        },
        {
            "company_name": "Microsoft",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/9/96/Microsoft_logo_%282012%29.svg",
            "title": "Data Analyst Intern",
            "description": "Analyze operational metrics across various consumer services. Leverage large datasets to build visualizations and deliver trends report to operations leads.",
            "responsibilities": "Clean large-scale datasets, construct SQL database scripts, compile interactive reports in Power BI, write Python analysis scripts.",
            "required_skills": ["SQL", "Python", "Pandas", "Tableau"],
            "eligibility_criteria": "Candidates pursuing BCA, MCA, B.Sc or B.Tech with analytical background. Min CGPA 7.5.",
            "degree_requirement": "B.Tech",
            "branch_requirement": ["Computer Science", "Information Technology", "Mathematics & Computing"],
            "location": "Bangalore",
            "mode": "Hybrid",
            "duration": 6,
            "stipend": 45000,
            "industry": "IT",
            "category": "Data Analytics",
            "application_deadline": "2026-10-10"
        },
        {
            "company_name": "Amazon",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
            "title": "Machine Learning Engineer Intern",
            "description": "Help our search catalog team optimize recommendation algorithms. Leverage natural language processing (NLP) to parse search intent and catalog matches.",
            "responsibilities": "Train basic classification pipelines, clean and tokenize raw textual data, monitor model accuracy scores, coordinate database logs.",
            "required_skills": ["Python", "Numpy", "Scikit-Learn", "Machine Learning", "Git"],
            "eligibility_criteria": "Pursuing B.Tech, M.Tech or MCA. Must have completed coursework in statistics or linear algebra. Min CGPA 8.0.",
            "degree_requirement": "B.Tech",
            "branch_requirement": ["Computer Science", "Information Technology", "Mathematics & Computing"],
            "location": "Chennai",
            "mode": "Remote",
            "duration": 6,
            "stipend": 48000,
            "industry": "IT",
            "category": "Artificial Intelligence",
            "application_deadline": "2026-09-15"
        },
        {
            "company_name": "Deloitte",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Deloitte_logo_with_tagline.svg",
            "title": "Financial Analyst Associate",
            "description": "Support our financial consultancy wing to review cash flows, balance sheets, and tax reports for corporate compliance accounts.",
            "responsibilities": "Compile cash flow summaries, verify tax invoice details, research regulatory adjustments, construct financial sheets in MS Excel.",
            "required_skills": ["Finance", "Accounting", "SQL", "Excel"],
            "eligibility_criteria": "Candidates pursuing MBA, B.Com, or BBA with specialization in Finance or Accounting.",
            "degree_requirement": "MBA",
            "branch_requirement": ["Finance", "Commerce", "Business Administration"],
            "location": "Hyderabad",
            "mode": "Onsite",
            "duration": 6,
            "stipend": 25000,
            "industry": "Finance",
            "category": "Finance",
            "application_deadline": "2026-10-05"
        },
        {
            "company_name": "Accenture",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/c/cd/Accenture.svg",
            "title": "IT Consultant Intern",
            "description": "Shadow our enterprise architects to design software integration plans for client organizations. Bridge the communication gap between development leads and client leads.",
            "responsibilities": "Draft tech requirements files, create slide briefs on software architectures, compile developer tickets, track deployment schedules.",
            "required_skills": ["Project Management", "Communication", "Agile", "SQL"],
            "eligibility_criteria": "Pursuing degree in B.Tech, BCA, MCA, or MBA. Excellent communication skills are essential.",
            "degree_requirement": "Any",
            "branch_requirement": ["Computer Science", "Information Technology", "Business Administration"],
            "location": "Gurgaon",
            "mode": "Hybrid",
            "duration": 3,
            "stipend": 22000,
            "industry": "IT",
            "category": "Product Management",
            "application_deadline": "2026-10-30"
        },
        {
            "company_name": "Tata Steel",
            "company_logo": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Tata_Steel_Logo.svg",
            "title": "Operations & CAD Intern",
            "description": "Collaborate with plant operations leads to maintain process efficiency sheets, check CAD drafts for components, and coordinate warehouse schedules.",
            "responsibilities": "Audit factory component CAD designs, update raw inventory database logs, track shift efficiency figures, inspect component tolerances.",
            "required_skills": ["Mechanical", "Problem Solving", "Teamwork", "Excel"],
            "eligibility_criteria": "Pursuing B.Tech or Diploma in Mechanical or Industrial engineering. Min CGPA 6.5.",
            "degree_requirement": "B.Tech",
            "branch_requirement": ["Mechanical Engineering", "Civil Engineering"],
            "location": "Jamshedpur",
            "mode": "Onsite",
            "duration": 6,
            "stipend": 17000,
            "industry": "Core Engineering",
            "category": "Core Engineering Operations",
            "application_deadline": "2026-09-10"
        }
    ]
    
    for item in internships_data:
        inst = Internship(
            company_name=item["company_name"],
            company_logo=item["company_logo"],
            title=item["title"],
            description=item["description"],
            responsibilities=item["responsibilities"],
            required_skills=item["required_skills"],
            eligibility_criteria=item["eligibility_criteria"],
            degree_requirement=item["degree_requirement"],
            branch_requirement=item["branch_requirement"],
            location=item["location"],
            mode=item["mode"],
            duration=item["duration"],
            stipend=item["stipend"],
            industry=item["industry"],
            category=item["category"],
            application_deadline=item["application_deadline"]
        )
        db.session.add(inst)
        
        db.session.commit()
        print("Database successfully seeded with default users and 10 internships.")

if __name__ == "__main__":
    seed_database()
