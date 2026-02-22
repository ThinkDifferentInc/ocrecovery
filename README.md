# ocrecovery 

> **An elegant, user-friendly macOS Recovery Image downloader for Vanilla Hackintoshing.**

`ocrecovery` is a reimagined, accessible way to pull macOS Recovery images directly from Apple's servers. Designed for the OpenCore/Vanilla Hackintosh community, it takes the powerful core logic of traditional command-line scripts and wraps it in a beautiful, interactive Terminal User Interface (TUI). 

No more looking around in the recovery_urls.txt file and copying and pasting. Just run the script, pick your macOS version from the menu, and watch the progress bar go.

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

### Usage

1. Clone or download this repository.
2. Run the script from your terminal:

```bash
python3 ocrecovery.py

```

3. Enter the number corresponding to the macOS version you want to download.
4. The script will create a `com.apple.recovery.boot` folder in your current directory and place the verified `BaseSystem.dmg` and `BaseSystem.chunklist` files inside, ready for your OpenCore USB!

---

## 📸 Preview

![ocrecovery.py showcase](https://github.com/ThinkDifferentInc/ocrecovery/blob/main/preview.png?raw=true)
---

## 📜 Credits & Acknowledgments

This project is built directly upon the foundation of **acidanthera's** official `macrecovery.py` script.

`ocrecovery` simply provides a modernized, interactive frontend and consolidates the workflow. All credit for the reverse-engineering of Apple's recovery servers, chunklist parsing, and cryptographic verification goes to the incredible work done by the Acidanthera team.

* [Acidanthera's macrecovery Project](https://github.com/acidanthera/OpenCorePkg/tree/master/Utilities/macrecovery)

_The project is licensed under the BSD-3-Clause License as acidanthera's OpenCorePkg Repository._
