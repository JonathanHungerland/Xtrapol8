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
            "ndimage.morphology",
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
        ddm_text = (REPO_ROOT / "ddm.py").read_text()
        self.assertNotIn("df_chain.append(", ddm_text)

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

    def test_panel_log_matches_actual_fextr_progress_marker_format(self):
        """Covers progress tracking so the GUI advances on the real Fextr.py map-calculation log line."""
        text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn('LOG_STEPS_CORE = ["TYPE OF ESFAS AND MAPS FOR OCCUPANCY"]', text)
        self.assertIn(
            'r"CALCULATING\\s+(\\S+)\\s+TYPE OF ESFAS AND MAPS FOR OCCUPANCY\\s+([0-9.]+)"',
            text,
        )
        self.assertNotIn('type of structure factors and maps for occupancy', text)
        self.assertNotIn('occ = line.split()[10]', text)

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

    def test_phenix_launchers_do_not_hardcode_four_workers(self):
        """Covers refinement parallelism so Phenix worker counts are not capped at four in source."""
        phenix_refinements = (REPO_ROOT / "phenix_refinements.py").read_text()
        refiner = (REPO_ROOT / "refiner.py").read_text()
        self.assertNotIn("refinement.main.nproc=4", phenix_refinements)
        self.assertNotIn(" nproc=4 ", phenix_refinements)
        self.assertNotIn("refinement.main.nproc=4", refiner)

    def test_occupancies_phil_exposes_parallel_controls(self):
        """Covers the occupancy scheduler knobs so worker parallelism stays user-visible and configurable."""
        text = (REPO_ROOT / "master.py").read_text()
        self.assertIn("parallel = *auto on off", text)
        self.assertIn("max_parallel = 0", text)

    def test_parallel_group_workers_write_separate_logs_and_preserve_gui_progress_markers(self):
        """Covers parallel group execution so worker logs stay separate while the main log keeps GUI progress markers."""
        fextr_text = (REPO_ROOT / "Fextr.py").read_text()
        panel_log_text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn('{}_occupancy_{:.3f}_Xtrapol8.log', fextr_text)
        self.assertIn("def redirect_process_output(log_path):", fextr_text)
        self.assertIn("os.dup2(worker_log.fileno(), 1)", fextr_text)
        self.assertIn("os.dup2(worker_log.fileno(), 2)", fextr_text)
        self.assertIn("flush_output_streams()", fextr_text)
        self.assertIn('return "[occupancy {:.3f}] step: {} {}".format(occ, step, maptype)', fextr_text)
        self.assertIn('return "[occupancy {:.3f}][{}] step: {} {}".format(occ, group_name, step, maptype)', fextr_text)
        self.assertIn('def group_job_worker_main(', fextr_text)
        self.assertIn('ctx.Process(target=group_job_worker_main', fextr_text)
        self.assertIn(r'r"\[occupancy\s+([0-9.]+)\](?:\[[^\]]+\])?\s+step:\s+\S+\s+(\S+)"', panel_log_text)

    def test_parallel_refinement_helpers_suffix_fixed_worker_files(self):
        """Covers per-maptype workers so cwd-fixed helper files stay unique without changing final output layout."""
        phenix_text = (REPO_ROOT / "phenix_refinements.py").read_text()
        refmac_text = (REPO_ROOT / "ccp4_refmac.py").read_text()
        self.assertIn('with_worker_suffix("map.params", self.worker_id)', phenix_text)
        self.assertIn("with_worker_suffix('launch_refmac_for_dm.sh', self.worker_id)", phenix_text)
        self.assertIn("with_worker_suffix('launch_dm.sh', self.worker_id)", phenix_text)
        self.assertIn('with_worker_suffix("fft.log", self.worker_id)', phenix_text)
        self.assertIn("with_worker_suffix('launch_refmac.sh', self.worker_id)", refmac_text)
        self.assertIn("with_worker_suffix('launch_dm.sh', self.worker_id)", refmac_text)
        self.assertIn('with_worker_suffix("fft.log", self.worker_id)', refmac_text)

    def test_fextr_overlaps_direct_real_space_with_reciprocal_branch(self):
        """Covers the refinement branch split so the direct real-space run can overlap reciprocal/DM refinement."""
        fextr_text = (REPO_ROOT / "Fextr.py").read_text()
        self.assertIn("from concurrent.futures import ThreadPoolExecutor", fextr_text)
        self.assertIn("def run_direct_real_space_refinement():", fextr_text)
        self.assertIn("with ThreadPoolExecutor(max_workers=2) as branch_pool:", fextr_text)
        self.assertIn("direct_real_space = branch_pool.submit(run_direct_real_space_refinement)", fextr_text)
        self.assertIn("pdb_out_real = direct_real_space.result()", fextr_text)

    def test_parallel_occupancy_workers_only_create_needed_output_dirs(self):
        """Covers shared occupancy output dirs so parallel q/k/unweighted workers do not race on unrelated mkdir/rmdir calls."""
        fextr_text = (REPO_ROOT / "Fextr.py").read_text()
        self.assertIn("def create_output_dirs(self, outdir, maptypes=None):", fextr_text)
        self.assertIn('need_q = any(mp.startswith("q") for mp in maptypes)', fextr_text)
        self.assertIn('need_k = any(mp.startswith("k") for mp in maptypes)', fextr_text)
        self.assertIn('need_unweighted = any(not mp.startswith(("q", "k")) for mp in maptypes)', fextr_text)
        self.assertIn("os.makedirs(new_dirpath_q, exist_ok=True)", fextr_text)
        self.assertIn("os.makedirs(new_dirpath_k, exist_ok=True)", fextr_text)
        self.assertIn("os.makedirs(new_dirpath, exist_ok=True)", fextr_text)
        self.assertIn("Fextr.create_output_dirs(outdir, final_maptypes)", fextr_text)
        self.assertIn("for path in cleanup_dirs:", fextr_text)

    def test_parallel_occupancy_failures_are_skipped_without_aborting_remaining_jobs(self):
        """Covers worker crashes so one failed occupancy does not suppress later successful occupancy estimation."""
        fextr_text = (REPO_ROOT / "Fextr.py").read_text()
        self.assertIn("failed_occupancies = set()", fextr_text)
        self.assertIn("def fail_occupancy(occ, group_name, message):", fextr_text)
        self.assertIn('pending[:] = [job for job in pending if job["occ"] != occ]', fextr_text)
        self.assertIn('successful_occupancies = [occ for occ in params.occupancies.list_occ if occ not in failed_occupancies]', fextr_text)
        self.assertIn('return results_in_order, successful_occupancies', fextr_text)
        self.assertIn('raise RuntimeError("All occupancy jobs failed. See the per-occupancy worker logs in {}".format(outdir))', fextr_text)

    def test_occupancy_estimation_uses_successful_occupancy_subset_after_parallel_failures(self):
        """Covers downstream indexing so alpha estimation and refinement outputs stay aligned after skipped occupancies."""
        fextr_text = (REPO_ROOT / "Fextr.py").read_text()
        self.assertIn("occupancy_results, successful_occupancies = run_parallel_occupancies(", fextr_text)
        self.assertIn('plotalpha(successful_occupancies, map_expl_lst[1:], map_expl_lst[0], mp_type, log=log).estimate_alpha()', fextr_text)
        self.assertIn('Distance_analysis(pdb_list, successful_occupancies, resids_lst= residlst, use_waters = distance_use_waters, outsuffix = mp_type, log = log).extract_alpha()', fextr_text)
        self.assertIn('Pymol_movie(successful_occupancies, resids_lst = residlst).write_pymol_appearance', fextr_text)
        self.assertIn('recref_pdb_lst[successful_occupancies.index(occ)+1]', fextr_text)

    def test_main_tab_population_is_deferred_until_finished_or_explicit_refresh(self):
        """Covers GUI responsiveness so active runs do not build Main-tab matplotlib widgets from timers while the user swaps tabs."""
        x8_gui_text = (REPO_ROOT / "X8_gui.py").read_text()
        panel_log_text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertIn("self.loaded_main_files = set()", panel_log_text)
        self.assertIn("self.loaded_fextr_files = set()", panel_log_text)
        self.assertIn("self.pending_main_files = []", panel_log_text)
        self.assertIn("self.pending_fextr_files = []", panel_log_text)
        self.assertIn("self.refresh_later = None", panel_log_text)
        self.assertIn("def queue_main_file(self, filepath):", panel_log_text)
        self.assertIn("def queue_fextr_file(self, maptype, filepath):", panel_log_text)
        self.assertIn("def cancel_refresh(self):", panel_log_text)
        self.assertIn("def schedule_refresh(self, delay_ms=150):", panel_log_text)
        self.assertIn("def _run_scheduled_refresh(self):", panel_log_text)
        self.assertIn("def refresh_pending(self):", panel_log_text)
        self.assertIn("def populate_finished_run(self, options):", panel_log_text)
        self.assertIn("self.loaded_fextr_files.clear()", panel_log_text)
        self.assertIn("self.pending_fextr_files = []", panel_log_text)
        self.assertNotIn("self.queue_fextr_file(maptype, filepath)", panel_log_text.split("def populate_finished_run(self, options):", 1)[1].split("def addPlot(self, pickle_file):", 1)[0])
        self.assertIn("if self.timerFextr.IsRunning():\n            self.timerFextr.Stop()", x8_gui_text)
        self.assertIn("if self.timer.IsRunning():\n            self.timer.Stop()", x8_gui_text)
        self.assertNotIn("self.timer.Start(2000)", x8_gui_text)
        self.assertNotIn("self.timerFextr.Start(2000)", x8_gui_text)
        self.assertIn("self.tabImg.schedule_refresh()", x8_gui_text)
        self.assertIn("self.tabImg.cancel_refresh()", x8_gui_text)
        self.assertIn("self.tabImg.populate_finished_run(self.options)", x8_gui_text)
        self.assertIn("queued_any = False", x8_gui_text)
        self.assertIn("if queued_any:\n                        tab.schedule_refresh()", x8_gui_text)
        self.assertNotIn("tab.queue_main_file(filepath)", x8_gui_text)
        self.assertIn("if self.parent.GetSelection() != 1:\n            return False", panel_log_text)

    def test_panel_log_clears_sizer_items_with_is_spacer_method_calls(self):
        """Covers tab refresh cleanup so Phoenix sizer items are destroyed instead of detached by a truthy bound-method check."""
        panel_log_text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        self.assertNotIn("if item.IsSpacer:", panel_log_text)
        self.assertEqual(panel_log_text.count("if item.IsSpacer():"), 2)

    def test_gui_scrolled_panels_disable_focus_driven_scroll_into_view(self):
        """Covers wx ScrolledPanel focus handling so tab/page switches do not trigger deprecated fractional Scroll() calls."""
        panel_log_text = (REPO_ROOT / "gui" / "panelLog.py").read_text()
        panel_ref_text = (REPO_ROOT / "gui" / "panelRefinement.py").read_text()
        panel_ext_text = (REPO_ROOT / "gui" / "panelExtrapolation.py").read_text()
        self.assertIn("self.SetupScrolling(scrollIntoView=False)", panel_log_text)
        self.assertEqual(panel_log_text.count("self.SetupScrolling(scrollIntoView=False)"), 2)
        self.assertIn("self.SetupScrolling(scrollIntoView=False)", panel_ref_text)
        self.assertIn("self.SetupScrolling(scrollIntoView=False)", panel_ext_text)


if __name__ == "__main__":
    unittest.main()
