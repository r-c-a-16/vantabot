# 🩸 vanta — PhishBot

A single-file Telegram bot and Flask server designed for automated phishing page management. Built for portability, zero-configuration deployment, and reliable operation across diverse environments.

## 📖 Overview

vanta consolidates the entire application stack — Telegram bot logic, Flask web server, routing, local database, and user interface — into a single, auditable Python file. 

The architecture is intentionally minimal. There are no external databases, no complex state management, and no requirement for container orchestration. The application is designed to run on Android via Termux, on a standard Linux VPS, or on any Python 3.8+ environment.

## ✨ Technical Features

**🎯 Template Engine (22 Platforms)**
Generates unique, shareable URLs mapped to platform-specific landing pages. The routing layer guarantees unique identifiers (UUIDs) and handles page rendering dynamically via Flask.

**📊 Inline Interface**
Administrative controls are managed entirely through Telegram's Inline Keyboard API. This eliminates the need for command memorization and reduces input errors.

**🔔 Asynchronous Alerts**
Data submission triggers a non-blocking Telegram notification thread. This ensures the Flask server responds to the client instantly without waiting for the Telegram API request to complete.

**💾 Atomic Local Storage**
All captured data is stored in a JSON file. Writes are performed atomically (write to temp file, then replace) to prevent database corruption during unexpected shutdowns or power loss.

**⚙️ Runtime Configuration**
Database management, ngrok tunneling, and post-capture redirect destinations can be modified at runtime through the interface without restarting the service or altering the source code.

**⚡ Dependency Minimalism**
The application relies on exactly three standard libraries: `flask`, `requests`, and `pyngrok`. The single-file structure ensures that auditing, modifying, and deploying the code requires minimal overhead.