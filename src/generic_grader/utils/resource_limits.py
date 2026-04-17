import os
import _thread
import signal
import sys
import threading
from contextlib import contextmanager

try:
    import resource
except ModuleNotFoundError:  # pragma: no cover - Windows
    resource = None

from generic_grader.utils.exceptions import UserTimeoutError


@contextmanager
def time_limit(seconds):
    """A context manager to limit the execution time of an enclosed block.
    Adapted from https://stackoverflow.com/a/601168
    """

    def timeout_message():
        return f"The time limit for this test is {seconds}" + (
            (seconds == 1 and " second.") or " seconds."
        )

    def handler(signum, frame):
        raise UserTimeoutError(timeout_message())

    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
        return

    timed_out = {"hit": False}

    def interrupt_main_thread():
        timed_out["hit"] = True
        _thread.interrupt_main()

    timer = threading.Timer(seconds, interrupt_main_thread)
    timer.daemon = True
    timer.start()

    try:
        yield
    except KeyboardInterrupt as e:
        if timed_out["hit"]:
            raise UserTimeoutError(timeout_message()) from e
        raise
    finally:
        timer.cancel()


def _get_current_vm_bytes():
    """Return the current virtual memory size of this process in bytes.

    Reads VmSize from /proc/self/status, which represents the total
    virtual address space used by the process.
    """
    proc_path = f"/proc/{os.getpid()}/status"
    if not os.path.exists(proc_path):
        return 0

    with open(proc_path) as f:
        for line in f:
            if line.startswith("VmSize:"):
                return int(line.split()[1]) * 1024  # kB to bytes
    return 0  # pragma: no cover


@contextmanager
def memory_limit(max_gibibytes):
    """A context manager to limit memory usage while running submitted code.

    Sets RLIMIT_AS relative to the current virtual memory usage so that
    the enclosed code gets exactly max_gibibytes of additional address
    space, regardless of how much memory the Python runtime and its
    libraries already consume.
    """
    if resource is None or not hasattr(resource, "RLIMIT_AS"):
        # Windows and some runtimes do not expose address-space limits.
        yield
        return

    GiB = 2**30
    max_bytes = int(max_gibibytes * GiB)
    current_vm = _get_current_vm_bytes()

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (current_vm + max_bytes, hard))
    try:
        yield
    except MemoryError:
        # Restore the previous limits
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
        message = (
            "Your program used more than the maximum allowed memory"
            f" of {max_gibibytes} GiB."
        )
        raise MemoryError(message).with_traceback(sys.exc_info()[2])
    else:
        # Restore the previous limits
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
