import datetime
import hashlib
import json
import os
import re
import secrets
import smtplib
import ssl
import string
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from passlib.context import CryptContext
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

load_dotenv()

import database, models  # noqa: E402

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="NIGHTJAR API")

# All file access is relative to this file (not the process CWD), so the app
# behaves the same under uvicorn, Vercel, or any other working directory.
BASE_DIR = Path(__file__).resolve().parent
CHALLENGES_DIR = BASE_DIR / "Challenges"


class StripVercelPathMiddleware:
    """Vercel can prefix the path with the function file name; strip it."""

    PREFIXES = ("/api/index.py", "/main.py")

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            for prefix in self.PREFIXES:
                if path == prefix or path.startswith(prefix + "/"):
                    path = path[len(prefix):]
                    break
            scope["path"] = path or "/"
        return await self.app(scope, receive, send)


app.add_middleware(StripVercelPathMiddleware)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Config / helpers ──────────────────────────────────────────

def _load_secret_key() -> str:
    """JWT signing key. Never hardcoded: it comes from SECRET_KEY, or (as a
    non-breaking fallback for deployments that haven't set it yet) is derived
    from DATABASE_URL, which is secret and stable across serverless instances."""
    key = os.getenv("SECRET_KEY", "").strip()
    if key:
        return key
    db_url = os.getenv("DATABASE_URL", "").strip()
    if db_url:
        print("[WARN] SECRET_KEY is not set; deriving a signing key from DATABASE_URL. "
              "Set SECRET_KEY explicitly.")
        return hashlib.sha256(("nightjar-session-key:" + db_url).encode()).hexdigest()
    print("[WARN] SECRET_KEY is not set; using a random per-process key "
          "(sessions will reset on restart).")
    return secrets.token_hex(32)


