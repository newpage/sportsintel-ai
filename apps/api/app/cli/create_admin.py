import argparse
import getpass

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.auth import AuditLog, User


def main():
    parser = argparse.ArgumentParser(description="Create or promote a SportsIntel administrator")
    parser.add_argument("--email", default=settings.admin_bootstrap_email)
    parser.add_argument("--name", default="SportsIntel Administrator")
    args = parser.parse_args()

    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        email = args.email.lower().strip()
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.display_name = user.display_name or args.name
            user.password_hash = hash_password(password)
            user.role = "ADMIN"
            user.is_active = True
            action = "ADMIN_PROMOTED"
        else:
            user = User(
                email=email,
                display_name=args.name,
                password_hash=hash_password(password),
                role="ADMIN",
                is_active=True,
            )
            db.add(user)
            db.flush()
            action = "ADMIN_CREATED"

        db.add(
            AuditLog(
                actor_user_id=user.id,
                action=action,
                entity_type="USER",
                entity_id=str(user.id),
                details="Created through secure bootstrap command",
            )
        )
        db.commit()
        print(f"Administrator ready: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
