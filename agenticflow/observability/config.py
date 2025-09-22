from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class OrchestratorPolicy:
    retry_backoff_base: float = 0.0
    retry_jitter: float = 0.0
    retry_max_backoff: Optional[float] = None
    circuit_failure_threshold: int = 0
    circuit_reset_seconds: float = 30.0
    default_agent_qps: Optional[float] = None


@dataclass(frozen=True)
class ObservabilityConfig:
    log_format: str = "json"  # json|text
    log_level: str = "INFO"
    metrics_backend: str = ""  # "prometheus" to enable
    prom_port: int = 8000


@dataclass(frozen=True)
class AppConfig:
    orchestrator: OrchestratorPolicy = OrchestratorPolicy()
    observability: ObservabilityConfig = ObservabilityConfig()


def load_config(path: str | None = None) -> AppConfig:
    # Load from env first
    orch = OrchestratorPolicy(
        retry_backoff_base=float(os.environ.get("AF_RETRY_BACKOFF_BASE", "0") or 0),
        retry_jitter=float(os.environ.get("AF_RETRY_JITTER", "0") or 0),
        retry_max_backoff=_to_opt_float(os.environ.get("AF_RETRY_MAX_BACKOFF")),
        circuit_failure_threshold=int(os.environ.get("AF_CIRCUIT_FAIL_THRESHOLD", "0") or 0),
        circuit_reset_seconds=float(os.environ.get("AF_CIRCUIT_RESET_SECONDS", "30") or 30),
        default_agent_qps=_to_opt_float(os.environ.get("AF_DEFAULT_AGENT_QPS")),
    )
    obs = ObservabilityConfig(
        log_format=os.environ.get("AGENTICFLOW_LOG_FORMAT", "json"),
        log_level=os.environ.get("AGENTICFLOW_LOG_LEVEL", "INFO"),
        metrics_backend=os.environ.get("AGENTICFLOW_METRICS", ""),
        prom_port=int(os.environ.get("AGENTICFLOW_PROM_PORT", "8000") or 8000),
    )
    cfg = AppConfig(orchestrator=orch, observability=obs)

    # Merge from file if provided (JSON/YAML)
    if path:
        p = Path(path)
        if p.exists():
            text = p.read_text()
            data = None
            if p.suffix.lower() in (".yaml", ".yml"):
                try:
                    import yaml  # type: ignore
                    data = yaml.safe_load(text)
                except Exception:
                    data = None
            else:
                try:
                    data = json.loads(text)
                except Exception:
                    data = None
            if isinstance(data, dict):
                cfg = _merge_cfg(cfg, data)
    return cfg


def _to_opt_float(v: str | None) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


def _merge_cfg(cfg: AppConfig, data: dict) -> AppConfig:
    # Simple overlay for known keys only
    orch = cfg.orchestrator
    o2 = data.get("orchestrator", {}) if isinstance(data.get("orchestrator"), dict) else {}
    orch = OrchestratorPolicy(
        retry_backoff_base=float(o2.get("retry_backoff_base", orch.retry_backoff_base)),
        retry_jitter=float(o2.get("retry_jitter", orch.retry_jitter)),
        retry_max_backoff=o2.get("retry_max_backoff", orch.retry_max_backoff),
        circuit_failure_threshold=int(o2.get("circuit_failure_threshold", orch.circuit_failure_threshold)),
        circuit_reset_seconds=float(o2.get("circuit_reset_seconds", orch.circuit_reset_seconds)),
        default_agent_qps=o2.get("default_agent_qps", orch.default_agent_qps),
    )
    obs = cfg.observability
    o3 = data.get("observability", {}) if isinstance(data.get("observability"), dict) else {}
    obs = ObservabilityConfig(
        log_format=str(o3.get("log_format", obs.log_format)),
        log_level=str(o3.get("log_level", obs.log_level)),
        metrics_backend=str(o3.get("metrics_backend", obs.metrics_backend)),
        prom_port=int(o3.get("prom_port", obs.prom_port)),
    )
    return AppConfig(orchestrator=orch, observability=obs)