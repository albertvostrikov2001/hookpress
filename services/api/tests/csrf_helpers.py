"""CSRF helpers for cookie-auth API tests."""

from httpx import Cookies, Response


def cookie_auth_from_login(login: Response) -> tuple[dict[str, str], dict[str, str]]:
    refresh = login.cookies.get("hookpress_refresh")
    csrf = login.cookies.get("hookpress_csrf")
    cookies = {"hookpress_refresh": refresh} if refresh else {}
    if csrf:
        cookies["hookpress_csrf"] = csrf
    headers = {"X-CSRF-Token": csrf} if csrf else {}
    return cookies, headers


def merge_cookie_auth(
    login: Response,
    *,
    extra_cookies: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    cookies, headers = cookie_auth_from_login(login)
    if extra_cookies:
        cookies.update(extra_cookies)
    return cookies, headers
