"""Configurable settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class DB(BaseSettings):
    """Settings for the DB."""

    filepath: str = "./rdsv3_modern_minimal.db"
    model_config = SettingsConfigDict(env_prefix="nsrl_db_")


class Server(BaseSettings):
    """Settings for the HTTP server."""

    host: str = "localhost"
    port: int = 8853
    workers: int = 1
    prefix: str = ""
    root_path: str = "/"
    # All IPs are allowed by default as forwarded_allow_ips doesn't support IP ranges (making it impossible to
    # statically identify Kubernetes ingresses) and this should always have an ingress in front of it anyway.
    forwarded_allow_ips: str = "*"
    # Security headers applied to the uvicorn server
    headers: dict[str, str] = dict()
    model_config = SettingsConfigDict(env_prefix="nsrl_server_")


class UI(BaseSettings):
    """Settings for the Web UI."""

    max_results: int = 25
    model_config = SettingsConfigDict(env_prefix="nsrl_ui_")


db = DB()
server = Server()
ui = UI()
