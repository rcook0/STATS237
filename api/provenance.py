from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import numpy as np
import scipy

from stats237_quantlib.meta import get_package_version


def canonical_json(obj: object) -> str:
    """Stable JSON string used for request hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeInfo:
    python: str
    numpy: str
    scipy: str
    platform: str


@dataclass(frozen=True)
class Provenance:
    package_version: str
    received_at: str
    request_id: str
    request_hash: str
    seed_effective: int
    runtime: RuntimeInfo
    git_sha: str | None = None


def make_provenance(payload: dict, seed_effective: int, request_id: str | None = None) -> Provenance:
    rid = request_id or str(uuid.uuid4())
    received_at = datetime.now(timezone.utc).isoformat()

    req_json = canonical_json(payload)
    req_hash = sha256_hex(req_json)

    git_sha = os.environ.get("GIT_SHA") or os.environ.get("STAT237_GIT_SHA")

    rt = RuntimeInfo(
        python=sys.version.split()[0],
        numpy=np.__version__,
        scipy=scipy.__version__,
        platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
    )

    return Provenance(
        package_version=get_package_version(),
        received_at=received_at,
        request_id=rid,
        request_hash=req_hash,
        seed_effective=int(seed_effective),
        runtime=rt,
        git_sha=git_sha,
    )


def provenance_to_dict(p: Provenance) -> dict:
    return asdict(p)
