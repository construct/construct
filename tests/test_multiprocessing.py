from tests.declarativeunittest import *
from construct import *
from construct.lib import *

def worker(q):
    obj = q.get()
    print(obj)

def test_multiprocessing():
    import multiprocessing

    queue = multiprocessing.Queue()

    p = multiprocessing.Process(target=worker, args=(queue,))
    p.start()

    obj = Container(name="test")
    print(obj)
    queue.put(obj)

    # Wait for the worker to finish
    queue.close()
    queue.join_thread()
    p.join()
