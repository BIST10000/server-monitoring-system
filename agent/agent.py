from __future__ import annotations

import os
import socket
import time
from datetime import datetime, timezone

import httpx
import psutil


def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None or not str(v).strip():
        raise RuntimeError(f"Missing env var: {name}")
    return str(v)


def collect_metrics() -> list[dict]:
    ts = datetime.now(timezone.utc).isoformat()
    vm = psutil.virtual_memory()
    disk_path = os.getenv("AGENT_DISK_PATH", "/")
    du = psutil.disk_usage(disk_path)

    metrics = [
        {"name": "cpu_percent", "value": float(psutil.cpu_percent(interval=0.2)), "tags": {}, "ts": ts},
        {"name": "mem_used_percent", "value": float(vm.percent), "tags": {}, "ts": ts},
        {"name": "disk_used_percent", "value": float(du.percent), "tags": {"path": disk_path}, "ts": ts},
    ]

    try:
        la = os.getloadavg()
        metrics.extend(
            [
                {"name": "loadavg_1m", "value": float(la[0]), "tags": {}, "ts": ts},
                {"name": "loadavg_5m", "value": float(la[1]), "tags": {}, "ts": ts},
                {"name": "loadavg_15m", "value": float(la[2]), "tags": {}, "ts": ts},
            ]
        )
    except (AttributeError, OSError):
        pass

    return metrics


def main() -> None:
    api_base = _env("API_BASE_URL", "http://localhost:8080")
    api_key = _env("API_KEY", "dev-key-1")
    server_name = os.getenv("SERVER_NAME") or socket.gethostname()
    agent_version = os.getenv("AGENT_VERSION", "0.1.0")
    interval_seconds = float(os.getenv("AGENT_INTERVAL_SECONDS", "15"))
    timeout_seconds = float(os.getenv("AGENT_TIMEOUT_SECONDS", "10"))

    headers = {"X-Api-Key": api_key}

    with httpx.Client(timeout=timeout_seconds) as client:
        while True:
            client.post(
                f"{api_base}/api/v1/heartbeats",
                headers=headers,
                json={"server_name": server_name, "agent_version": agent_version, "payload": {"hostname": server_name}},
            ).raise_for_status()

            for m in collect_metrics():
                client.post(
                    f"{api_base}/api/v1/metrics",
                    headers=headers,
                    json={"server_name": server_name, **m},
                ).raise_for_status()

            time.sleep(max(1.0, interval_seconds))


if __name__ == "__main__":
    main()

