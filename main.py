import os
import io
import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Form, status, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from database import Base, engine, SessionLocal, User, Goal, Milestone, Reminder, Conversation, Memory, Artifact, AppealRequest
from auth import hash_password, verify_password, create_access_token, decode_access_token
from llm_router import run_llm_with_failover
from agent_worker import AutonomousAgent
from vector_service import LocalRAGService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AURA-Core")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_STORAGE_DIR = os.path.join(BASE_DIR, "artifacts_storage")
AVATAR_DIR = os.path.join(ARTIFACT_STORAGE_DIR, "avatars")
os.makedirs(ARTIFACT_STORAGE_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate new columns
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE conversations ADD COLUMN session_id VARCHAR(50)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE goals ADD COLUMN daily_routine TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE reminders ADD COLUMN goal_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE reminders ADD COLUMN completed_at DATETIME"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN dob VARCHAR(30)"))
        except Exception:
            pass
        conn.commit()
        
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            pwd_hash, salt = hash_password("admin123")
            db.add(User(
                username="admin", 
<<<<<<< HEAD
                email="admin@aura.internal",
                phone="+1-800-AURA-ADM",
=======
                full_name="AURA Prime Controller",
                email="admin@aura.internal",
                phone="+1-800-AURA-ADM",
                dob="1990-01-01",
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)
                address="Neural Ops Central, Floor 10",
                bio="Platform Administrator & Core Controller",
                password_hash=pwd_hash, 
                salt=salt, 
                role="admin", 
                status="active",
                freeze_tokens=5
            ))
<<<<<<< HEAD
        elif not getattr(admin, "salt", None):
            pwd_hash, salt = hash_password("admin123")
            admin.password_hash = pwd_hash
            admin.salt = salt
            admin.status = "active"
=======
        else:
            if not getattr(admin, "salt", None):
                pwd_hash, salt = hash_password("admin123")
                admin.password_hash = pwd_hash
                admin.salt = salt
                admin.status = "active"
            if not admin.full_name:
                admin.full_name = "AURA Prime Controller"
            if not admin.dob:
                admin.dob = "1990-01-01"
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)

        john = db.query(User).filter(User.username == "john").first()
        if not john:
            pwd_hash, salt = hash_password("operator123")
            db.add(User(
                username="john", 
<<<<<<< HEAD
                email="john@operator.io",
                phone="+1-555-019-2834",
=======
                full_name="John Operator",
                email="john@operator.io",
                phone="+1-555-019-2834",
                dob="1998-05-15",
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)
                address="Sector 4B, Operator Quad",
                bio="Systems Reliability Engineer",
                password_hash=pwd_hash, 
                salt=salt, 
                role="operator", 
                status="active",
                freeze_tokens=2
            ))
<<<<<<< HEAD
        elif not getattr(john, "salt", None):
            pwd_hash, salt = hash_password("operator123")
            john.password_hash = pwd_hash
            john.salt = salt
            john.status = "active"
=======
        else:
            if not getattr(john, "salt", None):
                pwd_hash, salt = hash_password("operator123")
                john.password_hash = pwd_hash
                john.salt = salt
                john.status = "active"
            if not john.full_name:
                john.full_name = "John Operator"
            if not john.dob:
                john.dob = "1998-05-15"
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)

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
<<<<<<< HEAD
=======
    session_id: Optional[str] = None
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)

class ArtifactChatPayload(BaseModel):
    artifact_id: int
    message: str
    conversation_history: Optional[List[ChatHistoryItem]] = []
<<<<<<< HEAD
=======
    session_id: Optional[str] = None
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)

class UserStatusAction(BaseModel):
    action: str  # 'approve', 'reject', 'ban', 'unban'
    reason: Optional[str] = None

class AppealSubmission(BaseModel):
    username: str
    appeal_type: str = "unban"  # "unban" or "info"
    message: str

class RecoverySubmission(BaseModel):
    submission_note: str

<<<<<<< HEAD
=======
class GoalCreatePayload(BaseModel):
    intention: str
    duration: str = "Unknown"
    experience: str = "Beginner"
    category: str = "General"

class ReminderCreatePayload(BaseModel):
    task_text: str
    priority: str = "Medium"
    due_info: str = "Today"
    goal_id: Optional[int] = None

class AuraVoicePayload(BaseModel):
    transcript: str
    voice_speed: Optional[float] = 1.0

JarvisVoicePayload = AuraVoicePayload

