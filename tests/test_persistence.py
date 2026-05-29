"""
test_persistence.py
Database and file I/O tests for SpiderFEA.
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.api import (
    init_database,
    save_design,
    load_design,
    list_designs,
    delete_design,
    export_database,
    import_database,
    create_design,
    update_geometry_parameter,
)


@pytest.fixture
def tmp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_database(db_path)
    yield db_path
    os.unlink(db_path)


def test_database_has_designs_table(tmp_db):
    conn = sqlite3.connect(tmp_db)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "designs" in tables
    conn.close()


def test_database_has_settings_table(tmp_db):
    conn = sqlite3.connect(tmp_db)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "settings" in tables
    conn.close()


def test_save_design_increments_id(tmp_db):
    d1 = create_design("First")
    d2 = create_design("Second")
    id1 = save_design(d1)
    id2 = save_design(d2)
    assert id2 == id1 + 1


def test_load_design_roundtrip(tmp_db):
    original = create_design("RoundTrip")
    original = update_geometry_parameter(original, "D_inner_spider", 88.0)
    design_id = save_design(original)
    loaded = load_design(design_id)
    assert loaded.name == "RoundTrip"
    assert loaded.D_inner_spider == 88.0


def test_list_designs_ordering(tmp_db):
    save_design(create_design("A"))
    save_design(create_design("B"))
    designs = list_designs()
    assert len(designs) == 2
    assert designs[0]["name"] == "A"
    assert designs[1]["name"] == "B"


def test_delete_design_removes_entry(tmp_db):
    design = create_design("ToDelete")
    design_id = save_design(design)
    delete_design(design_id)
    with pytest.raises(ValueError):
        load_design(design_id)


def test_export_database_creates_valid_sqlite(tmp_db, tmp_path, monkeypatch):
    monkeypatch.setattr("src.database._get_default_db_path", lambda: tmp_db)
    save_design(create_design("Original"))
    backup = tmp_path / "backup.db"
    export_database(str(backup))
    assert backup.is_file()
    conn = sqlite3.connect(str(backup))
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "designs" in tables
    assert "settings" in tables


def test_import_database_replace(tmp_db, tmp_path, monkeypatch):
    monkeypatch.setattr("src.database._get_default_db_path", lambda: tmp_db)
    # Populate original DB
    save_design(create_design("Original"))
    # Create backup with different design
    backup = tmp_path / "backup.db"
    export_database(str(backup))
    # Replace and verify backup contents
    import_database(str(backup), merge=False)
    designs = list_designs()
    assert len(designs) == 1
    assert designs[0]["name"] == "Original"
