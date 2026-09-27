import os
import io
import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from database import Base, engine, SessionLocal, User, Goal, Milestone, Reminder, Conversation, Memory, Artifact , AppealRequest
from auth import hash_password, verify_password, create_access_token, decode_access_token
from llm_router import run_llm_with_failover
from agent_worker import AutonomousAgent
from vector_service import LocalRAGService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AURA-Core")

# Storage Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_STORAGE_DIR = os.path.join(BASE_DIR, "artifacts_storage")
os.makedirs(ARTIFACT_STORAGE_DIR, exist_ok=True)

# Background Scheduler
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_default_users()
    scheduler.add_job(AutonomousAgent.midnight_decay_and_alert, CronTrigger(hour=0, minute=0))
    scheduler.add_job(AutonomousAgent.audit_and_nudge, CronTrigger(hour=8, minute=30))
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="AURA Intelligence Engine", version="2.0-hardened", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication Dependencies
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing, expired, or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative privileges required")
    return current_user

def seed_default_users():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            pwd_hash, salt = hash_password("admin123")
            db.add(User(username="admin", password_hash=pwd_hash, salt=salt, role="admin", freeze_tokens=5))
        if not db.query(User).filter(User.username == "john").first():
            pwd_hash, salt = hash_password("operator123")
            db.add(User(username="john", password_hash=pwd_hash, salt=salt, role="operator", freeze_tokens=2))
        db.commit()
    finally:
        db.close()

# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class ChatMessagePayload(BaseModel):
    message: str
    conversation_history: Optional[List[ChatHistoryItem]] = []

class ModuleChatPayload(BaseModel):
    module_key: str
    message: str
    conversation_history: Optional[List[ChatHistoryItem]] = []

class ArtifactChatPayload(BaseModel):
    artifact_id: int
    message: str
    conversation_history: Optional[List[ChatHistoryItem]] = []

class CreateGoalRequest(BaseModel):
    intention: str
    timeline: str = "3 months"
    current_level: str = "Beginner"

class RecoverySubmission(BaseModel):
    submission_note: str

# In D:\aura\main.py:

class UserStatusAction(BaseModel):
    action: str  # 'approve', 'reject', 'ban', 'unban'
    reason: Optional[str] = None

class AppealSubmission(BaseModel):
    username: str
    appeal_type: str = "unban"  # "unban" or "info"
    message: str

@app.post("/auth/register")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    clean_username = username.strip().lower()
    if db.query(User).filter(User.username == clean_username).first():
        raise HTTPException(status_code=400, detail="Username is already registered")

    avatar_path = None
    if avatar and avatar.filename:
        safe_fn = f"{clean_username}_{int(datetime.utcnow().timestamp())}_{avatar.filename}"
        avatar_path = os.path.join(AVATAR_DIR, safe_fn)
        with open(avatar_path, "wb") as f:
            f.write(await avatar.read())

    pwd_hash, salt = hash_password(password.strip())
    new_user = User(
        username=clean_username,
        email=email.strip().lower() if email else None,
        phone=phone.strip() if phone else None,
        address=address.strip() if address else None,
        bio=bio.strip() if bio else None,
        profile_pic=avatar_path,
        password_hash=pwd_hash,
        salt=salt,
        role="operator",
        status="pending",  # Requires Admin Approval
        freeze_tokens=2
    )
    db.add(new_user)
    db.commit()
    return {"status": "pending_approval", "message": "Account registration submitted. An administrator must approve your account before login."}

@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_username = payload.username.strip().lower()
    user = db.query(User).filter(User.username == clean_username).first()
    user_salt = getattr(user, "salt", None)
    
    if not user or not verify_password(payload.password.strip(), user.password_hash, user_salt):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Enforce User Lifecycle Governance
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="ACCOUNT_PENDING: Your registration request is pending administrative review.")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="ACCOUNT_REJECTED: Your operator registration request was declined.")
    if user.status == "banned":
        reason = user.ban_reason or "Suspicious or unauthorized activities detected."
        raise HTTPException(status_code=403, detail=f"ACCOUNT_BANNED: Access suspended. Reason: {reason}")

    token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "bio": user.bio,
        "profile_pic": user.profile_pic
    }

