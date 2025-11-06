"""Test the web server."""

import os
import sqlite3
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from azul_nsrl_lookup_server.models import Reflected
from azul_nsrl_lookup_server.server import app, get_db


class TestServer(unittest.TestCase):
    """Functional tests for the server."""

    @classmethod
    def setUpClass(cls) -> None:
        """Construct a test database."""
        cls.db_file = tempfile.NamedTemporaryFile().name
        db_url = f"sqlite:///{cls.db_file}"

        db = sqlite3.connect(cls.db_file)
        script = os.path.join(os.path.dirname(__file__), "data", "rdsv3_minimal.schema.sql")
        with open(script) as f:
            db.executescript(f.read())

        cls.valid_sha256 = "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
        cls.valid_sha1 = "AC91EF00F33F12DD491CC91EF00F33F12DD491CA"
        cls.valid_md5 = "DC2311FFDC0015FCCC12130FF145DE78"
        cls.partial_sha256a = "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E541"
        cls.partial_sha256b = "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E542"
        cls.partial_sha256c = "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E543"
        cls.partial_sha1a = "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932131"
        cls.partial_sha1b = "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932132"
        cls.partial_sha1c = "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932133"
        cls.partial_md5a = "1B6A3B720DEC5E60FDA2ECB0EE713661"
        cls.partial_md5b = "1B6A3B720DEC5E60FDA2ECB0EE713662"
        cls.partial_md5c = "1B6A3B720DEC5E60FDA2ECB0EE713663"
        script = f"""
            insert into MFG values ('1', 'Microsoft Corporation');
            insert into MFG values ('2', 'Rand Corporation');
            insert into OS values ('1', 'Windows NT', '4.0', '1');
            insert into OS values ('2', 'Custom OS', '1.0', '2');
            insert into PKG values ('1', 'Microsoft Word', '2000', '1', '1', 'English', 'Operating System');
            insert into PKG values ('2', 'Word', '2000', '1', '1', 'English', 'Operating System');
            insert into PKG values ('3', 'PKG1', '2007', '2', '2', 'English', 'Operating System');
            insert into PKG values ('4', 'PKG1', '2007', NULL, '2', 'English', 'Operating System');
            insert into PKG values ('5', 'PKG1', '2007', '2', NULL, 'English', 'Operating System');
            insert into FILE values ('{cls.valid_sha256}', '{cls.valid_sha1}', '{cls.valid_md5}', 'WORD.EXE', '1217645', '1');
            insert into FILE values ('{cls.valid_sha256}', '{cls.valid_sha1}', '{cls.valid_md5}', 'WORD.EXE', '1217645', '2');
            insert into FILE values ('{cls.partial_sha256a}', '{cls.partial_sha1a}', '{cls.partial_md5a}', 'FILEa.EXE', '123456', '3');
            insert into FILE values ('{cls.partial_sha256b}', '{cls.partial_sha1b}', '{cls.partial_md5b}', 'FILEb.EXE', '123456', '4');
            insert into FILE values ('{cls.partial_sha256c}', '{cls.partial_sha1c}', '{cls.partial_md5c}', 'FILEc.EXE', '123456', '5');
        """
        db.executescript(script)
        db.commit()
        db.close()

        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Reflected.prepare(engine=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove the test database."""
        try:
            os.unlink(cls.db_file)
        except:
            pass

    def test_valid_distinct(self):
        """Validate DISTINCT lookups."""
        expected = {"sha256": self.valid_sha256, "sha1": self.valid_sha1, "md5": self.valid_md5}
        response = self.client.get(f"/exists/{self.valid_md5}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)

        response = self.client.get(f"/exists/{self.valid_sha1}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)

        response = self.client.get(f"/exists/{self.valid_sha256}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)

        response = self.client.get(f"/exists/{self.valid_sha256.lower()}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)

        response = self.client.get(f"/exists/{self.valid_sha256.upper()}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)

    def test_invalid_distinct(self):
        """Invalid digest given."""
        response = self.client.get(f"/exists/notadigest")
        self.assertEqual(response.status_code, 400, response.text)

    def test_notfound_distinct(self):
        """Digest not in dataset."""
        digest = "a" * 32
        response = self.client.get(f"/exists/{digest}")
        self.assertEqual(response.status_code, 404, response.text)

    def test_invalid_details(self):
        """Invalid digest given."""
        response = self.client.get(f"/details/notadigest")
        self.assertEqual(response.status_code, 400, response.text)

    def test_notfound_details(self):
        """Digest not in dataset."""
        digest = "a" * 32
        response = self.client.get(f"/details/{digest}")
        self.assertEqual(response.status_code, 404, response.text)

    def test_valid_details(self):
        """Validate detailed lookups."""
        expected = [
            {
                "sha256": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                "sha1": "AC91EF00F33F12DD491CC91EF00F33F12DD491CA",
                "md5": "DC2311FFDC0015FCCC12130FF145DE78",
                "file_name": "WORD.EXE",
                "file_size": 1217645,
                "package": {
                    "name": "Microsoft Word",
                    "version": "2000",
                    "manufacturer": {"name": "Microsoft Corporation"},
                    "language": "English",
                    "application_type": "Operating System",
                    "operating_system": {
                        "name": "Windows NT",
                        "version": "4.0",
                        "manufacturer": {"name": "Microsoft Corporation"},
                    },
                },
            },
            {
                "sha256": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                "sha1": "AC91EF00F33F12DD491CC91EF00F33F12DD491CA",
                "md5": "DC2311FFDC0015FCCC12130FF145DE78",
                "file_name": "WORD.EXE",
                "file_size": 1217645,
                "package": {
                    "name": "Word",
                    "version": "2000",
                    "manufacturer": {"name": "Microsoft Corporation"},
                    "language": "English",
                    "application_type": "Operating System",
                    "operating_system": {
                        "name": "Windows NT",
                        "version": "4.0",
                        "manufacturer": {"name": "Microsoft Corporation"},
                    },
                },
            },
        ]
        response = self.client.get(f"/details/{self.valid_md5}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)

    def test_partial_details(self):
        """Validate partial details lookups."""
        expected_a = [
            {
                "sha256": "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E541",
                "sha1": "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932131",
                "md5": "1B6A3B720DEC5E60FDA2ECB0EE713661",
                "file_name": "FILEa.EXE",
                "file_size": 123456,
                "package": {
                    "name": "PKG1",
                    "version": "2007",
                    "operating_system": {
                        "name": "Custom OS",
                        "version": "1.0",
                        "manufacturer": {"name": "Rand Corporation"},
                    },
                    "manufacturer": {"name": "Rand Corporation"},
                    "language": "English",
                    "application_type": "Operating System",
                },
            }
        ]
        response_a = self.client.get(f"/details/{self.partial_md5a}")
        self.assertEqual(response_a.status_code, 200, response_a.text)
        self.assertEqual(response_a.json(), expected_a)

        expected_b = [
            {
                "sha256": "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E542",
                "sha1": "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932132",
                "md5": "1B6A3B720DEC5E60FDA2ECB0EE713662",
                "file_name": "FILEb.EXE",
                "file_size": 123456,
                "package": {
                    "name": "PKG1",
                    "version": "2007",
                    "operating_system": None,
                    "manufacturer": {"name": "Rand Corporation"},
                    "language": "English",
                    "application_type": "Operating System",
                },
            }
        ]
        response_b = self.client.get(f"/details/{self.partial_md5b}")
        self.assertEqual(response_b.status_code, 200, response_b.text)
        self.assertEqual(response_b.json(), expected_b)

        expected_c = [
            {
                "sha256": "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E543",
                "sha1": "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932133",
                "md5": "1B6A3B720DEC5E60FDA2ECB0EE713663",
                "file_name": "FILEc.EXE",
                "file_size": 123456,
                "package": {
                    "name": "PKG1",
                    "version": "2007",
                    "operating_system": {"name": "Custom OS", "version": "1.0", "manufacturer": None},
                    "manufacturer": None,
                    "language": "English",
                    "application_type": "Operating System",
                },
            }
        ]
        response_c = self.client.get(f"/details/{self.partial_md5c}")
        self.assertEqual(response_c.status_code, 200, response_c.text)
        self.assertEqual(response_c.json(), expected_c)
