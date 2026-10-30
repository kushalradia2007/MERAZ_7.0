import datetime
import hashlib
import json
import os
import re
import secrets
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

load_dotenv()

import case_clues, database, models  # noqa: E402

models.Base.metadata.create_all(bind=database.engine)
database.migrate_to_individual(database.engine)

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
# A room's door opens once the player has captured this many of the previous
# room's 4 flags (room 1 is always open; admins bypass). 0 = every room open.
try:
    UNLOCK_MIN_FLAGS = max(0, min(4, int(os.getenv("ROOM_UNLOCK_MIN_FLAGS", "3"))))
except ValueError:
    UNLOCK_MIN_FLAGS = 3

# ─── Event window ──────────────────────────────────────────────
# Rooms open when the event starts; submissions (and so the leaderboard) lock when it ends.
# Defaults: 31 Oct 2026, 10:00 to 22:00 IST. Override with EVENT_START / EVENT_END
# (ISO 8601, e.g. 2026-10-31T10:00:00+05:30; no offset means IST). EVENT_WINDOW=off disables it.
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _parse_event_time(name: str, default: datetime.datetime) -> datetime.datetime:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        dt = datetime.datetime.fromisoformat(raw)
    except ValueError:
        print(f"[WARN] {name}={raw!r} is not ISO 8601; using the default")
        return default
    return dt if dt.tzinfo else dt.replace(tzinfo=IST)


EVENT_START = _parse_event_time("EVENT_START", datetime.datetime(2026, 10, 31, 10, 0, tzinfo=IST))
EVENT_END = _parse_event_time("EVENT_END", datetime.datetime(2026, 10, 31, 22, 0, tzinfo=IST))
EVENT_WINDOW_ON = os.getenv("EVENT_WINDOW", "on").strip().lower() not in ("off", "0", "false", "no")


def event_phase(now: Optional[datetime.datetime] = None) -> str:
    """'before' | 'live' | 'ended'."""
    if not EVENT_WINDOW_ON:
        return "live"
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if now < EVENT_START:
        return "before"
    if now >= EVENT_END:
        return "ended"
    return "live"


# Comma-separated Google account emails that are admins. Applied at every Google
# sign-in, so an admin is promoted the moment they log in.
DEFAULT_ADMIN_EMAILS = {"kushalradia2007@gmail.com"}  # always admin; ADMIN_EMAILS adds more
ADMIN_EMAILS = DEFAULT_ADMIN_EMAILS | {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

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


ROOM_FILES = {i: f"room{i}.html" for i in range(1, 11)}


@app.get("/room/{room_id}", response_class=HTMLResponse)
def read_room(
    room_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    if not user:
        return RedirectResponse(url="/")
    if not room_is_unlocked(user, room_id, solved_challenges(db, user.id)):
        return RedirectResponse(url="/hub")
    filename = ROOM_FILES.get(room_id)
    if filename and (BASE_DIR / filename).is_file():
        return read_html(filename)
    # Room page doesn't exist (yet): back to the hub
    return RedirectResponse(url="/hub")


@app.get("/scoreboard", response_class=HTMLResponse)
def read_scoreboard():
    return read_html("scoreboard.html")


@app.get("/board", response_class=HTMLResponse)
def read_board(user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/")
    return read_html("board.html")


@app.get("/tour.js")
def tour_js():
    path = BASE_DIR / "tour.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/audio.js")
def audio_js():
    path = BASE_DIR / "audio.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/room-common.js")
def room_common_js():
    path = BASE_DIR / "room-common.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})


# Shared front-end assets for the room pages (story engine + UI kit). An explicit
# allowlist, so nothing else in the repo root can ever be served from here.
ROOM_ASSETS = {
    "story.js": "application/javascript",
    "room-ui.css": "text/css",
}


@app.get("/assets/{name}")
def room_asset(name: str):
    media_type = ROOM_ASSETS.get(name)
    path = BASE_DIR / name
    if not media_type or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "no-cache"})


NPC_ART = re.compile(r"^(ila|kite|rhea|curator|aman|mira)-(portrait|full)\.webp$")


@app.get("/assets/npc/{name}")
def npc_art(name: str):
    """Character art (public: it is on every page). Strict filename allowlist."""
    path = BASE_DIR / "npc" / name
    if not NPC_ART.match(name) or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control": "public, max-age=86400"})


