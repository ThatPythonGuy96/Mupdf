# Mupdf PDF Reader

Mupdf is a desktop PDF reader built with Python, PyQt6, and Qt PDF. It opens multiple documents in one window and displays them in closable tabs.

## Features

- Open one or several PDF files from **File → Open** or from the command line.
- Navigate between pages with the left rail or its page number field.
- Zoom in and out, or fit a page to the available width or height.
- Use the icon toolbar and hover over controls for tooltips.
- Open multiple PDFs in the same window.

## Run from source

From the project folder, install the Python dependencies and launch Mupdf:

```powershell
python -m pip install -r requirements.txt
python mupdf.py
```

You can also open PDFs when launching the app:

```powershell
python mupdf.py "C:\path\to\first.pdf" "C:\path\to\second.pdf"
```

If using the included virtual environment:

```powershell
.\pdfnv\Scripts\Activate.ps1
python mupdf.py
```

## Build the Windows executable

Install PyInstaller in the environment, then build from the included spec file:

```powershell
python -m pip install pyinstaller
pyinstaller mupdf.spec
```

The installer script expects the packaged executable at `dist\Mupdf.exe`.

## Build the Windows installer

Open `Mupdf.iss` with Inno Setup Compiler and compile it after building the executable. Installing Mf registers it as an available PDF app and adds **Open with Mupdf** to the PDF right-click context menu. The installer also creates a Start Menu shortcut; the desktop shortcut is optional.

Uninstalling Mupdf removes the PDF context-menu entry and its app registration.
