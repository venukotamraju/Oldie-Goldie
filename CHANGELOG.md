# 📦 Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_Features and fixes added since `v0.4` milestone._

### 🚧 Added
- Final feature for tunnel lifecycle (TBD)
- Improvements to PSK input UX and tunnel error handling

### 🐛 Fixed

### 🛠 Improvements

### 🔧 Changed

### 🧪 Experimental
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

## [v0.3] - *(No changelog recorded)*

First structured changelog starts from `v0.4`.
