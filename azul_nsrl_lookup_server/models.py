"""Pydantic models.

Models for validation and swagger ui.
"""

import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base, Reflected


class File(Reflected, Base):
    """File details."""

    __tablename__ = "FILE"

    sha256 = Column(String, primary_key=True)
    sha1 = Column(String, primary_key=True)
    md5 = Column(String, primary_key=True)
    file_name = Column(String, primary_key=True)
    file_size = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("PKG.package_id"), primary_key=True)

    package = relationship("Pkg", back_populates="files")


class Mfg(Reflected, Base):
    """Manufacturer."""

    __tablename__ = "MFG"

    manufacturer_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    operating_systems = relationship("Os", back_populates="manufacturer")

    packages = relationship("Pkg", back_populates="manufacturer")


class Os(Reflected, Base):
    """Operating System details."""

    __tablename__ = "OS"

    operating_system_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("MFG.manufacturer_id"), primary_key=True)

    manufacturer = relationship("Mfg", back_populates="operating_systems")

    packages = relationship("Pkg", back_populates="operating_system")


class Pkg(Reflected, Base):
    """Application package details."""

    __tablename__ = "PKG"

    package_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    operating_system_id = Column(Integer, ForeignKey("OS.operating_system_id"), primary_key=True)
    manufacturer_id = Column(Integer, ForeignKey("MFG.manufacturer_id"), primary_key=True)
    language = Column(String, primary_key=True)
    application_type = Column(String, primary_key=True)

    operating_system = relationship("Os", back_populates="packages")
    manufacturer = relationship("Mfg", back_populates="packages")

    files = relationship("File", back_populates="package")


class Version(Reflected, Base):
    """File version."""

    __tablename__ = "VERSION"

    version = Column(String, unique=True, primary_key=True)
    build_set = Column(String, nullable=False)
    build_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    release_date = Column(TIMESTAMP, nullable=False)
    description = Column(String, nullable=False)


class DistinctHash(Reflected, Base):
    """Distinct file VIEW."""

    __tablename__ = "DISTINCT_HASH"

    sha256 = Column(String, primary_key=True)
    sha1 = Column(String, primary_key=True)
    md5 = Column(String, primary_key=True)
