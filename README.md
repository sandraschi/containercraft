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
