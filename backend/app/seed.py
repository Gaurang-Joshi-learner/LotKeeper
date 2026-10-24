"""Demo data. Run with `python -m app.seed` (idempotent) or set SEED_ON_STARTUP=true."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import User, Vehicle
from app.services.auth_service import AuthService

# (make, model, category, price, quantity, year, color)
VEHICLES = [
    ("Toyota", "Corolla", "Sedan", 21500, 6, 2025, "#C9CCD1"),
    ("Honda", "Civic", "Sedan", 24800, 4, 2025, "#9B1C20"),
    ("Tesla", "Model 3", "Sedan", 41990, 3, 2025, "#E7E9EC"),
    ("BMW", "M340i", "Sedan", 62500, 1, 2024, "#1F3A5F"),
    ("Toyota", "RAV4", "SUV", 33900, 5, 2025, "#2F5D50"),
    ("Hyundai", "Tucson", "SUV", 31200, 4, 2025, "#B8C2CC"),
    ("Volvo", "XC90", "SUV", 58900, 2, 2024, "#3B4B59"),
    ("Land Rover", "Defender 110", "SUV", 71500, 1, 2025, "#4E5B3A"),
    ("Ford", "F-150", "Truck", 44900, 3, 2025, "#B5521B"),
    ("Rivian", "R1T", "Truck", 73000, 0, 2024, "#E0A526"),
    ("Mazda", "MX-5 Miata", "Convertible", 31700, 2, 2025, "#C23B22"),
    ("Porsche", "911 Carrera", "Coupe", 118000, 1, 2024, "#202428"),
    ("Chevrolet", "Corvette", "Coupe", 69900, 0, 2024, "#E4C21F"),
    ("Kia", "EV6", "Hatchback", 44500, 3, 2025, "#6C7A89"),
    ("Volkswagen", "Golf GTI", "Hatchback", 33400, 2, 2025, "#0E3B7A"),
    ("Chrysler", "Pacifica", "Van", 41200, 2, 2024, "#7A8793"),
]


def seed(db: Session) -> None:
    settings = get_settings()
    auth = AuthService(db)
    existing = {e for (e,) in db.execute(select(User.email))}
    if settings.seed_admin_email not in existing:
        auth.register(settings.seed_admin_email, settings.seed_admin_password, role="admin")
    if settings.seed_user_email not in existing:
        auth.register(settings.seed_user_email, settings.seed_user_password)
    if settings.seed_demo_vehicles and db.scalar(select(func.count(Vehicle.id))) == 0:
        for make, model, category, price, qty, year, color in VEHICLES:
            db.add(Vehicle(make=make, model=model, category=category, price=price, quantity=qty, year=year, color=color))
        db.commit()


if __name__ == "__main__":
    from app.core.database import Base, engine

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed(session)
    print("Seeded demo data.")
