import ast
import re
import unittest

from tests.helpers import REPO_ROOT


class GuiSourceRegressionTests(unittest.TestCase):
    """Source-level guards for GUI regressions exposed by wxPython Phoenix."""

    def setUp(self):
        self.python_files = sorted(REPO_ROOT.glob("*.py")) + sorted((REPO_ROOT / "gui").glob("*.py"))

    def test_deprecated_gui_api_patterns_are_absent(self):
        """Covers the Python 3/Phoenix API replacements already applied in the GUI code."""
        deprecated_patterns = [
            "sys.maxint",
            "InsertStringItem(",
            "SetStringItem(",
            "unicode)",
            "wx.PyValidator",
            "string.letters",
            "wx.NewId(",
        ]
        for pattern in deprecated_patterns:
            offenders = [path.name for path in self.python_files if pattern in path.read_text()]
            self.assertEqual(
                offenders,
                [],
                f"Deprecated API pattern {pattern!r} reappeared in {offenders}",
            )

    def test_wx_pubsub_import_is_confined_to_compat_layer(self):
        """Covers direct deprecated wx pubsub imports so they stay isolated in the fallback shim."""
        offenders = []
        for path in self.python_files:
            text = path.read_text()
            if "from wx.lib.pubsub import pub" in text and path.name != "pubsub_compat.py":
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_gui_modules_import_pubsub_via_compat_layer(self):
        """Covers that GUI entry points use the compatibility wrapper instead of importing pubsub directly."""
        x8_gui = (REPO_ROOT / "X8_gui.py").read_text()
        panel_log = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("from pubsub_compat import pub", x8_gui)
        self.assertIn("from pubsub_compat import pub", panel_log)

    def test_toolbar_addtool_calls_use_phoenix_signature(self):
        """Covers Phoenix toolbar construction by requiring AddTool calls to pass id, label, and bitmap."""
        tree = ast.parse((REPO_ROOT / "X8_gui.py").read_text())
        addtool_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "AddTool":
                addtool_calls.append(node)
        self.assertGreaterEqual(len(addtool_calls), 2)
        for call in addtool_calls:
            self.assertGreaterEqual(
                len(call.args),
                3,
                "Phoenix ToolBar.AddTool calls must pass toolId, label, and bitmap",
            )

    def test_open_phil_returns_early_when_no_path_was_selected(self):
        """Covers canceled phil selection so the GUI does not try to open a None path."""
        text = (REPO_ROOT / "X8_gui.py").read_text()
        self.assertIn("if phil_file is None:\n            return", text)

    def test_x8_thread_decodes_subprocess_output_as_text(self):
        """Covers GUI log updates so worker output reaches pubsub as text instead of raw bytes."""
        text = (REPO_ROOT / "X8_gui.py").read_text()
        self.assertIn("text=True, encoding='utf-8', errors='replace'", text)

    def test_x8_thread_uses_non_deprecated_event_api(self):
        """Covers thread stop checks so Python 3.10 does not warn on deprecated Event.isSet()."""
        text = (REPO_ROOT / "X8_gui.py").read_text()
        self.assertIn("self._stop_event = threading.Event()", text)
        self.assertIn("return self._stop_event.is_set()", text)
        self.assertNotIn("isSet()", text)
        self.assertNotIn("self._stop = threading.Event()", text)

    def test_panel_extrapolation_uses_window_newcontrolid(self):
        """Covers the Phoenix-safe control ID creation path in the extrapolation panel."""
        text = (REPO_ROOT / "gui" / "panelExtrapolation.py").read_text()
        self.assertNotIn("wx.NewId()", text)
        self.assertEqual(text.count("wx.Window.NewControlId()"), 5)

    def test_panel_refinement_adds_runref_once(self):
        """Covers the duplicate-sizer bug by asserting that Run refinement is added only once."""
        text = (REPO_ROOT / "gui" / "panelRefinement.py").read_text()
        matches = re.findall(r"ref_sizer\.Add\(self\.RunRef,\s*0\)", text)
        self.assertEqual(len(matches), 1)

    def test_occupancy_box_adds_child_sizers_without_vertical_alignment_flags(self):
        """Covers the Phoenix sizer assertion by forbidding vertical-alignment flags on child sizers."""
        text = (REPO_ROOT / "gui" / "panelExtrapolation.py").read_text()
        self.assertIn("self.occ_sizer_final.Add(occ_sizer, 0, wx.ALL, 0)", text)
        self.assertIn("self.occ_sizer_final.Add(list_occ_sizer, 0, wx.ALL, 0)", text)

    def test_panel_log_adds_child_sizers_without_vertical_alignment_flags(self):
        """Covers the Phoenix sizer assertion in the occupancy results tab."""
        text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("self.mainSizer.Add(self.occNfextrSizer, 0, wx.ALL, border=5)", text)
        self.assertIn("self.mainSizer.Add(self.ImgSizer, 1, wx.ALIGN_CENTER_HORIZONTAL)", text)

    def test_panel_log_skips_missing_occupancy_pickle_on_finish(self):
        """Covers failed runs so the results tab does not raise a second exception for a missing pickle."""
        text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("if not os.path.isfile(pickle_fn):\n            return", text)

    def test_panel_log_normalizes_non_string_log_lines(self):
        """Covers log updates so bytes-like payloads are coerced to text before marker matching."""
        text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("if not isinstance(line, str):", text)
        self.assertIn("if hasattr(line, \"decode\"):", text)


if __name__ == "__main__":
    unittest.main()
