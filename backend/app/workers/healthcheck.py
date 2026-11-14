"""Container health check: exit 0 while the consumer loop has written a heartbeat in the last 60s."""

import sys

from app.workers.runtime import heartbeat_is_fresh

sys.exit(0 if heartbeat_is_fresh() else 1)
