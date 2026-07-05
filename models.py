import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='candidate')  # 'candidate' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    saved_internships = db.relationship('SavedInternship', backref='user', cascade="all, delete-orphan")
    recommendations = db.relationship('RecommendationHistory', backref='user', cascade="all, delete-orphan")
    applications = db.relationship('ApplicationHistory', backref='user', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    college = db.Column(db.String(200), nullable=True)
    education_level = db.Column(db.String(100), nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    branch = db.Column(db.String(100), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    
    # Stored as JSON strings
    _skills = db.Column(db.Text, default='[]')
    _interests = db.Column(db.Text, default='[]')
    
    preferred_industry = db.Column(db.String(100), nullable=True)
    preferred_job_role = db.Column(db.String(100), nullable=True)
    preferred_location = db.Column(db.String(100), nullable=True)
    resume_filename = db.Column(db.String(200), nullable=True)
    
    @property
    def skills(self):
        try:
            return json.loads(self._skills) if self._skills else []
        except:
            return []
            
    @skills.setter
    def skills(self, value):
        self._skills = json.dumps(value if isinstance(value, list) else [])
        
    @property
    def interests(self):
        try:
            return json.loads(self._interests) if self._interests else []
        except:
            return []
            
    @interests.setter
    def interests(self, value):
        self._interests = json.dumps(value if isinstance(value, list) else [])

class Internship(db.Model):
    __tablename__ = 'internships'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    company_logo = db.Column(db.String(500), nullable=True)  # URL or base64 or placeholder
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.Text, nullable=True)  # Comma-separated or bullet points
    
    # Stored as JSON strings
    _required_skills = db.Column(db.Text, default='[]')
    
    eligibility_criteria = db.Column(db.Text, nullable=True)
    degree_requirement = db.Column(db.String(100), nullable=True)
    
    # Stored as JSON strings
    _branch_requirement = db.Column(db.Text, default='[]')
    
    location = db.Column(db.String(100), nullable=False)
    mode = db.Column(db.String(50), nullable=False)  # 'Remote', 'Hybrid', 'Onsite'
    duration = db.Column(db.Integer, nullable=False)  # in months
    stipend = db.Column(db.Integer, nullable=False)  # per month in INR
    industry = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    application_deadline = db.Column(db.String(50), nullable=True)  # Date string or DateTime
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def required_skills(self):
        try:
            return json.loads(self._required_skills) if self._required_skills else []
        except:
            return []
            
    @required_skills.setter
    def required_skills(self, value):
        self._required_skills = json.dumps(value if isinstance(value, list) else [])
        
    @property
    def branch_requirement(self):
        try:
            return json.loads(self._branch_requirement) if self._branch_requirement else []
        except:
            return []
            
    @branch_requirement.setter
    def branch_requirement(self, value):
        self._branch_requirement = json.dumps(value if isinstance(value, list) else [])

class SavedInternship(db.Model):
    __tablename__ = 'saved_internships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internships.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='saved')  # 'saved' or 'applied'
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    internship = db.relationship('Internship')

class RecommendationHistory(db.Model):
    __tablename__ = 'recommendation_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internships.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    
    # Stored details for explainable AI
    _reasons = db.Column(db.Text, default='[]')
    _missing_skills = db.Column(db.Text, default='[]')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    internship = db.relationship('Internship')
    
    @property
    def reasons(self):
        try:
            return json.loads(self._reasons) if self._reasons else []
        except:
            return []
            
    @reasons.setter
    def reasons(self, value):
        self._reasons = json.dumps(value if isinstance(value, list) else [])
        
    @property
    def missing_skills(self):
        try:
            return json.loads(self._missing_skills) if self._missing_skills else []
        except:
            return []
            
    @missing_skills.setter
    def missing_skills(self, value):
        self._missing_skills = json.dumps(value if isinstance(value, list) else [])

class ApplicationHistory(db.Model):
    __tablename__ = 'application_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internships.id', ondelete='CASCADE'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    internship = db.relationship('Internship')
