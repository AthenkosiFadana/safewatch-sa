import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "safewatch.db"))

    # Storage backend: "sqlite" (local development) or "dynamodb" (AWS)
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "sqlite")
    DYNAMODB_TABLE = os.getenv("INCIDENTS_TABLE", os.getenv("DYNAMODB_TABLE", "SafeWatchIncidents"))
    USERS_TABLE = os.getenv("USERS_TABLE", "SafeWatchUsers")
    ALERTS_TABLE = os.getenv("ALERTS_TABLE", "SafeWatchAlerts")
    AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_REGION_NAME", "eu-west-1"))

    # Image/evidence bucket (Amazon S3)
    S3_BUCKET = os.getenv("S3_BUCKET", "")

    # Alert notifications (Amazon SNS)
    SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

    TOKEN_EXPIRES_MINUTES = int(os.getenv("TOKEN_EXPIRES_MINUTES", "720"))

    # Moderation / anti-abuse rules
    DUPLICATE_WINDOW_MINUTES = int(os.getenv("DUPLICATE_WINDOW_MINUTES", "15"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))

    # Demo data is clearly labelled so it is never mistaken for SAPS statistics
    DATA_SOURCES = ("COMMUNITY", "SAPS_OFFICIAL", "DEMO")
