from flask import Blueprint, render_template, request, jsonify, session
from models import db, Internship, Profile, SavedInternship, RecommendationHistory
from ml.recommender import get_recommendations, clean_text
import re

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/internships', methods=['GET'])
def list_internships():
    # Retrieve query parameters
    query = request.args.get('q', '').strip().lower()
    mode_filter = request.args.get('mode', '').strip()  # 'Remote', 'Hybrid', 'Onsite'
    location_filter = request.args.get('location', '').strip()
    industry_filter = request.args.get('industry', '').strip()
    duration_filter = request.args.get('duration', '').strip()  # e.g., '3' or '6'
    skills_filter = request.args.get('skills', '').strip()  # comma separated
    company_filter = request.args.get('company', '').strip()
    sort_by = request.args.get('sort', 'latest').strip().lower()  # 'latest', 'stipend', 'match'

    # Start database query
    query_obj = Internship.query

    # Base filters
    if mode_filter:
        query_obj = query_obj.filter(Internship.mode.ilike(mode_filter))
    if location_filter:
        query_obj = query_obj.filter(Internship.location.ilike(f"%{location_filter}%"))
    if industry_filter:
        query_obj = query_obj.filter(Internship.industry.ilike(f"%{industry_filter}%"))
    if duration_filter:
        try:
            val = int(duration_filter)
            query_obj = query_obj.filter(Internship.duration <= val)
        except ValueError:
            pass
    if company_filter:
        query_obj = query_obj.filter(Internship.company_name.ilike(f"%{company_filter}%"))

    internships = query_obj.all()

    # Client-side filtering for skills
    if skills_filter:
        skills_to_match = [s.strip().lower() for s in skills_filter.split(',') if s.strip()]
        filtered = []
        for inst in internships:
            inst_skills = [s.lower() for s in inst.required_skills]
            if any(s in inst_skills for s in skills_to_match):
                filtered.append(inst)
        internships = filtered

    # Intelligent Query Parsing (e.g. "Python Remote Mumbai")
    if query:
        terms = [t for t in re.split(r'\s+', query) if t]
        scored_internships = []
        for inst in internships:
            score = 0
            inst_text = f"{inst.title} {inst.company_name} {inst.description} {inst.location} {inst.mode} {' '.join(inst.required_skills)}".lower()
            
            for term in terms:
                # Direct match counts
                if term in inst_text:
                    score += 5
                # Exact matches on specific columns count higher
                if term == inst.mode.lower():
                    score += 10
                if term in inst.title.lower():
                    score += 8
                if term in inst.company_name.lower():
                    score += 8
                if term in [s.lower() for s in inst.required_skills]:
                    score += 12
                    
            if score > 0 or not terms:
                scored_internships.append((inst, score))
                
        # Sort by search term relevance score
        scored_internships.sort(key=lambda x: x[1], reverse=True)
        internships = [x[0] for x in scored_internships]

    # Calculate match scores for recommendations sorting if user is logged in
    user_id = session.get('user_id')
    user_role = session.get('role')
    user_recs_map = {}
    
    if user_id and user_role == 'candidate':
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile and profile.skills:
            # We fetch user recommendations to map match percentages
            recs = get_recommendations(profile)
            user_recs_map = {r["internship"].id: r for r in recs}

    # Serialization
    serialized = []
    for inst in internships:
        match_info = user_recs_map.get(inst.id, {
            "match_score": 50,
            "reasons": ["Complete your profile to see tailored insights."],
            "missing_skills": inst.required_skills,
            "confidence_score": "Medium"
        })
        
        status = "none"
        if user_id:
            saved_status = SavedInternship.query.filter_by(user_id=user_id, internship_id=inst.id).first()
            if saved_status:
                status = saved_status.status

        serialized.append({
            "id": inst.id,
            "company_name": inst.company_name,
            "company_logo": inst.company_logo or "https://via.placeholder.com/60",
            "title": inst.title,
            "description": inst.description,
            "responsibilities": inst.responsibilities,
            "eligibility_criteria": inst.eligibility_criteria,
            "degree_requirement": inst.degree_requirement,
            "required_skills": inst.required_skills,
            "location": inst.location,
            "mode": inst.mode,
            "duration": inst.duration,
            "stipend": inst.stipend,
            "industry": inst.industry,
            "category": inst.category,
            "application_deadline": inst.application_deadline,
            "match_score": match_info["match_score"],
            "reasons": match_info["reasons"],
            "missing_skills": match_info["missing_skills"],
            "confidence": match_info["confidence_score"],
            "status": status
        })

    # Sort Results
    if sort_by == 'stipend':
        serialized.sort(key=lambda x: x["stipend"], reverse=True)
    elif sort_by == 'match' and user_recs_map:
        serialized.sort(key=lambda x: x["match_score"], reverse=True)
    else:  # 'latest'
        serialized.sort(key=lambda x: x["id"], reverse=True)

    return jsonify(serialized), 200

@main_bp.route('/api/internships/<int:id>', methods=['GET'])
def get_internship_detail(id):
    inst = Internship.query.get_or_404(id)
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    match_score = 50
    reasons = ["Please log in as a student to see match explanations."]
    missing_skills = inst.required_skills
    confidence = "Medium"
    status = "none"
    
    if user_id and user_role == 'candidate':
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            recs = get_recommendations(profile)
            match_rec = next((r for r in recs if r["internship"].id == inst.id), None)
            if match_rec:
                match_score = match_rec["match_score"]
                reasons = match_rec["reasons"]
                missing_skills = match_rec["missing_skills"]
                confidence = match_rec["confidence_score"]
                
            saved_status = SavedInternship.query.filter_by(user_id=user_id, internship_id=inst.id).first()
            if saved_status:
                status = saved_status.status

    return jsonify({
        "id": inst.id,
        "company_name": inst.company_name,
        "company_logo": inst.company_logo or "https://via.placeholder.com/60",
        "title": inst.title,
        "description": inst.description,
        "responsibilities": inst.responsibilities or "",
        "eligibility_criteria": inst.eligibility_criteria or "",
        "degree_requirement": inst.degree_requirement or "Any",
        "branch_requirement": inst.branch_requirement,
        "location": inst.location,
        "mode": inst.mode,
        "duration": inst.duration,
        "stipend": inst.stipend,
        "industry": inst.industry or "",
        "category": inst.category or "",
        "application_deadline": inst.application_deadline or "",
        "match_score": match_score,
        "reasons": reasons,
        "missing_skills": missing_skills,
        "confidence": confidence,
        "status": status
    }), 200
