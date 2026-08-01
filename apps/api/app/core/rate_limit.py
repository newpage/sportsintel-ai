from redis import Redis

from app.core.config import settings


def redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def login_rate_key(email: str, ip_address: str | None) -> str:
    return f"auth:login:{email.lower()}:{ip_address or 'unknown'}"


def consume_login_attempt(email: str, ip_address: str | None) -> tuple[int, int]:
    client = redis_client()
    key = login_rate_key(email, ip_address)
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    count, ttl = pipe.execute()
    if ttl < 0:
        client.expire(key, settings.login_lockout_minutes * 60)
        ttl = settings.login_lockout_minutes * 60
    return int(count), int(ttl)


def clear_login_attempts(email: str, ip_address: str | None) -> None:
    redis_client().delete(login_rate_key(email, ip_address))