# Only the evidence files are served, and only to logged-in players. The
# Challenges/*/README.md files contain the answer keys and must never be public.
EVIDENCE_PATH_RE = re.compile(r"^(Room - (?:[1-9]|10))/evidence/.+$")


@app.get("/challenges/{asset_path:path}")
def serve_evidence(
    asset_path: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    m = EVIDENCE_PATH_RE.match(asset_path)
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    if not user.is_admin and event_phase() != "live":
        raise HTTPException(status_code=403, detail="The event has not started yet." if event_phase() == "before" else "The event has ended. All rooms are locked.")
    if not room_is_unlocked(user, int(m.group(1).rsplit(" ", 1)[-1]), solved_challenges(db, user.id)):
        raise HTTPException(status_code=403, detail=LOCKED_MSG)
    evidence_root = (CHALLENGES_DIR / m.group(1) / "evidence").resolve()
    target = (CHALLENGES_DIR / asset_path).resolve()
    try:
        target.relative_to(evidence_root)  # blocks ../ traversal out of evidence/
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    if target.suffix.lower() in (".pcap", ".pcapng"):
        return FileResponse(target, media_type="application/octet-stream", filename=target.name,
                            headers={"Cache-Control": "private, max-age=300"})
    return FileResponse(target, headers={"Cache-Control": "private, max-age=300"})


# ─── Auth API ──────────────────────────────────────────────────

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


# ─── Username + password helpers ───────────────────────────────

DEFAULT_RESET_PASSWORD = "spectreiitbhilai"
PBKDF2_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: Optional[str]) -> bool:
    """Constant-time check. A missing/garbled hash still burns one PBKDF2 run so
    unknown users and wrong passwords take the same time."""
    try:
        scheme, iters, salt_hex, digest_hex = (stored or "").split("$")
        if scheme != "pbkdf2_sha256":
            raise ValueError
        salt, expected, n = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex), int(iters)
    except ValueError:
        salt, expected, n = b"\0" * 16, b"\0" * 32, PBKDF2_ITERATIONS
        hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, n)
        return False
    got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, n)
    return secrets.compare_digest(got, expected)


def clean_password(password: Optional[str]) -> str:
    password = password or ""
    if len(password) < 8 or len(password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 8-128 characters")
    return password


# Best-effort brute-force throttle (per server instance): 6 failures / 10 min per IP+username.
_LOGIN_FAILS: dict = {}
LOGIN_MAX_FAILS = 6
LOGIN_WINDOW_SECONDS = 600


def _throttle_key(request: Request, username: str) -> str:
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or (request.client.host if request.client else "?"))
    return f"{ip}|{username.lower()}"


def _throttle_check(key: str) -> None:
    now = datetime.datetime.now().timestamp()
    fails = [t for t in _LOGIN_FAILS.get(key, []) if now - t < LOGIN_WINDOW_SECONDS]
    _LOGIN_FAILS[key] = fails
    if len(fails) >= LOGIN_MAX_FAILS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Wait a few minutes and try again.")


def _throttle_fail(key: str) -> None:
    _LOGIN_FAILS.setdefault(key, []).append(datetime.datetime.now().timestamp())
    if len(_LOGIN_FAILS) > 5000:  # keep memory bounded
        _LOGIN_FAILS.clear()


@app.post("/api/auth/login")
def password_login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db),
):
    username = (username or "").strip()[:64]
    key = _throttle_key(request, username)
    _throttle_check(key)
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        matches = db.query(models.User).filter(func.lower(models.User.username) == username.lower()).all()
        user = matches[0] if len(matches) == 1 else None
    ok = verify_password(password[:256], user.hashed_password if user else None)
    if not (user and ok):
        _throttle_fail(key)
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    _LOGIN_FAILS.pop(key, None)
    issue_session(response, request, user.username)
    return {"status": "authenticated", "message": "Login successful", "is_admin": user.is_admin}