class ProfileUpdatePayload(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    profile_pic: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)
# ----------------- SYSTEM & AUTH -----------------

@app.get("/health")
def system_health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "online" if db_ok else "degraded", "database": db_ok, "timestamp": datetime.utcnow().isoformat()}

@app.post("/auth/register")
async def register_user(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    avatar_path = None
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        username = str(form.get("username", "")).strip().lower()
        password = str(form.get("password", "")).strip()
        full_name = str(form.get("full_name", "")).strip() or None
        email = str(form.get("email", "")).strip().lower() or None
        phone = str(form.get("phone", "")).strip() or None
        dob = str(form.get("dob", "")).strip() or None
        address = str(form.get("address", "")).strip() or None
        bio = str(form.get("bio", "")).strip() or None
        avatar = form.get("avatar")
        profile_pic_data = form.get("profile_pic_data")
        
        if avatar and hasattr(avatar, "filename") and avatar.filename:
            safe_fn = f"{username}_{int(datetime.utcnow().timestamp())}_{os.path.basename(avatar.filename)}"
            disk_path = os.path.join(AVATAR_DIR, safe_fn)
            content = await avatar.read()
            with open(disk_path, "wb") as f:
                f.write(content)
            avatar_path = f"/avatars/{safe_fn}"
        elif profile_pic_data:
            avatar_path = str(profile_pic_data).strip()
    else:
        body = await request.json()
        username = str(body.get("username", "")).strip().lower()
        password = str(body.get("password", "")).strip()
        full_name = str(body.get("full_name", "")).strip() or None
        email = str(body.get("email", "")).strip().lower() or None
        phone = str(body.get("phone", "")).strip() or None
        dob = str(body.get("dob", "")).strip() or None
        address = str(body.get("address", "")).strip() or None
        bio = str(body.get("bio", "")).strip() or None
        avatar_path = body.get("profile_pic")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username is already registered")

    pwd_hash, salt = hash_password(password)
    new_user = User(
        username=username,
        full_name=full_name or username.capitalize(),
        email=email,
        phone=phone,
        dob=dob,
        address=address,
        bio=bio,
        profile_pic=avatar_path,
        password_hash=pwd_hash,
        salt=salt,
        role="operator",
        status="active",
        freeze_tokens=2
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username, "user_id": new_user.id, "role": new_user.role})
    return {
        "status": "success",
        "message": "Account created successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "email": new_user.email,
        "phone": new_user.phone,
        "dob": new_user.dob,
        "address": new_user.address,
        "bio": new_user.bio,
        "profile_pic": new_user.profile_pic,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }

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
        "full_name": getattr(user, "full_name", None) or user.username.capitalize(),
        "role": user.role,
        "email": user.email,
        "phone": user.phone,
        "dob": getattr(user, "dob", None),
        "address": user.address,
        "bio": user.bio,
        "profile_pic": user.profile_pic,
        "status": user.status,
        "freeze_tokens": user.freeze_tokens,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

# ----------------- OPERATOR PROFILE ENDPOINTS -----------------

@app.get("/user/profile")
def get_user_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).all()
    convs_count = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    
    active_goals = len(goals)
    completed_tasks = sum(1 for r in reminders if r.is_completed)
    pending_tasks = sum(1 for r in reminders if not r.is_completed)
    peak_streak = max([g.streak_count for g in goals], default=0)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name or current_user.username.capitalize(),
        "email": current_user.email,
        "phone": current_user.phone,
        "dob": current_user.dob,
        "address": current_user.address,
        "bio": current_user.bio,
        "profile_pic": current_user.profile_pic,
        "role": current_user.role,
        "status": current_user.status,
        "freeze_tokens": current_user.freeze_tokens,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "stats": {
            "active_goals": active_goals,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "peak_streak": peak_streak,
            "total_chats": convs_count
        }
    }

