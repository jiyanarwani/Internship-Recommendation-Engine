import os
from typing import List
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from sqlmodel import Session, select, delete
from database import get_session
from models import User, Profile, Internship, SavedInternship, RecommendationHistory, ApplicationHistory
from dependencies import get_current_candidate
from config import Config
from services.resume_parser import parse_resume_pdf
from ml.recommender import get_recommendations
from ml.roadmap_generator import generate_roadmap, SKILL_RESOURCES
from schemas import ProfileUpdateRequest

candidate_router = APIRouter()

def calculate_completion_percentage(profile: Profile) -> int:
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

@candidate_router.get('/profile')
def get_profile(current_user: User = Depends(get_current_candidate)):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    return {
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
    }

@candidate_router.post('/profile')
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    try:
        if payload.full_name is not None:
            profile.full_name = payload.full_name.strip()
        if payload.phone is not None:
            profile.phone = payload.phone.strip()
        if payload.college is not None:
            profile.college = payload.college.strip()
        if payload.education_level is not None:
            profile.education_level = payload.education_level.strip()
        if payload.degree is not None:
            profile.degree = payload.degree.strip()
        if payload.branch is not None:
            profile.branch = payload.branch.strip()
            
        if payload.graduation_year is not None:
            profile.graduation_year = payload.graduation_year
        if payload.cgpa is not None:
            profile.cgpa = payload.cgpa
            
        if payload.skills is not None:
            profile.skills = payload.skills
        if payload.interests is not None:
            profile.interests = payload.interests
            
        if payload.preferred_industry is not None:
            profile.preferred_industry = payload.preferred_industry.strip()
        if payload.preferred_job_role is not None:
            profile.preferred_job_role = payload.preferred_job_role.strip()
        if payload.preferred_location is not None:
            profile.preferred_location = payload.preferred_location.strip()
            
        session.add(profile)
        session.commit()
        session.refresh(profile)
        
        return {
            "message": "Profile updated successfully", 
            "completion_percentage": calculate_completion_percentage(profile)
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@candidate_router.post('/profile/upload-resume')
async def upload_resume(
    resume: UploadFile = File(...),
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    # 1. Validate file extension
    extension = Path(resume.filename).suffix.lower()
    if extension != '.pdf':
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
        
    # 2. Validate MIME type
    if resume.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Invalid file type. Must be application/pdf")
        
    # 3. Read content & validate file size (Limit = 16 MB)
    contents = await resume.read()
    if len(contents) > 16 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 16 MB limit")
        
    try:
        # 4. Generate unique filename
        filename = f"{uuid.uuid4()}{extension}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Save file to upload directory
        with open(filepath, "wb") as f:
            f.write(contents)
            
        # Parse resume text
        parsed_data = parse_resume_pdf(filepath)
        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse PDF content")
            
        # Save resume filename to database profile
        profile = current_user.profile
        profile.resume_filename = filename
        session.add(profile)
        session.commit()
        
        # Add filename to parsed data
        parsed_data['resume_filename'] = filename
        
        return {
            "message": "Resume uploaded and analyzed successfully!",
            "parsed_data": parsed_data
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload or parse resume: {str(e)}")

@candidate_router.get('/recommendations')
def fetch_recommendations(
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    profile = current_user.profile
    if not profile or not profile.skills:
        return {
            "error": "Please complete your profile and add skills to receive recommendations.",
            "code": "PROFILE_INCOMPLETE"
        }
        
    try:
        recs = get_recommendations(profile, session)
        
        # Clear old recommendation history for this user
        session.exec(delete(RecommendationHistory).where(RecommendationHistory.user_id == current_user.id))
        session.commit()
        
        # Save top 10 recommendations to history database
        for r in recs[:10]:
            hist = RecommendationHistory(
                user_id=current_user.id,
                internship_id=r["internship"].id,
                score=r["match_score"],
                reasons=r["reasons"],
                missing_skills=r["missing_skills"]
            )
            session.add(hist)
        session.commit()
        
        # Return serialized results
        serialized = []
        for r in recs:
            inst = r["internship"]
            # Check if saved or applied
            saved_status = session.exec(
                select(SavedInternship).where(
                    SavedInternship.user_id == current_user.id,
                    SavedInternship.internship_id == inst.id
                )
            ).first()
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
            
        return serialized
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to compute recommendations: {str(e)}")

@candidate_router.get('/recommendations/history')
def get_recommendation_history(
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    statement = select(RecommendationHistory).where(
        RecommendationHistory.user_id == current_user.id
    ).order_by(RecommendationHistory.created_at.desc())
    histories = session.exec(statement).all()
    
    serialized = []
    for h in histories:
        inst = h.internship
        saved_status = session.exec(
            select(SavedInternship).where(
                SavedInternship.user_id == current_user.id,
                SavedInternship.internship_id == inst.id
            )
        ).first()
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
    return serialized

@candidate_router.get('/recommendations/{internship_id}/roadmap')
def fetch_roadmap(
    internship_id: int,
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Calculate missing skills
    user_skills = {s.lower().strip() for s in profile.skills}
    missing_skills = [s for s in inst.required_skills if s.lower().strip() not in user_skills]
    
    roadmap_data = generate_roadmap(missing_skills)
    return roadmap_data

@candidate_router.get('/saved')
def get_saved(
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    statement = select(SavedInternship).where(
        SavedInternship.user_id == current_user.id,
        SavedInternship.status == 'saved'
    )
    saved = session.exec(statement).all()
    
    serialized = []
    for s in saved:
        inst = s.internship
        # Get score if exists in history
        history = session.exec(
            select(RecommendationHistory).where(
                RecommendationHistory.user_id == current_user.id,
                RecommendationHistory.internship_id == inst.id
            )
        ).first()
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
    return serialized

@candidate_router.post('/saved/{internship_id}')
def save_internship(
    internship_id: int,
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    existing = session.exec(
        select(SavedInternship).where(
            SavedInternship.user_id == current_user.id,
            SavedInternship.internship_id == inst.id
        )
    ).first()
    
    if existing:
        if existing.status == 'applied':
            raise HTTPException(status_code=400, detail="Already applied, cannot change to saved")
        return {"message": "Already saved", "status": "saved"}
    
    try:
        saved = SavedInternship(user_id=current_user.id, internship_id=inst.id, status='saved')
        session.add(saved)
        session.commit()
        return {"message": "Internship saved successfully", "status": "saved"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save internship: {str(e)}")

@candidate_router.delete('/saved/{internship_id}')
def delete_saved_internship(
    internship_id: int,
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    existing = session.exec(
        select(SavedInternship).where(
            SavedInternship.user_id == current_user.id,
            SavedInternship.internship_id == inst.id
        )
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Not saved")
        
    if existing.status == 'applied':
        raise HTTPException(status_code=400, detail="Cannot delete applied internship record")
        
    try:
        session.delete(existing)
        session.commit()
        return {"message": "Internship removed from saved list", "status": "none"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete saved internship: {str(e)}")

@candidate_router.get('/applied')
def get_applied(
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    statement = select(ApplicationHistory).where(
        ApplicationHistory.user_id == current_user.id
    ).order_by(ApplicationHistory.applied_at.desc())
    apps = session.exec(statement).all()
    
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
    return serialized

@candidate_router.post('/apply/{internship_id}')
def apply_internship(
    internship_id: int,
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    inst = session.get(Internship, internship_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check if already applied
    existing_app = session.exec(
        select(ApplicationHistory).where(
            ApplicationHistory.user_id == current_user.id,
            ApplicationHistory.internship_id == inst.id
        )
    ).first()
    if existing_app:
        return {"message": "Already applied to this internship", "status": "applied"}
        
    try:
        # Add to application history
        app = ApplicationHistory(user_id=current_user.id, internship_id=inst.id)
        session.add(app)
        
        # Update or create saved internship status to 'applied'
        saved = session.exec(
            select(SavedInternship).where(
                SavedInternship.user_id == current_user.id,
                SavedInternship.internship_id == inst.id
            )
        ).first()
        
        if saved:
            saved.status = 'applied'
            session.add(saved)
        else:
            saved = SavedInternship(user_id=current_user.id, internship_id=inst.id, status='applied')
            session.add(saved)
            
        session.commit()
        return {"message": "Application submitted successfully!", "status": "applied"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")

@candidate_router.get('/insights')
def get_insights(
    current_user: User = Depends(get_current_candidate),
    session: Session = Depends(get_session)
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    # Analyze all internships to compute weak skills & recommended skills
    all_internships = session.exec(select(Internship)).all()
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
            
    # Sort missing skills by popularity to suggest "Weak Skills"
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
        
    return {
        "top_skills": profile.skills[:5],
        "weak_skills": weak_skills,
        "recommended_skills": recommendations_list,
        "suggested_domains": list(set(domains))[:3],
        "completion_percentage": calculate_completion_percentage(profile)
    }
