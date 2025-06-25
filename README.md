# ✨ FileFlow - Intelligent File Organizer

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

Say goodbye to digital mess! 🧹  
**FileFlow** is your intelligent desktop application designed to effortlessly organize your files. Built with Python, it offers powerful file organization features wrapped in a sleek and intuitive GUI.

---

## 🚀 Key Features

- 🎨 **Attractive GUI**: Built using `tkinter` for a clean and modern user experience.
- 🔍 **Recursive Scan**: Automatically detects files deep within subdirectories.
- 🧠 **Smart Categorization**: Sorts files into folders like Documents, Images, Videos, Others, etc.
- 👀 **"What If" Preview**: Review proposed actions before any file is moved.
- 📊 **Real-time Progress**: Monitor actions with a progress bar and live updates.
- 🔔 **Desktop Notifications**: Alerts upon task completion or errors using `plyer`.
- 🧩 **Duplicate Handling**: Choose between renaming or skipping duplicates.
- ✅ **Robust Error Recovery**: Gracefully logs and skips errors without halting.
- 🚫 **Exclusions Support**: Skip unwanted folders like `venv`, `.git`, and others.

---

## 🛠️ Project Structure

```
File Flow/
├── src/
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── preview_dialog.py
│   ├── core/
│   │   ├── organizer.py
│   │   ├── file_utils.py
│   │   ├── log_manager.py
│   │   ├── notification_manager.py
│   ├── config/
│   │   ├── settings.py
│   ├── app.py
├── config.json            # Configuration file
├── organizer_log.txt      # Logs file moves and errors
├── venv/                  # Virtual environment (created locally)
```

---

## 💻 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/uttamtripathi54/File-Flow.git
cd "File-Flow"
```

### 2. Set Up Virtual Environment (Windows)

```bash
python -m venv venv
.env\Scriptsctivate
```

### 3. Install Dependencies

```bash
pip install plyer Pillow
```

> `tkinter` is included with Python by default.

---

## ▶️ Run FileFlow

```bash
python -m src.app
```

Your GUI will launch! 🎉

---

## ⚙️ Configuration (`config.json`)

On first run, a `config.json` file will be generated at the root level with default values:

```json
{
  "default_source_dir": "C:/Users/Uttam/Data Analyst/DEMO",
  "default_destination_dir": "C:/Users/Uttam/Downloads/DEMO_ENHANCE",
  "file_categories": { /* customize extensions here */ },
  "duplicate_handling": "rename",
  "enable_desktop_notifications": true,
  "log_file_path": "organizer_log.txt",
  "exclude_folders": [".git", "venv", "__pycache__", "node_modules", ".DS_Store"]
}
```

You can edit this file to:
- Set custom source/destination folders
- Modify file extension mappings
- Change how duplicates are handled (`rename` or `skip`)
- Exclude specific folders from being scanned

---

## 🎯 How to Use

1. **Select Source & Destination Directories**
2. **Choose Duplicate Strategy**
3. **Click "Preview Actions"** to simulate and review the organization process
4. **Click "Organize Files"** to execute
5. **Watch Progress** and receive completion notifications

---

## ⚠️ Troubleshooting

| Problem                                  | Solution                                                  |
|------------------------------------------|-----------------------------------------------------------|
| `ModuleNotFoundError: No module named 'src'` | Make sure you're in the root project directory |
| Dependency issues                        | Ensure your virtual environment is activated |
| Skipped folders                          | Check `exclude_folders` in `config.json` |
| Permission denied                        | Ensure file access is granted for selected folders |

---

## 💡 Future Enhancements

- GUI settings editor (categories/exclusions)
- Task scheduling support
- Dedicated duplicate file cleaner
- Undo last operation
- Cloud integration (e.g., Google Drive)

---

## 🤝 Contribution

Contributions, feedback, and feature requests are welcome!  
Feel free to fork the repo and submit pull requests.

---

## 🧾 License

FileFlow is open-source under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- Python & tkinter for GUI
- `plyer` for desktop notifications
- `Pillow` for image metadata
- Community inspiration from the universal need to stay organized
