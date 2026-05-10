# FontFlow Studio

**Professional Font Family Curation Tool**

> *"Flow is sacred. State is persistent. Decisions are reversible."*

---

## What is FontFlow?

FontFlow is a **desktop application** for designers, type foundries, and creative studios who need to organize massive font libraries. 

**Keyboard-driven. Persian-ready. Crash-proof.**

Stop dragging files manually. Start curating at the speed of thought.

---

## Quick Start

### 1. Install Python 3.11+

```bash
python --version
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run FontFlow

```bash
python main.py
```

### 4. Select Your Font Library

- Click "Select Font Library Folder"
- Choose folder with `.ttf`, `.otf`, `.woff2` files
- Watch the magic happen ✨

---

## What Makes FontFlow Special?

### Blazing Fast
| Before | After |
|--------|-------|
| 3 minutes to scan 18k fonts | **3 seconds** |
| 500MB RAM usage | **20MB** |

### ⌨️ Keyboard-First Workflow

```
1-9, 0    → Classify into categories
Space     → Skip current font
/         → Mark as uncertain (moves to REVIEW_LATER)
←/→       → Navigate families
↑/↓       → Manual style cycle
Ctrl+Z/Y  → Undo/Redo
[/]       → Adjust auto-cycle speed
```

**All shortcuts fully customizable with Ctrl+K!**

### Persian & RTL Support

- Proper letter reshaping (گ پ چ ژ)
- Right-to-left text rendering
- Bidirectional text handling
- Persian stress test mode

### Crash-Proof

- **Write-ahead logging** – every operation is tracked
- **Atomic file moves** – all or nothing
- **Automatic rollback** on failure
- **Recycle bin integration** – no permanent deletes
- **Session auto-save** every 30 seconds

### Special Modes

| Mode | Shortcut | What It Does |
|------|----------|--------------|
| Weight Stress Test | `W` | Shows H1/Body/UI simultaneously |
| Logo Test | `L` | Centered brand evaluation |
| Persian Stress | `P` | Cycles through demanding samples |
| Comparison | `C` | Side-by-side font viewing |

### Search & Export

- **Real-time search** – name, language, weight, status
- **HTML reports** – professional classification summaries
- **Statistics** – track your progress

---

## What FontFlow Does With Your Files

### Before
```
YourFontLibrary/
├── Montserrat-Regular.ttf
├── Montserrat-Bold.ttf
├── Inter-Regular.otf
├── Inter-Bold.otf
└── [5000 more messy files]
```

### After
```
YourFontLibrary/
├── 01_Sans_Modern/
│   ├── A_Favorite/
│   │   └── Montserrat/
│   ├── B_Primary/
│   │   └── Inter/
│   └── C_Secondary/
├── 02_Sans_Classic/
├── 03_Serif_Editorial/
├── 04_Serif_Display/
├── 05_Display_Geometric/
├── 06_Display_Decorative/
├── 07_Script/
├── 08_Monospace/
├── 09_Arabic_Persian/
├── 10_Experimental/
└── REVIEW_LATER/
```

**Fully customizable categories in `config.yaml`!**

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Windows 10/11, macOS, Linux |
| Python | 3.11+ |
| RAM | 512MB (2GB+ recommended for 10k+ fonts) |
| Disk | 50MB for app + space for fonts |

---

## Configuration

Edit `config.yaml` to customize:

### Categories (Stage A)
```yaml
categories:
  "1":
    name: "Sans Serif - Modern"
    folder: "01_Sans_Modern"
    color: "#00ff88"
```

### Subcategories (Stage B)
```yaml
subcategories:
  "1":
    name: "⭐ Favorite - Use Often"
    folder: "A_Favorite"
