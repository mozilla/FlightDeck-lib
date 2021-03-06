import logging
import os
import sys

config = os.environ.setdefault("CELERY_TEST_CONFIG_MODULE",
                               "celery.tests.config")

os.environ["CELERY_CONFIG_MODULE"] = config
os.environ["CELERY_LOADER"] = "default"


def teardown():
    # Don't want SUBDEBUG log messages at finalization.
    from multiprocessing.util import get_logger
    get_logger().setLevel(logging.WARNING)
    import threading
    import os
    if os.path.exists("test.db"):
        os.remove("test.db")
    remaining_threads = [thread for thread in threading.enumerate()
                            if thread.name != "MainThread"]
    if remaining_threads:
        sys.stderr.write(
            "\n\n**WARNING**: Remaning threads at teardown: %r...\n" % (
                remaining_threads))
