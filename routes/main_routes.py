import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from database import get_session
from models import Internship, Profile, SavedInternship
from ml.recommender import get_recommendations

main_router = APIRouter()

@main_router.get('/')
def index():
    return FileResponse('templates/index.html')

@main_router.get('/api/internships')
def list_internships(
    q: str = "",
    mode: str = "",
    location: str = "",
    industry: str = "",
    duration: str = "",
    skills: str = "",
    company: str = "",
    sort: str = "latest",
    request: Request = None,
    session: Session = Depends(get_session)
):
    # Start database query
    query_obj = select(Internship)

    # Base filters
    if mode:
        query_obj = query_obj.where(Internship.mode.ilike(mode))
    if location:
        query_obj = query_obj.where(Internship.location.ilike(f"%{location}%"))
    if industry:
        query_obj = query_obj.where(Internship.industry.ilike(f"%{industry}%"))
    if duration:
        try:
            val = int(duration)
            query_obj = query_obj.where(Internship.duration <= val)
        except ValueError:
            pass
    if company:
        query_obj = query_obj.where(Internship.company_name.ilike(f"%{company}%"))

    internships = session.exec(query_obj).all()

    # Client-side filtering for skills
    if skills:
        skills_to_match = [s.strip().lower() for s in skills.split(',') if s.strip()]
        filtered = []
        for inst in internships:
            inst_skills = [s.lower() for s in inst.required_skills]
            if any(s in inst_skills for s in skills_to_match):
                filtered.append(inst)
        internships = filtered

    # Intelligent Query Parsing (e.g. "Python Remote Mumbai")
    if q:
        terms = [t for t in re.split(r'\s+', q) if t]
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
    user_id = request.session.get('user_id') if request else None
    user_role = request.session.get('role') if request else None
    user_recs_map = {}
    
    if user_id and user_role == 'candidate':
        profile = session.exec(select(Profile).where(Profile.user_id == user_id)).first()
        if profile and profile.skills:
            recs = get_recommendations(profile, session)
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
            saved_status = session.exec(
                select(SavedInternship).where(
                    SavedInternship.user_id == user_id, 
                    SavedInternship.internship_id == inst.id
                )
            ).first()
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
    if sort == 'stipend':
        serialized.sort(key=lambda x: x["stipend"], reverse=True)
    elif sort == 'match' and user_recs_map:
        serialized.sort(key=lambda x: x["match_score"], reverse=True)
    else:  # 'latest'
        serialized.sort(key=lambda x: x["id"], reverse=True)

    return serialized

@main_router.get('/api/internships/{internship_id}')
def get_internship_detail(
    internship_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    match_score = 50
    reasons = ["Please log in as a student to see match explanations."]
    missing_skills = inst.required_skills
    confidence = "Medium"
    status = "none"
    
    if user_id and user_role == 'candidate':
        profile = session.exec(select(Profile).where(Profile.user_id == user_id)).first()
        if profile:
            recs = get_recommendations(profile, session)
            match_rec = next((r for r in recs if r["internship"].id == inst.id), None)
            if match_rec:
                match_score = match_rec["match_score"]
                reasons = match_rec["reasons"]
                missing_skills = match_rec["missing_skills"]
                confidence = match_rec["confidence_score"]
                
            saved_status = session.exec(
                select(SavedInternship).where(
                    SavedInternship.user_id == user_id, 
                    SavedInternship.internship_id == inst.id
                )
            ).first()
            if saved_status:
                status = saved_status.status

    return {
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
    }
