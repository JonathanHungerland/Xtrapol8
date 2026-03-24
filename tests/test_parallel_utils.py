import unittest

from tests.helpers import load_module_from_repo


class ParallelUtilsTests(unittest.TestCase):
    def load_module(self):
        return load_module_from_repo("parallel_utils_under_test", "parallel_utils.py")

    def test_resolve_nproc_uses_affinity_size_for_auto(self):
        module = self.load_module()
        original_sched_getaffinity = getattr(module.os, "sched_getaffinity", None)
        original_cpu_count = module.os.cpu_count
        module.os.sched_getaffinity = lambda pid: {0, 1, 2, 3, 4, 5}
        module.os.cpu_count = lambda: 64
        try:
            self.assertEqual(module.resolve_nproc(0), 6)
            self.assertEqual(module.resolve_nproc(None), 6)
        finally:
            if original_sched_getaffinity is None:
                delattr(module.os, "sched_getaffinity")
            else:
                module.os.sched_getaffinity = original_sched_getaffinity
            module.os.cpu_count = original_cpu_count

    def test_resolve_nproc_preserves_explicit_worker_counts(self):
        module = self.load_module()
        self.assertEqual(module.resolve_nproc(12), 12)


if __name__ == "__main__":
    unittest.main()
