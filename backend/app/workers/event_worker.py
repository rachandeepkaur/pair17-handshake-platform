"""p17-event-worker: consumes Kafka events and maintains the event registration log and counts in MongoDB."""

from app.events import topics
from app.workers.handlers import build_event_handler
from app.workers.runtime import run_worker

TOPICS = (topics.EVENT_REGISTRATION_CREATED,)

if __name__ == "__main__":
    run_worker("event-worker", TOPICS, build_event_handler)
