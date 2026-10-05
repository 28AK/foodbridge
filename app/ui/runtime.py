"""Bridge between Streamlit (synchronous scripts) and the async services.

One background thread runs an asyncio event loop for the whole server. It holds
the MongoDB connection and the scheduler (expiry / re-matching), and every
Streamlit session submits coroutines to it with `run(...)`.
"""
import asyncio
import logging
import threading

import streamlit as st
from fastapi import HTTPException

from app import db
from app.services import scheduler
from app.services.classifier import get_analyzer

log = logging.getLogger(__name__)


class Runtime:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True, name="foodbridge-loop").start()
        self.run(db.connect())
        self.scheduler = asyncio.run_coroutine_threadsafe(scheduler.run_forever(), self.loop)
        # Load the AI model in the background so the first page isn't blocked
        threading.Thread(target=self._warm_up_ai, daemon=True, name="foodbridge-ai").start()

    @staticmethod
    def _warm_up_ai():
        try:
            get_analyzer().load()
        except Exception:
            log.warning("AI model unavailable; listings will use time-only risk scoring")

    def run(self, coro, timeout: float = 180):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)


@st.cache_resource(show_spinner="Starting FoodBridge…")
def get_runtime() -> Runtime:
    return Runtime()


def run(coro):
    """Run an async service call from Streamlit code and return its result."""
    return get_runtime().run(coro)


def try_run(coro):
    """Like run(), but shows service errors (HTTPException) as a red message; returns None."""
    try:
        return run(coro)
    except HTTPException as exc:
        st.error(exc.detail)
        return None