@app.put("/user/profile")
def update_user_profile(payload: ProfileUpdatePayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.email is not None:
        current_user.email = payload.email.strip().lower() if payload.email.strip() else None
    if payload.phone is not None:
        current_user.phone = payload.phone.strip() if payload.phone.strip() else None
    if payload.dob is not None:
        current_user.dob = payload.dob.strip() if payload.dob.strip() else None
    if payload.address is not None:
        current_user.address = payload.address.strip() if payload.address.strip() else None
    if payload.bio is not None:
        current_user.bio = payload.bio.strip() if payload.bio.strip() else None
    if payload.profile_pic is not None:
        current_user.profile_pic = payload.profile_pic.strip() if payload.profile_pic.strip() else None

    if payload.new_password:
        if not payload.current_password:
            raise HTTPException(status_code=400, detail="Current password required to update password")
        if not verify_password(payload.current_password.strip(), current_user.password_hash, getattr(current_user, "salt", None)):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        new_hash, salt = hash_password(payload.new_password.strip())
        current_user.password_hash = new_hash
        current_user.salt = salt

    db.commit()
    db.refresh(current_user)
    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name or current_user.username.capitalize(),
            "email": current_user.email,
            "phone": current_user.phone,
            "dob": current_user.dob,
            "address": current_user.address,
            "bio": current_user.bio,
            "profile_pic": current_user.profile_pic,
            "role": current_user.role,
            "status": current_user.status,
            "freeze_tokens": current_user.freeze_tokens
        }
    }

