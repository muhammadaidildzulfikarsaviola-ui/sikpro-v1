import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ui.theme import ThemeManager


class ThemePersistenceTests(unittest.TestCase):
    def test_light_is_default_and_theme_round_trips_without_losing_other_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Path(folder) / "settings.json"
            settings.write_text('{"recent_project":"sample.sik"}', encoding="utf-8")
            manager = ThemeManager(SimpleNamespace(), settings)
            self.assertEqual(manager.mode, "light")
            manager.mode = "dark"
            manager.save()
            reloaded = ThemeManager(SimpleNamespace(), settings)
            self.assertEqual(reloaded.mode, "dark")
            self.assertIn("recent_project", settings.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
