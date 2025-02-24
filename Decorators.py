import json
import time
from functools import wraps

from HANDLERS import LOGHandler


def failures_decorator(function):
    @wraps(function)
    def failures_decorator(*args, **kwargs):
        from HANDLERS.FailureHandler import FailureHandler, Error, Warning
        failureHandler = FailureHandler()
        result = function(*args, **kwargs)
        if type(result) is Error:
            failureHandler.handleError(result, function.__name__)
        if type(result) is dict and 'output' in result and type(result['output']) is Warning \
                and 'warnings' in result:
            failureHandler.handleWarning(result['output'], result['warnings'], function.__name__)
        return result

    return failures_decorator


def log_decorator(function):
    @wraps(function)
    def log_decorator(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        for i in range(0, len(args_repr)):
            if type(args[i]) is dict or type(args[i]) is list:
                args_repr[i] = "\n" + json.dumps(args[i], indent=4) + "\n"
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)

        LOGHandler.logDebug(function.__name__, signature)

        result = function(*args, **kwargs)
        return result

    return log_decorator


def time_decorator(function):
    @wraps(function)
    def time_decorator(*args, **kwargs):
        start = time.perf_counter()
        result = function(*args, **kwargs)
        runtime = time.perf_counter() - start

        LOGHandler.logInfo(function.__name__, runtime, result)

        return result

    return time_decorator