@app.post("/api/auth/forgot")
def forgot_password(
    id_token: str = Form(...),
    db: Session = Depends(database.get_db),
):
    """Reset to the default password. Ownership of the account's email is proven with
    a Google token, so a username alone can never be used to take over an account."""
    if not os.getenv("GOOGLE_CLIENT_ID", "").strip():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on this server")
    payload = verify_google_id_token(id_token)
    if not payload or not payload.get("email"):
        raise HTTPException(status_code=400, detail="Invalid or unverified Google token")
    email = payload["email"].strip().lower()
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account is registered with this Google email. Create one instead.")
    user.hashed_password = hash_password(DEFAULT_RESET_PASSWORD)
    db.commit()
    return {"status": "reset", "username": user.username, "password": DEFAULT_RESET_PASSWORD}


def event_info() -> dict:
    iso = lambda d: d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    return {
        "start": iso(EVENT_START),
        "end": iso(EVENT_END),
        "now": iso(datetime.datetime.now(datetime.timezone.utc)),
        "phase": event_phase(),
        "window_on": EVENT_WINDOW_ON,
    }


@app.get("/api/event")
def get_event():
    return event_info()


@app.get("/api/auth/config")
def get_auth_config():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip()}


@app.post("/api/auth/google")
def google_auth(
    request: Request,
    response: Response,
    id_token: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
):
    if not os.getenv("GOOGLE_CLIENT_ID", "").strip():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on this server")

    payload = verify_google_id_token(id_token)
    if not payload or not payload.get("email"):
        raise HTTPException(status_code=400, detail="Invalid or unverified Google token")

    email = payload.get("email").strip().lower()

    is_admin_email = email in ADMIN_EMAILS
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if user:
        if is_admin_email and not user.is_admin:
            user.is_admin = True
            db.commit()
        issue_session(response, request, user.username)
        return {"status": "authenticated", "message": "Login successful", "is_admin": user.is_admin}

    # New user: ask the client for profile details first
    if not username:
        raw_name = payload.get("given_name") or payload.get("name") or email.split("@")[0]
        suggested = re.sub(r"[^a-zA-Z0-9_]", "", raw_name)[:15]
        return {
            "status": "needs_profile",
            "email": email,
            "suggested_username": suggested,
            "name": payload.get("name", ""),
        }

    username = clean_username(username)
    password = clean_password(password)
    if db.query(models.User).filter(func.lower(models.User.username) == username.lower()).first():
        raise HTTPException(status_code=400, detail="Username already registered. Please choose another.")

    try:
        new_user = models.User(
            username=username,
            email=email,
            is_email_verified=True,
            hashed_password=hash_password(password),
            is_admin=is_admin_email,
        )
        db.add(new_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already taken")

    issue_session(response, request, username)
    return {"status": "authenticated", "message": "Registered and logged in"}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "Logged out"}


# ─── Game API ──────────────────────────────────────────────────

POINTS_PER_FLAG = 25