@app.post("/user/profile-photo")
async def upload_profile_photo(photo: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not photo.filename:
        raise HTTPException(status_code=400, detail="No photo file was uploaded")
    safe_fn = f"{current_user.username}_{int(datetime.utcnow().timestamp())}_{os.path.basename(photo.filename)}"
    disk_path = os.path.join(AVATAR_DIR, safe_fn)
    content = await photo.read()
    with open(disk_path, "wb") as f:
        f.write(content)
    avatar_url = f"/avatars/{safe_fn}"
    current_user.profile_pic = avatar_url
    db.commit()
    return {"status": "success", "profile_pic": avatar_url}

@app.get("/user/avatar/{user_id}")
def get_user_avatar(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.profile_pic:
        raise HTTPException(status_code=404, detail="Avatar not found")
    if user.profile_pic.startswith("/avatars/"):
        rel_fn = user.profile_pic.replace("/avatars/", "")
        p = os.path.join(AVATAR_DIR, rel_fn)
        if os.path.exists(p):
            return FileResponse(p)
    elif os.path.exists(user.profile_pic):
        return FileResponse(user.profile_pic)
    raise HTTPException(status_code=404, detail="Avatar file not found on disk")

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

# ----------------- CHAT & REASONING -----------------

@app.post("/chat")
def chat_endpoint(payload: ChatMessagePayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memories = db.query(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.created_at.desc()).limit(5).all()
    mem_context = "\n".join([f"- [{m.category}] {m.fact}" for m in memories]) if memories else "No prior history."

    system_prompt = (
        f"You are AURA, a brilliant, thoughtful, and warm personal partner and assistant to {current_user.username.capitalize()}.\n"
        f"User context:\n{mem_context}\n"
        "Communicate with natural human warmth, clarity, and genuine intelligence. Be helpful, direct, and thoughtful."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for item in (payload.conversation_history or [])[-6:]:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": payload.message})

    reply, provider = run_llm_with_failover(messages)
    formatted = f"{reply}\n\n*(Engine: {provider})*"

    c_user = Conversation(user_id=current_user.id, role="user", content=payload.message, session_id=payload.session_id)
    c_asst = Conversation(user_id=current_user.id, role="assistant", content=formatted, session_id=payload.session_id)
    
    db.add(c_user)
    db.add(c_asst)
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

    c_user = Conversation(user_id=current_user.id, role="user", content=f"[{art.filename}] {payload.message}", session_id=payload.session_id)
    c_asst = Conversation(user_id=current_user.id, role="assistant", content=formatted, session_id=payload.session_id)
    
    db.add(c_user)
    db.add(c_asst)
    db.commit()

    return {"response": formatted}

<<<<<<< HEAD
=======
@app.get("/chat/history")
def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Group by session_id
    rows = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.timestamp.desc()).all()
    sessions = {}
    for r in rows:
        sid = getattr(r, "session_id", None) or "legacy_session"
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append({"role": r.role, "content": r.content, "time": r.timestamp.isoformat()})
    
    out = []
    for sid, msgs in sessions.items():
        # Reverse to chronological order
        msgs.reverse()
        preview = msgs[0]["content"][:50] + "..." if msgs else "Empty Chat"
        out.append({"session_id": sid, "preview": preview, "messages": msgs})
    return {"history": out}

@app.delete("/chat/session/{session_id}")
def delete_chat_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted_count = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.session_id == session_id
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "deleted", "deleted_count": deleted_count, "session_id": session_id}

# --- AURA NEURAL VOICE DIRECTIVE ROUTE ---
@app.post("/aura/directive")
@app.post("/jarvis/directive")
def execute_aura_directive(
    payload: AuraVoicePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = payload.transcript.strip()
    
    # Context retrieval: user profile, active goals, open tasks
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id, Reminder.is_completed == False).all()
    
    context_str = f"Operator: {current_user.username.upper()} (Role: {current_user.role})\n"
    context_str += f"Goals: {', '.join([g.intention for g in goals[:3]]) if goals else 'No active goals'}\n"
    context_str += f"Pending Tasks: {', '.join([r.task_text for r in reminders[:3]]) if reminders else 'All directives cleared'}\n"

    system_instruction = (
        f"You are AURA, a brilliant, thoughtful, and warm personal partner to {current_user.username.capitalize()}.\n"
        "Communicate just like an articulate, empathetic, supportive human having a real-time voice conversation.\n"
        "Guidelines:\n"
        "- Tone: Genuine, calm, intelligent, and warm. Sound human, not like a chatbot or computer system.\n"
        "- Length: Keep verbal responses concise and natural (typically 1 to 3 sentences) so you don't overwhelm the user or talk over them.\n"
        "- Style: Never use robotic phrases like 'As an AI', 'Directive acknowledged', 'Cognitive systems nominal', or mechanical bullet dumps. Use natural, human conversational flow.\n"
        "- If the user shares a goal, problem, or feeling, acknowledge it with genuine human empathy and clarity.\n"
        f"Context about {current_user.username.capitalize()}:\n{context_str}"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": query}
    ]

    reply, provider = run_llm_with_failover(messages)

    # Save to history
    db.add(Conversation(user_id=current_user.id, role="user", content=f"[AURA Voice] {query}", session_id="aura_voice"))
    db.add(Conversation(user_id=current_user.id, role="assistant", content=f"[AURA] {reply}", session_id="aura_voice"))
    db.commit()

    return {
        "status": "acknowledged",
        "response_text": reply,
        "engine": provider,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/export/json")
def export_workspace(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).all()
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "operator": current_user.username,
        "goals": [{"intention": g.intention, "timeline": g.timeline, "streak": g.streak_count, "progress": g.progress_percentage} for g in goals],
        "reminders": [{"task": r.task_text, "completed": r.is_completed} for r in reminders],
        "conversations": [{"role": c.role, "content": c.content, "timestamp": c.timestamp.isoformat()} for c in conversations]
    }

>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)
# ----------------- GOALS & DASHBOARD -----------------

@app.get("/goals/freeze-status")
def get_freeze_status(current_user: User = Depends(get_current_user)):
    return {"freeze_tokens": current_user.freeze_tokens}

@app.post("/goals/buy-freeze")
def add_freeze_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.freeze_tokens += 1
    db.commit()
    return {"freeze_tokens": current_user.freeze_tokens}

def compute_auto_progress(goal: Goal, db: Session) -> int:
    import re
    # Priority 1: Progress driven by tasks completion
    tasks = db.query(Reminder).filter(Reminder.goal_id == goal.id).all()
    milestones = db.query(Milestone).filter(Milestone.goal_id == goal.id).all()

    if tasks:
        comp_tasks = sum(1 for t in tasks if t.is_completed)
        task_ratio = comp_tasks / len(tasks)
        if milestones:
            comp_m = sum(1 for m in milestones if m.is_completed)
            m_ratio = comp_m / len(milestones)
            auto_prog = int((0.7 * task_ratio + 0.3 * m_ratio) * 100)
        else:
            auto_prog = int(task_ratio * 100)
    elif milestones:
        comp_m = sum(1 for m in milestones if m.is_completed)
        auto_prog = int((comp_m / len(milestones)) * 100)
    else:
        timeline_str = (goal.timeline or "").lower()
        days = 30
        if "week" in timeline_str:
            nums = re.findall(r'\d+', timeline_str)
            days = (int(nums[0]) if nums else 1) * 7
        elif "month" in timeline_str:
            nums = re.findall(r'\d+', timeline_str)
            days = (int(nums[0]) if nums else 1) * 30
        elif "year" in timeline_str:
            nums = re.findall(r'\d+', timeline_str)
            days = (int(nums[0]) if nums else 1) * 365
        elif "day" in timeline_str:
            nums = re.findall(r'\d+', timeline_str)
            days = int(nums[0]) if nums else 30
        days = max(1, days)
        auto_prog = int(min(1.0, goal.streak_count / max(1, days)) * 100)

    return max(0, min(100, auto_prog))

@app.get("/dashboard/summary")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).order_by(Reminder.is_completed.asc(), Reminder.id.desc()).all()
    for g in goals:
        auto_prog = compute_auto_progress(g, db)
        if g.progress_percentage != auto_prog:
            g.progress_percentage = auto_prog
    db.commit()
    
    goal_map = {g.id: g.intention for g in goals}
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
                "recovery_task": g.recovery_task,
                "daily_routine": getattr(g, "daily_routine", None) or "No routine generated."
            }
            for g in goals
        ],
        "reminders": [
            {
                "id": r.id,
                "task": r.task_text,
                "priority": r.priority,
                "due": r.due_info,
                "is_completed": bool(r.is_completed),
                "goal_id": r.goal_id,
                "goal_title": goal_map.get(r.goal_id)
            }
            for r in reminders
        ]
    }

