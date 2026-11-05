# ContainerCraft

Container workstation over docker or podman. One craft replacing the docker-mcp, podman-mcp
and kubernetes-mcp container verbs.

## Verbs
- `containercraft status`: probe engine + daemon (`down` receipt when unreachable)
- `containercraft ps [--running]`: containers with name, image, state
- `containercraft logs --ctr NAME [--tail N]`
- `containercraft exec --ctr NAME -- cmd...`
- `containercraft images`
- `containercraft run-echo [--image hello-world]`: throwaway container, `--network none`, never pulls
- `containercraft compose-ps --dir DIR`
- `containercraft mcp`: FastMCP stdio server

## Honesty rules
- Daemon absent means `status: down`, exit 0. It is reported, never counted as a pass of real work.
- `run-echo` skips (`status: skipped`) when the image is not already local.

## Status — does today / next week / non-goals

**Does today:** Python FastMCP (`cli.py` + `mcp_server.py`), justfile,
AGENTS; 6 test fns; day-1 scaffold fusing docker/podman/k8s container
verbs.

**Next week:** probe daemons on Goliath (canonical backend for CI);
3 recipes (list, logs-tail, exec-echo); k8s scope in writing.

**Non-goals:** not a docker brand (name deliberate); daemon-absent CI =
`DOWN` receipt, never red.

## Lineage — the Storytold craft-app pattern

Storytold ArtCraft ([storytold/artcraft](https://github.com/storytold/artcraft) — "the IDE for artists") was the starting point. The 16 craft apps in the Storytold stable each ship one binary that is both the human CLI and the agent MCP server (stdio), headless-first, with `run.json` + report artifacts. That modus operandi and harness is what this repo implements; the code here is independent, the pattern is shared.
