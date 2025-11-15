# 💬 Usage Guide

> full CLI options + examples

## Running a Server

### Local Server

```bash
og-server --host local
```

### Public (via Cloudflared Tunnel)

```bash
og-server --host public
```

### Invite-Protected

```bash
og-server --host public --invite-token --token-count 2
```

### Bound Token Mode

```bash
og-server --host public --invite-token --bind alice bob
```

## Running a Client

### Local

```bash
og-client --server-host local
```

### Remote

```bash
og-client --server-host public --url <server-url>
```

### Remote with Token

```bash
og-client --server-host public --url <server-url> --token <token>
```

## Typical Flow

1. Server owner starts server

2. Shares URL and token (optional) with a peer

3. User registers using their pseudonym

4. Use `/list_users` to discover each other

5. Request connection via `/connect @username`

6. Both parties enter the pre-shared key

7. If both match → secure tunnel opens

8. If mismatch → session terminates and blocks usernames
