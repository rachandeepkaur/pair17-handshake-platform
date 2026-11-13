"""p17-job-worker: consumes Kafka events and maintains the job search index in MongoDB."""

from app.events import topics
from app.workers.handlers import build_job_handler
from app.workers.runtime import run_worker

TOPICS = (topics.JOB_CREATED,)

if __name__ == "__main__":
    run_worker("job-worker", TOPICS, build_job_handler)
