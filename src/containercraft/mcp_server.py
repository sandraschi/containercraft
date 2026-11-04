"""FastMCP server for ContainerCraft."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from . import cli

mcp = FastMCP("ContainerCraft", version="0.1.0")


@mcp.tool()
def status() -> dict[str, Any]:
    """Probe the container engine and daemon; reports `down` when unreachable."""
    return cli.engine_status()


@mcp.tool()
def list_containers(all_containers: bool = True) -> dict[str, Any]:
    """List containers with name, image, and state."""
    return cli.ps(all_containers=all_containers)


@mcp.tool()
def container_logs(container: str, tail: int = 20) -> dict[str, Any]:
    """Tail the last lines of a container's logs."""
    return cli.logs(container, tail)


@mcp.tool()
def container_exec(container: str, command: list[str]) -> dict[str, Any]:
    """Execute a command inside a running container."""
    return cli.exec_in(container, command)


@mcp.tool()
def list_images() -> dict[str, Any]:
    """List local images."""
    return cli.images()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
