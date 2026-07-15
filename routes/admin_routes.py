from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from database import get_session
from models import User, Profile, Internship, SavedInternship, RecommendationHistory, ApplicationHistory
from dependencies import get_current_admin
from schemas import InternshipCreateRequest
from sqlalchemy import func

admin_router = APIRouter()

@admin_router.get('/users')
def get_users(
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    users = session.exec(select(User).where(User.role == 'candidate')).all()
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
    return serialized

@admin_router.post('/internships')
def add_internship(
    payload: InternshipCreateRequest,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    try:
        inst = Internship(
            company_name=payload.company_name.strip(),
            company_logo=payload.company_logo.strip() if payload.company_logo else "https://via.placeholder.com/60",
            title=payload.title.strip(),
            description=payload.description.strip(),
            responsibilities=payload.responsibilities.strip() if payload.responsibilities else "",
            required_skills=payload.required_skills if payload.required_skills else [],
            eligibility_criteria=payload.eligibility_criteria.strip() if payload.eligibility_criteria else "",
            degree_requirement=payload.degree_requirement.strip() if payload.degree_requirement else "Any",
            branch_requirement=payload.branch_requirement if payload.branch_requirement else [],
            location=payload.location.strip(),
            mode=payload.mode.strip(),
            duration=payload.duration,
            stipend=payload.stipend,
            industry=payload.industry.strip() if payload.industry else "",
            category=payload.category.strip() if payload.category else "",
            application_deadline=payload.application_deadline.strip() if payload.application_deadline else ""
        )
        session.add(inst)
        session.commit()
        session.refresh(inst)
        return {"message": "Internship added successfully", "id": inst.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add internship: {str(e)}")

@admin_router.put('/internships/{internship_id}')
def update_internship(
    internship_id: int,
    payload: InternshipCreateRequest,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    try:
        inst.company_name = payload.company_name.strip()
        if payload.company_logo is not None:
            inst.company_logo = payload.company_logo.strip()
        inst.title = payload.title.strip()
        inst.description = payload.description.strip()
        if payload.responsibilities is not None:
            inst.responsibilities = payload.responsibilities.strip()
        if payload.required_skills is not None:
            inst.required_skills = payload.required_skills
        if payload.eligibility_criteria is not None:
            inst.eligibility_criteria = payload.eligibility_criteria.strip()
        if payload.degree_requirement is not None:
            inst.degree_requirement = payload.degree_requirement.strip()
        if payload.branch_requirement is not None:
            inst.branch_requirement = payload.branch_requirement
        inst.location = payload.location.strip()
        inst.mode = payload.mode.strip()
        inst.duration = payload.duration
        inst.stipend = payload.stipend
        if payload.industry is not None:
            inst.industry = payload.industry.strip()
        if payload.category is not None:
            inst.category = payload.category.strip()
        if payload.application_deadline is not None:
            inst.application_deadline = payload.application_deadline.strip()
            
        session.add(inst)
        session.commit()
        return {"message": "Internship updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")

@admin_router.delete('/internships/{internship_id}')
def delete_internship(
    internship_id: int,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    try:
        session.delete(inst)
        session.commit()
        return {"message": "Internship deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")

@admin_router.get('/stats')
def get_stats(
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    try:
        total_users = session.exec(select(func.count(User.id)).where(User.role == 'candidate')).one()
        total_internships = session.exec(select(func.count(Internship.id))).one()
        
        avg_score_query = session.exec(select(func.avg(RecommendationHistory.score))).one()
        avg_score = round(float(avg_score_query), 1) if avg_score_query else 0.0
        
        modes = session.exec(select(Internship.mode, func.count(Internship.id)).group_by(Internship.mode)).all()
        mode_data = {m[0]: m[1] for m in modes}
        
        locations = session.exec(
            select(Internship.location, func.count(Internship.id))
            .group_by(Internship.location)
            .order_by(func.count(Internship.id).desc())
            .limit(5)
        ).all()
        loc_data = {l[0]: l[1] for l in locations}
        
        companies = session.exec(
            select(Internship.company_name, func.count(Internship.id))
            .group_by(Internship.company_name)
            .order_by(func.count(Internship.id).desc())
            .limit(5)
        ).all()
        company_data = {c[0]: c[1] for c in companies}
        
        applied_internships = session.exec(
            select(Internship.company_name, Internship.title, func.count(ApplicationHistory.id))
            .join(ApplicationHistory, ApplicationHistory.internship_id == Internship.id)
            .group_by(Internship.id)
            .order_by(func.count(ApplicationHistory.id).desc())
            .limit(5)
        ).all()
        applied_data = [
            {"label": f"{a[0]} - {a[1][:20]}...", "count": a[2]} for a in applied_internships
        ]
        
        profiles = session.exec(select(Profile)).all()
        skill_counts = {}
        for p in profiles:
            for skill in p.skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        skills_data = [{"skill": s[0], "count": s[1]} for s in sorted_skills]
        
        return {
            "total_users": total_users,
            "total_internships": total_internships,
            "average_match_score": avg_score,
            "mode_distribution": mode_data,
            "popular_locations": loc_data,
            "popular_companies": company_data,
            "most_applied_internships": applied_data,
            "most_searched_skills": skills_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")