@app.post("/goals")
def create_goal(payload: GoalCreatePayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prompt = (
        f"The user wants to achieve this goal: '{payload.intention}'.\n"
        f"Category: {payload.category}\n"
        f"Duration: {payload.duration}\n"
        f"User Experience Level: {payload.experience}\n"
        "Generate a highly detailed strategic plan. Return ONLY a JSON object with EXACTLY these keys:\n"
        "- 'timeline': (string, e.g., '30 Days' or '12 Weeks')\n"
        "- 'phases': (list of 3-5 strings, major milestone titles)\n"
        "- 'summary': (string, 1-2 sentences summarizing what this goal entails)\n"
        "- 'roadmap': (list of 4-6 strings, detailed milestone steps where each item starts with a phase/timeline marker like 'Phase 1: ...' or 'Week 1: ...')\n"
        "- 'daily_tasks': (list of 3-5 strings, specific actionable daily habits the user should do each day)\n"
    )
    content, _ = run_llm_with_failover([{"role": "user", "content": prompt}], json_mode=True)
    try:
        cleaned_content = content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:]
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3]
        data = json.loads(cleaned_content.strip())
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON: {e} | Content: {content}")
        data = {
            "timeline": payload.duration, 
            "phases": ["Planning", "Execution", "Review"], 
            "summary": "Take consistent action towards your goal.",
            "roadmap": [
                "Phase 1 (Setup): Establish fundamentals and review tools.",
                "Phase 2 (Core Build): Implement core concepts and practice daily.",
                "Phase 3 (Mastery): Review metrics, refine output, and consolidate learnings."
            ],
            "daily_tasks": ["Work on primary objective for 30-45 minutes", "Log key takeaways and blockers"]
        }

    goal = Goal(
        user_id=current_user.id,
        intention=payload.intention,
        timeline=data.get("timeline", payload.duration or "30 Days"),
        current_level=payload.experience or "Beginner",
        last_check_in_date=None
    )

    summary_text = str(data.get("summary", "Take consistent daily action towards this goal.")).strip()
    roadmap_raw = data.get("roadmap", ["Focus on daily execution and review progress."])
    daily_tasks = data.get("daily_tasks", ["Dedicate 30 minutes to focused goal execution", "Record daily insights and progress"])

    markdown_text = f"### 📋 Goal Summary\n{summary_text}\n\n### 🗺️ Strategic Roadmap\n"
    if isinstance(roadmap_raw, list):
        for item in roadmap_raw:
            clean_item = str(item).strip()
            if clean_item:
                if not clean_item.startswith("-") and not clean_item.startswith("*"):
                    markdown_text += f"- {clean_item}\n"
                else:
                    markdown_text += f"{clean_item}\n"
    else:
        for line in str(roadmap_raw).split("\n"):
            clean_line = line.strip()
            if clean_line:
                if not clean_line.startswith("-") and not clean_line.startswith("*") and not (len(clean_line) > 1 and clean_line[0].isdigit() and clean_line[1] in [".", ")"]):
                    markdown_text += f"- {clean_line}\n"
                else:
                    markdown_text += f"{clean_line}\n"

    markdown_text += "\n### ✅ Daily Action Plan\n"
    for task in daily_tasks:
        clean_task = str(task).strip()
        if clean_task:
            if not clean_task.startswith("-") and not clean_task.startswith("*"):
                markdown_text += f"- {clean_task}\n"
            else:
                markdown_text += f"{clean_task}\n"

    setattr(goal, "daily_routine", markdown_text)
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    for phase in data.get("phases", []):
        db.add(Milestone(goal_id=goal.id, phase_title=phase))
        
    for rem in data.get("daily_tasks", []):
        db.add(Reminder(user_id=current_user.id, goal_id=goal.id, task_text=rem, priority="High", due_info="Today"))
        
    db.commit()
    return {"status": "created", "goal_id": goal.id}

