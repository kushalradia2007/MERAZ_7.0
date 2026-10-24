# MERAZ 7.0

## Running locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Without `DATABASE_URL` the app uses a local SQLite file (`nightjar.db`). Create the first admin with:

```
ADMIN_EMAIL='you@gmail.com' python create_admin.py
```

## Individual play

The event is individual: there are no teams. Every participant signs in with Google on their own, and score and room progress are stored on the user. Admins don't appear on the public scoreboard.

Sign-in is Google only (no passwords or email codes). Existing accounts keep working when they sign in with the Google account that matches their saved email. Existing databases from the team-based version are upgraded automatically on startup (`database.migrate_to_individual`): each member inherits their old team's score and room, and old submissions are credited to the team leader. The legacy `teams` table and `users.team_id` column are left in place, unused. For a fresh event, use **RESET ALL** in the admin console.

## Hub world

- Fixed layout (rooms 1-5 along the top, then the trail drops down the right edge and rooms 6-10 run along the bottom), so the minimap and the objective arrow always mean the same thing.
- Door states come from `/api/progress`: **locked** (padlock), **open**, **in progress** (amber, flag pips), **cleared** (green) and **sealed** (any room at or beyond `PLAYABLE_ROOMS` in `index.html`; currently none, all 10 rooms are playable). Returning to the hub after unlocking or clearing a room plays a banner, a burst and a sound.
- The **objective bar** above the hub and a bouncing arrow (edge-of-screen arrow when the target is off screen) point at the next thing to do; the **minimap** (bottom-right) shows every door, the allies, your viewport and the objective.
- **Sound** (`audio.js`) is synthesised in the browser (no audio files): a quiet drone with sparse pings plus footstep/door/unlock sounds. It starts after the first key press or click, is toggled with the ♪ button or the `M` key, and the choice is remembered. `NJAudio.sfx('success')` etc. can be reused on other pages.

## Case Board and first-login guide

- **Case Board** (`/board`, `board.html`): every solved challenge pins an evidence card, so the board is a personal, spoiler-safe view of what a player has uncovered. Players drag cards, tie red string between them (drag from a card's pin onto another card, or tap one pin then another card) and add sticky notes. The layout autosaves per player (`users.board_data`). Locked challenges show as classified placeholders that link to their room.
- Card text lives in `case_clues.py` and is sent to the player only **after** they solve that challenge. Never put a flag, or another challenge's answer, in a card.
- **First-login guide** (`tour.js`): an interactive spotlight tour on the hub, shown once per account (`users.has_seen_tour`) and replayable from the **? GUIDE** button. Steps that point at an element which isn't on screen fall back to a centred card, so it works on phones.

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | production | Postgres/Supabase connection string (falls back to SQLite locally) |
| `SECRET_KEY` | **yes, in production** | Signs login cookies. Use a long random string (e.g. `python -c "import secrets;print(secrets.token_hex(32))"`). If unset, a key is derived from `DATABASE_URL` (or random locally) and a warning is logged |
| `CHALLENGE_FLAGS_JSON` | **yes, on Vercel** | JSON string mapping room numbers to lists of flag variants. On local dev, `flags.json` (gitignored) is loaded automatically. |
| `ROOM_UNLOCK_MIN_FLAGS` | no (default `3`) | A room's door opens once the player has captured this many of the previous room's 4 flags. `0` opens every room from the start; admins always bypass. Enforced on the room page, flag submission and evidence files |
| `GOOGLE_CLIENT_ID` | **yes** | OAuth client ID for Google sign-in, the only way to log in. Without it the login page shows a setup notice |
| `ADMIN_EMAILS` | no | Extra comma-separated Google emails that are admins. `kushalradia2007@gmail.com` is always an admin (built in). Applied at every sign-in |

## Notes for challenge authors

- Flags are stored securely in `CHALLENGE_FLAGS_JSON` (Vercel) or `flags.json` (local, gitignored). They are loaded dynamically in `main.py` (4 per room, 25 pts each). See `flags.example.json` for structure. Matching ignores case and surrounding spaces.
- Only `Challenges/Room - N/evidence/**` is served to players (login required). The `README.md` files in `Challenges/` contain answers and are never served.
- Room pages must not contain flags: they verify through `/api/submit_flag` and restore progress from `/api/progress` (see `room-common.js`).

## Contributing Guidelines

- Fork the repository by clicking on fork button (Forking is COMPULSORY)

- Clone the forked repo to your local machine

- Create a separate branch from main

```
git branch <branch_name>

git checkout <branch_name>
```

- Do all your work in this newly created branch

- When your changes are ready and you feel you need to push, fetch the latest changes from main branch first (as the main branch may have moved since you made a branch)

```
git checkout main
git pull https://github.com/SpectreIITBH/MERAZ_7.0

git checkout <branch_name>
git rebase main
```

(If any merge conflicts arise, discuss among yourselves or make most appropriate changes, have a thought!)

- Now after clearing all merge conflicts (if exist) you are ready to push your changes

```
git push origin <branch_name> -f
```

- You can raise a pull request from the github UI after the previous command 


## NPC art

Character art lives in `npc/` (`<id>-portrait.webp`, `<id>-full.webp` for ila, kite, rhea, curator, aman, mira) and is served from `/assets/npc/<file>` (strict filename allowlist). `story.js` uses the portraits for cutscenes and comms avatars (SVG fallback if an image fails), the hub sidebar shows Ila/Rhea/Kite faces, and Room 7 uses Kite's portrait.
