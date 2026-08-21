import copy
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path("/root/.openclaw/workspace")
SCRIPT = ROOT / "scripts/check-entity-write-path-registry.py"
REGISTRY = ROOT / "config/entity-write-path-registry.json"
SPEC = importlib.util.spec_from_file_location("entity_registry_check", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class EntityWritePathRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_production_registry_is_structurally_valid(self):
        errors, warnings = MODULE.validate_registry(copy.deepcopy(self.registry))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 5)

    def test_missing_required_entity_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["entities"] = [entity for entity in registry["entities"] if entity["id"] != "applications"]
        errors, _ = MODULE.validate_registry(registry)
        self.assertTrue(any("missing required entities: applications" in error for error in errors))

    def test_duplicate_entity_id_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["entities"].append(copy.deepcopy(registry["entities"][0]))
        errors, _ = MODULE.validate_registry(registry)
        self.assertTrue(any("duplicate entity ids: jobs" in error for error in errors))

    def test_missing_governance_gate_fails(self):
        registry = copy.deepcopy(self.registry)
        del registry["entities"][0]["governance"]["kill_switch"]
        errors, _ = MODULE.validate_registry(registry)
        self.assertTrue(any("missing governance gate kill_switch" in error for error in errors))

    def test_writable_entity_without_entry_point_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["entities"][0]["write_contract"]["entry_points"] = []
        errors, _ = MODULE.validate_registry(registry)
        self.assertTrue(any("writable entity needs a controlled entry point" in error for error in errors))

    def test_incomplete_workflow_measurement_fails(self):
        registry = copy.deepcopy(self.registry)
        del registry["workflows"][0]["metrics"]["manual_touch_minutes"]
        errors, _ = MODULE.validate_registry(registry)
        self.assertTrue(any("missing metric manual_touch_minutes" in error for error in errors))

    def test_live_sqlite_check_passes_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "evidence.sqlite"
            connection = sqlite3.connect(database)
            connection.execute("CREATE TABLE present_table (id INTEGER PRIMARY KEY)")
            connection.commit()
            connection.close()
            entities = [
                {
                    "id": "fixture",
                    "live_evidence": [
                        {"type": "sqlite_table", "path": str(database), "table": "present_table"},
                        {"type": "sqlite_table", "path": str(database), "table": "missing_table"},
                    ],
                }
            ]
            results, failures = MODULE.run_live_checks(entities)
            self.assertTrue(results[0]["ok"])
            self.assertFalse(results[1]["ok"])
            self.assertEqual(len(failures), 1)
            self.assertIn("missing_table", failures[0])


if __name__ == "__main__":
    unittest.main()
