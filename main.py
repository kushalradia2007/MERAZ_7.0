from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
import jwt
import datetime
import os
import random
import string
import json
import urllib.request
import re
from dotenv import load_dotenv

load_dotenv()

import database, models

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="NIGHTJAR API")

class StripVercelPathMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path.startswith("/api/index.py"):
                path = path.replace("/api/index.py", "", 1)
            elif path.startswith("/main.py"):
                path = path.replace("/main.py", "", 1)
            scope["path"] = path or "/"
        return await self.app(scope, receive, send)

app.add_middleware(StripVercelPathMiddleware)

from fastapi.staticfiles import StaticFiles
import os

if os.path.isdir("Challenges"):
    app.mount("/challenges", StaticFiles(directory="Challenges"), name="challenges")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "nightjar_super_secret" 

def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(models.User).filter(models.User.username == username).first()
        return user
    except jwt.PyJWTError:
        return None

def require_admin(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ─── Page Routes ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: models.User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/hub")
    with open("login.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/hub", response_class=HTMLResponse)
async def read_hub(request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/")
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request, user: models.User = Depends(get_current_user)):
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    with open("admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/room/{room_id}", response_class=HTMLResponse)
async def read_room(room_id: int, request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/")
    room_files = {
        1: "room1.html",
        2: "room2.html",
        3: "room3.html",
        4: "room4.html",
        5: "room5.html",
        6: "room6.html",
        7: "room7.html",
        8: "room8.html",
        9: "room9.html",
    }
    filename = room_files.get(room_id)
    if filename and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    # Fallback: redirect to hub if room page doesn't exist yet
    return RedirectResponse(url="/hub")

@app.get("/scoreboard", response_class=HTMLResponse)
async def read_scoreboard():
    with open("scoreboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ─── Auth API ──────────────────────────────────────────────────

@app.post("/api/send-code")
async def send_verification_code(
    email: str = Form(...),
    db: Session = Depends(database.get_db)
):
    code = ''.join(random.choices(string.digits, k=6))
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    
    vc = db.query(models.VerificationCode).filter(models.VerificationCode.email == email).first()
    if vc:
        vc.code = code
        vc.expires_at = expire
    else:
        vc = models.VerificationCode(email=email, code=code, expires_at=expire)
        db.add(vc)
    db.commit()
    
    print(f"\n[MOCK EMAIL] Verification code for {email} is: {code}\n")
    return {"message": "Verification code sent to email"}

@app.post("/api/register")
async def register(
    response: Response,
    action: str = Form(...),
    email: str = Form(...),
    verification_code: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    team_name: str = Form(None),
    invite_code: str = Form(None),
    db: Session = Depends(database.get_db)
):
    vc = db.query(models.VerificationCode).filter(models.VerificationCode.email == email).first()
    if not vc or vc.code != verification_code or vc.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    team = None
    if action == "create_team":
        if not team_name:
            raise HTTPException(status_code=400, detail="Team name required to create team")
        if db.query(models.Team).filter(models.Team.name == team_name).first():
            raise HTTPException(status_code=400, detail="Team name already taken")
        
        new_invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        team = models.Team(name=team_name, invite_code=new_invite_code)
        db.add(team)
        db.commit()
        db.refresh(team)
    elif action == "join_team":
        if not invite_code:
            raise HTTPException(status_code=400, detail="Invite code required to join team")
        team = db.query(models.Team).filter(models.Team.invite_code == invite_code).first()
        if not team:
            raise HTTPException(status_code=400, detail="Invalid invite code")
        if len(team.users) >= 4:
            raise HTTPException(status_code=400, detail="Team is full (max 4 members)")
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    hashed_password = pwd_context.hash(password)
    user = models.User(
        username=username, 
        email=email,
        is_email_verified=True,
        hashed_password=hashed_password, 
        team_id=team.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    if action == "create_team":
        team.leader_id = user.id
        db.commit()
    
    db.delete(vc)
    db.commit()

    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return {"message": "Registered successfully"}

def verify_google_id_token(token: str):
    """Verifies a Google ID token using Google's public tokeninfo endpoint."""
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        req = urllib.request.Request(url, headers={"User-Agent": "SPECTRE-FastAPI"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
            
            if data.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                return None
                
            google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
            if google_client_id and data.get("aud") != google_client_id:
                return None
                
            ev = data.get("email_verified")
            if str(ev).lower() not in ["true", "1"]:
                return None
                
            return data
    except Exception as e:
        print(f"Error validating Google token: {e}")
        return None

@app.get("/api/auth/config")
async def get_auth_config():
    return {
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip()
    }

@app.post("/api/auth/google")
async def google_auth(
    response: Response,
    id_token: str = Form(...),
    username: str = Form(None),
    action: str = Form(None),
    team_name: str = Form(None),
    invite_code: str = Form(None),
    db: Session = Depends(database.get_db)
):
    payload = verify_google_id_token(id_token)
    if not payload or not payload.get("email"):
        raise HTTPException(status_code=400, detail="Invalid or unverified Google token")

    email = payload.get("email").strip().lower()

    # Check if a user already exists with this email
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()

    if user:
        # Existing user: Log in directly
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        token = jwt.encode({"sub": user.username, "exp": expire}, SECRET_KEY, algorithm="HS256")
        response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
        return {"status": "authenticated", "message": "Login successful", "is_admin": user.is_admin}

    # New user: Check if operative profile details provided
    if not username or not action:
        raw_name = payload.get("given_name") or payload.get("name") or email.split("@")[0]
        suggested = re.sub(r'[^a-zA-Z0-9_]', '', raw_name)[:15]
        return {
            "status": "needs_profile",
            "email": email,
            "suggested_username": suggested,
            "name": payload.get("name", "")
        }

    username = username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Operative codename (username) is required")

    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered. Please choose another.")

    team = None
    if action == "create_team":
        if not team_name or not team_name.strip():
            raise HTTPException(status_code=400, detail="Team name is required to create a team")
        team_name = team_name.strip()
        if db.query(models.Team).filter(models.Team.name == team_name).first():
            raise HTTPException(status_code=400, detail="Team name already taken")

        new_invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        team = models.Team(name=team_name, invite_code=new_invite_code)
        db.add(team)
        db.commit()
        db.refresh(team)
    elif action == "join_team":
        if not invite_code or not invite_code.strip():
            raise HTTPException(status_code=400, detail="Invite code is required to join a team")
        invite_code = invite_code.strip().upper()
        team = db.query(models.Team).filter(models.Team.invite_code == invite_code).first()
        if not team:
            raise HTTPException(status_code=400, detail="Invalid team invite code")
        if len(team.users) >= 4:
            raise HTTPException(status_code=400, detail="Team is full (maximum 4 members)")
    else:
        raise HTTPException(status_code=400, detail="Invalid team action")

    # Create new verified user
    new_user = models.User(
        username=username,
        email=email,
        is_email_verified=True,
        hashed_password=None,
        team_id=team.id,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if action == "create_team":
        team.leader_id = new_user.id
        db.commit()

    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return {"status": "authenticated", "message": "Registered and logged in"}

@app.post("/api/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.hashed_password or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=400, 
            detail="Incorrect username or password. (If registered via Google, please sign in with Google.)"
        )

    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return {"message": "Login successful", "is_admin": user.is_admin}

@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

# ─── Game API ──────────────────────────────────────────────────

@app.post("/api/submit_flag")
async def submit_flag(room_id: int = Form(...), flag: str = Form(...), user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Define valid flags per room — each room has 4 challenges worth 25 pts each
    valid_flags = {
        1: [
            "NIGHTJAR{aether_07_nothing_stays_local}",
            "NIGHTJAR{parallax_systems_aman_v}",
            "NIGHTJAR{nexus-meraz.festival.in.net}",
            "NIGHTJAR{curator_404}"
        ],
        2: [
            "NIGHTJAR{the_host_with_the_blue_name_is_lying}",
            "NIGHTJAR{blue_name_is_host_alias_not_a_person}",
            "NIGHTJAR{ask_the_person_who_never_signs_in}",
            "NIGHTJAR{aether_7_relay_compromised}"
        ],
        3: [
            "NIGHTJAR{10.7.7.43_to_203.0.113.77_port_8443}",
            "NIGHTJAR{maint_window_0200_user_kite_backup}",
            "NIGHTJAR{restore_aether_core_confirmed}",
            "NIGHTJAR{port_4477_mira_7_propagation_service}"
        ],
        4: [
            "NIGHTJAR{nexus_health_monitor_pid_2847_opt_mira}",
            "NIGHTJAR{kite_backup_session_via_auth_token_0137}",
            "NIGHTJAR{suid_aether_restart_owned_by_root_writable_by_nexus}",
            "NIGHTJAR{ed25519_kite_backup_2019_added_oct_2026_aetherforge}"
        ],
        5: [
            "NIGHTJAR{idor_volunteer_0x7F_infra_access_no_orientation}",
            "NIGHTJAR{jwt_role_volunteer_plus_admin_cert_renewal}",
            "NIGHTJAR{cmd_injection_mira_config_at_etc_nexus_mira_conf}",
            "NIGHTJAR{maint_nexus_portal_certrenew_api_v1_renew}"
        ],
        6: [
            "NIGHTJAR{ghost_record_vol_127_nexus_svc_auto_insert_no_sponsor}",
            "NIGHTJAR{continuity_delegate_role_read_all_plus_cert_trust_store}",
            "NIGHTJAR{badge_0x7F_infra_dual_scan_main_stage_server_b3_61s}",
            "NIGHTJAR{trust_chain_aether_core_to_release_controller_full_trust}"
        ],
        7: [
            "NIGHTJAR{phish_kabir_sep27_nexus_support_spoofed_real_ticket_ref}",
            "NIGHTJAR{impossible_travel_kabir_amsterdam_0135_stolen_session_token}",
            "NIGHTJAR{mfa_fatigue_14_pushes_auto_approve_30s_timeout_gateway}",
            "NIGHTJAR{persona_kite_backup_simulated_insider_from_stolen_creds}"
        ],
        8: [
            "NIGHTJAR{pe_header_mismatch_fake_sig_section_rwx_not_nexus_registry}",
            "NIGHTJAR{c2_parallax_sys_net_xor_key_0x4d_beacon_300s_nothing_stays_local}",
            "NIGHTJAR{mira_propagate_dormant_nexus_zone_core_aether7_activated}",
            "NIGHTJAR{mira7_built_oct3_auto_aether_forge_not_curator_manual}"
        ],
        9: [
            "NIGHTJAR{timeline_staging_sep28_nexus_sync_precheck_clock_skew}",
            "NIGHTJAR{gap_420s_auditd_buffer_flush_ipmi_bmc_continuity_uid0}",
            "NIGHTJAR{path_kite_to_maint_to_continuity_to_aether7_master_relay}",
            "NIGHTJAR{rca_cr0919_autofailover_human_gate_disabled_latency_spike}"
        ]
    }
    
    if room_id in valid_flags and flag in valid_flags[room_id]:
        if user.team:
            # Check if this exact flag was already submitted by this team
            already = db.query(models.FlagSubmission).filter(
                models.FlagSubmission.team_id == user.team.id,
                models.FlagSubmission.room_id == room_id,
                models.FlagSubmission.is_correct == True,
                models.FlagSubmission.flag_value == flag
            ).first()
            if already:
                return {"success": True, "message": "Already submitted! Flag was correct."}
            
            # Record the submission
            sub = models.FlagSubmission(
                team_id=user.team.id,
                room_id=room_id,
                is_correct=True,
                flag_value=flag
            )
            db.add(sub)
            user.team.score += 25  # Each flag gives 25 points
            
            # Check if all 4 flags for this room are solved
            correct_in_room = db.query(models.FlagSubmission).filter(
                models.FlagSubmission.team_id == user.team.id,
                models.FlagSubmission.room_id == room_id,
                models.FlagSubmission.is_correct == True
            ).count() + 1  # +1 for the one we're about to add
            
            if correct_in_room >= 4 and user.team.current_room <= room_id:
                user.team.current_room = room_id + 1
            
            db.commit()
        return {"success": True, "message": "Correct! Flag accepted."}
    
    # Log incorrect submission
    if user.team:
        sub = models.FlagSubmission(
            team_id=user.team.id,
            room_id=room_id,
            is_correct=False,
            flag_value=flag
        )
        db.add(sub)
        db.commit()
    
    if flag == "TEST_FLAG":
        return {"success": True, "message": "Correct! Room unlocked (TEST)."}
        
    return {"success": False, "message": "Incorrect flag. Try again."}

@app.get("/api/me")
async def get_me(user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "username": user.username,
        "is_admin": user.is_admin,
        "team": user.team.name if user.team else None,
        "invite_code": user.team.invite_code if (user.team and user.team.leader_id == user.id) else None,
        "is_leader": (user.team and user.team.leader_id == user.id)
    }

# ─── Scoreboard API (public) ──────────────────────────────────

@app.get("/api/scoreboard")
async def get_scoreboard(db: Session = Depends(database.get_db)):
    teams = db.query(models.Team).order_by(models.Team.score.desc(), models.Team.created_at.asc()).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "score": t.score,
            "current_room": t.current_room,
            "members": len(t.users),
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in teams
    ]

# ─── Admin API (protected) ────────────────────────────────────

@app.get("/api/admin/teams")
async def admin_get_teams(admin: models.User = Depends(require_admin), db: Session = Depends(database.get_db)):
    teams = db.query(models.Team).order_by(models.Team.created_at.asc()).all()
    result = []
    for t in teams:
        members = [{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in t.users]
        subs = db.query(models.FlagSubmission).filter(models.FlagSubmission.team_id == t.id).count()
        correct = db.query(models.FlagSubmission).filter(
            models.FlagSubmission.team_id == t.id,
            models.FlagSubmission.is_correct == True
        ).count()
        result.append({
            "id": t.id,
            "name": t.name,
            "score": t.score,
            "current_room": t.current_room,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "members": members,
            "total_submissions": subs,
            "correct_submissions": correct
        })
    return result

@app.put("/api/admin/teams/{team_id}/score")
async def admin_update_score(
    team_id: int,
    score: int = Body(..., embed=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.score = score
    db.commit()
    return {"message": f"Score updated to {score}", "team": team.name}

@app.put("/api/admin/teams/{team_id}/room")
async def admin_update_room(
    team_id: int,
    room: int = Body(..., embed=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.current_room = room
    db.commit()
    return {"message": f"Room updated to {room}", "team": team.name}

@app.delete("/api/admin/teams/{team_id}")
async def admin_delete_team(
    team_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    # Delete users and submissions first
    db.query(models.FlagSubmission).filter(models.FlagSubmission.team_id == team_id).delete()
    db.query(models.User).filter(models.User.team_id == team_id).delete()
    db.delete(team)
    db.commit()
    return {"message": f"Team '{team.name}' deleted"}

@app.put("/api/admin/users/{user_id}/toggle-admin")
async def admin_toggle_admin(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin status")
    user.is_admin = not user.is_admin
    db.commit()
    return {"message": f"Admin status for '{user.username}' set to {user.is_admin}"}

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"message": f"User '{user.username}' deleted"}

@app.post("/api/admin/reset-scores")
async def admin_reset_scores(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    db.query(models.Team).update({models.Team.score: 0, models.Team.current_room: 1})
    db.query(models.FlagSubmission).delete()
    db.commit()
    return {"message": "All scores and progress reset"}

@app.get("/api/admin/stats")
async def admin_stats(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db)
):
    total_teams = db.query(models.Team).count()
    total_users = db.query(models.User).count()
    total_subs = db.query(models.FlagSubmission).count()
    correct_subs = db.query(models.FlagSubmission).filter(models.FlagSubmission.is_correct == True).count()
    top_team = db.query(models.Team).order_by(models.Team.score.desc()).first()
    return {
        "total_teams": total_teams,
        "total_users": total_users,
        "total_submissions": total_subs,
        "correct_submissions": correct_subs,
        "top_team": {"name": top_team.name, "score": top_team.score} if top_team else None
    }

