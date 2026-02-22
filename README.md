# ocrecovery

> **An elegant, user-friendly macOS Recovery Image downloader for Vanilla Hackintoshing.**

`ocrecovery` is a reimagined, accessible way to pull macOS Recovery images directly from Apple's servers. Designed for the OpenCore/Vanilla Hackintosh community, it takes the powerful core logic of traditional command-line scripts and wraps it in a beautiful, interactive Terminal User Interface (TUI). 

No more searching for the recovery_urls.txt file and copying and pasting. Just run the script, pick your macOS version from the menu, and watch the progress bar.

---

## ✨ Features

* **Interactive Menu:** Select your desired macOS version (from Lion to Tahoe) from a clean, numbered list.
* **Beautiful UI:** Powered by the `rich` Python library, featuring real-time download speeds, accurate byte tracking, and visual ETA.
* **Automatic Verification:** Seamlessly verifies chunklist hashes with a clean visual spinner to ensure your `.dmg` isn't corrupted.
* **Cross-Platform:** Runs natively via Python on Windows, macOS, and Linux.

## 🚀 Getting Started

### Prerequisites

You need Python 3 installed on your system, along with the `rich` library for the terminal UI.

```bash
pip install rich
```
