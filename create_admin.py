"""Create/promote an admin by Google account email. Run once to seed the first admin.

    ADMIN_EMAIL='you@gmail.com' python create_admin.py

Sign-in is Google only, so an admin is simply a user whose Google email is
marked as admin. If that email has already signed in, the existing player is
promoted. Otherwise a placeholder account (username 'admin') is created and
claimed automatically the first time that Google account signs in.

You can also set ADMIN_EMAILS (comma separated) in the environment: any listed
email is promoted at sign-in, with no script needed.
"""
import os
import sys

sys.path.insert(0, ".")
import database, models
from sqlalchemy import func

models.Base.metadata.create_all(bind=database.engine)
database.migrate_to_individual(database.engine)

email = (os.getenv("ADMIN_EMAIL") or (sys.argv[1] if len(sys.argv) > 1 else "")).strip().lower()
if "@" not in email:
    sys.exit("Set ADMIN_EMAIL (or pass the email as an argument). Nothing was changed.")

db = database.SessionLocal()
try:
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if user:
        user.is_admin = True
        db.commit()
        print(f"Player '{user.username}' ({email}) promoted to admin")
    else:
        name = "admin"
        n = 1
        while db.query(models.User).filter(models.User.username == name).first():
            n += 1
            name = f"admin{n}"
        db.add(models.User(username=name, email=email, is_email_verified=True, is_admin=True))
        db.commit()
        print(f"Admin '{name}' created for {email}. Sign in with that Google account.")
finally:
    db.close()
