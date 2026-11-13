"""p17-application-worker: consumes Kafka events and maintains the application timeline and status notifications in MongoDB."""

from app.events import topics
from app.workers.handlers import build_application_handler
from app.workers.runtime import run_worker

TOPICS = (topics.APPLICATION_CREATED, topics.APPLICATION_UPDATED, topics.APPLICATION_STATUS_CHANGED)

if __name__ == "__main__":
    run_worker("application-worker", TOPICS, build_application_handler)
