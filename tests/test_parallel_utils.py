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

    def test_plan_equal_cpu_workers_uses_one_worker_per_job_when_possible(self):
        module = self.load_module()
        self.assertEqual(module.plan_equal_cpu_workers(6, total_cpus=64), (6, 10))

    def test_plan_equal_cpu_workers_caps_workers_to_available_cpus(self):
        module = self.load_module()
        self.assertEqual(module.plan_equal_cpu_workers(10, total_cpus=4), (4, 1))

    def test_plan_equal_cpu_workers_honors_explicit_worker_limit(self):
        module = self.load_module()
        self.assertEqual(module.plan_equal_cpu_workers(6, total_cpus=64, max_workers=3), (3, 21))

    def test_with_worker_suffix_inserts_worker_id_before_extension(self):
        module = self.load_module()
        self.assertEqual(module.with_worker_suffix("launch_dm.sh", 3), "launch_dm_worker3.sh")
        self.assertEqual(module.with_worker_suffix("/tmp/map.params", 7), "/tmp/map_worker7.params")
        self.assertEqual(module.with_worker_suffix("fft.log", None), "fft.log")

    def test_plan_parallel_occupancy_maps_prefers_full_map_parallelism(self):
        module = self.load_module()
        self.assertEqual(module.plan_parallel_occupancy_maps(3, 2, total_cpus=4), [2, 1, 1])

    def test_plan_parallel_occupancy_maps_scales_per_map_budget(self):
        module = self.load_module()
        self.assertEqual(module.plan_parallel_occupancy_maps(6, 2, total_cpus=64), [2, 2, 2, 2, 2, 2])

    def test_plan_parallel_occupancy_maps_honors_max_parallel_occupancies(self):
        module = self.load_module()
        self.assertEqual(module.plan_parallel_occupancy_maps(6, 2, total_cpus=64, max_occupancies=3), [2, 2, 2])


if __name__ == "__main__":
    unittest.main()
