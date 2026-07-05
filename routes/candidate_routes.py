import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from models import db, User, Profile, Internship, SavedInternship, RecommendationHistory, ApplicationHistory
from services.resume_parser import parse_resume_pdf
from ml.recommender import get_recommendations
from ml.roadmap_generator import generate_roadmap, SKILL_RESOURCES

candidate_bp = Blueprint('candidate', __name__)

# Helper to verify candidate login
def get_current_candidate():
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user or user.role != 'candidate':
        return None
    return user

def calculate_completion_percentage(profile):
    fields = [
        profile.full_name,
        profile.phone,
        profile.college,
        profile.degree,
        profile.branch,
        profile.graduation_year,
        profile.cgpa,
        profile.preferred_industry,
        profile.preferred_job_role,
        profile.preferred_location,
        profile.resume_filename
    ]
    filled = sum(1 for f in fields if f)
    if profile.skills:
        filled += 1
    if profile.interests:
        filled += 1
    # Max count = 13 fields
    return round((filled / 13) * 100)

@candidate_bp.route('/profile', methods=['GET'])
def get_profile():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    profile = user.profile
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
        
    return jsonify({
        "full_name": profile.full_name,
        "phone": profile.phone or "",
        "college": profile.college or "",
        "degree": profile.degree or "",
        "branch": profile.branch or "",
        "graduation_year": profile.graduation_year or "",
        "cgpa": profile.cgpa or "",
        "skills": profile.skills,
        "interests": profile.interests,
        "preferred_industry": profile.preferred_industry or "",
        "preferred_job_role": profile.preferred_job_role or "",
        "preferred_location": profile.preferred_location or "",
        "resume_filename": profile.resume_filename or "",
        "completion_percentage": calculate_completion_percentage(profile)
    }), 200

