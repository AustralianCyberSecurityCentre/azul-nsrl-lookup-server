"""Database queries."""

from typing import Union

from sqlalchemy.orm import Session, joinedload

from . import models, schema


def digest_type(digest: str) -> str:
    """Figure out what type of digest was provided."""
    if len(digest) == 32:
        digest_type = "md5"
    elif len(digest) == 40:
        digest_type = "sha1"
    elif len(digest) == 64:
        digest_type = "sha256"
    else:
        raise ValueError(f"Invalid digest type specified: '{digest}'")
    return digest_type


def get_distinct(db: Session, digest: str) -> Union[schema.DistinctHash, None]:
    """Retrieve distinct file."""
    kwargs = {digest_type(digest): digest.upper()}
    query = db.query(models.DistinctHash).filter_by(**kwargs)
    # debug output for ORM query to SQL:
    # print(str(query.statement.compile()))
    return query.first()


def get_details(db: Session, digest: str) -> list[schema.FileDetails]:
    """Retrieve all details for given digest."""
    kwargs = {digest_type(digest): digest.upper()}
    query = (
        db.query(models.File)
        .options(joinedload(models.File.package).joinedload(models.Pkg.manufacturer))
        .options(
            joinedload(models.File.package).joinedload(models.Pkg.operating_system).joinedload(models.Os.manufacturer)
        )
        .filter_by(**kwargs)
    )
    # debug output for ORM query to SQL:
    # print(str(query.statement.compile()))

    def build_package_dict(obj: object) -> dict[str, dict]:
        result = {}
        if obj.package:
            result = {
                "name": obj.package.name,
                "version": obj.package.version,
                "language": obj.package.language,
                "application_type": obj.package.application_type,
            }
            os_val = obj.package.operating_system
            manufacturer = obj.package.manufacturer
            if manufacturer:
                result["manufacturer"] = {
                    "name": manufacturer.name,
                }

            if os_val:
                result["operating_system"] = {
                    "name": os_val.name,
                    "version": os_val.version,
                }

                if manufacturer:
                    result["operating_system"]["manufacturer"] = {
                        "name": manufacturer.name,
                    }

        if len(result.keys()) == 0:
            return None
        return result

    result = [
        schema.FileDetails(
            **{
                "sha256": r.sha256,
                "sha1": r.sha1,
                "md5": r.md5,
                "file_name": r.file_name,
                "file_size": r.file_size,
                "package": build_package_dict(r),
            }
        )
        for r in query.all()
    ]
    return result
