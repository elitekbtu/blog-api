from urllib.parse import urlencode
from rest_framework.request import Request as DRFRequest

def build_posts_cache_key(request: DRFRequest) -> str:
    language = getattr(request, "LANGUAGE_CODE", "en")

    params = request.GET.copy()
    params.pop("lang", None)

    query_string = urlencode(sorted(params.items()))

    return f"published_posts_list:{language}:{query_string}"
