# Discord Chat Overlay

A lightweight overlay application built with **Python** and **PyQt5** that connects to a Discord channel and displays recent messages in a small always-on-top window. It also allows sending text and file attachments directly to the configured Discord channel.

## Features
- Display recent messages from a specific Discord channel (live).
- Send messages from the overlay UI.
- Attach and upload files (images, audio, etc.) to the Discord channel.
- Always-on-top, small and draggable overlay — suited for gaming or streaming.
- Scrollable message area (keeps overlay size fixed).

## Quick Start

### Prerequisites
- Python 3.8+ installed
- Discord bot with `MESSAGE CONTENT INTENT` enabled and invited to the server/channel

### Install
1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USER/YOUR_REPO.git
   cd YOUR_REPO
