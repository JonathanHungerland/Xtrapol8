import os
import pickle
import tempfile
import types
import unittest
from pathlib import Path

import matplotlib

from tests.helpers import load_module_from_repo, patched_sys_modules


matplotlib.use("Agg")


def make_fake_crystallography_modules():
    iotbx = types.ModuleType("iotbx")
    iotbx_mtz = types.ModuleType("iotbx.mtz")
    iotbx_symmetry = types.ModuleType("iotbx.symmetry")
    iotbx_pdb = types.ModuleType("iotbx.pdb")
    iotbx_pdb.hierarchy = object()
    iotbx_file_reader = types.ModuleType("iotbx.file_reader")
    iotbx_file_reader.any_file = object()
    iotbx.mtz = iotbx_mtz
    iotbx.symmetry = iotbx_symmetry
    iotbx.pdb = iotbx_pdb
    iotbx.file_reader = iotbx_file_reader

    cctbx = types.ModuleType("cctbx")
    cctbx_miller = types.ModuleType("cctbx.miller")
    cctbx_crystal = types.ModuleType("cctbx.crystal")
    cctbx_xray = types.ModuleType("cctbx.xray")
    cctbx_array_family = types.ModuleType("cctbx.array_family")
    cctbx_array_family.flex = object()
    cctbx.miller = cctbx_miller
    cctbx.crystal = cctbx_crystal
    cctbx.xray = cctbx_xray
    cctbx.array_family = cctbx_array_family

    scipy = types.ModuleType("scipy")
    scipy_stats = types.ModuleType("scipy.stats")
    scipy_stats.linregress = lambda *args, **kwargs: None
    scipy.stats = scipy_stats

    return {
        "iotbx": iotbx,
        "iotbx.mtz": iotbx_mtz,
        "iotbx.symmetry": iotbx_symmetry,
        "iotbx.pdb": iotbx_pdb,
        "iotbx.file_reader": iotbx_file_reader,
        "cctbx": cctbx,
        "cctbx.miller": cctbx_miller,
        "cctbx.crystal": cctbx_crystal,
        "cctbx.xray": cctbx_xray,
        "cctbx.array_family": cctbx_array_family,
        "scipy": scipy,
        "scipy.stats": scipy_stats,
    }


class PlotFextrSigmasTests(unittest.TestCase):
    def load_module(self):
        with patched_sys_modules(make_fake_crystallography_modules()):
            return load_module_from_repo("fextr_utils_under_test", "Fextr_utils.py")

    def test_plot_fextr_sigmas_handles_mixed_scalar_and_bin_lists(self):
        module = self.load_module()
        records = [
            [
                0.100,
                "FoFo",
                "qFextr",
                [99.0, 2.4, 1.8],
                [0.0, 12.0, 8.0],
                [0.0, 1.2, 0.8],
                [0.0, 6.0, 3.0],
                [0.0, 0.6, 0.3],
            ],
            [
                0.200,
                "FoFo",
                "qFextr",
                [99.0, 2.4, 1.8],
                [0.0, 10.0, 7.0],
                [0.0, 1.0, 0.7],
                [0.0, 6.0, 3.0],
                [0.0, 0.6, 0.3],
            ],
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pickle_path = tmp_path / "Fextr_binstats.pickle"
            with pickle_path.open("wb") as handle:
                for record in records:
                    pickle.dump(record, handle)

            cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                module.plot_Fextr_sigmas(str(pickle_path))
            finally:
                os.chdir(cwd)

            self.assertTrue((tmp_path / "qFextr_sigmas.png").is_file())
            self.assertTrue((tmp_path / "FoFo_sigmas.png").is_file())


if __name__ == "__main__":
    unittest.main()
