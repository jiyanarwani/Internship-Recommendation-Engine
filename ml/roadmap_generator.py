# Curated directory mapping skills to learning resources
SKILL_RESOURCES = {
    'Python': {
        'course_name': 'Python for Everybody Specialization',
        'platform': 'Coursera / freeCodeCamp',
        'hours': 20,
        'url': 'https://www.coursera.org/specializations/python',
        'topics': ['Syntax & Variables', 'Lists & Dictionaries', 'Functions & Loops', 'File Handling', 'APIs']
    },
    'Flask': {
        'course_name': 'Flask Web Development Course',
        'platform': 'freeCodeCamp (YouTube) / Official Docs',
        'hours': 12,
        'url': 'https://flask.palletsprojects.com/',
        'topics': ['Routing & Views', 'Templates (Jinja2)', 'Flask-SQLAlchemy Database Integration', 'User Sessions', 'RESTful APIs']
    },
    'Docker': {
        'course_name': 'Docker for Beginners',
        'platform': 'KodeKloud / freeCodeCamp',
        'hours': 8,
        'url': 'https://www.docker.com/get-started/',
        'topics': ['Containers vs VMs', 'Dockerfile Basics', 'Docker Images', 'Container Volumes', 'Docker Compose']
    },
    'PostgreSQL': {
        'course_name': 'Intro to PostgreSQL & Relational DBs',
        'platform': 'Udacity / Khan Academy',
        'hours': 15,
        'url': 'https://www.postgresql.org/docs/',
        'topics': ['Relational Schema Design', 'SQL Queries (SELECT, JOIN)', 'Indexes & Optimization', 'Database Migrations']
    },
    'SQL': {
        'course_name': 'SQL Boot Camp',
        'platform': 'Khan Academy / SQLBolt',
        'hours': 10,
        'url': 'https://sqlbolt.com/',
        'topics': ['SELECT Statements', 'Filtering & Sorting', 'Aggregations (GROUP BY)', 'JOINS', 'Subqueries']
    },
    'React': {
        'course_name': 'React Official Tutorial & Full Course',
        'platform': 'Scrimba / React.dev',
        'hours': 24,
        'url': 'https://react.dev/',
        'topics': ['Components & Props', 'State Management (useState)', 'Hooks (useEffect)', 'Virtual DOM', 'Routing (React Router)']
    },
    'JavaScript': {
        'course_name': 'Modern JavaScript From The Beginning',
        'platform': 'MDN Web Docs / JavaScript.info',
        'hours': 18,
        'url': 'https://javascript.info/',
        'topics': ['DOM Manipulation', 'ES6+ Syntax', 'Asynchronous JS (Promises, Async/Await)', 'Fetch API & JSON']
    },
    'Machine Learning': {
        'course_name': 'Supervised Machine Learning: Regression and Classification',
        'platform': 'DeepLearning.AI / Coursera',
        'hours': 35,
        'url': 'https://www.coursera.org/specializations/machine-learning-introduction',
        'topics': ['Linear & Logistic Regression', 'Overfitting & Regularization', 'Decision Trees', 'Feature Engineering', 'Model Evaluation']
    },
    'HTML': {
        'course_name': 'HTML5 & CSS3 Basics',
        'platform': 'MDN Web Docs / freeCodeCamp',
        'hours': 6,
        'url': 'https://developer.mozilla.org/en-US/docs/Web/HTML',
        'topics': ['Semantic HTML Tags', 'Forms & Inputs', 'SEO Basics', 'Accessibility (ARIA)']
    },
    'CSS': {
        'course_name': 'CSS Grid & Flexbox Masterclass',
        'platform': 'CSS-Tricks / MDN Web Docs',
        'hours': 8,
        'url': 'https://developer.mozilla.org/en-US/docs/Web/CSS',
        'topics': ['Box Model', 'Flexbox Layouts', 'CSS Grid', 'Media Queries & Responsiveness', 'Transitions & Keyframe Animations']
    },
    'Git': {
        'course_name': 'Git & GitHub Version Control',
        'platform': 'GitHub Learning Lab',
        'hours': 5,
        'url': 'https://github.com/resources/videos/git-learning-resources',
        'topics': ['Repository Init & Cloning', 'Branching & Merging', 'Commits & Reverting', 'Pull Requests & Collaboration']
    },
    'AWS': {
        'course_name': 'AWS Certified Cloud Practitioner',
        'platform': 'AWS Skill Builder / freeCodeCamp',
        'hours': 15,
        'url': 'https://aws.amazon.com/training/',
        'topics': ['EC2 Instances', 'S3 Storage buckets', 'IAM Security Roles', 'RDS Database hosting', 'CloudFront CDN']
    }
}

def generate_roadmap(missing_skills):
    """
    Given a list of missing skills, generates gap details and a weekly roadmap.
    """
    if not missing_skills:
        return {
            "has_gap": False,
            "roadmap": [
                {
                    "week": 1,
                    "title": "Build a Portfolio Project",
                    "description": "You already have all the required skills! Use this time to build a robust open-source project to showcase on your profile.",
                    "platform": "GitHub",
                    "hours": 15,
                    "topics": ["Setup repository", "Structure project code", "Deploy demo online", "Add README documentation"]
                }
            ]
        }

    roadmap_steps = []
    gap_details = []
    
    # Process each missing skill
    for i, skill in enumerate(missing_skills):
        week_num = i + 1
        
        # Check standard lookup table, fallback to dynamic generator
        skill_clean = skill.strip()
        skill_key = next((k for k in SKILL_RESOURCES.keys() if k.lower() == skill_clean.lower()), None)
        
        if skill_key:
            res = SKILL_RESOURCES[skill_key]
        else:
            # Fallback info
            res = {
                'course_name': f'{skill_clean} Fundamentals & Advanced Concepts',
                'platform': 'Udemy / Official Documentation',
                'hours': 10,
                'url': f'https://www.google.com/search?q={skill_clean}+official+documentation',
                'topics': [f'{skill_clean} syntax & principles', 'Best practices & design patterns', f'Building a simple {skill_clean} application']
            }
            
        gap_details.append({
            "skill": skill_clean,
            "course": res["course_name"],
            "platform": res["platform"],
            "hours": res["hours"],
            "url": res["url"]
        })
        
        roadmap_steps.append({
            "week": week_num,
            "title": f"Master {skill_clean}",
            "description": f"Focus on building core competencies in {skill_clean} using the recommended material on {res['platform']}.",
            "course_name": res["course_name"],
            "url": res["url"],
            "hours": res["hours"],
            "topics": res["topics"]
        })
        
    # Append a final capstone project week
    final_week = len(missing_skills) + 1
    roadmap_steps.append({
        "week": final_week,
        "title": "Capstone Project Integration",
        "description": "Integrate all newly learned skills into a single, comprehensive capstone project. Deploy it online to demonstrate proficiency.",
        "course_name": "Project Building & Deployment",
        "url": "https://github.com",
        "hours": 12,
        "topics": ["Architecture design", "Database design", "Frontend integration", "Deployment to cloud"]
    })

    return {
        "has_gap": True,
        "gap_details": gap_details,
        "roadmap": roadmap_steps
    }
