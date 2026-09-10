import os
from typing import Optional

try:
    from supabase import create_client, Client  # type: ignore
except ImportError:
    create_client = None  # type: ignore
    Client = None  # type: ignore

from dotenv import load_dotenv

# Load .env from project root (one level above database/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
# also try default cwd
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://obvqgqevyliacsfuiovp.supabase.co")
# Support both SUPABASE_KEY and SUPABASE_ANON_KEY
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

_client: Optional["Client"] = None


def get_supabase_client() -> Optional["Client"]:
    """Return a Supabase client if configured, else None. Safe to call even when offline."""
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if create_client is None:
        # supabase not installed (should be in requirements.txt)
        return None
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except Exception:
        return None


def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def test_supabase_connection() -> dict:
    """Lightweight test — tries to list tables via a simple query. Returns status dict."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "Supabase not configured or supabase package not installed"}
    try:
        # Try a simple query on a known table; if tables don't exist yet, still confirms auth
        # Use rpc or just list from a table that should exist after migration
        result = client.table("users").select("id").limit(1).execute()
        return {"success": True, "message": f"Connected to {SUPABASE_URL}", "data": str(result.data)[:200]}
    except Exception as e:
        # If table doesn't exist, that's okay — connection still works, just needs schema creation
        err = str(e)
        if "does not exist" in err or "relation" in err:
            return {"success": True, "message": f"Connected to {SUPABASE_URL} (tables not yet created — run schema.sql in Supabase SQL editor)", "warning": err}
        return {"success": False, "error": err}
