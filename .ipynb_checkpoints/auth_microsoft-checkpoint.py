import os
import secrets
import requests
import streamlit as st
from dotenv import load_dotenv
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import OAuthError
from streamlit_cookies_manager import EncryptedCookieManager

st.session_state["_cookies_saved"] = False

load_dotenv()

CLIENT_ID = os.getenv("AUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH_CLIENT_SECRET")
TENANT_ID = os.getenv("AUTH_TENANT_ID")
REDIRECT_URI = os.getenv("AUTH_REDIRECT_URI")
COOKIE_SECRET = os.getenv("AUTH_SESSION_SECRET")

AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"
SCOPE = ["openid", "email", "profile", "User.Read"]

ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "").strip().lower()
ADMIN_EMAILS = {
    e.strip().lower()
    for e in (os.getenv("ADMIN_EMAILS") or "").split(",")
    if e.strip()
}

def get_cookies():
    if "cookies" in st.session_state:
        return st.session_state["cookies"]

    cookie_secret = os.getenv("AUTH_SESSION_SECRET")
    if not cookie_secret:
        return None

    cookies = EncryptedCookieManager(prefix="myapp_", password=cookie_secret)

    if not cookies.ready():
        return None

    st.session_state["cookies"] = cookies
    return cookies
    
def save_cookies_once(cookies):
    if not st.session_state.get("_cookies_saved"):
        cookies.save()
        st.session_state["_cookies_saved"] = True

def _start_login(oauth: OAuth2Session, prompt=None):
    state = secrets.token_urlsafe(32)
    cookies = get_cookies()
    cookies["oauth_state"] = state
    save_cookies_once(cookies)

    auth_url, _ = oauth.create_authorization_url(
        AUTH_URL,
        state=state,
        prompt=prompt
    )

    st.markdown(
        f"""
        <div style='text-align:left; margin-top:2em;'>
            <a href="{auth_url}" target="_self">
                <button style='
                    background-color:#00AAFF;
                    color:white;
                    padding:0.75em 2em;
                    font-size:1.1em;
                    border:none;
                    border-radius:20px;
                    cursor:pointer;
                '>🪟 Se connecter avec Microsoft</button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

def login_via_microsoft():
    st.session_state["_cookies_saved"] = False

    cookies = get_cookies()
    if cookies is None:
        st.info("Initialisation des cookies… (rafraîchis dans 1s)")
        st.stop()
    
    if not st.session_state.get("authenticated") and cookies.get("authenticated") == "1":
        st.session_state["authenticated"] = True
        st.session_state["email"] = cookies.get("email")
        st.session_state["username"] = cookies.get("username")
        st.session_state["role"] = cookies.get("role") or "user"
        return True

    if st.session_state.get("authenticated"):
        return True

    cookies = get_cookies()

    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )
    
    if "code" in st.query_params:

        code = st.query_params.get("code")
        returned_state = st.query_params.get("state")
        expected_state = cookies.get("oauth_state")

        if st.session_state.get("oauth_code_used") == code:
            st.query_params.clear()
            st.rerun()

        if (not expected_state) or (returned_state != expected_state):
            cookies.pop("oauth_state", None)
            save_cookies_once(cookies)
            st.session_state.pop("oauth_code_used", None)
            st.query_params.clear()
            _start_login(oauth, prompt="select_account")
            return

        st.session_state["oauth_code_used"] = code

        try:
            token = oauth.fetch_token(
                TOKEN_URL,
                code=code,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
            )
        except OAuthError as e:
            st.session_state.pop("oauth_state", None)
            st.session_state.pop("oauth_code_used", None)
            st.query_params.clear()
            _start_login(oauth)

        cookies.pop("oauth_state")
        save_cookies_once(cookies)

        headers = {"Authorization": f"Bearer {token['access_token']}"}
        resp = requests.get(USER_INFO_URL, headers=headers, timeout=10)

        if resp.status_code != 200:
            st.query_params.clear()
            st.error("Erreur d'authentification (Graph).")
            st.stop()

        user_info = resp.json()
        email = (user_info.get("userPrincipalName") or "").lower()
        name = user_info.get("displayName") or email

        if ALLOWED_DOMAIN and not email.endswith("@" + ALLOWED_DOMAIN):
            st.error("Domaine non autorisé")
            st.stop()

        st.session_state["authenticated"] = True
        st.session_state["email"] = email
        st.session_state["username"] = name
        st.session_state["role"] = "admin" if email in ADMIN_EMAILS else "user"

        cookies["authenticated"] = "1"
        cookies["email"] = email
        cookies["username"] = name
        cookies["role"] = st.session_state["role"]
        save_cookies_once(cookies)

        st.session_state.pop("oauth_code_used", None)
        st.query_params.clear()
        st.rerun()

    prompt = "select_account" if st.session_state.pop("force_account_switch", False) else None
    _start_login(oauth, prompt=prompt)

def logout():
    cookies = get_cookies()

    for k in ["oauth_state", "authenticated", "email", "username", "role"]:
        cookies.pop(k, None)

    save_cookies_once(cookies)
    st.query_params.clear()
    st.rerun()

def switch():
    cookies = get_cookies()

    for k in ["oauth_state", "authenticated", "email", "username", "role"]:
        cookies.pop(k, None)

    save_cookies_once(cookies)
    st.session_state["force_account_switch"] = True
    st.query_params.clear()
    st.rerun()