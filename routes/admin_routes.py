from flask import Blueprint, request, jsonify, session
from models import db, User, Profile, Internship, SavedInternship, RecommendationHistory, ApplicationHistory
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

# Helper to verify admin login
def is_admin():
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != 'admin':
        return False
    user = User.query.get(user_id)
    return user is not None and user.role == 'admin'

@admin_bp.route('/users', methods=['GET'])
def get_users():
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    users = User.query.filter_by(role='candidate').all()
    serialized = []
    for u in users:
        p = u.profile
        serialized.append({
            "id": u.id,
            "email": u.email,
            "name": p.full_name if p else "New Candidate",
            "college": p.college if p else "N/A",
            "degree": p.degree if p else "N/A",
            "branch": p.branch if p else "N/A",
            "cgpa": p.cgpa if p else 0.0,
            "created_at": u.created_at.strftime("%Y-%m-%d")
        })
    return jsonify(serialized), 200

@admin_bp.route('/internships', methods=['POST'])
def add_internship():
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    
    try:
        inst = Internship(
            company_name=data.get('company_name', '').strip(),
            company_logo=data.get('company_logo', '').strip() or "https://via.placeholder.com/60",
            title=data.get('title', '').strip(),
            description=data.get('description', '').strip(),
            responsibilities=data.get('responsibilities', '').strip(),
            required_skills=data.get('required_skills', []),
            eligibility_criteria=data.get('eligibility_criteria', '').strip(),
            degree_requirement=data.get('degree_requirement', '').strip(),
            branch_requirement=data.get('branch_requirement', []),
            location=data.get('location', '').strip(),
            mode=data.get('mode', 'Onsite').strip(),
            duration=int(data.get('duration', 6)),
            stipend=int(data.get('stipend', 0)),
            industry=data.get('industry', '').strip(),
            category=data.get('category', '').strip(),
            application_deadline=data.get('application_deadline', '').strip()
        )
        db.session.add(inst)
        db.session.commit()
        return jsonify({"message": "Internship added successfully", "id": inst.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add internship: {str(e)}"}), 500

@admin_bp.route('/internships/<int:id>', methods=['PUT', 'DELETE'])
def manage_internship(id):
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    inst = Internship.query.get_or_404(id)
    
    if request.method == 'PUT':
        data = request.get_json() or {}
        try:
            inst.company_name = data.get('company_name', inst.company_name).strip()
            inst.company_logo = data.get('company_logo', inst.company_logo).strip()
            inst.title = data.get('title', inst.title).strip()
            inst.description = data.get('description', inst.description).strip()
            inst.responsibilities = data.get('responsibilities', inst.responsibilities).strip()
            inst.required_skills = data.get('required_skills', inst.required_skills)
            inst.eligibility_criteria = data.get('eligibility_criteria', inst.eligibility_criteria).strip()
            inst.degree_requirement = data.get('degree_requirement', inst.degree_requirement).strip()
            inst.branch_requirement = data.get('branch_requirement', inst.branch_requirement)
            inst.location = data.get('location', inst.location).strip()
            inst.mode = data.get('mode', inst.mode).strip()
            inst.duration = int(data.get('duration', inst.duration))
            inst.stipend = int(data.get('stipend', inst.stipend))
            inst.industry = data.get('industry', inst.industry).strip()
            inst.category = data.get('category', inst.category).strip()
            inst.application_deadline = data.get('application_deadline', inst.application_deadline).strip()
            
            db.session.commit()
            return jsonify({"message": "Internship updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update: {str(e)}"}), 500
            
    elif request.method == 'DELETE':
        try:
            db.session.delete(inst)
            db.session.commit()
            return jsonify({"message": "Internship deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete: {str(e)}"}), 500

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        total_users = User.query.filter_by(role='candidate').count()
        total_internships = Internship.query.count()
        
        # Average recommendation score
        avg_score_query = db.session.query(func.avg(RecommendationHistory.score)).scalar()
        avg_score = round(float(avg_score_query), 1) if avg_score_query else 0.0
        
        # Mode distribution (Remote, Hybrid, Onsite)
        modes = db.session.query(Internship.mode, func.count(Internship.id)).group_by(Internship.mode).all()
        mode_data = {m[0]: m[1] for m in modes}
        
        # Popular locations (Top 5)
        locations = db.session.query(Internship.location, func.count(Internship.id))\
                              .group_by(Internship.location)\
                              .order_by(func.count(Internship.id).desc())\
                              .limit(5).all()
        loc_data = {l[0]: l[1] for l in locations}
        
        # Popular companies (Top 5)
        companies = db.session.query(Internship.company_name, func.count(Internship.id))\
                              .group_by(Internship.company_name)\
                              .order_by(func.count(Internship.id).desc())\
                              .limit(5).all()
        company_data = {c[0]: c[1] for c in companies}
        
        # Most applied internships (Top 5)
        applied_internships = db.session.query(Internship.company_name, Internship.title, func.count(ApplicationHistory.id))\
                                        .join(ApplicationHistory, ApplicationHistory.internship_id == Internship.id)\
                                        .group_by(Internship.id)\
                                        .order_by(func.count(ApplicationHistory.id).desc())\
                                        .limit(5).all()
        applied_data = [
            {"label": f"{a[0]} - {a[1][:20]}...", "count": a[2]} for a in applied_internships
        ]
        
        # Most searched/requested skills (aggregating candidate skills)
        profiles = Profile.query.all()
        skill_counts = {}
        for p in profiles:
            for skill in p.skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        skills_data = [{"skill": s[0], "count": s[1]} for s in sorted_skills]
        
        return jsonify({
            "total_users": total_users,
            "total_internships": total_internships,
            "average_match_score": avg_score,
            "mode_distribution": mode_data,
            "popular_locations": loc_data,
            "popular_companies": company_data,
            "most_applied_internships": applied_data,
            "most_searched_skills": skills_data
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve analytics: {str(e)}"}), 500
