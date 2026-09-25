"""Safety alert notifications.

In AWS this publishes to an Amazon SNS topic that subscribers (email/SMS)
receive. Locally the message is logged so development never depends on cloud
credentials.
"""

import logging

from app.config import Config

logger = logging.getLogger("safewatch.alerts")


def publish_alert(alert: dict) -> dict:
    message = (
        f"SAFETY ALERT — {alert['area']}\n"
        f"{alert['message']}\n"
        f"Category: {alert['category']} | Incidents: {len(alert['incidentIds'])}"
    )
    if Config.SNS_TOPIC_ARN:
        try:
            import boto3

            sns = boto3.client("sns", region_name=Config.AWS_REGION)
            sns.publish(TopicArn=Config.SNS_TOPIC_ARN, Subject=f"SafeWatch SA: {alert['area']}", Message=message)
            return {"channel": "sns", "delivered": True}
        except Exception as exc:  # pragma: no cover - only hit without AWS access
            logger.error("SNS publish failed: %s", exc)
            return {"channel": "sns", "delivered": False, "error": str(exc)}
    logger.info("ALERT (local) %s", message.replace("\n", " | "))
    return {"channel": "local-log", "delivered": True}