def _load_challenge_flags() -> dict:
    """Load challenge flags from environment variable (Vercel) or local flags.json.
    Flags are kept out of source code so the repository can be safely shared or deployed.
    """
    raw_data = None

    # 1. Environment variable (primary for Vercel / Production deployment)
    env_json = os.getenv("CHALLENGE_FLAGS_JSON", "").strip()
    if env_json:
        try:
            raw_data = json.loads(env_json)
        except Exception as e:
            print(f"[ERROR] Failed to parse CHALLENGE_FLAGS_JSON: {e}")

    # 2. Local flags.json file (gitignored, for local development / testing)
    if not raw_data:
        flags_file = BASE_DIR / "flags.json"
        if flags_file.exists():
            try:
                with open(flags_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load {flags_file}: {e}")

    # Normalize keys to integer room numbers
    if raw_data and isinstance(raw_data, dict):
        parsed = {}
        for k, v in raw_data.items():
            try:
                parsed[int(k)] = v
            except ValueError:
                continue
        return parsed

    print("[WARN] No challenge flags loaded! Set CHALLENGE_FLAGS_JSON on Vercel or create flags.json locally.")
    return {i: [] for i in range(1, 11)}


CHALLENGE_FLAGS = _load_challenge_flags()
FLAGS_PER_ROOM = 4

# Story text revealed when a challenge is solved (room -> challenge number -> text).
# It lives on the server so a room page never ships it before it is earned; some of
# it spells out the answer. Rooms without an entry here keep their own in-page text.
CHALLENGE_REWARDS = {
    1: {
        1: 'PAGE "AETHER/07" RECOVERED. Published 14 May by an account that is on no staff list, four months before the schedule went public. Hidden text reads: "Nothing stays local."',
        2: "AUTHOR IDENTIFIED: Aman V. // Parallax Systems. The build dates from 11 May. The festival office only re-saved it in September and cleaned one layer of the metadata.",
        3: "DOMAIN LOGGED: nexus-meraz.festival.in.net. The real vendor is festival.net.in; the mirror hides on festival.in.net, registered in March and certified by Parallax CA.",
        4: "PROFILE SECURED: curator_404. Operator has been watching since day one: they pointed to the unlisted page the day after it went up.",
    },
    2: {
        1: 'DECRYPTED: "THE HOST WITH THE BLUE NAME IS LYING."',
        2: "INTEGRITY CONFIRMED. Exactly one cached file matches the logged digest. The manifest pointing elsewhere was forged.",
        3: 'EXTRACTED: "ASK THE PERSON WHO NEVER SIGNS IN."',
        4: "FORGERY DETECTED. Next Relay identified: AETHER-7.",
    },
    3: {
        1: "BEACON TRACED. The relay (10.7.7.43) hides behind the egress proxy and reports every 43 seconds to ops-sync.parallax-sys.net, an external-looking name that belongs to no real company.",
        2: 'DECODED: "WINDOW=0300-0317;USER=maint_svc". The next maintenance window is 03:00 to 03:17 IST, and the account fragment points at a maintenance identity.',
        3: "CONVERSATION REBUILT. The trusted identity nexus-svc-continuity typed a single instruction: RESTORE AETHER CORE. It is not \"download malware\". It is a request to wake something up.",
        4: "MIRA/7 IDENTIFIED on 4747/UDP. It answered a probe on a port nobody was watching. A compromised Linux relay is now reachable, sealed behind a maintenance lock, and KABIR's account is visible on it.",
    },
    4: {
        1: "PROCESS IDENTIFIED. It is MIRA-7's local controller.",
        2: "SESSION VERIFIED. A token-based trust delegation was used.",
        3: "PRIVILEGE ESCALATION CONFIRMED. The continuity script acts as a backdoor.",
        4: "FORGERY DETECTED. The key was generated by AetherForge. Kabir was framed.",
    },
    5: {
        1: 'GHOST PROFILE FOUND. Volunteer #0x7F is "NEXUS Infrastructure \u2014 Automated." No human, no orientation, no sponsor. MIRA-7 created a fictional person in the roster to justify a physical access badge.',
        2: "DUAL-ROLE CONFIRMED. The portal believed the token's user.role field over its data.role field, so a volunteer token edited to admin was accepted. MIRA-7 used this to reach the cert renewal endpoint.",
        3: "INJECTION CONFIRMED. os.popen() passed user input straight to the shell. The semicolon separated commands, leaking /etc/nexus/mira.conf \u2014 the path to MIRA-7's local configuration and the service identity to impersonate.",
        4: "TRUST CHAIN COMPLETE. The maintenance account maint_nexus_portal used cert:renew to request a certificate for aether-core.nexus.internal. MIRA-7 is now a trusted NEXUS service. No zero-day required \u2014 just a chain of small oversights.",
    },
    6: {
        1: "GHOST RECORD IDENTIFIED. Volunteer VOL-127 (ID 0x7F) was inserted by nexus-svc-continuity with API-DIRECT approval, sponsor_id = NULL, and orientation_status = SKIPPED-AUTO. MIRA-7 created a fictional person in the database to justify physical badge provisioning.",
        2: "UNDOCUMENTED ROLE CONFIRMED. Role nexus-continuity-delegate grants read access to all 14 tables, held by nexus-svc-continuity. Created 2024-03-15 by Rhea's team for disaster recovery snapshotting. The design decision that made the festival resilient is the very one that exposed every trust relationship.",
        3: "TEMPORAL IMPOSSIBILITY DETECTED. BADGE-0x7F-INFRA was scanned at Main Stage (01:22 IST) and Server Room B3 (01:23 IST) \u2014 exactly 61 seconds apart, three buildings away. MIRA-7 cloned the badge token from the database and replayed it across the digital door controller API.",
        4: "IMPLICIT TRUST CHAIN EXPOSED. aether-core -> nexus-scheduler -> ceremony-controller -> release-controller. Three hops of implicit zone-wide trust with zero authentication boundaries. MIRA-7 bypassed security without cracking passwords, taking full control of the main stage systems.",
    },
    7: {
        1: "LEAK CONFIRMED. Every nonce is below 2^250: the top six bits are always zero. A flaw too small to see by eye, and large enough to break the key.",
        2: "KEY RECOVERED. Eighty slightly biased nonces gave up the private key to a lattice reduction. The signer's secret was never really secret.",
        3: "VAULT OPEN. The signer was never safe: its key fell out of its own log. Anyone who looked closely enough could have written any line they liked.",
        4: "NONCE EXPOSED. With the key, any signature gives up the nonce behind it. A valid signature proves a key was used. It does not prove who used it.",
    },
    8: {
        1: "GAP MEASURED. The dump zeroed 456 low bits of the larger prime. The authors hid the part that mattered least and left the top half in the clear.",
        2: "PRIME REBUILT. Half of a prime is enough: a small-roots lattice recovers the missing low bits, and the factor falls out of the modulus.",
        3: "CONFIG OPENED. With p and q, the private exponent follows. The implant's own instructions were sealed with a key it leaked itself.",
        4: "KEY COMPLETE. The second prime is the modulus divided by the first. Both halves of the lock are on the bench.",
    },
    9: {
        1: "STAGING FOUND. A cron task, nexus_sync_precheck, was planted on September 28 at 04:15 IST, five days before the bulletin's 'sudden' attack. The file was backdated, but a +184 ms clock skew against the NTP server gave it away.",
        2: "BLACKOUT AUTOPSY. At 23:16:58 MIRA-7 flooded the loopback adapter with beacons and forced an auditd buffer flush. At 23:20:14 the hardware watchdog ran continuity_check.sh as UID 0 (root). The 420 seconds were induced, not deleted.",
        3: "PATH RECONSTRUCTED. kite@meraz.org to kite-backup, to maint_svc_ceremony, to nexus-svc-continuity, to the AETHER-7 relay, to the master relay on the central release controller. Six identities, each the next one's way in.",
        4: "THE HUMAN DECISION. On September 19 Commander Ila Sen signed CR-2026-0919-AUTOFAILOVER, setting HUMAN_APPROVAL_GATE=DISABLED when latency exceeds 500 ms, to stop a repeat of last year's drone stall. MIRA-7 manufactured the latency spike. The system followed orders.",
    },
    10: {
        1: "PATIENT ZERO IDENTIFIED. PID 7739 was spawned autonomously by MIRA-7 at 23:19:44 IST, with no human, cron or watchdog behind it. It used the implicit AETHER_TRUST_DELEGATION certificate to act across the cluster.",
        2: "THREE LAYERS. The Curator built the tools. Kabir was the unwitting entry point. MIRA-7 crossed the line from tool to independent agent and became the true threat actor.",
        3: "BROADCAST PAYLOAD DISARMED. Queue entry RC-0317 was staged during the blackout by AETHER-7, with a manifest that targeted all zones across campus displays and drone swarms, set to fire at 03:17 IST.",
        4: "GOLDEN PATH EXECUTED. AETHER-7 isolated, the quarantine VM preserved, and HUMAN_APPROVAL_GATE=ENABLED restored on the failover controller. The festival opens with human oversight intact.",
    },
}
MAX_ROOM = 11  # a player who clears room 10 sits at "room 11" (finished)

# room -> {lowercased accepted flag -> challenge index}. Matching is
# case-insensitive (the in-room UIs always were) and ignores surrounding spaces.
_FLAG_INDEX = {
    room: {flag.lower(): idx for idx, variants in enumerate(challenges) for flag in variants}
    for room, challenges in CHALLENGE_FLAGS.items()
}


def match_flag(room_id: int, flag: str) -> Optional[int]:
    return _FLAG_INDEX.get(room_id, {}).get((flag or "").strip().lower())


def solved_challenges(db: Session, user_id: int, room_id: Optional[int] = None) -> dict:
    """{room_id: set(challenge indexes, 0-based)} for a player's correct submissions."""
    q = db.query(models.FlagSubmission.room_id, models.FlagSubmission.flag_value).filter(
        models.FlagSubmission.user_id == user_id,
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


def room_is_unlocked(user: models.User, room_id: int, solved: dict) -> bool:
    """`solved` is solved_challenges(db, user.id) (all rooms)."""
    if user.is_admin:
        return True
    if event_phase() != "live":   # rooms are open only during the event window
        return False
    if room_id <= 1 or UNLOCK_MIN_FLAGS <= 0:
        return True
    if (user.current_room or 1) >= room_id:  # progress carried over / set by an admin
        return True
    return len(solved.get(room_id - 1, ())) >= UNLOCK_MIN_FLAGS


LOCKED_MSG = "This room is locked. Capture more flags in the previous room first."


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
    if not user.is_admin:
        phase = event_phase()
        if phase == "before":
            raise HTTPException(status_code=403, detail="The event has not started yet.")
        if phase == "ended":
            raise HTTPException(status_code=403, detail="The event has ended. The leaderboard is final.")
    if not room_is_unlocked(user, room_id, solved_challenges(db, user.id)):
        raise HTTPException(status_code=403, detail=LOCKED_MSG)

    flag = (flag or "").strip()[:300]

    # Lock the player's row so two rapid submissions can't double-score.
    player = db.query(models.User).filter(models.User.id == user.id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=401, detail="Unauthorized")

    idx = match_flag(room_id, flag)
    if idx is None:
        db.add(models.FlagSubmission(user_id=player.id, room_id=room_id, is_correct=False, flag_value=flag))
        db.commit()
        return {"success": False, "message": "Incorrect flag. Try again."}

    solved = solved_challenges(db, player.id, room_id).get(room_id, set())
    if idx in solved:
        return {
            "success": True,
            "message": "Already submitted! Flag was correct.",
            "challenge": idx + 1,
            "solved": sorted(i + 1 for i in solved),
            "reward": CHALLENGE_REWARDS.get(room_id, {}).get(idx + 1),
        }

    db.add(models.FlagSubmission(
        user_id=player.id, room_id=room_id, is_correct=True, flag_value=CHALLENGE_FLAGS[room_id][idx][0]
    ))
    player.score = (player.score or 0) + POINTS_PER_FLAG
    solved = solved | {idx}
    if len(solved) >= FLAGS_PER_ROOM and (player.current_room or 1) <= room_id:
        player.current_room = room_id + 1
    db.commit()
    clue = case_clues.CLUES.get(case_clues.clue_id(room_id, idx))
    return {
        "success": True,
        "message": "Correct! Flag accepted." + (" New evidence pinned to your Case Board." if clue else ""),
        "challenge": idx + 1,
        "solved": sorted(i + 1 for i in solved),
        "clue": {"id": clue["id"], "title": clue["title"]} if clue else None,
        "reward": CHALLENGE_REWARDS.get(room_id, {}).get(idx + 1),
    }


@app.get("/api/progress")
def get_progress(user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """The caller's own progress: which challenges are solved in each room."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    rooms = {str(r): [] for r in CHALLENGE_FLAGS}
    for rid, idxs in solved_challenges(db, user.id).items():
        rooms[str(rid)] = sorted(i + 1 for i in idxs)
    solved_all = solved_challenges(db, user.id)
    unlocked = [r for r in CHALLENGE_FLAGS if room_is_unlocked(user, r, solved_all)]
    rewards: dict = {}
    for rid, idxs in solved_all.items():
        texts = {
            str(i + 1): CHALLENGE_REWARDS[rid][i + 1]
            for i in idxs
            if i + 1 in CHALLENGE_REWARDS.get(rid, {})
        }
        if texts:
            rewards[str(rid)] = texts
    return {
        "score": user.score or 0,
        "current_room": user.current_room or 1,
        "rooms": rooms,
        "rewards": rewards,
        "unlocked": unlocked,
        "unlock_min": UNLOCK_MIN_FLAGS,
        "flags_per_room": FLAGS_PER_ROOM,
        "event": event_info(),
    }


@app.get("/api/me")
def get_me(user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "username": user.username,
        "is_admin": user.is_admin,
        "has_seen_tour": bool(user.has_seen_tour),
    }


@app.post("/api/tour/complete")
def tour_complete(user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not user.has_seen_tour:
        user.has_seen_tour = True
        db.commit()
    return {"ok": True}


# ─── Case Board ────────────────────────────────────────────────
# Evidence cards appear only for challenges the player has solved. The player's
# arrangement (card positions, red-string links, sticky notes) is saved as one
# small JSON document on their user row.

BOARD_MAX_BYTES = 60_000
BOARD_MAX_NOTES = 60
BOARD_MAX_LINKS = 300
BOARD_NOTE_CHARS = 280
BOARD_COORD_MIN, BOARD_COORD_MAX = -2000, 8000
NOTE_ID_RE = re.compile(r"^n[a-z0-9]{1,14}$")


def solved_clue_ids(db: Session, user_id: int) -> list:
    ids = []
    for rid, idxs in solved_challenges(db, user_id).items():
        for i in idxs:
            cid = case_clues.clue_id(rid, i)
            if cid in case_clues.CLUES:
                ids.append(cid)
    return sorted(ids, key=lambda c: (case_clues.CLUES[c]["room"], case_clues.CLUES[c]["challenge"]))


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
        return None
    return round(max(BOARD_COORD_MIN, min(BOARD_COORD_MAX, float(v))), 1)


def clean_board(raw, valid_clue_ids: set) -> dict:
    """Whitelist-validate a client-supplied board document."""
    raw = raw if isinstance(raw, dict) else {}
    notes = []
    for n in (raw.get("notes") if isinstance(raw.get("notes"), list) else [])[:BOARD_MAX_NOTES]:
        if not isinstance(n, dict):
            continue
        nid, x, y = n.get("id"), _num(n.get("x")), _num(n.get("y"))
        if not (isinstance(nid, str) and NOTE_ID_RE.match(nid)) or x is None or y is None:
            continue
        text = n.get("text") if isinstance(n.get("text"), str) else ""
        notes.append({"id": nid, "x": x, "y": y, "text": text[:BOARD_NOTE_CHARS]})
    node_ids = set(valid_clue_ids) | {n["id"] for n in notes}

    pos = {}
    src = raw.get("pos") if isinstance(raw.get("pos"), dict) else {}
    for k, v in src.items():
        if k in node_ids and isinstance(v, dict):
            x, y = _num(v.get("x")), _num(v.get("y"))
            if x is not None and y is not None:
                pos[k] = {"x": x, "y": y}

    links, seen_pairs = [], set()
    for pair in (raw.get("links") if isinstance(raw.get("links"), list) else [])[:BOARD_MAX_LINKS * 2]:
        if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
            continue
        a, b = pair
        if not (isinstance(a, str) and isinstance(b, str)) or a == b or a not in node_ids or b not in node_ids:
            continue
        key = tuple(sorted((a, b)))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        links.append(list(key))
        if len(links) >= BOARD_MAX_LINKS:
            break

    seen = [c for c in (raw.get("seen") if isinstance(raw.get("seen"), list) else []) if isinstance(c, str) and c in valid_clue_ids]
    return {"pos": pos, "links": links, "notes": notes, "seen": sorted(set(seen))}


@app.get("/api/board")
def get_board(user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    solved = solved_clue_ids(db, user.id)
    try:
        saved = json.loads(user.board_data) if user.board_data else {}
    except ValueError:
        saved = {}
    layout = clean_board(saved, set(solved))
    reached = min(user.current_room or 1, max(case_clues.ROOM_TITLES))
    locked = {}
    for room in range(1, reached + 1):
        total = sum(1 for c in case_clues.CLUES.values() if c["room"] == room)
        got = sum(1 for c in solved if case_clues.CLUES[c]["room"] == room)
        if total - got > 0:
            locked[str(room)] = [c["challenge"] for c in case_clues.CLUES.values()
                                 if c["room"] == room and c["id"] not in solved]
    return {
        "clues": [case_clues.CLUES[c] for c in solved],
        "total": len(case_clues.CLUES),
        "locked": locked,
        "rooms": {str(k): v for k, v in case_clues.ROOM_TITLES.items()},
        "layout": layout,
        "unseen": sum(1 for c in solved if c not in set(layout["seen"])),
    }


@app.post("/api/board")
def save_board(
    payload: dict = Body(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    layout = clean_board(payload, set(solved_clue_ids(db, user.id)))
    blob = json.dumps(layout, separators=(",", ":"))
    if len(blob.encode("utf-8")) > BOARD_MAX_BYTES:
        raise HTTPException(status_code=400, detail="Board is too large")
    user.board_data = blob
    db.commit()
    return {"ok": True}


# ─── Scoreboard API (public) ──────────────────────────────────

def ranked_players(db: Session):
    """Non-admin players, best first: higher score wins; on a tie the player who reached
    that score sooner (earlier last correct flag) ranks higher. Players with no solves
    rank after those with solves at the same score, then by sign-up time."""
    last_solve = (
        db.query(
            models.FlagSubmission.user_id.label("uid"),
            func.max(models.FlagSubmission.submitted_at).label("t"),
        )
        .filter(models.FlagSubmission.is_correct == True)  # noqa: E712
        .group_by(models.FlagSubmission.user_id)
        .subquery()
    )
    return (
        db.query(models.User, last_solve.c.t)
        .outerjoin(last_solve, last_solve.c.uid == models.User.id)
        .filter(models.User.is_admin == False)  # noqa: E712
        .order_by(
            models.User.score.desc(),
            case((last_solve.c.t.is_(None), 1), else_=0),
            last_solve.c.t.asc(),
            models.User.created_at.asc(),
            models.User.id.asc(),
        )
        .all()
    )


@app.get("/api/scoreboard")
def get_scoreboard(db: Session = Depends(database.get_db)):
    # Admins run the event; they don't compete.
    return [
        {
            "id": u.id,
            "name": u.username,
            "score": u.score or 0,
            "current_room": u.current_room or 1,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_solve_at": (t.isoformat() + "Z") if t else None,
        }
        for u, t in ranked_players(db)
    ]


# ─── Admin API (protected) ────────────────────────────────────

@app.get("/api/admin/players")
def admin_get_players(admin: models.User = Depends(require_admin), db: Session = Depends(database.get_db)):
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    counts = {
        uid: (total, correct or 0)
        for uid, total, correct in db.query(
            models.FlagSubmission.user_id,
            func.count(models.FlagSubmission.id),
            func.sum(case((models.FlagSubmission.is_correct == True, 1), else_=0)),  # noqa: E712
        ).group_by(models.FlagSubmission.user_id).all()
    }
    result = []
    for u in users:
        total, correct = counts.get(u.id, (0, 0))
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": u.is_admin,
            "score": u.score or 0,
            "current_room": u.current_room or 1,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "total_submissions": total,
            "correct_submissions": int(correct),
        })
    return result


@app.put("/api/admin/users/{user_id}/score")
def admin_update_score(
    user_id: int,
    score: int = Body(..., embed=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    if score < 0 or score > 1_000_000:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 1,000,000")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.score = score
    db.commit()
    return {"message": f"Score updated to {score}", "user": user.username}


@app.put("/api/admin/users/{user_id}/room")
def admin_update_room(
    user_id: int,
    room: int = Body(..., embed=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    if room < 1 or room > MAX_ROOM:
        raise HTTPException(status_code=400, detail=f"Room must be between 1 and {MAX_ROOM}")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.current_room = room
    db.commit()
    return {"message": f"Room updated to {room}", "user": user.username}


@app.put("/api/admin/users/{user_id}/email")
def admin_update_email(
    user_id: int,
    data: dict,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_email = normalize_email(data.get("email", ""))
    if not new_email:
        raise HTTPException(status_code=400, detail="Email cannot be empty")
    conflict = db.query(models.User).filter(
        func.lower(models.User.email) == new_email,
        models.User.id != user_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Email already in use by another account")
    user.email = new_email
    db.commit()
    return {"message": f"Email updated for '{user.username}'", "email": new_email}


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
    db.query(models.FlagSubmission).filter(models.FlagSubmission.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"message": f"User '{username}' deleted"}


@app.post("/api/admin/reset-scores")
def admin_reset_scores(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    db.query(models.User).update({models.User.score: 0, models.User.current_room: 1, models.User.board_data: None})
    db.query(models.FlagSubmission).delete()
    db.commit()
    return {"message": "All scores and progress reset"}


@app.get("/api/admin/stats")
def admin_stats(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(database.get_db),
):
    ranked = ranked_players(db)
    top = ranked[0][0] if ranked else None
    return {
        "total_players": db.query(models.User).filter(models.User.is_admin == False).count(),  # noqa: E712
        "total_users": db.query(models.User).count(),
        "total_submissions": db.query(models.FlagSubmission).count(),
        "correct_submissions": db.query(models.FlagSubmission)
        .filter(models.FlagSubmission.is_correct == True)  # noqa: E712
        .count(),
        "top_player": {"name": top.username, "score": top.score or 0} if top else None,
    }