@app.post("/reminders")
def create_reminder(payload: ReminderCreatePayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task_text = payload.task_text.strip()
    if not task_text:
        raise HTTPException(status_code=400, detail="Task text cannot be empty")
    r = Reminder(
        user_id=current_user.id,
        task_text=task_text,
        priority=payload.priority,
        due_info=payload.due_info,
        goal_id=payload.goal_id
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    if payload.goal_id:
        goal = db.query(Goal).filter(Goal.id == payload.goal_id).first()
        if goal:
            goal.progress_percentage = compute_auto_progress(goal, db)
            db.commit()
    return {"status": "created", "id": r.id}

@app.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Directive not found")
    goal_id = r.goal_id
    db.delete(r)
    db.commit()
    if goal_id:
        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        if goal:
            goal.progress_percentage = compute_auto_progress(goal, db)
            db.commit()
    return {"status": "deleted"}

@app.post("/reminders/{reminder_id}/toggle")
def toggle_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Directive not found")
    r.is_completed = not r.is_completed
    r.completed_at = datetime.utcnow() if r.is_completed else None
    
    streak_updated = False
    goal_streak = None
    goal_progress = None
    
    if r.goal_id:
        goal = db.query(Goal).filter(Goal.id == r.goal_id).first()
        if goal:
            today = date.today()
            # Check how many tasks are completed for this goal
            completed_tasks_count = db.query(Reminder).filter(
                Reminder.goal_id == goal.id,
                Reminder.is_completed == True
            ).count()
            
            # User requirement: "daily streak should update only after i complete atleast one or two daily task of that particular goal"
            if r.is_completed and completed_tasks_count >= 1:
                if goal.last_check_in_date != today:
                    goal.streak_count += 1
                    goal.last_check_in_date = today
                    goal.streak_frozen = False
                    goal.in_recovery = False
                    streak_updated = True
            
            # Update progress based on completed tasks
            goal.progress_percentage = compute_auto_progress(goal, db)
            goal_streak = goal.streak_count
            goal_progress = goal.progress_percentage
            
    db.commit()
    return {
        "status": "updated",
        "is_completed": r.is_completed,
        "streak_updated": streak_updated,
        "goal_streak": goal_streak,
        "goal_progress": goal_progress
    }

@app.get("/briefing/speak")
async def get_briefing_audio(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from briefing_service import BriefingService
    import asyncio
    import uuid
    import pyttsx3

    briefing = BriefingService.generate_morning_briefing()
    text = f"{briefing['headline']}. {briefing['status_summary']} {briefing['focus_directive']}"
    
    filename = f"briefing_{uuid.uuid4().hex}.wav"
    filepath = os.path.join(ARTIFACT_STORAGE_DIR, filename)

    def _generate_audio():
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.save_to_file(text, filepath)
        engine.runAndWait()

    await asyncio.to_thread(_generate_audio)
    
    return FileResponse(filepath, media_type="audio/wav")

@app.get("/briefing/listen")
async def get_briefing_audio_alias(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await get_briefing_audio(current_user=current_user, db=db)

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
        goal.progress_percentage = compute_auto_progress(goal, db)
        db.commit()
    return {"streak": goal.streak_count, "progress": goal.progress_percentage}

@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"status": "deleted"}

class ProgressPayload(BaseModel):
    progress: int

@app.put("/goals/{goal_id}/progress")
def update_progress(goal_id: int, payload: ProgressPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal.progress_percentage = max(0, min(100, payload.progress))
    db.commit()
    return {"status": "updated", "progress": goal.progress_percentage}

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

# ----------------- ADMIN GOVERNANCE -----------------

@app.get("/admin/users")
def get_all_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": [{"id": u.id, "username": u.username, "role": u.role, "status": u.status, "freeze_tokens": u.freeze_tokens} for u in users]}

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
<<<<<<< HEAD
    ]}
=======
    ]}

# --- SERVE AVATARS & MODERN UNIFIED WEB APPLICATION ---
WEB_DIR = os.path.join(BASE_DIR, "web")
os.makedirs(WEB_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)
app.mount("/avatars", StaticFiles(directory=AVATAR_DIR), name="avatars")
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)