@app.post("/auth/appeal")
def submit_appeal(payload: AppealSubmission, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="Operator record not found")
    if user.status != "banned":
        raise HTTPException(status_code=400, detail="Only banned operators may file appeals")

    appeal = AppealRequest(
        user_id=user.id,
        appeal_type=payload.appeal_type,
        message=payload.message.strip()
    )
    db.add(appeal)
    db.commit()
    return {"status": "received", "message": "Appeal request transmitted to Admin review dispatch."}

# Admin Governance Endpoints
@app.get("/admin/pending-operators")
def list_pending_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.status == "pending").all()
    return {"pending_operators": [{"id": u.id, "username": u.username, "email": u.email, "bio": u.bio, "requested_at": u.created_at} for u in users]}

@app.post("/admin/operators/{user_id}/status")
def update_user_status(user_id: int, payload: UserStatusAction, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target operator not found")
    if target_user.role == "admin":
        raise HTTPException(status_code=400, detail="Administrative accounts cannot be modified")

    if payload.action == "approve":
        target_user.status = "active"
        target_user.ban_reason = None
    elif payload.action == "reject":
        target_user.status = "rejected"
    elif payload.action == "ban":
        target_user.status = "banned"
        target_user.ban_reason = payload.reason or "Security audit infraction"
    elif payload.action == "unban":
        target_user.status = "active"
        target_user.ban_reason = None
    
    db.commit()
    return {"status": "success", "username": target_user.username, "new_state": target_user.status}

@app.get("/admin/appeals")
def get_appeals(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    appeals = db.query(AppealRequest).filter(AppealRequest.status == "pending").all()
    return {"appeals": [
        {"id": a.id, "user_id": a.user_id, "username": a.user.username, "type": a.appeal_type, "message": a.message, "date": a.created_at}
        for a in appeals
    ]}

# ----------------- SYSTEM & AUTH ENDPOINTS -----------------

@app.get("/health")
def system_health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "online" if db_ok else "degraded", "database": db_ok, "timestamp": datetime.utcnow().isoformat()}

@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip().lower()).first()
    if not user or not verify_password(payload.password.strip(), user.password_hash, user.salt):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

# ----------------- REASONING & CHAT -----------------

