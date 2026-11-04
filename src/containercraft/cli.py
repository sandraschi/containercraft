"""ContainerCraft CLI: container/image/volume/network verbs over docker or podman.

Every verb reports a `status` of ok | down | error. A missing daemon is `down`,
never a silent zero. Only `exec` and `run-echo` execute anything inside a container.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any

TIMEOUT_S = 60


def find_engine() -> str | None:
    """Return the first container engine binary on PATH (docker, then podman)."""
    for name in ("docker", "podman"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _run(argv: list[str], timeout: int = TIMEOUT_S) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def _down(reason: str) -> dict[str, Any]:
    return {"status": "down", "available": False, "message": reason}


def engine_status() -> dict[str, Any]:
    """Probe the engine binary and daemon."""
    eng = find_engine()
    if not eng:
        return _down("no docker or podman binary on PATH")
    try:
        proc = _run([eng, "version", "--format", "{{.Server.Version}}"], timeout=20)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return _down(f"engine call failed: {exc}")
    if proc.returncode != 0:
        return _down(proc.stderr.strip()[:300] or "daemon not reachable")
    return {"status": "ok", "available": True, "engine": eng, "server_version": proc.stdout.strip()}


def _json_lines(text: str) -> list[dict[str, Any]]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def ps(all_containers: bool = True) -> dict[str, Any]:
    st = engine_status()
    if st["status"] != "ok":
        return {**st, "containers": []}
    argv = [st["engine"], "ps", "--format", "{{json .}}"]
    if all_containers:
        argv.insert(2, "-a")
    proc = _run(argv)
    if proc.returncode != 0:
        return {"status": "error", "error": proc.stderr.strip()[:300], "containers": []}
    rows = [
        {
            "name": r.get("Names"),
            "image": r.get("Image"),
            "state": r.get("State"),
            "status_text": r.get("Status"),
        }
        for r in _json_lines(proc.stdout)
    ]
    running = sum(1 for r in rows if r["state"] == "running")
    return {"status": "ok", "count": len(rows), "running": running, "containers": rows}


def logs(ctr: str, tail: int = 20) -> dict[str, Any]:
    st = engine_status()
    if st["status"] != "ok":
        return {**st, "lines": []}
    proc = _run([st["engine"], "logs", "--tail", str(tail), ctr])
    if proc.returncode != 0:
        return {"status": "error", "container": ctr, "error": proc.stderr.strip()[:300], "lines": []}
    lines = (proc.stdout + proc.stderr).splitlines()[-tail:]
    return {"status": "ok", "container": ctr, "line_count": len(lines), "lines": lines}


def exec_in(ctr: str, cmd: list[str]) -> dict[str, Any]:
    st = engine_status()
    if st["status"] != "ok":
        return {**st}
    proc = _run([st["engine"], "exec", ctr, *cmd])
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "container": ctr,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip()[:2000],
        "stderr": proc.stderr.strip()[:500],
    }


def images() -> dict[str, Any]:
    st = engine_status()
    if st["status"] != "ok":
        return {**st, "images": []}
    proc = _run([st["engine"], "images", "--format", "{{json .}}"])
    rows = [
        {"repository": r.get("Repository"), "tag": r.get("Tag"), "size": r.get("Size")}
        for r in _json_lines(proc.stdout)
    ]
    return {"status": "ok", "count": len(rows), "images": rows}


def run_echo(image: str, text: str) -> dict[str, Any]:
    """Run `echo` in a throwaway container. Never pulls: the image must exist locally."""
    st = engine_status()
    if st["status"] != "ok":
        return {**st}
    have = _run([st["engine"], "image", "inspect", image])
    if have.returncode != 0:
        return {"status": "skipped", "reason": f"image '{image}' not present locally (no pull)"}
    proc = _run([st["engine"], "run", "--rm", "--network", "none", image, "echo", text])
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "image": image,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip()[:500],
        "stderr": proc.stderr.strip()[:300],
    }


def compose_ps(directory: str) -> dict[str, Any]:
    st = engine_status()
    if st["status"] != "ok":
        return {**st, "services": []}
    proc = subprocess.run(
        [st["engine"], "compose", "ps", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=directory or None,
        check=False,
    )
    if proc.returncode != 0:
        return {"status": "error", "error": proc.stderr.strip()[:300], "services": []}
    rows = _json_lines(proc.stdout)
    return {"status": "ok", "count": len(rows), "services": rows}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="containercraft", description="ContainerCraft: docker/podman workstation CLI")
    p.add_argument("--version", action="version", version="containercraft 0.1.0")
    sub = p.add_subparsers(dest="verb", required=True)

    sub.add_parser("status", help="Probe engine and daemon").add_argument("--json", action="store_true")
    s = sub.add_parser("ps", help="List containers")
    s.add_argument("--running", action="store_true", help="Running only")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("logs", help="Tail container logs")
    s.add_argument("--ctr", required=True)
    s.add_argument("--tail", type=int, default=20)
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("exec", help="Exec a command in a running container")
    s.add_argument("--ctr", required=True)
    s.add_argument("--json", action="store_true")
    s.add_argument("cmd", nargs="+")
    s = sub.add_parser("images", help="List local images")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("run-echo", help="Echo inside a throwaway local-image container (no pull)")
    s.add_argument("--image", default="hello-world")
    s.add_argument("--text", default="containercraft")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("compose-ps", help="List compose services in a directory")
    s.add_argument("--dir", default="")
    s.add_argument("--json", action="store_true")
    sub.add_parser("mcp", help="Run FastMCP stdio server")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.verb == "mcp":
            from .mcp_server import mcp

            mcp.run()
            return 0
        if args.verb == "status":
            res = engine_status()
        elif args.verb == "ps":
            res = ps(all_containers=not args.running)
        elif args.verb == "logs":
            res = logs(args.ctr, args.tail)
        elif args.verb == "exec":
            res = exec_in(args.ctr, args.cmd)
        elif args.verb == "images":
            res = images()
        elif args.verb == "run-echo":
            res = run_echo(args.image, args.text)
        else:
            res = compose_ps(args.dir)
        print(json.dumps(res, indent=2))
        return 0 if res.get("status") in {"ok", "down", "skipped"} else 1
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
