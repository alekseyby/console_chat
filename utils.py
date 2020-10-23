import time


def timer(func):
    """ Decorator to get function execution time """
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        end = time.time()
        print('"{}" execution time: {} seconds.'.format(func.__name__, end - start))
        return res
    return wrapper