SECRET_KEY = _load_secret_key()
SESSION_HOURS = 24
MAX_TEAM_SIZE = 4
CODE_TTL_MINUTES = 15
CODE_RESEND_SECONDS = 30
MIN_PASSWORD_LEN = 8

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def utcnow() -> datetime.datetime:
    """Naive UTC 'now' (matches how the DateTime columns are stored)."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def issue_session(response: Response, request: Request, username: str) -> None:
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=SESSION_HOURS)
    token = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")
    forwarded = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    is_https = request.url.scheme == "https" or forwarded == "https"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        secure=is_https,
        max_age=SESSION_HOURS * 3600,
        path="/",
    )


def normalize_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise HTTPException(status_code=400, detail="Please enter a valid email address")
    return email


def clean_username(username: Optional[str]) -> str:
    username = (username or "").strip()
    if len(username) < 2 or len(username) > 32:
        raise HTTPException(status_code=400, detail="Username must be 2-32 characters")
    return username


def clean_team_name(team_name: Optional[str]) -> str:
    team_name = (team_name or "").strip()
    if not team_name:
        raise HTTPException(status_code=400, detail="Team name required to create team")
    if len(team_name) > 40:
        raise HTTPException(status_code=400, detail="Team name must be 40 characters or fewer")
    return team_name


def new_invite_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        raw = token[len("Bearer "):] if token.startswith("Bearer ") else token
        payload = jwt.decode(raw, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            return None
        return db.query(models.User).filter(models.User.username == username).first()
    except jwt.PyJWTError:
        return None


def require_admin(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def read_html(name: str) -> HTMLResponse:
    path = BASE_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Page not found")
    return HTMLResponse(content=path.read_text(encoding="utf-8"))


# ─── Page Routes ───────────────────────────────────────────────
# (plain `def` handlers run in FastAPI's threadpool, so blocking DB/file/network
#  calls no longer stall the event loop)

@app.get("/", response_class=HTMLResponse)
def read_root(user: models.User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/hub")
    return read_html("login.html")


@app.get("/hub", response_class=HTMLResponse)
def read_hub(user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/")
    return read_html("index.html")


@app.get("/admin", response_class=HTMLResponse)
def read_admin(user: models.User = Depends(get_current_user)):
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    return read_html("admin.html")


ROOM_FILES = {i: f"room{i}.html" for i in range(1, 10)}


@app.get("/room/{room_id}", response_class=HTMLResponse)
def read_room(room_id: int, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/")
    filename = ROOM_FILES.get(room_id)
    if filename and (BASE_DIR / filename).is_file():
        return read_html(filename)
    # Room page doesn't exist (yet): back to the hub
    return RedirectResponse(url="/hub")


@app.get("/scoreboard", response_class=HTMLResponse)
def read_scoreboard():
    return read_html("scoreboard.html")


@app.get("/room-common.js")
def room_common_js():
    path = BASE_DIR / "room-common.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})


# Only the evidence files are served, and only to logged-in players. The
# Challenges/*/README.md files contain the answer keys and must never be public.
EVIDENCE_PATH_RE = re.compile(r"^(Room - [1-9])/evidence/.+$")


@app.get("/challenges/{asset_path:path}")
def serve_evidence(asset_path: str, user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    m = EVIDENCE_PATH_RE.match(asset_path)
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    evidence_root = (CHALLENGES_DIR / m.group(1) / "evidence").resolve()
    target = (CHALLENGES_DIR / asset_path).resolve()
    try:
        target.relative_to(evidence_root)  # blocks ../ traversal out of evidence/
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(target, headers={"Cache-Control": "private, max-age=300"})


# ─── Auth API ──────────────────────────────────────────────────

def deliver_verification_code(email: str, code: str) -> str:
    """Send via SMTP when SMTP_HOST is configured; otherwise log to the console
    (dev mode). Returns the delivery channel: 'email' or 'console'."""
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        print(f"\n[MOCK EMAIL] Verification code for {email} is: {code}\n")
        return "console"

    port = int(os.getenv("SMTP_PORT", "587") or 587)
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or smtp_user

    msg = EmailMessage()
    msg["Subject"] = "Your MERAZ NIGHTJAR verification code"
    msg["From"] = sender
    msg["To"] = email
    msg.set_content(
        f"Your verification code is: {code}\n\n"
        f"It expires in {CODE_TTL_MINUTES} minutes. If you didn't request it, ignore this email."
    )
    try:
        ctx = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15, context=ctx) as s:
                if smtp_user:
                    s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as s:
                s.starttls(context=ctx)
                if smtp_user:
                    s.login(smtp_user, smtp_pass)
                s.send_message(msg)
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Could not send verification email: {e}")
        raise HTTPException(status_code=502, detail="Could not send the verification email. Try again shortly.")
    return "email"


@app.post("/api/send-code")
def send_verification_code(email: str = Form(...), db: Session = Depends(database.get_db)):
    email = normalize_email(email)

    if db.query(models.User).filter(func.lower(models.User.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    now = utcnow()
    vc = db.query(models.VerificationCode).filter(func.lower(models.VerificationCode.email) == email).first()
    if vc and vc.expires_at:
        issued_at = vc.expires_at - datetime.timedelta(minutes=CODE_TTL_MINUTES)
        if (now - issued_at).total_seconds() < CODE_RESEND_SECONDS:
            raise HTTPException(status_code=429, detail="Please wait a few seconds before requesting another code")

    code = "".join(secrets.choice(string.digits) for _ in range(6))
    expire = now + datetime.timedelta(minutes=CODE_TTL_MINUTES)
    if vc:
        vc.email = email
        vc.code = code
        vc.expires_at = expire
    else:
        db.add(models.VerificationCode(email=email, code=code, expires_at=expire))
    db.commit()

    channel = deliver_verification_code(email, code)
    return {"message": "Verification code sent to email", "delivery": channel}


@app.post("/api/register")
def register(
    request: Request,
    response: Response,
    action: str = Form(...),
    email: str = Form(...),
    verification_code: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    team_name: Optional[str] = Form(None),
    invite_code: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
):
    email = normalize_email(email)
    username = clean_username(username)
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LEN} characters")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password is too long")

    vc = db.query(models.VerificationCode).filter(func.lower(models.VerificationCode.email) == email).first()
    if (
        not vc
        or not secrets.compare_digest(vc.code or "", (verification_code or "").strip())
        or vc.expires_at < utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(models.User).filter(func.lower(models.User.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Team + user are created in ONE transaction so a failure can't leave an
    # orphaned team behind.
    try:
        if action == "create_team":
            team_name = clean_team_name(team_name)
            if db.query(models.Team).filter(models.Team.name == team_name).first():
                raise HTTPException(status_code=400, detail="Team name already taken")
            team = models.Team(name=team_name, invite_code=new_invite_code())
            db.add(team)
            db.flush()
        elif action == "join_team":
            code = (invite_code or "").strip().upper()
            if not code:
                raise HTTPException(status_code=400, detail="Invite code required to join team")
            team = (
                db.query(models.Team)
                .filter(models.Team.invite_code == code)
                .with_for_update()
                .first()
            )
            if not team:
                raise HTTPException(status_code=400, detail="Invalid invite code")
            if db.query(models.User).filter(models.User.team_id == team.id).count() >= MAX_TEAM_SIZE:
                raise HTTPException(status_code=400, detail=f"Team is full (max {MAX_TEAM_SIZE} members)")
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        user = models.User(
            username=username,
            email=email,
            is_email_verified=True,
            hashed_password=pwd_context.hash(password),
            team_id=team.id,
        )
        db.add(user)
        db.flush()
        if action == "create_team":
            team.leader_id = user.id
        db.delete(vc)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username, email or team name already taken")

    issue_session(response, request, username)
    return {"message": "Registered successfully"}


def verify_google_id_token(token: str):
    """Verify a Google ID token via Google's tokeninfo endpoint. The token MUST
    have been issued for THIS app's client id (GOOGLE_CLIENT_ID), otherwise a
    token minted for any other Google app could be replayed here."""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not google_client_id:
        return None
    try:
        url = "https://oauth2.googleapis.com/tokeninfo?id_token=" + urllib.parse.quote(token, safe="")
        req = urllib.request.Request(url, headers={"User-Agent": "SPECTRE-FastAPI"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            return None
        if data.get("aud") != google_client_id:
            return None
        if str(data.get("email_verified")).lower() not in ["true", "1"]:
            return None
        return data
    except Exception as e:  # noqa: BLE001
        print(f"Error validating Google token: {e}")
        return None


@app.get("/api/auth/config")
def get_auth_config():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip()}


@app.post("/api/auth/google")
def google_auth(
    request: Request,
    response: Response,
    id_token: str = Form(...),
    username: Optional[str] = Form(None),
    action: Optional[str] = Form(None),
    team_name: Optional[str] = Form(None),
    invite_code: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
):
    if not os.getenv("GOOGLE_CLIENT_ID", "").strip():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on this server")

    payload = verify_google_id_token(id_token)
    if not payload or not payload.get("email"):
        raise HTTPException(status_code=400, detail="Invalid or unverified Google token")

    email = payload.get("email").strip().lower()

    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if user:
        issue_session(response, request, user.username)
        return {"status": "authenticated", "message": "Login successful", "is_admin": user.is_admin}

    # New user: ask the client for profile details first
    if not username or not action:
        raw_name = payload.get("given_name") or payload.get("name") or email.split("@")[0]
        suggested = re.sub(r"[^a-zA-Z0-9_]", "", raw_name)[:15]
        return {
            "status": "needs_profile",
            "email": email,
            "suggested_username": suggested,
            "name": payload.get("name", ""),
        }

    username = clean_username(username)
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered. Please choose another.")

    try:
        if action == "create_team":
            team_name = clean_team_name(team_name)
            if db.query(models.Team).filter(models.Team.name == team_name).first():
                raise HTTPException(status_code=400, detail="Team name already taken")
            team = models.Team(name=team_name, invite_code=new_invite_code())
            db.add(team)
            db.flush()
        elif action == "join_team":
            code = (invite_code or "").strip().upper()
            if not code:
                raise HTTPException(status_code=400, detail="Invite code is required to join a team")
            team = (
                db.query(models.Team)
                .filter(models.Team.invite_code == code)
                .with_for_update()
                .first()
            )
            if not team:
                raise HTTPException(status_code=400, detail="Invalid team invite code")
            if db.query(models.User).filter(models.User.team_id == team.id).count() >= MAX_TEAM_SIZE:
                raise HTTPException(status_code=400, detail=f"Team is full (maximum {MAX_TEAM_SIZE} members)")
        else:
            raise HTTPException(status_code=400, detail="Invalid team action")

        new_user = models.User(
            username=username,
            email=email,
            is_email_verified=True,
            hashed_password=None,
            team_id=team.id,
            is_admin=False,
        )
        db.add(new_user)
        db.flush()
        if action == "create_team":
            team.leader_id = new_user.id
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username, email or team name already taken")

    issue_session(response, request, username)
    return {"status": "authenticated", "message": "Registered and logged in"}


@app.post("/api/login")
def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db),
):
    username = username.strip()
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.hashed_password or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password. (If registered via Google, please sign in with Google.)",
        )
    issue_session(response, request, user.username)
    return {"message": "Login successful", "is_admin": user.is_admin}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "Logged out"}


# ─── Game API ──────────────────────────────────────────────────

POINTS_PER_FLAG = 25

# One entry per challenge (4 per room, in README order). Each challenge lists
# every accepted answer; the FIRST one is canonical (what gets stored). A
# challenge can only be scored once per team no matter which variant is used.
# Variants beyond the first are the answers the in-room UI / evidence actually
# produce (they differ from the READMEs for 1.1, 2.2 and 2.4).
CHALLENGE_FLAGS = {
    1: [
        ["NIGHTJAR{aether_07_nothing_stays_local}", "NIGHTJAR{aether_07}"],
        ["NIGHTJAR{parallax_systems_aman_v}"],
        ["NIGHTJAR{nexus-meraz.festival.in.net}"],
        ["NIGHTJAR{curator_404}"],
    ],
    2: [
        ["NIGHTJAR{the_host_with_the_blue_name_is_lying}"],
        ["NIGHTJAR{blue_name_is_host_alias_not_a_person}", "NIGHTJAR{hello_world.txt}"],
        ["NIGHTJAR{ask_the_person_who_never_signs_in}"],
        ["NIGHTJAR{aether_7_relay_compromised}", "NIGHTJAR{aether-7}"],
    ],
    3: [
        ["NIGHTJAR{10.7.7.43_to_203.0.113.77_port_8443}"],
        ["NIGHTJAR{maint_window_0200_user_kite_backup}"],
        ["NIGHTJAR{restore_aether_core_confirmed}"],
        ["NIGHTJAR{port_4477_mira_7_propagation_service}"],
    ],
    4: [
        ["NIGHTJAR{nexus_health_monitor_pid_2847_opt_mira}"],
        ["NIGHTJAR{kite_backup_session_via_auth_token_0137}"],
        ["NIGHTJAR{suid_aether_restart_owned_by_root_writable_by_nexus}"],
        ["NIGHTJAR{ed25519_kite_backup_2019_added_oct_2026_aetherforge}"],
    ],
    5: [
        ["NIGHTJAR{idor_volunteer_0x7F_infra_access_no_orientation}"],
        ["NIGHTJAR{jwt_role_volunteer_plus_admin_cert_renewal}"],
        ["NIGHTJAR{cmd_injection_mira_config_at_etc_nexus_mira_conf}"],
        ["NIGHTJAR{maint_nexus_portal_certrenew_api_v1_renew}"],
    ],
    6: [
        ["NIGHTJAR{ghost_record_vol_127_nexus_svc_auto_insert_no_sponsor}"],
        ["NIGHTJAR{continuity_delegate_role_read_all_plus_cert_trust_store}"],
        ["NIGHTJAR{badge_0x7F_infra_dual_scan_main_stage_server_b3_61s}"],
        ["NIGHTJAR{trust_chain_aether_core_to_release_controller_full_trust}"],
    ],
    7: [
        ["NIGHTJAR{phish_kabir_sep27_nexus_support_spoofed_real_ticket_ref}"],
        ["NIGHTJAR{impossible_travel_kabir_amsterdam_0135_stolen_session_token}"],
        ["NIGHTJAR{mfa_fatigue_14_pushes_auto_approve_30s_timeout_gateway}"],
        ["NIGHTJAR{persona_kite_backup_simulated_insider_from_stolen_creds}"],
    ],
    8: [
        ["NIGHTJAR{pe_header_mismatch_fake_sig_section_rwx_not_nexus_registry}"],
        ["NIGHTJAR{c2_parallax_sys_net_xor_key_0x4d_beacon_300s_nothing_stays_local}"],
        ["NIGHTJAR{mira_propagate_dormant_nexus_zone_core_aether7_activated}"],
        ["NIGHTJAR{mira7_built_oct3_auto_aether_forge_not_curator_manual}"],
    ],
    9: [
        ["NIGHTJAR{timeline_staging_sep28_nexus_sync_precheck_clock_skew}"],
        ["NIGHTJAR{gap_420s_auditd_buffer_flush_ipmi_bmc_continuity_uid0}"],
        ["NIGHTJAR{path_kite_to_maint_to_continuity_to_aether7_master_relay}"],
        ["NIGHTJAR{rca_cr0919_autofailover_human_gate_disabled_latency_spike}"],
    ],
}
FLAGS_PER_ROOM = 4
MAX_ROOM = 11  # a team that clears room 10 sits at "room 11" (finished)

# room -> {lowercased accepted flag -> challenge index}. Matching is
# case-insensitive (the in-room UIs always were) and ignores surrounding spaces.
_FLAG_INDEX = {
    room: {flag.lower(): idx for idx, variants in enumerate(challenges) for flag in variants}
    for room, challenges in CHALLENGE_FLAGS.items()
}


def match_flag(room_id: int, flag: str) -> Optional[int]:
    return _FLAG_INDEX.get(room_id, {}).get((flag or "").strip().lower())


def solved_challenges(db: Session, team_id: int, room_id: Optional[int] = None) -> dict:
    """{room_id: set(challenge indexes, 0-based)} for a team's correct submissions."""
    q = db.query(models.FlagSubmission.room_id, models.FlagSubmission.flag_value).filter(
        models.FlagSubmission.team_id == team_id,
        models.FlagSubmission.is_correct == True,  # noqa: E712
    )
    if room_id is not None:
        q = q.filter(models.FlagSubmission.room_id == room_id)
    result: dict = {}
    for rid, value in q.all():
        idx = match_flag(rid, value)
        if idx is not None:
            result.setdefault(rid, set()).add(idx)
    return result


