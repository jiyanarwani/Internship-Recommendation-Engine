from flask import Blueprint, request, jsonify, session
from models import db, User, Profile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'candidate').strip().lower()  # 'candidate' or 'admin'
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    if role not in ['candidate', 'admin']:
        role = 'candidate'
        
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400
        
    try:
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Auto-create empty profile if they are a candidate
        if role == 'candidate':
            profile = Profile(
                user_id=user.id,
                full_name=email.split('@')[0].capitalize(),
                skills=[],
                interests=[]
            )
            db.session.add(profile)
            db.session.commit()
            
        return jsonify({"message": "Registration successful. You can now login.", "user_id": user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
        
    # Store session
    session['user_id'] = user.id
    session['role'] = user.role
    
    # Check profile completion
    profile_completed = False
    full_name = "User"
    if user.role == 'candidate' and user.profile:
        full_name = user.profile.full_name
        # Profile is considered filled if they have added education, degree, branch, and some skills
        p = user.profile
        if p.education_level and p.degree and p.branch and p.skills:
            profile_completed = True

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "name": full_name,
            "profile_completed": profile_completed
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/session', methods=['GET'])
def check_session():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"logged_in": False}), 200
        
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({"logged_in": False}), 200
        
    profile_completed = False
    full_name = "User"
    if user.role == 'candidate' and user.profile:
        full_name = user.profile.full_name
        p = user.profile
        if p.education_level and p.degree and p.branch and p.skills:
            profile_completed = True
            
    return jsonify({
        "logged_in": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "name": full_name,
            "profile_completed": profile_completed
        }
    }), 200
