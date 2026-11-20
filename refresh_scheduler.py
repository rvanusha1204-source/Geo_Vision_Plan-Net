"""
refresh_scheduler.py
Runs build_cache.py automatically on a repeating schedule, so cache/ (and
therefore the dashboard) stays up to date without you ever running
build_cache.py by hand again.

Why a separate process instead of a background thread inside server.py:
Earth Engine calls in build_cache.py can run for tens of minutes. Keeping
that fully separate from server.py means a slow/failed refresh can NEVER
freeze or crash the live web server users are actively looking at — the
dashboard keeps serving the last-known-good cache the entire time a refresh
is running, and again if a refresh fails outright.

Usage:
    python refresh_scheduler.py                  # refresh every 7 days (default)
    python refresh_scheduler.py --interval-days 3 # custom interval
    python refresh_scheduler.py --once            # run a single refresh now and exit
                                                   # (good for a Windows Task Scheduler
                                                   # entry instead of a long-running loop)

Recommended interval: 7 days. Sentinel-2 (the satellite source used in
analysis_pipeline.py) only revisits any given location every ~5 days, and
each full refresh runs 10 districts x 5 Earth Engine compute calls = 50
calls with retry logic — running this daily mostly burns your Earth Engine
quota for no new imagery. Don't go below ~3 days unless you have a specific
reason to.

Leave this running in its own terminal (or as a Windows scheduled task)
alongside `python server.py`.
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone

LOG_FILE = "refresh_log.txt"


def log(message):
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_once():
    log("Starting build_cache.py refresh run...")
    try:
        # Runs as its own process (not imported) so a crash or hang in the
        # Earth Engine pipeline can never take down this scheduler itself.
        result = subprocess.run(
            [sys.executable, "build_cache.py"],
            capture_output=True, text=True, timeout=60 * 60 * 3  # 3 hour hard ceiling
        )
        # Mirror build_cache.py's own console output into the scheduler log too.
        for line in result.stdout.splitlines():
            log(f"  build_cache: {line}")
        if result.returncode != 0:
            log(f"build_cache.py exited with code {result.returncode}. See errors above.")
            for line in result.stderr.splitlines():
                log(f"  build_cache STDERR: {line}")
        else:
            log("Refresh run finished. cache/last_refresh.json has the details.")
    except subprocess.TimeoutExpired:
        log("Refresh run exceeded 3 hours and was killed. Check Earth Engine quota/status "
            "and your internet connection.")
    except Exception as e:
        log(f"Refresh run failed to start: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-days", type=float, default=7,
                         help="Days between refreshes (default: 7)")
    parser.add_argument("--once", action="store_true",
                         help="Run a single refresh immediately and exit (no loop)")
    args = parser.parse_args()

    if args.once:
        run_once()
        return

    log(f"refresh_scheduler.py started. Refreshing every {args.interval_days} day(s). "
        f"Press Ctrl+C to stop.")
    while True:
        run_once()
        sleep_seconds = args.interval_days * 24 * 60 * 60
        next_run = datetime.now(timezone.utc).timestamp() + sleep_seconds
        log(f"Sleeping until next refresh at "
            f"{datetime.fromtimestamp(next_run, tz=timezone.utc).isoformat(timespec='seconds')}")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
