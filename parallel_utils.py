import os


def available_cpu_count():
    """
    Return the number of CPUs available to this process.
    Prefer scheduler affinity when available so cgroup/taskset limits are honored.
    """
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


def resolve_nproc(nproc):
    """
    Resolve a requested worker count.
    A value of 0 or None means "use all available CPUs".
    """
    try:
        requested = int(nproc)
    except (TypeError, ValueError):
        requested = 0

    if requested <= 0:
        return available_cpu_count()
    return requested


def supports_fork_parallelism():
    """
    Return whether the current Python runtime supports fork-based workers.
    Xtrapol8's occupancy workers rely on fork so they can inherit the
    crystallographic objects prepared in the parent process without pickling.
    """
    try:
        import multiprocessing
    except ImportError:
        return False

    try:
        return "fork" in multiprocessing.get_all_start_methods()
    except (AttributeError, NotImplementedError):
        return False


def plan_equal_cpu_workers(job_count, total_cpus=None, max_workers=0):
    """
    Split a CPU budget evenly across concurrent jobs.

    Returns a tuple of:
      (worker_count, nproc_per_worker)

    The worker count is capped by the number of jobs and the available CPU
    budget. Each worker receives the same integer CPU count. Any remainder CPUs
    stay unused instead of creating uneven worker allocations.
    """
    try:
        jobs = int(job_count)
    except (TypeError, ValueError):
        jobs = 0
    jobs = max(0, jobs)
    if jobs == 0:
        return 0, 0

    if total_cpus is None:
        cpus = available_cpu_count()
    else:
        try:
            cpus = int(total_cpus)
        except (TypeError, ValueError):
            cpus = available_cpu_count()
    cpus = max(1, cpus)

    try:
        requested_workers = int(max_workers)
    except (TypeError, ValueError):
        requested_workers = 0

    if requested_workers <= 0:
        worker_count = min(jobs, cpus)
    else:
        worker_count = min(jobs, cpus, requested_workers)

    nproc_per_worker = max(1, cpus // worker_count)
    return worker_count, nproc_per_worker


def with_worker_suffix(path, worker_id):
    """
    Add a worker suffix before the filename extension.
    """
    if worker_id in (None, ""):
        return path
    root, ext = os.path.splitext(path)
    return "{}_worker{}{}".format(root, worker_id, ext)


def plan_parallel_occupancy_maps(
    occupancy_count,
    map_count_per_occupancy,
    total_cpus=None,
    max_occupancies=0,
):
    """
    Plan concurrent occupancy workers by budgeting one CPU per active map.

    Returns a list of per-occupancy CPU budgets for the active occupancy slots.
    Each active occupancy receives at least one CPU. Remaining CPUs are
    distributed across the active occupancies until each one can run all of its
    map types concurrently or the CPU budget is exhausted.
    """
    try:
        occupancies = int(occupancy_count)
    except (TypeError, ValueError):
        occupancies = 0
    occupancies = max(0, occupancies)
    if occupancies == 0:
        return 0, 0, 0

    try:
        maps_per_occupancy = int(map_count_per_occupancy)
    except (TypeError, ValueError):
        maps_per_occupancy = 0
    maps_per_occupancy = max(1, maps_per_occupancy)

    if total_cpus is None:
        cpus = available_cpu_count()
    else:
        try:
            cpus = int(total_cpus)
        except (TypeError, ValueError):
            cpus = available_cpu_count()
    cpus = max(1, cpus)

    try:
        requested_occupancies = int(max_occupancies)
    except (TypeError, ValueError):
        requested_occupancies = 0

    if requested_occupancies <= 0:
        requested_occupancies = occupancies
    else:
        requested_occupancies = min(occupancies, requested_occupancies)

    occupancy_worker_count = min(requested_occupancies, cpus)
    occupancy_worker_count = max(1, occupancy_worker_count)

    budgets = [1] * occupancy_worker_count
    remaining = cpus - occupancy_worker_count
    while remaining > 0:
        progressed = False
        for index in range(occupancy_worker_count):
            if budgets[index] >= maps_per_occupancy:
                continue
            budgets[index] += 1
            remaining -= 1
            progressed = True
            if remaining == 0:
                break
        if not progressed:
            break

    return budgets