```

### Keyboard Shortcuts
Edit `keyboard` section in `config.yaml` or press `Ctrl+K` in the app!

---

## Keyboard Shortcut Reference

| Category | Shortcut | Action |
|----------|----------|--------|
| **Classification** | `1-9, 0` | Primary categories |
| | `Space` | Skip |
| | `/` | Uncertain → REVIEW_LATER |
| **Navigation** | `←/→` | Prev/Next family |
| | `↑/↓` | Manual style cycle |
| **Undo/Redo** | `Ctrl+Z` | Undo |
| | `Ctrl+Y` | Redo |
| **Speed** | `[` | Slow down |
| | `]` | Speed up |
| **Zoom** | `Ctrl+Scroll` | Zoom in/out |
| | `Ctrl+0` | Reset zoom |
| **Modes** | `C` | Comparison |
| | `W` | Weight test |
| | `L` | Logo test |
| | `P` | Persian stress |
| **Settings** | `Ctrl+L` | Language selector |
| | `Ctrl+K` | Shortcut editor |
| | `Ctrl+F` | Search |
| | `Ctrl+E` | Export report |
| | `F1` | Help |

---

## Troubleshooting

### "No fonts found"
- Make sure folder contains `.ttf`, `.otf`, or `.woff2` files
- Check file permissions

### WOFF2 errors
```bash
pip install brotli
```

### Persian text not showing correctly
```bash
pip install arabic-reshaper python-bidi
```

### App won't start
- Python 3.11+ required
- Run `pip install -r requirements.txt`

---

## Project Structure

```
fontflow/
├── main.py                 ← RUN THIS!
├── config.yaml            ← Edit categories here
├── requirements.txt       ← Dependencies
│
├── core/                  ← Core logic
│   ├── engine.py          ← Main controller
│   ├── fast_library.py    ← Lazy loading (3 sec scan!)
│   └── session.py         ← Session persistence
│
├── models/                ← Data structures
│   ├── font_family.py     ← FontFamily & FontStyle
│   └── classification.py  ← Categories & undo/redo
│
├── ui/                    ← User interface
│   ├── main_window.py     ← Keyboard handling
│   ├── preview_panel.py   ← Preview + HUD + zoom
│   ├── search_panel.py    ← Search & filter
│   ├── shortcut_editor.py ← Custom shortcuts
│   └── theme.py           ← Dark theme
│
├── utils/                 ← Utilities
│   ├── font_loader.py     ← Real font loading
│   ├── file_ops.py        ← Atomic file moves
│   ├── logger.py          ← JSONL logging
│   ├── transaction_manager.py ← Crash recovery
│   └── report_generator.py ← HTML export
│
└── data/                  ← Runtime data
    ├── sessions/          ← Auto-saved progress
    ├── logs/              ← Audit trail
    └── transactions/      ← Crash recovery logs
```

---

## Built With

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core language |
| **PyQt6** | UI framework |
| **fontTools** | Font metadata parsing |
| **arabic-reshaper** | Persian letter shaping |
| **send2trash** | Recycle bin integration |

---

## Roadmap

### v1.0 (Current)
- Lazy loading (3 sec for 18k fonts)
- Auto-cycling preview
- Two-stage classification
- Undo/redo system
- Persian/RTL support
- Crash recovery with transactions
- Keyboard shortcut editor
- Search & filter
- HTML export reports

### v1.1 (Planned)
- Statistics dashboard (charts & graphs)
- Font subset preview (Unicode ranges)
- Batch operations
- PDF export
- Dark/light theme toggle

---

## Contributing

FontFlow is open source! Contributions welcome:

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/mh3nj/fontflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mh3nj/fontflow/discussions)

---

## Credits

- **FontBase** – for being the best font manager, inspiring this organizer
- **PyQt6 team** – for cross-platform UI
- **fontTools team** – for metadata parsing
- **arabic-reshaper** – for Persian text support

---

## Author

**Mohsen Jafari** - Creator, Developer, Designer

- GitHub: [mh3nj](https://github.com/mh3nj)
- LinkedIn: [mh3nj](https://linkedin.com/in/mh3nj)
- Websites: [Parsegan.com](https://parsegan.com) (logo design), [Dahgan.com](https://dahgan.com) (land surveying/portfolio)

---

## Final Words

> *"I had 18,000 fonts scattered across folders. Some were duplicates. Many were lost. Most were unorganized. FontFlow gave me back control."*

Every keyboard shortcut. Every Persian letter. Every atomic file move. Every auto-cycle.

**Your fonts are finally organized. <3**

---

*Made during internet restrictions in Iran – January to May 2026*  
*No cloud needed. No tracking. Just your fonts and your flow. ;D*

---

**FontFlow Studio v1.0 – "Flow is sacred" Edition**  
*Keyboard-driven. Persian-ready. Crash-proof. Forever offline. ;D*
