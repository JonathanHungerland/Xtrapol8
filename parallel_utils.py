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
