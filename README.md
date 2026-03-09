# TG-Auth

A personal CLI tool for managing Telegram sessions and storing credentials in Kubernetes secrets.

## Overview

This is a personal project for managing Telegram authentication sessions. It allows me to:
- Login to Telegram and save session credentials as Kubernetes secrets
- Verify existing Telegram sessions stored in Kubernetes
- Manage both user and bot Telegram sessions

## Features

### Commands

- `tg-auth login`: Login to Telegram session and save as Kubernetes secret
- `tg-auth verify`: Verify existing Kubernetes secret for active Telegram session
- `tg-auth logout`: (Not yet implemented)

### How it works

1. **Login Process**:
   - Connects to Telegram using API credentials
   - Creates both user and bot sessions
   - Stores session strings and credentials as Kubernetes secrets in the `default` namespace

2. **Verification Process**:
   - Checks if Telegram sessions stored in Kubernetes are still valid
   - Tests connection to both user and bot sessions
   - Reports connection status

## Requirements

- Python 3.12+
- Kubernetes cluster configured (kubeconfig)
- Telegram API credentials (API ID, API Hash, phone number, bot token)

## Installation

```bash
# Install using pip (from source)
pip install .

# Or using uv
uv pip install .
```

## Usage

```bash
# Login and create Telegram sessions
tg-auth login

# Verify existing sessions
tg-auth verify

# Get help
tg-auth --help
```

## Configuration

The tool stores Telegram credentials as a Kubernetes secret named `tg-auth` with the following fields:
- `TELEGRAM_API_ID`: Your Telegram API ID
- `TELEGRAM_API_HASH`: Your Telegram API Hash
- `TELEGRAM_NUMBER`: Your phone number (with country code)
- `TELEGRAM_SESSION`: User session string
- `TELEGRAM_BOT_TOKEN`: Your bot token
- `TELEGRAM_BOT_SESSION`: Bot session string

## Notes

- This is a personal project tailored for my specific use case
- Requires Kubernetes access and proper RBAC permissions
- Session data is stored as base64-encoded Kubernetes secrets
- The logout functionality is not yet implemented

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests (if any)
# Add your test commands here
```

## License

This is a personal project, no formal license specified.