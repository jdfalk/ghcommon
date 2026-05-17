#!/usr/bin/env bash
# file: scripts/setup-ci-app.sh
# version: 1.1.0
# guid: 7e4a8c92-3b1f-4e5d-9a2c-6f8e1b3d4a7c
#
# One-shot GitHub App creator for jdfalk CI plumbing.
#
# Drives GitHub's App manifest flow end-to-end:
#   1. Generates an app manifest with the permissions our release workflows need.
#   2. Spins up a localhost callback listener.
#   3. Opens your browser on a page that POSTs the manifest to GitHub.
#   4. You click "Create GitHub App" once. GitHub redirects back to the listener.
#   5. Script exchanges the callback code for App ID + private key.
#   6. Script writes the PEM to ~/.config/github-apps/<slug>.pem (chmod 600).
#   7. Script distributes CI_APP_ID + CI_APP_PRIVATE_KEY to every target repo's secrets.
#   8. Script prints the install URL you'll click once to attach the App to those repos.
#
# After this runs, every workflow just needs:
#     - uses: actions/create-github-app-token@v1
#       with:
#         app-id: ${{ secrets.CI_APP_ID }}
#         private-key: ${{ secrets.CI_APP_PRIVATE_KEY }}
# to mint a short-lived token that can push refs containing workflow-file changes.
#
# Usage:
#     ./setup-ci-app.sh [owner/repo ...]
# If no repos are given, DEFAULT_REPOS below is used.
#
# Environment overrides:
#     APP_NAME       - defaults to 'jdfalk-ci-bot'. Must be globally unique on GitHub.
#     CALLBACK_PORT  - defaults to 8765. Pick another if it's in use.

set -euo pipefail

APP_NAME="${APP_NAME:-jdfalk-ci-bot}"
APP_URL="https://github.com/jdfalk"
CALLBACK_PORT="${CALLBACK_PORT:-8765}"
CALLBACK_PATH="/callback"
STATE=$(openssl rand -hex 16)

DEFAULT_REPOS=(
  jdfalk/audiobook-organizer
  jdfalk/ghcommon
  jdfalk/migrate-loop
  jdfalk/release-go-action
  jdfalk/gha-release-go
  jdfalk/release-frontend-action
  jdfalk/gha-release-frontend
  jdfalk/release-docker-action
  jdfalk/gha-release-docker
)

if [ "$#" -gt 0 ]; then
  REPOS=("$@")
else
  REPOS=("${DEFAULT_REPOS[@]}")
fi

# ─── preflight ──────────────────────────────────────────────────────────────

for bin in gh python3 jq openssl; do
  command -v "$bin" >/dev/null 2>&1 || {
    echo "✗ required binary not found: $bin" >&2
    exit 1
  }
done
gh auth status >/dev/null 2>&1 || {
  echo "✗ gh not authenticated — run 'gh auth login' first" >&2
  exit 1
}

# Fail fast if any target repo is unreachable under current gh auth. Saves
# the user from doing the browser dance just to have distribution fail.
echo "Verifying access to target repos..."
for repo in "${REPOS[@]}"; do
  if ! gh api "repos/$repo" >/dev/null 2>&1; then
    echo "  ✗ No access to $repo (check gh auth scopes)" >&2
    exit 1
  fi
  echo "  ✓ $repo"
done

# Bail if port is already bound.
if lsof -iTCP:"$CALLBACK_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "✗ Port $CALLBACK_PORT is already in use. Set CALLBACK_PORT=<free-port> and re-run." >&2
  exit 1
fi

# ─── manifest ───────────────────────────────────────────────────────────────

MANIFEST=$(jq -n \
  --arg name "$APP_NAME" \
  --arg url "$APP_URL" \
  --arg redirect "http://localhost:${CALLBACK_PORT}${CALLBACK_PATH}" \
  '{
    name: $name,
    url: $url,
    redirect_url: $redirect,
    public: true,
    default_events: [],
    default_permissions: {
      contents: "write",
      workflows: "write",
      metadata: "read",
      actions: "read",
      pull_requests: "write",
      issues: "write"
    }
  }')

# ─── one-shot auto-submit HTML page ─────────────────────────────────────────
# The manifest must be POSTed to github.com/settings/apps/new. Browsers can't
# POST from a plain URL, so we serve a tiny HTML page with a form that
# submits itself.

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

MANIFEST_ESCAPED=$(printf '%s' "$MANIFEST" | jq -c . |
  python3 -c 'import sys,html; print(html.escape(sys.stdin.read(), quote=True))')

cat >"$TMPDIR/go.html" <<EOF
<!doctype html>
<meta charset="utf-8">
<title>Create $APP_NAME</title>
<body onload="document.forms[0].submit()" style="font-family:system-ui;padding:2em">
<p>Submitting manifest to GitHub… if nothing happens, click below:</p>
<form action="https://github.com/settings/apps/new?state=$STATE" method="post">
  <input type="hidden" name="manifest" value="$MANIFEST_ESCAPED">
  <button type="submit">Create GitHub App</button>
</form>
</body>
EOF