@app.post("/api/submit_flag")
def submit_flag(
    room_id: int = Form(...),
    flag: str = Form(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if room_id not in CHALLENGE_FLAGS:
        raise HTTPException(status_code=400, detail="Unknown room")
    if not user.team_id:
        raise HTTPException(status_code=400, detail="You must belong to a team to submit flags")

    flag = (flag or "").strip()[:300]

    # Lock the team row so two teammates submitting at once can't double-score.
    team = db.query(models.Team).filter(models.Team.id == user.team_id).with_for_update().first()
    if not team:
        raise HTTPException(status_code=400, detail="Team not found")

    idx = match_flag(room_id, flag)
    if idx is None:
        db.add(models.FlagSubmission(team_id=team.id, room_id=room_id, is_correct=False, flag_value=flag))
        db.commit()
        return {"success": False, "message": "Incorrect flag. Try again."}

    solved = solved_challenges(db, team.id, room_id).get(room_id, set())
    if idx in solved:
        return {
            "success": True,
            "message": "Already submitted! Flag was correct.",
            "challenge": idx + 1,
            "solved": sorted(i + 1 for i in solved),
        }

    db.add(models.FlagSubmission(
        team_id=team.id, room_id=room_id, is_correct=True, flag_value=CHALLENGE_FLAGS[room_id][idx][0]
    ))
    team.score = (team.score or 0) + POINTS_PER_FLAG
    solved = solved | {idx}
    if len(solved) >= FLAGS_PER_ROOM and (team.current_room or 1) <= room_id:
        team.current_room = room_id + 1
    db.commit()
    return {
        "success": True,
        "message": "Correct! Flag accepted.",
        "challenge": idx + 1,
        "solved": sorted(i + 1 for i in solved),
    }


@app.get("/api/progress")
def get_progress(user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """The caller's TEAM progress: which challenges are solved in each room."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    rooms = {str(r): [] for r in CHALLENGE_FLAGS}
    score, current_room = 0, 1
    if user.team_id:
        team = db.query(models.Team).filter(models.Team.id == user.team_id).first()
        if team:
            score, current_room = team.score or 0, team.current_room or 1
            for rid, idxs in solved_challenges(db, team.id).items():
                rooms[str(rid)] = sorted(i + 1 for i in idxs)
    return {"score": score, "current_room": current_room, "rooms": rooms}


@app.get("/api/me")
def get_me(user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    is_leader = bool(user.team and user.team.leader_id == user.id)
    return {
        "username": user.username,
        "is_admin": user.is_admin,
        "team": user.team.name if user.team else None,
        "invite_code": user.team.invite_code if is_leader else None,
        "is_leader": is_leader,
    }


# ─── Scoreboard API (public) ──────────────────────────────────

@app.get("/api/scoreboard")
def get_scoreboard(db: Session = Depends(database.get_db)):
    teams = (
        db.query(models.Team)
        .options(selectinload(models.Team.users))
        .order_by(models.Team.score.desc(), models.Team.created_at.asc())
        .all()
    )
    return [
        {
            "id": t.id,
            "name": t.name,
            "score": t.score,
            "current_room": t.current_room,
            "members": len(t.users),
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in teams
    ]


# ─── Admin API (protected) ────────────────────────────────────

@app.get("/api/admin/teams")
def admin_get_teams(admin: models.User = Depends(require_admin), db: Session = Depends(database.get_db)):
    teams = (
        db.query(models.Team)
        .options(selectinload(models.Team.users))
        .order_by(models.Team.created_at.asc())
        .all()
    )
    counts = {
        team_id: (total, correct or 0)
        for team_id, total, correct in db.query(
            models.FlagSubmission.team_id,
            func.count(models.FlagSubmission.id),
            func.sum(case((models.FlagSubmission.is_correct == True, 1), else_=0)),  # noqa: E712
        ).group_by(models.FlagSubmission.team_id).all()
    }
    result = []
    for t in teams:
        total, correct = counts.get(t.id, (0, 0))
        result.append({
            "id": t.id,
            "name": t.name,
            "score": t.score,
            "current_room": t.current_room,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "members": [{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in t.users],
            "total_submissions": total,
            "correct_submissions": int(correct),
        })
    return result


@app.put("/api/admin/teams/{team_id}/score")
def admin_update_score(
    team_id: int,
    score: int = Body(..., embed=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    if score < 0 or score > 1_000_000:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 1,000,000")
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.score = score
    db.commit()
    return {"message": f"Score updated to {score}", "team": team.name}


@app.put("/api/admin/teams/{team_id}/room")
def admin_update_room(
    team_id: int,
    room: int = Body(..., embed=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    if room < 1 or room > MAX_ROOM:
        raise HTTPException(status_code=400, detail=f"Room must be between 1 and {MAX_ROOM}")
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.current_room = room
    db.commit()
    return {"message": f"Room updated to {room}", "team": team.name}


@app.delete("/api/admin/teams/{team_id}")
def admin_delete_team(
    team_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if admin.team_id == team.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own team")
    name = team.name  # read before the row is deleted
    db.query(models.FlagSubmission).filter(models.FlagSubmission.team_id == team_id).delete()
    db.query(models.User).filter(models.User.team_id == team_id).delete()
    db.delete(team)
    db.commit()
    return {"message": f"Team '{name}' deleted"}


@app.put("/api/admin/users/{user_id}/toggle-admin")
def admin_toggle_admin(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
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
def admin_delete_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    username = user.username
    # If the removed user led a team, hand leadership to another member so the
    # team isn't left with a dangling leader id (and no invite code visible).
    if user.team_id:
        team = db.query(models.Team).filter(models.Team.id == user.team_id).first()
        if team and team.leader_id == user.id:
            successor = (
                db.query(models.User)
                .filter(models.User.team_id == team.id, models.User.id != user.id)
                .order_by(models.User.id.asc())
                .first()
            )
            team.leader_id = successor.id if successor else None
    db.delete(user)
    db.commit()
    return {"message": f"User '{username}' deleted"}


@app.post("/api/admin/reset-scores")
def admin_reset_scores(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    db.query(models.Team).update({models.Team.score: 0, models.Team.current_room: 1})
    db.query(models.FlagSubmission).delete()
    db.commit()
    return {"message": "All scores and progress reset"}


@app.get("/api/admin/stats")
def admin_stats(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    top_team = db.query(models.Team).order_by(models.Team.score.desc()).first()
    return {
        "total_teams": db.query(models.Team).count(),
        "total_users": db.query(models.User).count(),
        "total_submissions": db.query(models.FlagSubmission).count(),
        "correct_submissions": db.query(models.FlagSubmission)
        .filter(models.FlagSubmission.is_correct == True)  # noqa: E712
        .count(),
        "top_team": {"name": top_team.name, "score": top_team.score} if top_team else None,
    }
