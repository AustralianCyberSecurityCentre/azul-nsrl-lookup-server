# NSRL Minimal Lookup Server

Self hosted service to lookup hashes from NSRL via REST API.

Path to existing SQLite DB should be provided by environment variable `NSRL_DB_FILEPATH`.
The database can be sourced from: [the NSRL website](https://www.nist.gov/itl/ssd/software-quality-group/national-software-reference-library-nsrl/nsrl-download/current-rds).

**This server only works with the `RDSv3 Modern Minimal Database` data set.**

## Installation

```bash
pip install azul-nsrl-lookup-server
```

## Db Installation

The database used by NSRL can be downloaded and updated using the scripts found in the docker-scripts folder.

This database can't be used for testing because it's too large (97GB at least).

Quick browsing of the db with sqlite3:
After downloading the database the recommended commands to get a quick summary of the db are:

```bash
sqlite3 RDS_2024.03.1_modern_minimal.db
```

```sql
.headers on
.mode column
.tables

SELECT * FROM DISTINCT_HASH LIMIT 5;
SELECT * FROM MFG LIMIT 5;
SELECT * FROM PKG LIMIT 5;
SELECT * FROM FILE LIMIT 5;
SELECT * FROM OS LIMIT 5;
SELECT * FROM VERSION LIMIT 5;
```

## Usage

```bash
 Usage: azul-nsrl-lookup-server [OPTIONS]

 Run the server.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --host                       TEXT     [default: localhost]                                       │
│ --port                       INTEGER  [default: 8853]                                            │
│ --workers                    INTEGER  [default: 1]                                               │
│ --forwarded-allow-ips        TEXT     [default: *]                                               │
│ --install-completion                  Install completion for the current shell.                  │
│ --show-completion                     Show completion for the current shell, to copy it or       │
│                                       customize the installation.                                │
│ --help                                Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

```

Example:

```bash
NSRL_DB_FILEPATH=<PATH_TO_SQLITE_DB> azul-nsrl-lookup-server
```

Note that by default all reverse proxies are trusted. Configure this with the `--forwarded-allow-ips` flag if you
intend to directly expose the NSRL lookup server.

## Docker

```bash
docker run -d \
 -v <PATH_TO_SQLITE3_DB>:/home/nsrl/rdsv3_modern_minimal.db \
 -p 8853:8853 \
 azul-nsrl-lookup-server:latest \
 --host 0.0.0.0
```

## Kube offline nist

The kube folder has a kubernetes yaml file that enables you to create a pod, pvc and service that will allow you
to host a directory browsing server.

The server has the minimal sql db for 2024.03.1 and the minimal delta for 2024.09.1

It is intended as a template for offline deployments of NSRL lookup server.

## Dependency management

Dependencies are managed in the pyproject.toml and debian.txt file.

Version pinning is achieved using the `uv.lock` file.
Because the `uv.lock` file is configured to use a private UV registry, external developers using UV will need to delete the existing `uv.lock` file and update the project configuration to point to the publicly available PyPI registry instead.

To add new dependencies it's recommended to use uv with the command `uv add <new-package>`
    or for a dev package `uv add --dev <new-dev-package>`

The tool used for linting and managing styling is `ruff` and it is configured via `pyproject.toml`

The debian.txt file manages the debian dependencies that need to be installed on development systems and docker images.

Sometimes the debian.txt file is insufficient and in this case the Dockerfile may need to be modified directly to
install complex dependencies.
