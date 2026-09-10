import streamlit as st
import streamlit.components.v1 as components

COOKIE_NAME = "mk_authtoken"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _cookie_js(value: str, max_age: int) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"""
<script>
(function () {{
  try {{
    window.parent.document.cookie = '{COOKIE_NAME}=' + encodeURIComponent('{escaped}') +
      '; path=/; max-age={max_age}; SameSite=Lax';
  }} catch (e) {{}}
}})();
</script>
"""


def set_persistent_cookie(token: str):
    components.html(_cookie_js(token, COOKIE_MAX_AGE), height=0)


def clear_persistent_cookie():
    components.html(_cookie_js("", 0), height=0)


def auto_login_script():
    components.html("""
<div style="display:none"></div>
<script>
(function () {
  try {
    var host = window.parent;
    var scriptText =
      "(function () {" +
      "try {" +
      "var m = document.cookie.match(/(?:^|; )MK_NAME=([^;]*)/);" +
      "var token = m ? decodeURIComponent(m[1]) : null;" +
      "var p = new URLSearchParams(location.search);" +
      "if (token && !p.has('auto_token')) { p.set('auto_token', token); location.search = p.toString(); }" +
      "else if (!token && p.has('auto_token')) { p.delete('auto_token'); location.search = p.toString(); }" +
      "} catch (e) {}" +
      "})();";
    scriptText = scriptText.replace('MK_NAME', '%s');
    var s = host.document.createElement('script');
    s.textContent = scriptText;
    (host.document.head || host.document.body).appendChild(s);
  } catch (e) {}
})();
</script>
""" % COOKIE_NAME, height=0)