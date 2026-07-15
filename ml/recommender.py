import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import Session, select
from models import Internship, Profile

def clean_text(text):
    """Normalize text for ML preprocessing."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\+\#\-]', ' ', text)  # Keep +, #, - for C++, C#, CI/CD
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_min_cgpa(eligibility_text):
    """Extract minimum CGPA requirement from internship eligibility description."""
    if not eligibility_text:
        return 0.0
    text = eligibility_text.lower()
    # Match patterns like "cgpa of 7.0", "7.5 cgpa", "min 6.0 cgpa", "cgpa: 7.0"
    matches = re.findall(r'(?:cgpa|gpa)(?:\s*(?:of|is|:)?\s*|\s+min(?:imum)?\s+)?(\d\.\d{1,2})|(\d\.\d{1,2})\s*(?:cgpa|gpa)', text)
    for m in matches:
        val = m[0] or m[1]
        if val:
            try:
                cgpa_val = float(val)
                if 4.0 <= cgpa_val <= 10.0:
                    return cgpa_val
            except ValueError:
                continue
    return 0.0

# Fuzzy Branch Match Configurations
BRANCH_GROUPS = {
    "COMPUTER": {
        "computer science",
        "computer engineering",
        "computer science engineering",
        "computer science and engineering",
        "cse",
        "ce",
        "cs",
        "computer",
        "software"
    },
    "IT": {
        "information technology",
        "it",
        "information science",
        "information science and engineering"
    },
    "ELECTRONICS": {
        "electronics",
        "electronics engineering",
        "electronics and telecommunication",
        "electronics and communication",
        "ece",
        "extc"
    },
    "ELECTRICAL": {
        "electrical",
        "electrical engineering",
        "electrical and electronics",
        "eee"
    },
    "MECHANICAL": {
        "mechanical",
        "mechanical engineering",
        "automobile",
        "production"
    },
    "CIVIL": {
        "civil",
        "civil engineering"
    },
    "CHEMICAL": {
        "chemical",
        "chemical engineering"
    },
    "BUSINESS": {
        "business",
        "finance",
        "commerce",
        "mba",
        "bba",
        "management"
    }
}

BRANCH_SIMILARITY_MATRIX = {
    'COMPUTER': {
        'COMPUTER': 1.0,
        'IT': 0.95,
        'ELECTRONICS': 0.75,
        'ELECTRICAL': 0.50,
    },
    'IT': {
        'COMPUTER': 0.95,
        'IT': 1.0,
        'ELECTRONICS': 0.70,
        'ELECTRICAL': 0.45,
    },
    'ELECTRONICS': {
        'COMPUTER': 0.75,
        'IT': 0.70,
        'ELECTRONICS': 1.0,
        'ELECTRICAL': 0.85,
    },
    'ELECTRICAL': {
        'COMPUTER': 0.50,
        'IT': 0.45,
        'ELECTRONICS': 0.85,
        'ELECTRICAL': 1.0,
    },
    'MECHANICAL': {
        'MECHANICAL': 1.0,
        'CIVIL': 0.25,
        'CHEMICAL': 0.20,
    },
    'CIVIL': {
        'MECHANICAL': 0.25,
        'CIVIL': 1.0,
        'CHEMICAL': 0.15,
    },
    'CHEMICAL': {
        'MECHANICAL': 0.20,
        'CIVIL': 0.15,
        'CHEMICAL': 1.0,
    },
}

def normalize_branch(name: str) -> str:
    if not name:
        return ""
    name_lower = name.lower().strip()
    # Remove degree prefixes to allow clean keyword matching
    name_clean = re.sub(r'\bb\.?\s*tech(nology)?\b', '', name_lower)
    name_clean = re.sub(r'\bb\.?\s*e\.?\b', '', name_clean)
    name_clean = re.sub(r'\bbachelor\s+of\s+(technology|engineering)\b', '', name_clean)
    name_clean = re.sub(r'[^a-z0-9\s\&]', ' ', name_clean)
    name_clean = re.sub(r'\s+', ' ', name_clean).strip()
    
    if not name_clean:
        name_clean = re.sub(r'[^a-z0-9\s\&]', ' ', name_lower)
        name_clean = re.sub(r'\s+', ' ', name_clean).strip()
    return name_clean

def get_branch_group(name: str) -> str:
    norm_name = normalize_branch(name)
    if not norm_name:
        return "OTHER"
    
    for group, keywords in BRANCH_GROUPS.items():
        for kw in keywords:
            if len(kw) <= 4:
                # Word boundary for short codes like cs, it, ce, me, eee
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, norm_name):
                    return group
            else:
                if kw in norm_name:
                    return group
    return "OTHER"

def get_branch_similarity(group1: str, group2: str) -> float:
    if group1 == group2:
        return 1.0
    if group1 in BRANCH_SIMILARITY_MATRIX and group2 in BRANCH_SIMILARITY_MATRIX[group1]:
        return BRANCH_SIMILARITY_MATRIX[group1][group2]
    if group2 in BRANCH_SIMILARITY_MATRIX and group1 in BRANCH_SIMILARITY_MATRIX[group2]:
        return BRANCH_SIMILARITY_MATRIX[group2][group1]
    return 0.0

def get_recommendations(profile, session: Session):
    """
    Run hybrid ML recommendation system.
    Returns: list of dicts containing internship object, match score, reasons, and missing skills.
    """
    internships = session.exec(select(Internship)).all()
    if not internships:
        return []

    # 1. Prepare texts for vectorization
    candidate_skills = " ".join(profile.skills)
    candidate_interests = " ".join(profile.interests)
    candidate_pref_role = profile.preferred_job_role or ""
    candidate_pref_ind = profile.preferred_industry or ""
    candidate_branch = profile.branch or ""
    
    # Combined profile document
    candidate_doc = clean_text(f"{profile.full_name} {profile.degree} {candidate_branch} {candidate_skills} {candidate_interests} {candidate_pref_role} {candidate_pref_ind}")

    internship_docs = []
    for inst in internships:
        inst_skills = " ".join(inst.required_skills)
        branch_req = " ".join(inst.branch_requirement)
        inst_doc = clean_text(f"{inst.title} {inst.company_name} {inst.description} {inst_skills} {branch_req} {inst.category} {inst.industry}")
        internship_docs.append(inst_doc)

    # All documents (internships + candidate at the end)
    all_docs = internship_docs + [candidate_doc]

    # 2. TF-IDF & Cosine Similarity
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_docs)
    
    candidate_vector = tfidf_matrix[-1]
    internship_vectors = tfidf_matrix[:-1]
    
    # Compute cosine similarity
    cosine_sims = cosine_similarity(candidate_vector, internship_vectors)[0]

    recommendations = []
    
    # Pre-parse candidate skills in lowercase for matching
    user_skills_set = {s.lower().strip() for s in profile.skills}

    for idx, inst in enumerate(internships):
        semantic_score = cosine_sims[idx] # between 0 and 1
        
        # 3. Structured Matches
        # Branch match
        branch_match = 1.0
        if inst.branch_requirement and profile.branch:
            user_branch_group = get_branch_group(profile.branch)
            max_sim = 0.0
            for req in inst.branch_requirement:
                req_group = get_branch_group(req)
                sim = get_branch_similarity(user_branch_group, req_group)
                if sim > max_sim:
                    max_sim = sim
            branch_match = max_sim
            
        # Degree match
        degree_match = 1.0
        if inst.degree_requirement and profile.degree:
            req_deg = inst.degree_requirement.lower().strip()
            user_deg = profile.degree.lower().strip()
            if req_deg != 'any':
                degree_match = 1.0 if (req_deg in user_deg or user_deg in req_deg) else 0.0
                
        # Location match
        location_match = 0.0
        if inst.mode.lower() in ['remote', 'hybrid']:
            location_match = 1.0
        elif profile.preferred_location and inst.location:
            user_loc = profile.preferred_location.lower().strip()
            inst_loc = inst.location.lower().strip()
            location_match = 1.0 if (user_loc in inst_loc or inst_loc in user_loc) else 0.0
            
        # Industry/Category match
        industry_match = 0.0
        if profile.preferred_industry and inst.category:
            user_ind = profile.preferred_industry.lower().strip()
            inst_cat = inst.category.lower().strip()
            industry_match = 1.0 if (user_ind in inst_cat or inst_cat in user_ind) else 0.0
            
        # CGPA match
        cgpa_match = 1.0
        min_cgpa = extract_min_cgpa(inst.eligibility_criteria)
        if min_cgpa > 0.0 and profile.cgpa:
            cgpa_match = 1.0 if profile.cgpa >= min_cgpa else 0.0

        # Skills match calculation
        matched_skills = []
        missing_skills = []
        for req_skill in inst.required_skills:
            req_skill_lower = req_skill.lower().strip()
            if req_skill_lower in user_skills_set:
                matched_skills.append(req_skill)
            else:
                missing_skills.append(req_skill)
                
        skills_match_score = 1.0
        if inst.required_skills:
            skills_match_score = len(matched_skills) / len(inst.required_skills)

        # Calculate structured score (weighted average of other features)
        structured_score = (
            0.25 * branch_match +
            0.25 * degree_match +
            0.20 * location_match +
            0.15 * cgpa_match +
            0.15 * industry_match
        )

        # Scale TF-IDF semantic score. Cosine similarity rarely exceeds 0.25 for short profiles,
        # so we scale it to fit [0.0, 1.0] dynamically
        scaled_semantic_score = min(1.0, semantic_score / 0.25)

        # 4. Hybrid Formulation: 60% Skills, 25% Other matches, 15% Semantic Similarity
        final_score = (0.60 * skills_match_score) + (0.25 * structured_score) + (0.15 * scaled_semantic_score)
        
        # Scale to 0-100%
        match_percentage = round(final_score * 100)
        # Boundary protection
        match_percentage = max(10, min(99, match_percentage))

        # 5. Explainable AI & Missing Skills
        reasons = []
        
        # Add score breakdown explanation
        skills_pct = round(skills_match_score * 100)
        eligibility_pct = round(structured_score * 100)
        semantic_pct = round(scaled_semantic_score * 100)
        
        reasons.append(f"Score Breakdown: Skills Match ({skills_pct}%), Eligibility Alignment ({eligibility_pct}%), Semantic Description Fit ({semantic_pct}%).")
        
        if skills_match_score == 1.0:
            reasons.append("✓ You have all required skills! The final score includes criteria like location, branch, degree requirements, and semantic text overlap.")
                
        for ms in matched_skills[:4]:
            reasons.append(f"Your {ms} skill matches the requirements.")
            
        # Interests match
        matched_interests = []
        for interest in profile.interests:
            interest_lower = interest.lower().strip()
            # check overlap in title/desc
            if interest_lower in inst.title.lower() or interest_lower in inst.description.lower() or interest_lower in (inst.category or "").lower():
                matched_interests.append(interest)
        
        for mi in matched_interests[:2]:
            reasons.append(f"Your interest in {mi} aligns with this opportunity.")

        # Structured reasons (Matches & Mismatches/Gaps)
        if branch_match == 1.0 and inst.branch_requirement:
            reasons.append("Your academic branch matches the eligibility profile.")
        elif branch_match > 0.0 and inst.branch_requirement:
            reasons.append(f"Branch overlap: Your branch ({profile.branch}) is closely related to required fields (similarity: {round(branch_match * 100)}%).")
        elif inst.branch_requirement:
            reasons.append(f"Branch mismatch: Required branch list is {', '.join(inst.branch_requirement)}, but your branch is {profile.branch or 'not specified'}.")

        if degree_match == 1.0 and inst.degree_requirement and inst.degree_requirement.lower() != 'any':
            reasons.append(f"Your {profile.degree} degree satisfies eligibility criteria.")
        elif degree_match < 1.0 and inst.degree_requirement:
            reasons.append(f"Degree gap: Required degree is {inst.degree_requirement}, but your degree is {profile.degree or 'not specified'}.")

        if location_match == 1.0:
            if inst.mode.lower() == 'remote':
                reasons.append("This is a remote position, fitting flexible location preferences.")
            else:
                reasons.append(f"Located in {inst.location}, matching your preferred location.")
        elif location_match < 1.0 and inst.location:
            reasons.append(f"Location mismatch: Job is in {inst.location} ({inst.mode}), but your preferred location is {profile.preferred_location or 'not specified'}.")

        if industry_match == 1.0:
            reasons.append(f"Fits your preferred {profile.preferred_industry} industry segment.")
        elif industry_match < 1.0 and inst.category:
            reasons.append(f"Industry mismatch: Job sector is {inst.category}, but your preferred industry is {profile.preferred_industry or 'not specified'}.")

        if cgpa_match == 1.0 and min_cgpa > 0.0:
            reasons.append("Your CGPA meets the academic requirements.")
        elif cgpa_match < 1.0 and min_cgpa > 0.0:
            reasons.append(f"CGPA gap: Required minimum CGPA is {min_cgpa}, but your CGPA is {profile.cgpa or 'not specified'}.")

        # Default reason if too short
        if not reasons:
            reasons.append("Matches your overall profile keywords and interests.")

        # Confidence Score
        confidence = "Low"
        if match_percentage >= 75:
            confidence = "High"
        elif match_percentage >= 50:
            confidence = "Medium"

        recommendations.append({
            "internship": inst,
            "match_score": match_percentage,
            "reasons": reasons,
            "missing_skills": missing_skills,
            "confidence_score": confidence
        })

    # Sort by match score descending
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations
