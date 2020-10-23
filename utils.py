import time


def time_execution(func):
    """ Decorator to get function execution time """

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print('"{}" execution time: {} seconds.'.format(func.__name__, time.time() - start))
        return result

    return wrapper


class TimeExecution:
    """ Context manager to get function execution time """

    def __init__(self, title):
        self.title = title

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        print('"{}" execution time: {} seconds.'.format(self.title, time.time() - self.start))
