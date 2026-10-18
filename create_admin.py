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
database.migrate_to_individual(database.engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = database.SessionLocal()
try:
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if admin:
        admin.is_admin = True
        db.commit()
        print("User 'admin' promoted to admin")
    else:
        password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Password for new 'admin' user: ")
        if len(password) < MIN_PASSWORD_LEN:
            sys.exit(f"Password must be at least {MIN_PASSWORD_LEN} characters. Nothing was created.")

        user = models.User(
            username="admin",
            hashed_password=pwd_context.hash(password),
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print("Created admin user 'admin'")
finally:
    db.close()
