"""p17-memory-worker: consolidates learned assistant memory and compacts ended sessions.

Model calls take minutes on a CPU, so this consumer gets a long poll interval and
processing budget; user requests only publish the event and return immediately.
"""

from app.events import topics
from app.workers.handlers import build_memory_handler
from app.workers.runtime import run_worker

TOPICS = (topics.MEMORY_CONSOLIDATION_REQUESTED, topics.MEMORY_SESSION_ENDED)

if __name__ == "__main__":
    run_worker("memory-worker", TOPICS, build_memory_handler, max_poll_interval_ms=1_800_000, max_processing_seconds=1_500)
