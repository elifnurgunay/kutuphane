"""Günlük görevi backend süreci içinde her gece çalıştırır (ek bağımlılık gerektirmez)."""

import asyncio
import logging
from datetime import datetime, time, timedelta

from app.core.db import SessionLocal
from app.jobs import daily

# uvicorn'un log kanalı: görev çıktısı sunucu loglarında görünür
logger = logging.getLogger("uvicorn.error")

RUN_AT = time(0, 5)  # yerel saatle her gün 00:05


def seconds_until_next_run(now: datetime, run_at: time = RUN_AT) -> float:
    target = datetime.combine(now.date(), run_at, tzinfo=now.tzinfo)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_once() -> None:
    with SessionLocal() as db:
        result = daily.run(db)
    logger.info("Günlük görev tamamlandı: %s", result)


async def run_forever() -> None:
    """Açılışta bir kez, sonra her gün RUN_AT saatinde çalışır."""
    while True:
        try:
            await asyncio.to_thread(_run_once)
        except Exception:
            logger.exception("Günlük görev başarısız oldu")
        await asyncio.sleep(seconds_until_next_run(datetime.now().astimezone()))
