"""Create/promote an admin user. Run once to seed the first admin.

    ADMIN_PASSWORD='choose-a-strong-one' python create_admin.py

If ADMIN_PASSWORD is not set you'll be prompted for one (input hidden).
If an 'admin' user already exists it is simply promoted; its password is
left untouched.
"""
import getpass
import os
import sys

sys.path.insert(0, ".")
import database, models
from passlib.context import CryptContext

MIN_PASSWORD_LEN = 8

models.Base.metadata.create_all(bind=database.engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = database.SessionLocal()
try:
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if admin:
        admin.is_admin = True
        db.commit()
        team_name = admin.team.name if admin.team else "no team"
        print(f"User 'admin' promoted to admin (team: {team_name})")
    else:
        password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Password for new 'admin' user: ")
        if len(password) < MIN_PASSWORD_LEN:
            sys.exit(f"Password must be at least {MIN_PASSWORD_LEN} characters. Nothing was created.")

        team = db.query(models.Team).filter(models.Team.name == "ORGANIZERS").first()
        if not team:
            team = models.Team(name="ORGANIZERS")
            db.add(team)
            db.commit()
            db.refresh(team)

        user = models.User(
            username="admin",
            hashed_password=pwd_context.hash(password),
            team_id=team.id,
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print("Created admin user 'admin' (team: ORGANIZERS)")
finally:
    db.close()
