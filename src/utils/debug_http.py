import pdb
import os
from functools import wraps

import httpx

# Tracks whether we've already broken once to avoid stopping repeatedly
_first_break = {"hit": False}

# Hosts filter: set DEBUG_HTTP_HOSTS="host1,host2" to restrict.
# By default, empty set -> no filtering (break on any JSON POST).
_hosts_env = os.environ.get("DEBUG_HTTP_HOSTS", "").strip()
if _hosts_env:
    _PROVIDER_HOSTS = {h.strip() for h in _hosts_env.split(",") if h.strip()}
else:
    _PROVIDER_HOSTS = set()


def _should_break(request: httpx.Request) -> bool:
    if _first_break["hit"]:
        return False
    if request.method.upper() != "POST":
        return False
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        return False
    host = request.url.host or ""
    if _PROVIDER_HOSTS and host not in _PROVIDER_HOSTS:
        return False
    return True


def _wrap_send_async(send_fn):
    @wraps(send_fn)
    async def wrapper(self, request: httpx.Request, *args, **kwargs):  # type: ignore[override]
        if _should_break(request):
            try:
                raw = (request.content or b"").decode("utf-8", errors="ignore")
            except Exception:
                raw = "<un-decodable>"
            print(
                f"\n=== HTTPX FIRST JSON REQUEST ===\n{request.method} {request.url}\nHeaders: {dict(request.headers)}\nBody:\n{raw}\n"
            )
            _first_break["hit"] = True
            pdb.set_trace()
        return await send_fn(self, request, *args, **kwargs)

    return wrapper


def _wrap_send_sync(send_fn):
    @wraps(send_fn)
    def wrapper(self, request: httpx.Request, *args, **kwargs):  # type: ignore[override]
        if _should_break(request):
            try:
                raw = (request.content or b"").decode("utf-8", errors="ignore")
            except Exception:
                raw = "<un-decodable>"
            print(
                f"\n=== HTTPX FIRST JSON REQUEST ===\n{request.method} {request.url}\nHeaders: {dict(request.headers)}\nBody:\n{raw}\n"
            )
            _first_break["hit"] = True
            pdb.set_trace()
        return send_fn(self, request, *args, **kwargs)

    return wrapper


def _try_patch_openai() -> None:
    """Fallback: also patch OpenAI SDK request methods in case httpx patch misses."""
    try:
        from openai._base_client import AsyncAPIClient, SyncAPIClient  # type: ignore
    except Exception:
        return

    # Sync
    if hasattr(SyncAPIClient, "request"):
        orig_sync = SyncAPIClient.request  # type: ignore[attr-defined]
        if getattr(orig_sync, "__wrapped__", None) is None:
            @wraps(orig_sync)
            def sync_wrapper(self, method, path, *args, **kwargs):  # type: ignore[override]
                if not _first_break["hit"]:
                    print(
                        f"\n=== OpenAI Sync request (fallback) ===\n{method} {path}\nKeys: {list(kwargs.keys())}\n"
                    )
                    _first_break["hit"] = True
                    pdb.set_trace()
                return orig_sync(self, method, path, *args, **kwargs)

            SyncAPIClient.request = sync_wrapper  # type: ignore[assignment]

    # Async
    if hasattr(AsyncAPIClient, "request"):
        orig_async = AsyncAPIClient.request  # type: ignore[attr-defined]
        if getattr(orig_async, "__wrapped__", None) is None:
            @wraps(orig_async)
            async def async_wrapper(self, method, path, *args, **kwargs):  # type: ignore[override]
                if not _first_break["hit"]:
                    print(
                        f"\n=== OpenAI Async request (fallback) ===\n{method} {path}\nKeys: {list(kwargs.keys())}\n"
                    )
                    _first_break["hit"] = True
                    pdb.set_trace()
                return await orig_async(self, method, path, *args, **kwargs)

            AsyncAPIClient.request = async_wrapper  # type: ignore[assignment]


def install_httpx_pdb_breakpoint() -> None:
    """Install a pdb breakpoint on the first outbound JSON POST via httpx.

    Idempotent: calling multiple times will not re-wrap methods.
    """
    # Wrap sync client
    if getattr(httpx.Client.send, "__wrapped__", None) is None:
        httpx.Client.send = _wrap_send_sync(httpx.Client.send)  # type: ignore[assignment]
    # Wrap async client
    if getattr(httpx.AsyncClient.send, "__wrapped__", None) is None:
        httpx.AsyncClient.send = _wrap_send_async(httpx.AsyncClient.send)  # type: ignore[assignment]
    # Also patch OpenAI SDK methods as a fallback
    _try_patch_openai() 