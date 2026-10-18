# MERAZ 7.0

## Running locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Without `DATABASE_URL` the app uses a local SQLite file (`nightjar.db`). Create the first admin with:

```
ADMIN_PASSWORD='choose-a-strong-one' python create_admin.py
```

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | production | Postgres/Supabase connection string (falls back to SQLite locally) |
| `SECRET_KEY` | **yes, in production** | Signs login cookies. Use a long random string (e.g. `python -c "import secrets;print(secrets.token_hex(32))"`). If unset, a key is derived from `DATABASE_URL` (or random locally) and a warning is logged |
| `GOOGLE_CLIENT_ID` | for Google sign-in | Google sign-in is disabled when unset |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | for email sign-up | Sends verification codes. If `SMTP_HOST` is unset, codes are printed to the server console (dev mode only) |

## Notes for challenge authors

- Flags live in `CHALLENGE_FLAGS` in `main.py` (4 per room, 25 pts each). A challenge may list several accepted answers; it is only scored once per team. Matching ignores case and surrounding spaces.
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

