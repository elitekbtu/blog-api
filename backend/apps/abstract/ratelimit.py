# Python modules
import time
from functools import wraps

# Django modules
from django.core.cache import cache

# Third-party modules
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_429_TOO_MANY_REQUESTS


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def ratelimit(key_func, rate, method="ALL"):

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if method != "ALL" and request.method != method:
                return func(self, request, *args, **kwargs)
            num_requests, period = rate.split("/")
            num_requests = int(num_requests)
            period_mapping = {
                "s": 1,
                "m": 60,
                "h": 3600,
                "d": 86400,
            }
            period_seconds = period_mapping.get(period, 60)

            key_suffix = key_func(request)
            cache_key = f"ratelimit:{func.__name__}:{key_suffix}"

            current_time = int(time.time())
            data = cache.get(cache_key, {"count": 0, "start_time": current_time})

            if current_time - data["start_time"] >= period_seconds:
                data = {"count": 1, "start_time": current_time}
                cache.set(cache_key, data, period_seconds)
                return func(self, request, *args, **kwargs)

            if data["count"] < num_requests:
                data["count"] += 1
                remaining_time = period_seconds - (current_time - data["start_time"])
                cache.set(cache_key, data, remaining_time)
                return func(self, request, *args, **kwargs)

            return DRFResponse(
                data={"detail": "Too many requests. Try again later."},
                status=HTTP_429_TOO_MANY_REQUESTS,
            )

        return wrapper

    return decorator
