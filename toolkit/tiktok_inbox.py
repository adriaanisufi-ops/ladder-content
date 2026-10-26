"""Send finished videos to Adriaan's TikTok inbox as drafts (Content Posting API, Upload).

Runs on GitHub Actions, because the Claude workspace can't reach TikTok.
    python3 toolkit/tiktok_inbox.py connect <auth_code>   one time: trade the login code for tokens
    python3 toolkit/tiktok_inbox.py upload <file.mp4> ...  upload videos as inbox drafts

Env: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, STATE_DIR (folder holding token.enc).
The refresh token is stored encrypted (AES via openssl, passphrase = client secret) in
STATE_DIR/token.enc; the workflow commits it to the `tiktok-state` branch after every run,
because TikTok may rotate the refresh token.
"""
import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

def fail(msg):
    # ::error:: makes the message show up in the run's Annotations box
    print(f"::error::{msg}", flush=True)
    sys.exit(1)


KEY = os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
if not KEY:
    fail("Secret TIKTOK_CLIENT_KEY ontbreekt of is leeg (Settings > Secrets and variables > Actions)")
if not SECRET:
    fail("Secret TIKTOK_CLIENT_SECRET ontbreekt of is leeg (Settings > Secrets and variables > Actions)")
STATE = os.path.join(os.environ.get("STATE_DIR", "state"), "token.enc")
REDIRECT = "https://adriaanisufi-ops.github.io/ladder-content/callback.html"
API = "https://open.tiktokapis.com"


def req(method, url, data=None, headers=None, raw=None):
    h = dict(headers or {})
    body = raw
    if data is not None and raw is None:
        if h.get("Content-Type", "").startswith("application/json"):
            body = json.dumps(data).encode()
        else:
            body = urllib.parse.urlencode(data).encode()
            h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            txt = resp.read().decode() or "{}"
            return resp.status, json.loads(txt) if txt.strip().startswith("{") else {}
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, {"raw": txt[:500]}


def save(tok):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    p = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-pass", "env:TIKTOK_CLIENT_SECRET", "-out", STATE],
                       input=json.dumps(tok).encode(), check=True)


def load():
    out = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-pass", "env:TIKTOK_CLIENT_SECRET", "-in", STATE],
                         capture_output=True, check=True).stdout
    return json.loads(out)


def token_call(extra):
    st, j = req("POST", f"{API}/v2/oauth/token/", dict(client_key=KEY, client_secret=SECRET, **extra))
    if "access_token" not in j:
        fail(f"TikTok weigerde de code ({st}): {j.get('error')} {j.get('error_description')}")
    return {k: j[k] for k in ("access_token", "refresh_token", "open_id", "scope") if k in j}


def connect(code):
    tok = token_call(dict(code=code, grant_type="authorization_code", redirect_uri=REDIRECT))
    save(tok)
    print("connected, scopes:", tok.get("scope"))


def access():
    tok = load()
    new = token_call(dict(grant_type="refresh_token", refresh_token=tok["refresh_token"]))
    tok.update(new)
    save(tok)
    return tok["access_token"]


def upload(path, at):
    size = os.path.getsize(path)
    hdr = {"Authorization": f"Bearer {at}", "Content-Type": "application/json; charset=UTF-8"}
    st, j = req("POST", f"{API}/v2/post/publish/inbox/video/init/",
                {"source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}}, hdr)
    if j.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"init {st}: {j['error']}")
    d = j["data"]
    with open(path, "rb") as f:
        blob = f.read()
    st2, j2 = req("PUT", d["upload_url"], raw=blob, headers={
        "Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}"})
    if st2 not in (200, 201):
        raise RuntimeError(f"upload {st2}: {j2}")
    for _ in range(30):
        time.sleep(5)
        st3, j3 = req("POST", f"{API}/v2/post/publish/status/fetch/", {"publish_id": d["publish_id"]}, hdr)
        s = j3.get("data", {}).get("status")
        if s in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return s
        if s == "FAILED":
            raise RuntimeError(f"failed: {j3['data'].get('fail_reason')}")
    return s or "UNKNOWN"


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "connect":
        connect(args[0].strip())
    elif cmd == "upload":
        at = access()
        bad = 0
        for p in args:
            try:
                print(os.path.basename(p), upload(p, at), flush=True)
            except Exception as e:
                bad += 1
                print(os.path.basename(p), "ERROR", e, flush=True)
            time.sleep(3)
        sys.exit(1 if bad else 0)
