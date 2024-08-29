import time
from functools import wraps

from loguru import logger

from HANDLERS import FILEHandler as fHandler
from HANDLERS.ERRORHandler import ErrorHandler, Error


def error_decorator(function):
    @wraps(function)
    def error_decorator(*args, **kwargs):
        result = function(*args, **kwargs)
        if type(result) is Error:
            ErrorHandler().handleError(result, function.__name__)
        return result

    return error_decorator


def log_decorator(function):
    @wraps(function)
    def log_decorator(*args, **kwargs):
        # args_repr = [repr(a) for a in args]
        # kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        # signature = ", ".join(args_repr + kwargs_repr)
        logger.debug(f">> {function.__name__}()")
        result = function(*args, **kwargs)
        return result

    return log_decorator


def time_decorator(function):
    @wraps(function)
    def time_decorator(*args, **kwargs):
        start = time.perf_counter()
        result = function(*args, **kwargs)
        runtime = time.perf_counter() - start
        logger.debug(f"<< {function.__name__}(): {runtime:.10f}")
        return result

    return time_decorator
