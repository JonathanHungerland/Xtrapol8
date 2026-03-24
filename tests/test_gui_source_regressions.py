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
            "wx.EVT_MENU(",
            "BitmapFromImage(",
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
        deprecated_regexes = [
            r"\bnp\.float\b(?!\d)",
            r"\bnp\.bool\b(?!_)",
        ]
        for pattern in deprecated_regexes:
            offenders = [path.name for path in self.python_files if re.search(pattern, path.read_text())]
            self.assertEqual(
                offenders,
                [],
                f"Deprecated API regex {pattern!r} reappeared in {offenders}",
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

    def test_gui_validation_rejects_missing_triggered_mtz(self):
        """Covers run validation so the GUI cannot launch with input.triggered_mtz left as None."""
        text = (REPO_ROOT / "X8_gui.py").read_text()
        self.assertIn("if len(tabIO.files[\"Triggered mtz\"]) == 0:\n            message_err += \"\\n- at least one triggered mtz (mtz or cif)\"\n            err = 1", text)

    def test_add_results_tab_uses_successful_append_to_define_run_index(self):
        """Covers results-tab bookkeeping so a prior failed construction cannot desynchronize Runs and ResultsBooks."""
        text = (REPO_ROOT / "X8_gui.py").read_text()
        self.assertIn("results_book = NoteBookResults(self.notebook, self.input_phil)", text)
        self.assertIn("self.notebook.Runs = len(self.notebook.ResultsBooks) - 1", text)
        self.assertIn("self.notebook.AddPage(results_book, \"Run #%i\" % (self.notebook.Runs + 1))", text)

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

    def test_panel_log_scales_images_with_integer_dimensions(self):
        """Covers Phoenix image scaling so wx.Image.Scale never receives float dimensions."""
        text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("NewH = int(round(self.photoMaxSize * H / W))", text)
        self.assertIn("NewW = int(round(self.photoMaxSize * W / H))", text)

    def test_panel_log_reads_ragged_pickles_without_plain_numpy_coercion(self):
        """Covers GUI plotting so ragged pickle payloads do not crash during NumPy conversion."""
        text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("stats = np.array(pickle.load(stats_file), dtype=object)", text)
        self.assertIn("_, FoFo_type, _, bin_res_cent_lst, _, _, fdif_data_lst, fdif_sigmas_lst = pickle.load(stats_file)", text)

    def test_map_explorer_uses_object_array_for_ragged_blob_rows(self):
        """Covers map-explorer blob collection so variable-length voxel-index payloads do not crash NumPy conversion."""
        text = (REPO_ROOT / "map_explorer.py").read_text()
        self.assertIn("all_atoms = np.array(all_atoms, dtype=object)", text)

    def test_gui_does_not_treat_optional_fextr_artifacts_as_missing_file_errors(self):
        """Covers optional result polling so mode-dependent qFextr plots do not emit misleading missing-file messages."""
        text = (REPO_ROOT / "X8_gui.py").read_text()
        self.assertNotIn('print("%s does not exists" %filepath)', text)


if __name__ == "__main__":
    unittest.main()
