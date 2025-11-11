# 📦 Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_Features and fixes added since `v0.4.1` milestone._

### 🚀 Added

- **Encryption and Decryption Helpers**
  - Introduced `shared/crypto/encryption_handlers.py` providing:
    - `encrypt_message(session_key: bytes, message: str) -> bytes`
    - `decrypt_message(session_key: bytes, encrypted_message: bytes) -> str`
  - Includes validation and complete secure workflow tests (PSK → hashing → shared secret → encryption → decryption).

- **Protocol-Level Encryption Flow**
  - Updated `protocol.py` to automatically encrypt/decrypt messages when a `session_key` is passed.
  - Introduced wrapper structure for encrypted payloads.

- **Peer-to-Peer Encrypted Messaging**
  - Enabled encrypted tunnel communication between users.
  - Added new input mode `encrypted` and integrated with `send_messages` and `handle_chat_input`.
  - Server now relays encrypted messages without decoding.

- **Token-Based Access System**
  - Added invite-token authentication to secure public servers.
  - Supports single-use, multi-use, bound, and non-expiring tokens.
  - Implemented validation during `process_request` before handler invocation.
  - Added periodic cleanup of expired tokens.

- **Command-Line Enhancements**
  - Added flexible CLI for both server and client:
    - `--host local|public`, `--client single|multiple`, `--invite-token`, `--bind <user1> <user2>`, `--token-count <n>`, `--no-expiry`
  - Added conditional logic and validation (e.g., `--bind` takes precedence over `--token-count`).

- **Port Tunneling Integration**
  - Integrated **Cloudflared** tunnel support directly in Python.
  - Server auto-launches tunnels when `--host public` is passed.
  - Added helper functions and installation instructions for Windows/Linux users.

- **New Commands**
  - `/list_users` — Lists currently connected users.
  - `/help` — Now supports colored text using updated `aprint()`.

### 🧩 UX Improvements

- PSK input now hidden (password mode with asterisks).
- Added color/styling for `safe_input` prompt text.
- Tunnel users no longer see global chat messages while active.
- Upgraded `aprint()` with color tag support for CLI formatting.

### 🛠 Improvements

- Added port argument parsing for both client and server.
- Improved command-line validation and contextual help.
- Revised internal logger to reduce prompt interference.
- Cleaned up project structure for packaging and deployment.

### 🧪 Experimental / 📈 Future

- **Planned / In Progress**
  - Add extended foreground and background color support for `safe_input`.
  - Add runtime server-side input to generate tokens on demand (no restart required).
  - Add `--reuse` flag for token reuse functionality.
  - Tidy server/client logs and improve consistency.
  - Review, clean, and refactor core modules.
  - Explore Android support for mobile client deployment.
  - Future tunneling provider support (Serveo, LocalTunnel).

### 🧰 Internal Notes

- All token and encryption flows manually verified.
- MVP validated as of **2025-11-11**.
- Candidate for **v0.5.0 Beta** release (first major public build).

---

## [v0.4.1] - 2025-09-19

### 🔗 Added support for `/exit_tunnel`

### 📋 Description

- Users can now use `/exit_tunnel` while in a `tunnel_active` state to exit the tunnel. When the command is used by a user, their state gets reset to default and along with them, the server relays the `tunnel_exit` to the peer, which when recieved triggers a `reset_state` on their side, making them exit the tunnel too successfully.

---

## [v0.4] - 2025-08-06

### 🔗 Tunnel-based `/connect @user` System

Implemented an interactive and secure peer-to-peer connection system using pre-shared key (PSK) authentication.

---

### 🚀 New Features

#### Server-side

- **Connection Request Flow**
  - Users initiate connection via `/connect @user`
  - Server relays request to target user

- **Connection Response**
  - Target can accept or deny
  - On accept, triggers tunnel key validation with 10s timeout

- **Tunnel Key Validation**
  - Both users prompted to enter pre-shared key
  - If matched: tunnel is established
  - On mismatch or timeout: users disconnected and temporarily blocked

- **Blocked Usernames**
  - In-memory blocklist used to prevent re-registration after failed tunnel attempts

---

#### Client-side

- **New Commands**
  - `/connect`, `/accept`, `/deny`, `/exit_tunnel`

- **Connection State Handling**
  - Implemented states: `idle`, `request_sent`, `request_received`, `tunnel_validating`, `tunnel_active`

- **PSK Input Prompt**
  - Triggered on tunnel validation request from server
  - 10s timeout for both users

- **Input System Upgrade**
  - Switched to `prompt_toolkit` for real-time input prompt refresh
  - Added `set_input_mode()` for state-based input control

---

#### Command Handler

- Added sync-to-async command execution wrapper
- Improved dynamic command registration

---

### 🛠 Fixes & Improvements

- Fixed PSK input delay due to flushing issue
- Logger patch: used `aprint()` to prevent prompt interference
- Fixed `dict changed during iteration` bug in tunnel validation logic
- Removed `async_io.py`, fully migrated to `prompt_toolkit`

---

### 📝 Internal Notes

- ✅ `connect_request`, `accept`, and tunnel flows manually verified
- [TODO] Write documentation and a blog post summarizing `/connect` feature

---

## [v0.3] - _(No changelog recorded)_

First structured changelog starts from `v0.4`.
