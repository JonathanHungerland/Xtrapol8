import types
import unittest

import numpy as np

from tests.helpers import load_module_from_repo, patched_sys_modules


def make_fake_distance_analysis_modules():
    iotbx = types.ModuleType("iotbx")
    iotbx_pdb = types.ModuleType("iotbx.pdb")
    iotbx_pdb.hierarchy = object()
    iotbx.pdb = iotbx_pdb

    fextr_utils = types.ModuleType("Fextr_utils")
    fextr_utils.check_file_existance = lambda *args, **kwargs: True

    return {
        "iotbx": iotbx,
        "iotbx.pdb": iotbx_pdb,
        "Fextr_utils": fextr_utils,
    }


class ModeValueTests(unittest.TestCase):
    def load_module(self):
        with patched_sys_modules(make_fake_distance_analysis_modules()):
            return load_module_from_repo("distance_analysis_under_test", "distance_analysis.py")

    def test_mode_value_handles_scalar_mode_results(self):
        module = self.load_module()

        class ScalarModeResult:
            def __init__(self, mode):
                self.mode = mode

        original_mode = module.scipy.stats.mode
        module.scipy.stats.mode = lambda values: ScalarModeResult(0.42)
        try:
            self.assertEqual(module._mode_value(np.array([0.42, 0.42, 0.18])), 0.42)
        finally:
            module.scipy.stats.mode = original_mode

    def test_mode_value_handles_array_mode_results(self):
        module = self.load_module()

        class ArrayModeResult:
            def __init__(self, mode):
                self.mode = np.array([mode])

        original_mode = module.scipy.stats.mode
        module.scipy.stats.mode = lambda values: ArrayModeResult(0.26)
        try:
            self.assertEqual(module._mode_value(np.array([0.26, 0.26, 0.18])), 0.26)
        finally:
            module.scipy.stats.mode = original_mode


class ScalarValueTests(unittest.TestCase):
    def load_module(self):
        with patched_sys_modules(make_fake_distance_analysis_modules()):
            return load_module_from_repo("distance_analysis_under_test", "distance_analysis.py")

    def test_scalar_value_extracts_python_float_from_length_one_array(self):
        module = self.load_module()

        value = module._scalar_value(np.array([0.18]))

        self.assertEqual(value, 0.18)
        self.assertIsInstance(value, float)


if __name__ == "__main__":
    unittest.main()
