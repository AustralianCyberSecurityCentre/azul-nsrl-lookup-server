"""Database Schema.

Database Schema extracted from the distributed NSRL database.
"""

from pydantic import BaseModel, ConfigDict


class DistinctFile(BaseModel):
    """Base Distinct File fields."""

    sha256: str
    sha1: str
    md5: str


class DistinctHash(DistinctFile):
    """Distinct Hash database VIEW."""

    model_config = ConfigDict(from_attributes=True)


class File(DistinctFile):
    """Base File fields."""

    file_name: str
    file_size: int


class FileORM(File):
    """File ORM Model."""

    package_id: int
    model_config = ConfigDict(from_attributes=True)


class Manufacturer(BaseModel):
    """Manufacturer fields."""

    name: str


class MfgORM(Manufacturer):
    """Manufacturer ORM model."""

    manufacturer_id: int
    model_config = ConfigDict(from_attributes=True)


class OperatingSystem(BaseModel):
    """Operating System Fields."""

    name: str
    version: str
    manufacturer: Manufacturer | None = None


class OsORM(OperatingSystem):
    """Operating System ORM model."""

    operating_system_id: int
    manufacturer_id: int
    model_config = ConfigDict(from_attributes=True)


class Package(BaseModel):
    """Application Package fields."""

    name: str
    version: str
    operating_system: OperatingSystem | None = None
    manufacturer: Manufacturer | None = None
    language: str
    application_type: str


class PkgORM(Package):
    """Application Package ORM model."""

    package_id: int
    operating_system_id: int
    manufacturer_id: int
    model_config = ConfigDict(from_attributes=True)


class VersionORM(BaseModel):
    """Version ORM model."""

    version: str
    build_set: str
    build_date: int
    release_date: int
    description: str
    model_config = ConfigDict(from_attributes=True)


class FileDetails(File):
    """Complete info for file."""

    package: Package | None = None


class SummaryPackageVersions(BaseModel):
    """A temporary structure to hold package versions."""

    name: str = ""
    app_type: str = ""
    versions: set[str] = set


class FlatDetails(File):
    """A flat summary of file details to report on."""

    package_name: str = ""
    package_app_type: str = ""
    package_language: str = ""
    package_version: str = ""
    package_manufacturer: str = ""
    operating_system_name: str = ""
    operating_system_version: str = ""
    operating_system_manufacturer: str = ""
