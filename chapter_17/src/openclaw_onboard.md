In "~/.openclaw" directory, run command `openclaw onboard --install-daemon`. 

Notice that, do NOT use `homebrew` to install skills like 'gemini` and `github`, 
because `homebrew` will create another `node_modules` by accident, "/home/linuxbrew/.linuxbrew/lib/node_modules/openclaw/dist/", 
in addition to the correct one, "home/robot/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/dist/"

~~~
robot@robot-test:~$ openclaw onboard --install-daemon

🦞 OpenClaw 2026.3.23-2 (7ffe7e4) — iMessage green bubble energy, but for everyone.

▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
██░▄▄▄░██░▄▄░██░▄▄▄██░▀██░██░▄▄▀██░████░▄▄▀██░███░██
██░███░██░▀▀░██░▄▄▄██░█░█░██░█████░████░▀▀░██░█░█░██
██░▀▀▀░██░█████░▀▀▀██░██▄░██░▀▀▄██░▀▀░█░██░██▄▀▄▀▄██
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
                  🦞 OPENCLAW 🦞                    
 
┌  OpenClaw setup
│
◇  Security ─────────────────────────────────────────────────────────────────────────────────╮
│                                                                                            │
│  Security warning — please read.                                                           │
│                                                                                            │
│  OpenClaw is a hobby project and still in beta. Expect sharp edges.                        │
│  By default, OpenClaw is a personal agent: one trusted operator boundary.                  │
│  This bot can read files and run actions if tools are enabled.                             │
│  A bad prompt can trick it into doing unsafe things.                                       │
│                                                                                            │
│  OpenClaw is not a hostile multi-tenant boundary by default.                               │
│  If multiple users can message one tool-enabled agent, they share that delegated tool      │
│  authority.                                                                                │
│                                                                                            │
│  If you’re not comfortable with security hardening and access control, don’t run           │
│  OpenClaw.                                                                                 │
│  Ask someone experienced to help before enabling tools or exposing it to the internet.     │
│                                                                                            │
│  Recommended baseline:                                                                     │
│  - Pairing/allowlists + mention gating.                                                    │
│  - Multi-user/shared inbox: split trust boundaries (separate gateway/credentials, ideally  │
│    separate OS users/hosts).                                                               │
│  - Sandbox + least-privilege tools.                                                        │
│  - Shared inboxes: isolate DM sessions (`session.dmScope: per-channel-peer`) and keep      │
│    tool access minimal.                                                                    │
│  - Keep secrets out of the agent’s reachable filesystem.                                   │
│  - Use the strongest available model for any bot with tools or untrusted inboxes.          │
│                                                                                            │
│  Run regularly:                                                                            │
│  openclaw security audit --deep                                                            │
│  openclaw security audit --fix                                                             │
│                                                                                            │
│  Must read: https://docs.openclaw.ai/gateway/security                                      │
│                                                                                            │
├────────────────────────────────────────────────────────────────────────────────────────────╯
│
◇  I understand this is personal-by-default and shared/multi-user use requires lock-down. Continue?
│  Yes
│
◇  Setup mode
│  Manual
│
◇  What do you want to set up?
│  Local gateway (this machine)
│
◇  Workspace directory
│  /home/robot/.openclaw/workspace
│
◇  Model/auth provider
│  Custom Provider
│
◇  API Base URL
│  https://dashscope.aliyuncs.com/compatible-mode/v1
│
◇  How do you want to provide this API key?
│  Paste API key now
│
◇  API Key (leave blank if not required)
│  sk-80f765b700fb461291067dcadb78bd43
│
◇  Endpoint compatibility
│  OpenAI-compatible
│
◇  Model ID
│  qwen-max
│
◇  Verification successful.
│
◇  Endpoint ID
│  custom-dashscope-aliyuncs-com
│
◇  Model alias (optional)
│  qwen-max
Configured custom provider: custom-dashscope-aliyuncs-com/qwen-max
│
◇  Gateway port
│  18789
│
◇  Gateway bind
│  Loopback (127.0.0.1)
│
◇  Gateway auth
│  Token
│
◇  Tailscale exposure
│  Off
│
◇  How do you want to provide the gateway token?
│  Generate/store plaintext token
│
◇  Gateway token (blank to generate)
│  openclaw_token
│
◇  Channel status ───────────────────╮
│                                    │
│  Telegram: needs token             │
│  Discord: needs token              │
│  IRC: needs host + nick            │
│  Slack: needs tokens               │
│  Signal: needs setup               │
│  signal-cli: missing (signal-cli)  │
│  iMessage: needs setup             │
│  imsg: missing (imsg)              │
│  LINE: needs token + secret        │
│  Accounts: 0                       │
│  WhatsApp: not configured          │
│  Google Chat: not configured       │
│  Feishu: installed                 │
│  Google Chat: installed            │
│  Nostr: installed                  │
│  Microsoft Teams: installed        │
│  Mattermost: installed             │
│  Nextcloud Talk: installed         │
│  Matrix: installed                 │
│  BlueBubbles: installed            │
│  Zalo: installed                   │
│  Zalo Personal: installed          │
│  Synology Chat: installed          │
│  Tlon: installed                   │
│  Twitch: installed                 │
│  WhatsApp: installed               │
│                                    │
├────────────────────────────────────╯
│
◇  Configure chat channels now?
│  No
Updated ~/.openclaw/openclaw.json
Workspace OK: ~/.openclaw/workspace
Sessions OK: ~/.openclaw/agents/main/sessions
│
◇  Web search ─────────────────────────────────────────────────────────────────╮
│                                                                              │
│  Web search lets your agent look things up online.                           │
│  Choose a provider. Some providers need an API key, and some work key-free.  │
│  Docs: https://docs.openclaw.ai/tools/web                                    │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────╯
│
◇  Search provider
│  Skip for now
│
◇  Skills status ─────────────╮
│                             │
│  Eligible: 9                │
│  Missing requirements: 34   │
│  Unsupported on this OS: 7  │
│  Blocked by allowlist: 0    │
│                             │
├─────────────────────────────╯
│
◇  Configure skills now? (recommended)
│  Yes
│
◇  Install missing skill dependencies
│  ✨ gemini, 🐙 github
│
◇  Homebrew recommended ──────────────────────────────────────────────────────────╮
│                                                                                 │
│  Many skill dependencies are shipped via Homebrew.                              │
│  Without brew, you'll need to build from source or download releases manually.  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────╯
│
◇  Show Homebrew install command?
│  No
│
◇  Install failed: gemini — brew not installed — Homebrew is not installed. Install it from https://brew.sh or install "gemini-cli" manually using your system package …
Tip: run `openclaw doctor` to review skills + requirements.
Docs: https://docs.openclaw.ai/skills
│
◇  Install failed: github — brew not installed — Homebrew is not installed. Install it from https://brew.sh or install "gh" manually using your system package manager …
Tip: run `openclaw doctor` to review skills + requirements.
Docs: https://docs.openclaw.ai/skills
│
◇  Set GOOGLE_PLACES_API_KEY for goplaces?
│  No
│
◇  Set NOTION_API_KEY for notion?
│  No
│
◇  Set ELEVENLABS_API_KEY for sag?
│  No
│
◇  Hooks ──────────────────────────────────────────────────────────────────╮
│                                                                          │
│  Hooks let you automate actions when agent commands are issued.          │
│  Example: Save session context to memory when you issue /new or /reset.  │
│                                                                          │
│  Learn more: https://docs.openclaw.ai/automation/hooks                   │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────╯
│
◇  Enable hooks?
│  📝 command-logger
│
◇  Hooks Configured ─────────────────╮
│                                    │
│  Enabled 1 hook: command-logger    │
│                                    │
│  You can manage hooks later with:  │
│    openclaw hooks list             │
│    openclaw hooks enable <name>    │
│    openclaw hooks disable <name>   │
│                                    │
├────────────────────────────────────╯
Config overwrite: /home/robot/.openclaw/openclaw.json (sha256 f3124349079453d3e703770269ee8969e2a400e25471e1e57496c01fe280918f -> 222cb59621fbc2bb26ba5f18f88189da87efa02ae60f81886db03456b01a734d, backup=/home/robot/.openclaw/openclaw.json.bak)
│
◇  Gateway service runtime
│  Node (recommended)
│
◒  Preparing Gateway service…│
◇  Gateway runtime ──────────────────────────────────────────────────────────────────╮
│                                                                                    │
│  System Node 12.22.9 at /usr/bin/node is below the required Node 22.16+. Using     │
│  /home/robot/.nvm/versions/node/v24.14.0/bin/node for the daemon. Install Node 24  │
│  (recommended) or Node 22 LTS from nodejs.org or Homebrew.                         │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────╯
◑  Installing Gateway service…
Installed systemd service: /home/robot/.config/systemd/user/openclaw-gateway.service
◇  Gateway service installed.
│
◇  
Agents: main (default)
Heartbeat interval: 30m (main)
Session store (main): /home/robot/.openclaw/agents/main/sessions/sessions.json (0 entries)
│
◇  Optional apps ────────────────────────╮
│                                        │
│  Add nodes for extra features:         │
│  - macOS app (system + notifications)  │
│  - iOS app (camera/canvas)             │
│  - Android app (camera/canvas)         │
│                                        │
├────────────────────────────────────────╯
│
◇  Control UI ────────────────────────────────────────────────────────╮
│                                                                     │
│  Web UI: http://127.0.0.1:18789/                                    │
│  Web UI (with token): http://127.0.0.1:18789/#token=openclaw_token  │
│  Gateway WS: ws://127.0.0.1:18789                                   │
│  Gateway: reachable                                                 │
│  Docs: https://docs.openclaw.ai/web/control-ui                      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────╯
│
◇  Start TUI (best option!) ─────────────────────────────────╮
│                                                            │
│  This is the defining action that makes your agent you.    │
│  Please take your time.                                    │
│  The more you tell it, the better the experience will be.  │
│  We will send: "Wake up, my friend!"                       │
│                                                            │
├────────────────────────────────────────────────────────────╯
│
◇  Token ────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                            │
│  Gateway token: shared auth for the Gateway + Control UI.                                  │
│  Stored in: ~/.openclaw/openclaw.json (gateway.auth.token) or OPENCLAW_GATEWAY_TOKEN.      │
│  View token: openclaw config get gateway.auth.token                                        │
│  Generate token: openclaw doctor --generate-gateway-token                                  │
│  Web UI keeps dashboard URL tokens in memory for the current tab and strips them from the  │
│  URL after load.                                                                           │
│  Open the dashboard anytime: openclaw dashboard --no-open                                  │
│  If prompted: paste the token into Control UI settings (or use the tokenized dashboard     │
│  URL).                                                                                     │
│                                                                                            │
├────────────────────────────────────────────────────────────────────────────────────────────╯
│
◇  How do you want to hatch your bot?
│  Open the Web UI
│
◇  Dashboard ready ───────────────────────────────────────────────────────────╮
│                                                                             │
│  Dashboard link (with token): http://127.0.0.1:18789/#token=openclaw_token  │
│  Opened in your browser. Keep that tab to control OpenClaw.                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────╯
│
◇  Workspace backup ────────────────────────────────────────╮
│                                                           │
│  Back up your agent workspace.                            │
│  Docs: https://docs.openclaw.ai/concepts/agent-workspace  │
│                                                           │
├───────────────────────────────────────────────────────────╯
│
◇  Security ──────────────────────────────────────────────────────╮
│                                                                 │
│  Running agents on your computer is risky — harden your setup:  │
│  https://docs.openclaw.ai/security                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────╯
│
◇  Web search ──────────────────────────────────────────────────────────╮
│                                                                       │
│  Web search is available via Gemini (Google Search) (auto-detected).  │
│  Docs: https://docs.openclaw.ai/tools/web                             │
│                                                                       │
├───────────────────────────────────────────────────────────────────────╯
│
◇  What now ─────────────────────────────────────────────────────────────╮
│                                                                        │
│  What now: https://openclaw.ai/showcase ("What People Are Building").  │
│                                                                        │
├────────────────────────────────────────────────────────────────────────╯
│
└  Onboarding complete. Dashboard opened; keep that tab to control OpenClaw.

robot@robot-test:~$ 

~~~
