from django.conf import settings
from django.utils import translation
from django.utils.translation import get_language_from_request


class LanguageMiddleware:
    """
    Resolves the active language for every request using four sources
    in priority order:

    1. Authenticated user's ``preferred_language`` profile field.
    2. ``?lang=`` query parameter.
    3. ``Accept-Language`` request header (parsed by Django).
    4. ``LANGUAGE_CODE`` from settings (fallback).

    The resolved language is activated for the full request/response
    cycle and advertised via the ``Content-Language`` response header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = self._resolve_language(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)

        response["Content-Language"] = language
        return response

    def _resolve_language(self, request) -> str:
        supported: set[str] = {code for code, _ in settings.LANGUAGES}

        if hasattr(request, "user") and request.user.is_authenticated:
            user_lang = getattr(request.user, "preferred_language", None)
            if user_lang and user_lang in supported:
                return user_lang
            
        lang_param = request.GET.get("lang", "").strip()
        if lang_param and lang_param in supported:
            return lang_param

        header_lang = get_language_from_request(request)
        if header_lang and header_lang in supported:
            return header_lang
        
        return settings.LANGUAGE_CODE
