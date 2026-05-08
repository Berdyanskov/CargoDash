"""Bounded thread-safe queue between modules.

stdlib `queue.Queue` already gives us blocking get/put + maxsize-based
backpressure + thread safety, which is exactly what streaming nodes need.
A custom ring-buffer would work in a single-threaded toy, but breaks the
moment two modules run concurrently.
"""
from queue import Queue


def make_stream_queue(maxsize: int = 16) -> Queue:
    return Queue(maxsize=maxsize)


# Sentinel pushed by an upstream node when it has no more output on a port.
# A downstream that has received SENTINEL from every upstream knows it can
# close its own outputs.
SENTINEL = object()
