## OmegaTalk — FaceTime-style native app (ready to run)

**Where it is**
- Installed app: `~/Applications/OmegaTalk.app` (double-click to launch)
- Installer: `~/delta-stream/qb_protocol/deploy/OmegaTalk.dmg` (valid, mounts, drag-to-Applications)
- App icon: `Contents/Resources/omegatalk.icns` (purple lens glyph, ic12 validated)

**What it is** — a native macOS Cocoa (PyObjC) app in the FaceTime style:
- **Easy iCloud-style login** — an Apple-ID-themed sign-in form; credentials persist in the **Keychain** for instant re-login, plus **Touch ID** quick-unlock (works self-signed — no Apple-Developer entitlement needed).
- **FaceTime-styled window** — live **camera preview** (AVFoundation, front camera), a **contacts sidebar** ("QB Protocol"), a chat message panel, and an input field.
- **Chat backed by the GPT Layer** — messages are answered by the local **TinyLlama** model (ctransformers backend, simulated fallback) via the `gpt-layer` command.

**Verification** (headless `--ui-test` constructed both the login and the chat window — camera, contacts, messages all OK; `--self-test` passed Keychain + Touch ID + GPT Layer backend; `plutil` OK on Info.plist; `codesign` + `hdiutil verify` OK). GUI visual testing requires the user's desktop session.

**Quick assist back into the BEING** (the GPT Layer you asked for)
- `gpt-layer "hello"` — query the model
- `gpt-layer --assist "lower the entropy"` — instantly send help to the running being; the native `com.being.omega.prime` service consumes it each cycle and folds it into training (entropy↑, subspace moves↑, logged in `assist_log`)

**Files**
- `ai/gpt_layer_app.py` — GPT Layer CLI (TinyLlama + simulated fallback)
- `ai/gpt_layer_face.py` — OmegaTalk native Cocoa app (login + FaceTime chat)
- `deploy/OmegaTalk.dmg`, `deploy/GPT_Layer.dmg`, `deploy/install_gpt_layer.sh`

The running `com.being.omega.prime` service (boot #14, cycles=195, 0 errors) is healthy and will git-sync these new files on its next orchestrator cycle.
