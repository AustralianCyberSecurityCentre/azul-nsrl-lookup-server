"""NSRL Minimal Lookup Server.

CLI for server.
"""

import typer
import uvicorn

from . import settings

cli = typer.Typer()


@cli.command()
def server(
    host: str = settings.server.host,
    port: int = settings.server.port,
    workers: int = settings.server.workers,
    forwarded_allow_ips: str = settings.server.forwarded_allow_ips,
):
    """Run the server."""
    headers: list[str, str] = []
    for header_label, header_val in settings.server.headers.items():
        headers.append((header_label.strip(), header_val.strip()))

    uvicorn.run(
        "azul_nsrl_lookup_server.server:app",
        host=host,
        port=port,
        workers=workers,
        forwarded_allow_ips=forwarded_allow_ips,
        headers=headers,
    )


if __name__ == "__main__":
    cli()