@candidate_bp.route('/profile', methods=['POST'])
def update_profile():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    profile = user.profile
    data = request.get_json() or {}
    
    try:
        profile.full_name = (data.get('full_name') or profile.full_name or '').strip()
        profile.phone = (data.get('phone') or profile.phone or '').strip()
        profile.college = (data.get('college') or profile.college or '').strip()
        profile.degree = (data.get('degree') or profile.degree or '').strip()
        profile.branch = (data.get('branch') or profile.branch or '').strip()
        
        grad_year = data.get('graduation_year')
        profile.graduation_year = int(grad_year) if grad_year else None
        
        cgpa = data.get('cgpa')
        profile.cgpa = float(cgpa) if cgpa else None
        
        profile.skills = data.get('skills', profile.skills)
        profile.interests = data.get('interests', profile.interests)
        profile.preferred_industry = (data.get('preferred_industry') or profile.preferred_industry or '').strip()
        profile.preferred_job_role = (data.get('preferred_job_role') or profile.preferred_job_role or '').strip()
        profile.preferred_location = (data.get('preferred_location') or profile.preferred_location or '').strip()
        
        db.session.commit()
        return jsonify({
            "message": "Profile updated successfully", 
            "completion_percentage": calculate_completion_percentage(profile)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500

@candidate_bp.route('/profile/upload-resume', methods=['POST'])
def upload_resume():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF resumes are supported"}), 400
        
    try:
        # Create user upload filename
        filename = secure_filename(f"user_{user.id}_resume.pdf")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse resume text
        parsed_data = parse_resume_pdf(filepath)
        if not parsed_data:
            return jsonify({"error": "Failed to parse PDF content"}), 500
            
        # Save resume filename to database profile
        profile = user.profile
        profile.resume_filename = filename
        db.session.commit()
        
        # Add filename to parsed data
        parsed_data['resume_filename'] = filename
        
        return jsonify({
            "message": "Resume uploaded and analyzed successfully!",
            "parsed_data": parsed_data
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to upload or parse resume: {str(e)}"}), 500

@candidate_bp.route('/recommendations', methods=['GET'])
def fetch_recommendations():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    profile = user.profile
    if not profile or not profile.skills:
        return jsonify({
            "error": "Please complete your profile and add skills to receive recommendations.",
            "code": "PROFILE_INCOMPLETE"
        }), 200
        
    try:
        recs = get_recommendations(profile)
        
        # Clear old recommendation history for this user
        RecommendationHistory.query.filter_by(user_id=user.id).delete()
        
        # Save top 10 recommendations to history database
        for r in recs[:10]:
            hist = RecommendationHistory(
                user_id=user.id,
                internship_id=r["internship"].id,
                score=r["match_score"],
                reasons=r["reasons"],
                missing_skills=r["missing_skills"]
            )
            db.session.add(hist)
        db.session.commit()
        
        # Return serialized results
        serialized = []
        for r in recs:
            inst = r["internship"]
            # Check if saved or applied
            saved_status = SavedInternship.query.filter_by(user_id=user.id, internship_id=inst.id).first()
            status = saved_status.status if saved_status else "none"
            
            serialized.append({
                "id": inst.id,
                "company_name": inst.company_name,
                "company_logo": inst.company_logo or "https://via.placeholder.com/60",
                "title": inst.title,
                "description": inst.description,
                "mode": inst.mode,
                "location": inst.location,
                "duration": inst.duration,
                "stipend": inst.stipend,
                "required_skills": inst.required_skills,
                "match_score": r["match_score"],
                "reasons": r["reasons"],
                "missing_skills": r["missing_skills"],
                "confidence": r["confidence_score"],
                "status": status,
                "application_deadline": inst.application_deadline
            })
            
        return jsonify(serialized), 200
    except Exception as e:
        return jsonify({"error": f"Failed to compute recommendations: {str(e)}"}), 500

@candidate_bp.route('/recommendations/history', methods=['GET'])
def get_recommendation_history():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    histories = RecommendationHistory.query.filter_by(user_id=user.id).order_by(RecommendationHistory.created_at.desc()).all()
    serialized = []
    for h in histories:
        inst = h.internship
        saved_status = SavedInternship.query.filter_by(user_id=user.id, internship_id=inst.id).first()
        status = saved_status.status if saved_status else "none"
        
        serialized.append({
            "id": inst.id,
            "company_name": inst.company_name,
            "company_logo": inst.company_logo or "https://via.placeholder.com/60",
            "title": inst.title,
            "match_score": h.score,
            "reasons": h.reasons,
            "missing_skills": h.missing_skills,
            "generated_at": h.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": status
        })
    return jsonify(serialized), 200

@candidate_bp.route('/recommendations/<int:internship_id>/roadmap', methods=['GET'])
def fetch_roadmap(internship_id):
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    inst = Internship.query.get_or_404(internship_id)
    profile = user.profile
    
    # Calculate missing skills
    user_skills = {s.lower().strip() for s in profile.skills}
    missing_skills = [s for s in inst.required_skills if s.lower().strip() not in user_skills]
    
    roadmap_data = generate_roadmap(missing_skills)
    return jsonify(roadmap_data), 200

@candidate_bp.route('/saved', methods=['GET'])
def get_saved():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    saved = SavedInternship.query.filter_by(user_id=user.id, status='saved').all()
    serialized = []
    for s in saved:
        inst = s.internship
        # Get score if exists in history
        history = RecommendationHistory.query.filter_by(user_id=user.id, internship_id=inst.id).first()
        score = history.score if history else 60 # fallback score
        
        serialized.append({
            "id": inst.id,
            "company_name": inst.company_name,
            "company_logo": inst.company_logo or "https://via.placeholder.com/60",
            "title": inst.title,
            "mode": inst.mode,
            "location": inst.location,
            "duration": inst.duration,
            "stipend": inst.stipend,
            "required_skills": inst.required_skills,
            "match_score": score,
            "status": "saved"
        })
    return jsonify(serialized), 200

@candidate_bp.route('/saved/<int:internship_id>', methods=['POST', 'DELETE'])
def toggle_save_internship(internship_id):
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    inst = Internship.query.get_or_404(internship_id)
    existing = SavedInternship.query.filter_by(user_id=user.id, internship_id=inst.id).first()
    
    if request.method == 'POST':
        if existing:
            if existing.status == 'applied':
                return jsonify({"message": "Already applied, cannot change to saved"}), 400
            return jsonify({"message": "Already saved", "status": "saved"}), 200
        
        saved = SavedInternship(user_id=user.id, internship_id=inst.id, status='saved')
        db.session.add(saved)
        db.session.commit()
        return jsonify({"message": "Internship saved successfully", "status": "saved"}), 201
        
    elif request.method == 'DELETE':
        if not existing:
            return jsonify({"message": "Not saved"}), 404
        if existing.status == 'applied':
            return jsonify({"error": "Cannot delete applied internship record"}), 400
            
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"message": "Internship removed from saved list", "status": "none"}), 200

@candidate_bp.route('/applied', methods=['GET'])
def get_applied():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    apps = ApplicationHistory.query.filter_by(user_id=user.id).order_by(ApplicationHistory.applied_at.desc()).all()
    serialized = []
    for a in apps:
        inst = a.internship
        serialized.append({
            "id": inst.id,
            "company_name": inst.company_name,
            "company_logo": inst.company_logo or "https://via.placeholder.com/60",
            "title": inst.title,
            "applied_at": a.applied_at.strftime("%Y-%m-%d %H:%M"),
            "location": inst.location,
            "mode": inst.mode,
            "stipend": inst.stipend,
            "status": "applied"
        })
    return jsonify(serialized), 200

@candidate_bp.route('/apply/<int:internship_id>', methods=['POST'])
def apply_internship(internship_id):
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    inst = Internship.query.get_or_404(internship_id)
    
    # Check if already applied
    existing_app = ApplicationHistory.query.filter_by(user_id=user.id, internship_id=inst.id).first()
    if existing_app:
        return jsonify({"message": "Already applied to this internship"}), 200
        
    try:
        # Add to application history
        app = ApplicationHistory(user_id=user.id, internship_id=inst.id)
        db.session.add(app)
        
        # Update or create saved internship status to 'applied'
        saved = SavedInternship.query.filter_by(user_id=user.id, internship_id=inst.id).first()
        if saved:
            saved.status = 'applied'
        else:
            saved = SavedInternship(user_id=user.id, internship_id=inst.id, status='applied')
            db.session.add(saved)
            
        db.session.commit()
        return jsonify({"message": "Application submitted successfully!", "status": "applied"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Application failed: {str(e)}"}), 500

@candidate_bp.route('/insights', methods=['GET'])
def get_insights():
    user = get_current_candidate()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    profile = user.profile
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
        
    # Analyze all internships to compute weak skills & recommended skills
    all_internships = Internship.query.all()
    user_skills_set = {s.lower().strip() for s in profile.skills}
    
    # Count frequency of skills required by internships
    skill_frequencies = {}
    for inst in all_internships:
        for skill in inst.required_skills:
            skill_clean = skill.strip()
            skill_lower = skill_clean.lower()
            skill_frequencies[skill_lower] = skill_frequencies.get(skill_lower, 0) + 1
            
    # Filter for skills the user doesn't possess
    missing_skill_freq = {}
    for sk_lower, freq in skill_frequencies.items():
        if sk_lower not in user_skills_set:
            # Map back to title case name
            title_name = sk_lower.title()
            if sk_lower == 'sql': title_name = 'SQL'
            elif sk_lower == 'html': title_name = 'HTML'
            elif sk_lower == 'css': title_name = 'CSS'
            missing_skill_freq[title_name] = freq
            
    # Sort missing skills by popularity to suggest "Weak Skills" (or areas of improvement)
    sorted_weak_skills = sorted(missing_skill_freq.items(), key=lambda x: x[1], reverse=True)
    weak_skills = [item[0] for item in sorted_weak_skills[:5]]
    
    # Recommended learning resources mapping
    recommendations_list = []
    for skill in weak_skills:
        res_key = next((k for k in SKILL_RESOURCES.keys() if k.lower() == skill.lower()), None)
        if res_key:
            info = SKILL_RESOURCES[res_key]
            recommendations_list.append({
                "skill": skill,
                "course": info["course_name"],
                "platform": info["platform"],
                "hours": info["hours"],
                "url": info["url"]
            })
        else:
            recommendations_list.append({
                "skill": skill,
                "course": f"{skill} Foundations",
                "platform": "YouTube / Udemy",
                "hours": 10,
                "url": "https://www.google.com"
            })
            
    # Suggested career domains based on user interests or branch
    domains = []
    user_branch_lower = (profile.branch or "").lower()
    user_interests_lower = [i.lower() for i in profile.interests]
    
    if 'computer' in user_branch_lower or 'information' in user_branch_lower or any('web' in i or 'software' in i or 'ai' in i or 'machine' in i for i in user_interests_lower):
        domains.extend(['Software Engineering', 'Full-Stack Web Development', 'Artificial Intelligence & Data Science'])
    if 'electronics' in user_branch_lower or 'electrical' in user_branch_lower:
        domains.extend(['Embedded Systems', 'IoT Engineering', 'VLSI Design'])
    if 'finance' in user_branch_lower or 'commerce' in user_branch_lower or 'business' in user_branch_lower or 'marketing' in user_branch_lower:
        domains.extend(['Financial Analytics', 'Business Analytics', 'Digital Product Management'])
    if 'mechanical' in user_branch_lower or 'civil' in user_branch_lower or 'chemical' in user_branch_lower:
        domains.extend(['Core Engineering Operations', 'Industrial Process Design', 'CAD Modeling'])
        
    # Default fallback domains
    if not domains:
        domains = ['General Management Operations', 'Data Analyst Associate', 'Technical Support Ops']
        
    return jsonify({
        "top_skills": profile.skills[:5],
        "weak_skills": weak_skills,
        "recommended_skills": recommendations_list,
        "suggested_domains": list(set(domains))[:3],
        "completion_percentage": calculate_completion_percentage(profile)
    }), 200
