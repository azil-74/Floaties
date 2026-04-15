# Floaties 📝

Floaties is a secure, minimalist sticky note application built for Linux and Windows. It focuses on privacy, local-first data ownership, and a distraction-free user experience.

## ✨ Key Features
* **Encryption by Default**: Uses Argon2id and AES-256 (via Fernet) to secure your notes in a local vault.
* **Minimalist UI**: Modern, frameless windows built with PyQt6.
* **Local Atomic Storage**: Powered by SQLite with a thread-safe persistence engine.
* **Smart Persistence**: Automatically saves window position, size, and states.

## 🚀 Getting Started

### Installation (Ubuntu Snap)
If you are on Ubuntu, you can install Floaties directly from the Snap Store:
`sudo snap install floaties`

### Manual Build
If you'd like to run from source locally, ensure you have Python 3.12+ and the dependencies installed:
`pip install -r requirements.txt`
`python main.py`

## 🛡️ Security Architecture
* **KDF**: Argon2id for memory-hard key derivation.
* **Storage**: Encrypted bytearrays in a local SQLite database.
* **Memory Protection**: Utilizes OS-level pinning to prevent sensitive data from paging to disk.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/azil-74/floaties/blob/main/LICENSE) file for details.
