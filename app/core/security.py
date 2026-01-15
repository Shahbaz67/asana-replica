import uuid


def generate_gid() -> str:
    """Generate a globally unique identifier (GID) similar to Asana's format."""
    return str(uuid.uuid4()).replace("-", "")[:16]


def generate_webhook_secret() -> str:
    """Generate a secret for webhook verification."""
    return str(uuid.uuid4())

