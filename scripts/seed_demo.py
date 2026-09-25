"""Seed SafeWatch SA with clearly-labelled DEMO data.

Demo data is stored with source=DEMO so it is never confused with live
community reports or official SAPS statistics.

    python scripts/seed_demo.py [--clear]
"""

import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app import create_app  # noqa: E402
from app.auth import hash_password  # noqa: E402
from services import storage  # noqa: E402

# Gqeberha (PE) area coordinates
AREAS = {
    "Central, Gqeberha": (-33.9614, 25.6022),
    "New Brighton": (-33.8866, 25.5817),
    "KwaMagxaki": (-33.8775, 25.5519),
    "Korsten": (-33.9358, 25.6129),
    "Summerstrand": (-33.9953, 25.6478),
    "Humewood": (-33.9764, 25.6286),
    "Mount Pleasant": (-33.9317, 25.5753),
    "Motherwell": (-33.8847, 25.5272),
    "Kganya Park": (-33.8672, 25.5675),
    "Saldanha Bay": (-33.0134, 17.9492),
}

CATEGORIES = ["THEFT", "ROBBERY", "ASSAULT", "VANDALISM", "SUSPICIOUS_ACTIVITY",
              "MISSING_PERSON", "ROAD_INCIDENT", "FIRE", "OTHER"]
WEIGHTS = [30, 18, 10, 14, 13, 3, 6, 3, 3]

DESCRIPTIONS = {
    "THEFT": ["Vehicle break-in reported near the shopping centre.", "Cellphone stolen at the taxi rank.",
              "Copper piping stolen from a construction site.", "Bicycle stolen outside the school gates."],
    "ROBBERY": ["Armed robbery reported at a spaza shop.", "Motorist robbed at a stop street.",
                "Delivery driver cornered and robbed of takings."],
    "ASSAULT": ["Altercation reported outside a tavern.", "Street fight involving two men."],
    "VANDALISM": ["Streetlights vandalised.", "Graffiti and broken windows at the community hall.",
                  "Municipal bin set alight."],
    "SUSPICIOUS_ACTIVITY": ["Unknown individuals circling the block in an unmarked vehicle.",
                            "People loitering near parked cars late at night."],
    "MISSING_PERSON": ["Elderly resident reported missing by family."],
    "ROAD_INCIDENT": ["Multi-vehicle collision blocking the intersection.", "Pedestrian knocked down at crossing."],
    "FIRE": ["Informal structure fire spreads to adjacent yard."],
    "OTHER": ["Noise complaint escalating into a neighbourhood dispute."],
}

SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_WEIGHTS = [35, 40, 18, 7]


def seed(clear: bool = False, incidents: int = 180):
    app = create_app()
    with app.app_context():
        if clear:
            if storage.use_dynamodb():
                print("--clear is only supported for the local sqlite backend")
            else:
                with storage.get_db().connect() as conn:
                    conn.execute("DELETE FROM incidents")
                    conn.execute("DELETE FROM users")
                    conn.execute("DELETE FROM alerts")
                    conn.execute("DELETE FROM report_log")
                print("cleared existing data")

        if not storage.get_user_by_email("admin@safewatch.co.za"):
            storage.insert_user({
                "userId": "USR-ADMIN0001",
                "email": "admin@safewatch.co.za",
                "name": "SafeWatch Admin",
                "passwordHash": hash_password("Admin123!"),
                "community": "Gqeberha",
                "role": "ADMIN",
                "createdAt": storage.utcnow(),
            })
            print("admin@safewatch.co.za / Admin123!")

        if not storage.get_user_by_email("demo@safewatch.co.za"):
            storage.insert_user({
                "userId": "USR-DEMO0001",
                "email": "demo@safewatch.co.za",
                "name": "Demo Resident",
                "passwordHash": hash_password("Demo123!"),
                "community": "Central, Gqeberha",
                "role": "MEMBER",
                "createdAt": storage.utcnow(),
            })
            print("demo@safewatch.co.za / Demo123!")

        rng = random.Random(42)
        now = datetime.now(timezone.utc)
        created = 0
        for n in range(incidents):
            area = rng.choice(list(AREAS))
            lat, lon = AREAS[area]
            category = rng.choices(CATEGORIES, weights=WEIGHTS, k=1)[0]
            severity = rng.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
            age = timedelta(days=rng.uniform(0, 45), hours=rng.uniform(0, 23))
            created_at = (now - age).replace(microsecond=0, tzinfo=timezone.utc)
            incident = {
                "incidentId": f"INC-{created_at.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                "userId": rng.choice(["USR-DEMO0001", "USR-ADMIN0001"]),
                "category": category,
                "description": rng.choice(DESCRIPTIONS[category]),
                "latitude": round(lat + rng.uniform(-0.03, 0.03), 6),
                "longitude": round(lon + rng.uniform(-0.03, 0.03), 6),
                "area": area,
                "severity": severity,
                "status": rng.choices(
                    ["PENDING", "UNDER_REVIEW", "VERIFIED", "RESOLVED", "REJECTED"],
                    weights=[10, 15, 25, 45, 5], k=1)[0],
                "source": "DEMO",
                "imageUrl": None,
                "duplicateOf": None,
                "createdAt": created_at.isoformat().replace("+00:00", "Z"),
                "updatedAt": created_at.isoformat().replace("+00:00", "Z"),
            }
            storage.create_incident(incident)
            created += 1

        print(f"seeded {created} demo incidents (source=DEMO)")
        print(f"total incidents in database: {len(storage.list_incidents())}")


if __name__ == "__main__":
    seed(clear="--clear" in sys.argv)
