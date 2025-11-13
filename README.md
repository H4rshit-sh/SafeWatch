# 🛡️ SafeWatch: Content safety moniter

In today's digital world, protecting children, families, and online communities from harmful content is a constant, overwhelming challenge. Every new file uploaded to a forum, school server, or family computer is a potential risk.

**SafeWatch is a real-life problem solver designed to be your first line of defense.**

It's an intelligent, automated system that stands guard over your specified folders. When a new file appears, SafeWatch instantly analyzes its content for a wide range of harmful categories. It then logs every file and presents all dangerous items in a simple web dashboard, creating an immediate review queue for a human moderator.

This process ensures that harmful content is identified the moment it arrives, creating a safer digital environment for everyone.


## ❓ How SafeWatch Solves The Problem

Imagine a school's homework submission portal or a community forum. When a user uploads a new file (a profile picture, a PDF, etc.), SafeWatch instantly intervenes:

1.  👁️ **Detects:** The file is immediately detected by the **File Watcher**.
2.  🤖 **Scans:** The **AI Scanner** analyzes the file's content (both text and pixels) against 17+ categories of unsafe content, including violence, gore, hate speech, and self-harm.
3.  🗃️ **Logs:** The result (e.g., "safe" or "danger") is logged to a secure **Database**.
4.  🔔 **Alerts:** If "danger," the file instantly appears on the **SafeWatch Dashboard**, where a human moderator can review it and take action.

This automated process ensures that harmful content is caught *before* it can spread, all while keeping a human in the loop for final decisions.

---

## ✨ Core Features

* **Real-Time Monitoring:** Actively guards a folder (and its subfolders). Any new or modified file is scanned the moment it appears.
* 🧠 **Intelligent AI Analysis:** Scans text within documents (`.pdf`, `.docx`, `.txt`) and the content of images (`.jpg`, `.png`) for harmful material.
* 🕊️ **Flexible Zero-Shot AI:** Our system uses advanced zero-shot models (`CLIP` and `BART`). This means you can add *new* violation categories (e.g., "cyberbullying") just by adding a word to a list, all without retraining the AI.
* 🧾 **Structured Audit Log:** Every scan (safe or danger) is recorded in a secure SQLite database, creating a complete audit trail for moderation.
* 📋 **Moderator Review Queue:** A simple, clean web dashboard that shows all flagged "danger" items, with the most recent at the top. Safe files are logged but don't clutter the queue.
* 🖱️ **One-Click Moderation:** Review an item on the dashboard and click "Mark as Reviewed" to update its status instantly without a page reload.

---

## ⚙️ How It Works: System Architecture

The project is broken into several modular components that work in sequence:

1.  **`watcher.py` (The Watcher)** 👀
    * The main entry point (`python watcher.py`).
    * Uses `watchdog` to monitor the target folder.
    * Handles `on_created` and `on_modified` events.
    * Implements a 3-second "debounce" logic to prevent re-scanning files as they are being saved.
    * Calls `scanner.py` for every new/modified file.
    * Calls `log_manager.py` to save the results.
    * Calls `log_manager.py` to delete logs when files are deleted.

2.  **`scanner.py` (The AI Engine)** 🧠
    * Contains the core `scan_files(file_path)` function.
    * **Text Moderation:** Uses `facebook/bart-large-mnli` (a zero-shot text classifier) to check text chunks against the `VIOLATION_LABELS` list.
    * **Image Moderation:** Uses `openai/clip-vit-base-patch32` (the CLIP model) for zero-shot image classification.
    * **Multi-Label Logic:** Crucially, this script uses `.sigmoid()` (not `softmax`) on the model's outputs. This provides an independent 0.0-1.0 probability for *every* label, allowing it to detect multiple violations (e.g., "violence" AND "weapon").
    * **Top-K Results:** Returns only the **Top 3** violations that also pass a minimum confidence threshold, providing a clean, relevant list.

3.  **`log_manager.py` (The Database Interface)** 💾
    * Handles all `sqlite3` database operations.
    * `init_db()`: Creates the `safewatch_db.sqlite` file and the `scan_log` table.
    * `log_scan()`: Writes a new scan result to the database.
    * `delete_logs()`: Removes a log entry when the file is deleted.
    * `get_all_logs()`, `mark_as_reviewed()`: Provides functions for the Flask dashboard to read and update data.

4.  **`dashboard.py` (The Web Server)** 🖥️
    * A `Flask` application that serves the web UI.
    * `/`: The main route that renders the dashboard.
    * `/api/logs`: An API endpoint that provides all