# ─── callback listener ──────────────────────────────────────────────────────
# Python one-shot: accepts one request on CALLBACK_PATH, validates state,
# writes the code to $CODE_FILE, returns a success page.

CODE_FILE="$TMPDIR/code.txt"

# The HTML form is served by the localhost server itself (not file://) so that
# browsers allow it to POST to github.com without CSRF/mixed-content issues.
HTML_BODY=$(
  cat <<HTMLEOF
<!doctype html>
<meta charset="utf-8">
<title>Create $APP_NAME</title>
<body onload="document.forms[0].submit()" style="font-family:system-ui;padding:2em">
<p>Submitting manifest to GitHub… if nothing happens, click below:</p>
<form action="https://github.com/settings/apps/new?state=$STATE" method="post">
  <input type="hidden" name="manifest" value="$MANIFEST_ESCAPED">
  <button type="submit">Create GitHub App</button>
</form>
</body>
HTMLEOF
)

python3 - <<PY &
import http.server, urllib.parse, sys

STATE = "$STATE"
RESULT = "$CODE_FILE"
CALLBACK = "$CALLBACK_PATH"
HTML = """$HTML_BODY"""

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path != CALLBACK:
            self.send_response(404); self.end_headers(); return
        q = urllib.parse.parse_qs(u.query)
        code = q.get("code", [""])[0]
        state = q.get("state", [""])[0]
        if state != STATE:
            self.send_response(400); self.end_headers()
            self.wfile.write(b"state mismatch - refusing")
            return
        with open(RESULT, "w") as f: f.write(code)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<!doctype html><meta charset=utf-8><title>Done</title>"
                         b"<body style='font-family:system-ui;padding:2em'>"
                         b"<h1>Done.</h1><p>Return to the terminal.</p></body>")

srv = http.server.HTTPServer(("127.0.0.1", $CALLBACK_PORT), H)
srv.timeout = 300
# Serve root + callback (2 requests max)
srv.handle_request()
srv.handle_request()
PY
SERVER_PID=$!

# Give the listener a moment to bind.
sleep 1

GO_URL="http://localhost:${CALLBACK_PORT}/"

echo
echo "Opening $GO_URL in your default browser..."
echo "(Make sure you're logged into github.com as jdfalk)"
echo

if [ "$(uname -s)" = "Darwin" ]; then
  open "$GO_URL"
else
  xdg-open "$GO_URL" 2>/dev/null || echo "Could not auto-open — visit $GO_URL manually"
fi

# ─── wait for callback ──────────────────────────────────────────────────────

wait "$SERVER_PID" 2>/dev/null || true

CODE=$(cat "$CODE_FILE" 2>/dev/null || true)
if [ -z "$CODE" ]; then
  echo "✗ No callback received within timeout." >&2
  exit 1
fi
echo "✓ Callback received"

# ─── exchange code for App credentials ──────────────────────────────────────

echo "Exchanging code for App credentials..."
CONVERSION=$(gh api -X POST "/app-manifests/$CODE/conversions")

APP_ID=$(jq -r '.id // empty' <<<"$CONVERSION")
PEM=$(jq -r '.pem // empty' <<<"$CONVERSION")
SLUG=$(jq -r '.slug // empty' <<<"$CONVERSION")

if [ -z "$APP_ID" ] || [ -z "$PEM" ] || [ -z "$SLUG" ]; then
  echo "✗ App-manifest conversion failed. Full response:" >&2
  echo "$CONVERSION" >&2
  exit 1
fi

# ─── save PEM locally (never commit) ────────────────────────────────────────

PEM_DIR="$HOME/.config/github-apps"
mkdir -p "$PEM_DIR"
chmod 700 "$PEM_DIR"
PEM_PATH="$PEM_DIR/$SLUG.pem"
printf '%s\n' "$PEM" >"$PEM_PATH"
chmod 600 "$PEM_PATH"

echo "✓ App created: $SLUG (id=$APP_ID)"
echo "✓ Private key saved to $PEM_PATH"

# ─── distribute secrets ─────────────────────────────────────────────────────

echo
echo "Setting CI_APP_ID + CI_APP_PRIVATE_KEY on target repos..."
for repo in "${REPOS[@]}"; do
  gh secret set CI_APP_ID --repo "$repo" --body "$APP_ID" >/dev/null
  gh secret set CI_APP_PRIVATE_KEY --repo "$repo" --body "$PEM" >/dev/null
  echo "  ✓ $repo"
done

# ─── install prompt ─────────────────────────────────────────────────────────
# Programmatic install requires an OAuth user token we don't have, so this
# step stays manual. One click.

cat <<EOF

────────────────────────────────────────
Almost done — one manual step left:

  Open: https://github.com/apps/$SLUG/installations/new

Pick either "All repositories" or these specific repos:
$(printf '  - %s\n' "${REPOS[@]}")

Then click Install. After that, any workflow in those repos can mint a token via:

  - uses: actions/create-github-app-token@v1
    with:
      app-id: \${{ secrets.CI_APP_ID }}
      private-key: \${{ secrets.CI_APP_PRIVATE_KEY }}
────────────────────────────────────────
EOF
