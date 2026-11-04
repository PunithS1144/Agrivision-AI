# ============================================================================
# Plantix AI / AgriVision Platform - Observability, Telemetry & Logging (Phase 9)
# Tracks request latency (p95), error rates, throughput, database file metrics,
# cache hit ratios, and subsystem health without logging sensitive PII.
# ============================================================================

import os
import time
import uuid
import threading
from datetime import datetime
from config import Config

class MonitoringService:
    def __init__(self):
        self._lock = threading.RLock()
        self.start_time = time.time()
        self.total_requests = 0
        self.status_codes = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
        self.latencies = [] # Store last 1000 request latencies in ms

    def record_request(self, status_code, latency_ms):
        """Records telemetry for an HTTP transaction."""
        with self._lock:
            self.total_requests += 1
            if 200 <= status_code < 300:
                self.status_codes["2xx"] += 1
            elif 300 <= status_code < 400:
                self.status_codes["3xx"] += 1
            elif 400 <= status_code < 500:
                self.status_codes["4xx"] += 1
            elif status_code >= 500:
                self.status_codes["5xx"] += 1

            self.latencies.append(latency_ms)
            if len(self.latencies) > 1000:
                self.latencies.pop(0)

    def get_metrics(self):
        """Calculates system metrics, throughput, error rates, and latency percentiles."""
        with self._lock:
            uptime_seconds = int(time.time() - self.start_time)
            req_count = self.total_requests
            errors = self.status_codes["4xx"] + self.status_codes["5xx"]
            error_rate = round((errors / req_count * 100), 2) if req_count > 0 else 0.0

            if self.latencies:
                sorted_lat = sorted(self.latencies)
                avg_lat = round(sum(sorted_lat) / len(sorted_lat), 1)
                p95_idx = int(len(sorted_lat) * 0.95)
                p95_lat = round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 1)
                min_lat = round(sorted_lat[0], 1)
                max_lat = round(sorted_lat[-1], 1)
            else:
                avg_lat = p95_lat = min_lat = max_lat = 0.0

            # Database disk file metrics
            db_size_bytes = os.path.getsize(Config.DATABASE_PATH) if os.path.exists(Config.DATABASE_PATH) else 0
            wal_path = Config.DATABASE_PATH + "-wal"
            wal_size_bytes = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0

            return {
                "uptime_seconds": uptime_seconds,
                "uptime_human": f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s",
                "traffic": {
                    "total_requests": req_count,
                    "requests_per_minute": round((req_count / max(1, uptime_seconds)) * 60, 2),
                    "status_breakdown": self.status_codes,
                    "error_rate_percent": error_rate
                },
                "latency_ms": {
                    "average": avg_lat,
                    "p95": p95_lat,
                    "min": min_lat,
                    "max": max_lat
                },
                "storage": {
                    "db_size_mb": round(db_size_bytes / (1024 * 1024), 2),
                    "wal_size_mb": round(wal_size_bytes / (1024 * 1024), 2),
                    "storage_engine": "SQLite WAL High-Concurrency"
                },
                "timestamp": datetime.now().isoformat()
            }

    def generate_correlation_id(self):
        """Generates a UUID4 correlation request ID."""
        return f"req_{uuid.uuid4().hex[:12]}"

monitoring_service = MonitoringService()