@app.post("/chat")
def chat_endpoint(payload: ChatMessagePayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memories = db.query(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.created_at.desc()).limit(5).all()
    mem_context = "\n".join([f"- [{m.category}] {m.fact}" for m in memories]) if memories else "No prior history."

    system_prompt = (
        f"You are AURA, an Adaptive Unified Reasoning Assistant.\n"
        f"Operator: {current_user.username} (Role: {current_user.role})\n"
        f"Cognitive User Context:\n{mem_context}\n"
        "Provide direct, high-density, analytical responses."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for item in (payload.conversation_history or [])[-6:]:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": payload.message})

    reply, provider = run_llm_with_failover(messages)
    formatted = f"{reply}\n\n*(Engine: {provider})*"

    db.add(Conversation(user_id=current_user.id, role="user", content=payload.message))
    db.add(Conversation(user_id=current_user.id, role="assistant", content=formatted))
    db.commit()

    return {"response": formatted, "provider": provider}

@app.post("/chat/artifact")
def artifact_chat(payload: ArtifactChatPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    art = db.query(Artifact).filter(Artifact.id == payload.artifact_id, Artifact.user_id == current_user.id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")

    content = ""
    if os.path.exists(art.file_path):
        with open(art.file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    chunks = LocalRAGService.rank_relevant_chunks(payload.message, content, top_k=3)
    grounded_context = "\n\n---\n\n".join(chunks) if chunks else content[:8000]

    sys_prompt = f"Grounded Artifact: {art.filename}\nContext:\n{grounded_context}\nAnswer citing specifics."
    messages = [{"role": "system", "content": sys_prompt}]
    for h in (payload.conversation_history or [])[-6:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": payload.message})

    reply, provider = run_llm_with_failover(messages)
    formatted = f"{reply}\n\n*(Engine: {provider} | Grounded: `{art.filename}`)*"

    db.add(Conversation(user_id=current_user.id, role="user", content=f"[{art.filename}] {payload.message}"))
    db.add(Conversation(user_id=current_user.id, role="assistant", content=formatted))
    db.commit()

    return {"response": formatted}

# ----------------- GOALS, STREAKS & FREEZES -----------------

@app.get("/goals/freeze-status")
def get_freeze_status(current_user: User = Depends(get_current_user)):
    return {"freeze_tokens": current_user.freeze_tokens}

@app.post("/goals/buy-freeze")
def add_freeze_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.freeze_tokens += 1
    db.commit()
    return {"freeze_tokens": current_user.freeze_tokens}

@app.get("/dashboard/summary")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id, Reminder.is_completed == False).all()
    return {
        "user": {"id": current_user.id, "username": current_user.username, "role": current_user.role},
        "goals": [
            {
                "id": g.id,
                "intention": g.intention,
                "timeline": g.timeline,
                "streak": g.streak_count,
                "saved_streak": g.saved_streak_count,
                "progress": g.progress_percentage,
                "streak_frozen": g.streak_frozen,
                "in_recovery": g.in_recovery,
                "recovery_task": g.recovery_task
            }
            for g in goals
        ],
        "reminders": [{"id": r.id, "task": r.task_text, "priority": r.priority, "due": r.due_info} for r in reminders]
    }

@app.post("/goals/{goal_id}/checkin")
def checkin_goal(goal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    today = date.today()
    if goal.last_check_in_date != today:
        goal.streak_count += 1
        goal.last_check_in_date = today
        goal.streak_frozen = False
        goal.in_recovery = False
        db.commit()
    return {"streak": goal.streak_count}

@app.post("/goals/{goal_id}/solve-recovery")
def solve_recovery(goal_id: int, payload: RecoverySubmission, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal or not goal.in_recovery:
        raise HTTPException(status_code=400, detail="Invalid recovery state")
    goal.streak_count = goal.saved_streak_count + 1
    goal.saved_streak_count = 0
    goal.in_recovery = False
    goal.recovery_task = None
    goal.last_check_in_date = date.today()
    db.commit()
    return {"status": "recovered", "streak": goal.streak_count}

# ----------------- ARTIFACT REPOSITORY -----------------

@app.post("/artifacts/upload")
async def upload_artifact(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("Analyze this file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_dir = os.path.join(ARTIFACT_STORAGE_DIR, f"user_{current_user.id}")
    os.makedirs(user_dir, exist_ok=True)
    file_bytes = await file.read()
    dest = os.path.join(user_dir, file.filename)
    with open(dest, "wb") as f:
        f.write(file_bytes)

    preview = file_bytes[:10000].decode("utf-8", errors="replace")
    analysis, provider = run_llm_with_failover([
        {"role": "system", "content": "You are AURA's Artifact Analyzer."},
        {"role": "user", "content": f"{prompt}\n\nDocument:\n{preview}"}
    ])
    art = Artifact(
        user_id=current_user.id,
        filename=file.filename,
        file_path=dest,
        file_size_bytes=len(file_bytes),
        analysis_summary=analysis
    )
    db.add(art)
    db.commit()
    return {"id": art.id, "filename": art.filename, "analysis": analysis}

@app.get("/artifacts")
def list_artifacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    arts = db.query(Artifact).filter(Artifact.user_id == current_user.id).all()
    return {"artifacts": [{"id": a.id, "filename": a.filename, "size_kb": round(a.file_size_bytes / 1024, 1)} for a in arts]}

# ----------------- WORKSPACE EXPORTS -----------------

@app.get("/export/json")
def export_json(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    mems = db.query(Memory).filter(Memory.user_id == current_user.id).all()
    convs = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    return {
        "operator": current_user.username,
        "goals": [{"intention": g.intention, "streak": g.streak_count} for g in goals],
        "memories": [{"fact": m.fact, "category": m.category} for m in mems],
        "transcripts": [{"role": c.role, "content": c.content} for c in convs]
    }

# ----------------- ADMIN CONSOLE -----------------

@app.get("/admin/users")
def get_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": [{"id": u.id, "username": u.username, "role": u.role, "freeze_tokens": u.freeze_tokens} for u in users]}

# In D:\aura\main.py

AVATAR_DIR = os.path.join(ARTIFACT_STORAGE_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

def seed_default_users():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            pwd_hash, salt = hash_password("admin123")
            db.add(User(
                username="admin", 
                email="admin@aura.internal",
                phone="+1-800-AURA-ADM",
                address="Neural Ops Central, Floor 10",
                bio="Platform Administrator & Core Controller",
                password_hash=pwd_hash, 
                salt=salt, 
                role="admin", 
                freeze_tokens=5
            ))
        elif not admin.salt:
            pwd_hash, salt = hash_password("admin123")
            admin.password_hash = pwd_hash
            admin.salt = salt

        john = db.query(User).filter(User.username == "john").first()
        if not john:
            pwd_hash, salt = hash_password("operator123")
            db.add(User(
                username="john", 
                email="john@operator.io",
                phone="+1-555-019-2834",
                address="Sector 4B, Operator Quad",
                bio="Systems Reliability Engineer",
                password_hash=pwd_hash, 
                salt=salt, 
                role="operator", 
                freeze_tokens=2
            ))
        elif not john.salt:
            pwd_hash, salt = hash_password("operator123")
            john.password_hash = pwd_hash
            john.salt = salt

        db.commit()
    finally:
        db.close()

# ----------------- REGISTRATION & LOGIN ENDPOINTS -----------------

@app.post("/auth/register")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    clean_username = username.strip().lower()
    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username is already claimed")

    if email:
        clean_email = email.strip().lower()
        if db.query(User).filter(User.email == clean_email).first():
            raise HTTPException(status_code=400, detail="Email is already registered")
    else:
        clean_email = None

    avatar_path = None
    if avatar and avatar.filename:
        safe_filename = f"{clean_username}_{int(datetime.utcnow().timestamp())}_{avatar.filename}"
        dest = os.path.join(AVATAR_DIR, safe_filename)
        avatar_bytes = await avatar.read()
        with open(dest, "wb") as f:
            f.write(avatar_bytes)
        avatar_path = dest

    pwd_hash, salt = hash_password(password.strip())
    new_user = User(
        username=clean_username,
        email=clean_email,
        phone=phone.strip() if phone else None,
        address=address.strip() if address else None,
        bio=bio.strip() if bio else None,
        profile_pic=avatar_path,
        password_hash=pwd_hash,
        salt=salt,
        role="operator",
        freeze_tokens=2
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username, "user_id": new_user.id, "role": new_user.role})
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "phone": new_user.phone,
            "address": new_user.address,
            "bio": new_user.bio,
            "role": new_user.role,
            "profile_pic": new_user.profile_pic
        }
    }

@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_username = payload.username.strip().lower()
    user = db.query(User).filter(User.username == clean_username).first()
    
    user_salt = getattr(user, "salt", None)
    if not user or not verify_password(payload.password.strip(), user.password_hash, user_salt):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "bio": user.bio,
        "profile_pic": user.profile_pic
    }

@app.get("/auth/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone,
        "address": current_user.address,
        "bio": current_user.bio,
        "role": current_user.role,
        "freeze_tokens": current_user.freeze_tokens,
        "profile_pic": current_user.profile_pic
    }