import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent, QSize, QPointF
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QSpinBox, QTabWidget, QToolButton, QVBoxLayout, QWidget, QSplashScreen
)


APP_DIR = Path(__file__).resolve().parent
ICON_DIR = APP_DIR / "icons"


class PdfTab(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = Path(path).resolve()
        self.document = QPdfDocument(self)
        self.viewer = QPdfView(self)
        self.viewer.setDocument(self.document)
        self.viewer.setPageMode(QPdfView.PageMode.SinglePage)
        self.viewer.setZoomMode(QPdfView.ZoomMode.FitInView)
        self.fit_mode = "page"
        self._build_ui()
        self.document.statusChanged.connect(self.on_status_changed)
        self.viewer.pageNavigator().currentPageChanged.connect(self.on_current_page_changed)
        self.viewer.viewport().installEventFilter(self)
        self.document.load(str(self.path))

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_toolbar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(78)
        self.sidebar.setObjectName("navigationRail")
        rail = QVBoxLayout(self.sidebar)
        rail.setContentsMargins(8, 12, 8, 10)
        rail.setSpacing(7)

        self.rail_toggle = self.make_icon_button("sidebar.png", "Toggle navigation panel", self.toggle_sidebar)
        rail.addWidget(self.rail_toggle, alignment=Qt.AlignmentFlag.AlignHCenter)
        rail.addSpacing(5)
        self.add_rail_button(rail, "previous.png", "Previous page", self.previous_page)
        self.page_number = QSpinBox()
        self.page_number.setRange(1, 1)
        self.page_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_number.setButtonSymbols(self.page_number.ButtonSymbols.NoButtons)
        self.page_number.setFixedHeight(34)
        self.page_number.setToolTip("Current page number")
        self.page_number.valueChanged.connect(self.go_to_page)
        rail.addWidget(self.page_number)
        self.page_count = QLabel("/ 1")
        self.page_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_count.setObjectName("pageCount")
        rail.addWidget(self.page_count)
        self.add_rail_button(rail, "next.png", "Next page", self.next_page)
        rail.addSpacing(5)
        self.add_rail_button(rail, "zoom-in.png", "Zoom in", self.zoom_in)
        self.zoom_status = QLabel("100%")
        self.zoom_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_status.setObjectName("zoomStatus")
        rail.addWidget(self.zoom_status)
        self.add_rail_button(rail, "zoom-out.png", "Zoom out", self.zoom_out)
        rail.addSpacing(7)
        self.add_rail_button(rail, "horizontal-fit.png", "Toggle full screen", self.toggle_fullscreen)
        self.add_rail_button(rail, "horizontal-fit.png", "Fit page to width", self.fit_width)
        self.add_rail_button(rail, "vertical-fit.png", "Fit page to height", self.fit_height)
        rail.addStretch(1)
        self.add_rail_button(rail, "rotate-right.png", "Rotate page clockwise", self.rotate_page)

        self.canvas = QWidget()
        self.canvas.setObjectName("pdfCanvas")
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.viewer)
        body.addWidget(self.sidebar)
        body.addWidget(self.canvas, 1)
        root.addLayout(body, 1)

    def _build_toolbar(self):
        bar = QWidget()
        bar.setObjectName("documentToolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(6)
        self.add_toolbar_button(layout, "sidebar.png", "Toggle navigation panel", self.toggle_sidebar)
        self.add_toolbar_button(layout, "plus.png", "Open PDF files", self.open_files)
        self.add_toolbar_button(layout, "save.png", "Save a copy of this PDF", self.save_copy)
        self.add_toolbar_button(layout, "print.png", "Print PDF", self.print_pdf)
        layout.addWidget(self.separator())
        self.add_toolbar_button(layout, "text-size.png", "Text selection tool", self.select_text)
        self.add_toolbar_button(layout, "arrows.png", "Pan tool", self.pan_tool)
        self.add_toolbar_button(layout, "highlighter-line.png", "Highlight tool", self.highlight_tool)
        layout.addStretch(1)
        self.add_toolbar_button(layout, "search.png", "Search in document", self.search_document)
        self.add_toolbar_button(layout, "horizontal-fit.png", "Toggle full screen", self.toggle_fullscreen)
        self.add_toolbar_button(layout, "settings.png", "Reader settings", self.show_settings)
        return bar

    @staticmethod
    def separator():
        line = QWidget()
        line.setObjectName("toolSeparator")
        line.setFixedSize(1, 26)
        return line

    def make_icon_button(self, icon_name, tooltip, callback, size=30):
        button = QToolButton()
        button.setIcon(QIcon(str(ICON_DIR / icon_name)))
        button.setIconSize(QSize(20, 20))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setFixedSize(size + 12, size + 8)
        button.clicked.connect(callback)
        return button

    def add_rail_button(self, layout, icon_name, tooltip, callback):
        layout.addWidget(self.make_icon_button(icon_name, tooltip, callback), alignment=Qt.AlignmentFlag.AlignHCenter)

    def add_toolbar_button(self, layout, icon_name, tooltip, callback):
        layout.addWidget(self.make_icon_button(icon_name, tooltip, callback, size=28))

    def on_status_changed(self, status):
        if status == QPdfDocument.Status.Ready:
            pages = max(1, self.document.pageCount())
            self.page_number.setRange(1, pages)
            self.page_count.setText(f"/ {pages}")
            self.fit_page()
        elif status == QPdfDocument.Status.Error:
            QMessageBox.critical(self, "PDF error", f"Could not open:\n{self.path}")

    def on_current_page_changed(self, page):
        self.page_number.blockSignals(True)
        self.page_number.setValue(page + 1)
        self.page_number.blockSignals(False)
        if self.fit_mode == "height":
            self.fit_height()
        elif self.fit_mode == "width":
            self.fit_width()

    def go_to_page(self, number):
        self.viewer.pageNavigator().jump(number - 1, QPointF(0, 0))

    def previous_page(self):
        self.page_number.setValue(max(1, self.page_number.value() - 1))

    def next_page(self):
        self.page_number.setValue(min(self.page_number.maximum(), self.page_number.value() + 1))

    def zoom_in(self):
        self.fit_mode = "custom"
        self.viewer.setZoomMode(QPdfView.ZoomMode.Custom)
        self.viewer.setZoomFactor(min(5.0, self.viewer.zoomFactor() * 1.2))
        self.show_zoom()

    def zoom_out(self):
        self.fit_mode = "custom"
        self.viewer.setZoomMode(QPdfView.ZoomMode.Custom)
        self.viewer.setZoomFactor(max(0.2, self.viewer.zoomFactor() / 1.2))
        self.show_zoom()

    def show_zoom(self):
        self.zoom_status.setText(f"{self.viewer.zoomFactor() * 100:.0f}%")

    def fit_page(self):
        self.fit_mode = "page"
        self.viewer.setZoomMode(QPdfView.ZoomMode.FitInView)
        self.zoom_status.setText(f"{self.viewer.zoomFactor() * 100:.0f}%")

    def fit_width(self):
        self.fit_mode = "width"
        self.viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.show_zoom()

    def fit_height(self):
        page = max(0, self.viewer.pageNavigator().currentPage())
        if not self.document.pageCount():
            return
        size = self.document.pagePointSize(page)
        if size.height() <= 0:
            return
        self.fit_mode = "height"
        self.viewer.setZoomMode(QPdfView.ZoomMode.Custom)
        self.viewer.setZoomFactor(max(0.2, (self.viewer.viewport().height() - 24) / size.height()))
        self.show_zoom()

    def open_files(self):
        self.window().open_files()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def toggle_fullscreen(self):
        window = self.window()
        window.showNormal() if window.isFullScreen() else window.showFullScreen()

    def rotate_page(self):
        self.window().statusBar().showMessage("Page rotation is not available in the embedded PDF viewer.", 3000)

    def save_copy(self):
        target, _ = QFileDialog.getSaveFileName(self, "Save a copy", self.path.name, "PDF files (*.pdf)")
        if target:
            if not target.lower().endswith(".pdf"):
                target += ".pdf"
            try:
                shutil.copy2(self.path, target)
                self.window().statusBar().showMessage(f"Saved a copy to {target}", 4000)
            except OSError as exc:
                QMessageBox.critical(self, "Save failed", str(exc))

    def print_pdf(self):
        self.window().statusBar().showMessage("Use your system PDF viewer to print this document.", 4000)

    def select_text(self):
        self.window().statusBar().showMessage("Text selection is available in the document view.", 3000)

    def pan_tool(self):
        self.viewer.setCursor(Qt.CursorShape.OpenHandCursor)
        self.window().statusBar().showMessage("Pan cursor selected.", 2500)

    def highlight_tool(self):
        self.window().statusBar().showMessage("Highlighting is not available in the embedded PDF viewer.", 3000)

    def search_document(self):
        from PyQt6.QtWidgets import QInputDialog
        query, accepted = QInputDialog.getText(self, "Search PDF", "Find text:")
        if accepted and query:
            self.window().statusBar().showMessage(f"Search for “{query}” is not supported by this viewer yet.", 3500)

    def show_settings(self):
        QMessageBox.information(self, "Reader settings", "Use the left rail to adjust page fit and zoom.")

    def eventFilter(self, watched, event):
        if watched is self.viewer.viewport() and event.type() == QEvent.Type.Resize:
            if self.fit_mode == "height":
                self.fit_height()
        return super().eventFilter(watched, event)


class PdfReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mupdf")
        self.setWindowIcon(QIcon(str(ICON_DIR / "pdf.ico")))
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        self.create_menus()
        self.create_tab_add_button()
        self.create_status_bar()
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f7fa; color: #202a33; }
            QMenuBar { background: #f5f7fa; padding: 4px 8px; }
            QMenuBar::item { padding: 5px 10px; }
            QTabWidget::pane { border: 0; background: #e9edf2; }
            QTabBar { background: #f5f7fa; }
            QTabBar::tab { background: #f5f7fa; color: #68717b; padding: 12px 18px; min-width: 170px; border: 0; border-bottom: 2px solid transparent; }
            QTabBar::tab:selected { color: #2868c7; border-bottom: 2px solid #3978dc; }
            QToolButton { border: 1px solid transparent; border-radius: 4px; background: transparent; }
            QToolButton:hover { background: #e7edf5; }
            QToolButton:pressed { background: #dce8fa; border-color: #4380db; }
            QWidget#navigationRail { background: #f5f7fa; border-right: 1px solid #dfe4e9; }
            QWidget#documentToolbar { background: #ffffff; border-bottom: 1px solid #dce1e6; }
            QWidget#pdfCanvas { background: #e9edf2; }
            QWidget#toolSeparator { background: #d9dee5; }
            QLabel#pageCount, QLabel#zoomStatus { color: #77818b; font-size: 11px; }
            QSpinBox { background: white; border: 1px solid #e1e5e9; border-radius: 5px; padding: 4px; }
            QStatusBar { background: #f5f7fa; color: #68717b; border-top: 1px solid #e0e4e9; }
        """)

    def create_menus(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("File")
        self.add_action(file_menu, "Open…", self.open_files, "Ctrl+O")
        self.add_action(file_menu, "Close tab", self.close_current_tab, "Ctrl+W")
        file_menu.addSeparator()
        self.add_action(file_menu, "Exit", self.close, "Alt+F4")
        edit_menu = bar.addMenu("Edit")
        self.add_action(edit_menu, "Copy", self.copy_text, "Ctrl+C")
        view_menu = bar.addMenu("View")
        for title, method, shortcut in (
            ("Zoom in", "zoom_in", "Ctrl+="), ("Zoom out", "zoom_out", "Ctrl+-"),
            ("Fit page to width", "fit_width", "Ctrl+1"), ("Fit page to height", "fit_height", "Ctrl+2"),
            ("Previous page", "previous_page", "Alt+Up"), ("Next page", "next_page", "Alt+Down"),
        ):
            self.add_action(view_menu, title, self.with_tab(method), shortcut)
        for title in ("Document", "Tools", "Help"):
            bar.addMenu(title)

    def create_tab_add_button(self):
        add = QToolButton()
        add.setIcon(QIcon(str(ICON_DIR / "plus.png")))
        add.setIconSize(QSize(17, 17))
        add.setToolTip("Open PDF files")
        add.clicked.connect(self.open_files)
        self.tabs.setCornerWidget(add, Qt.Corner.TopRightCorner)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready  •  Open a PDF to begin")

    def add_action(self, menu, title, callback, shortcut=None):
        action = QAction(title, self)
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        menu.addAction(action)
        return action

    def copy_text(self):
        self.statusBar().showMessage("Select text in the document to copy.", 3000)

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open PDF files", "", "PDF files (*.pdf)")
        for path in paths:
            self.add_pdf(path)

    def add_pdf(self, path):
        tab = PdfTab(path, self.tabs)
        index = self.tabs.addTab(tab, Path(path).name)
        self.tabs.setTabIcon(index, QIcon(str(ICON_DIR / "file.png")))
        self.tabs.setCurrentIndex(index)
        self.statusBar().showMessage(f"{Path(path).name}  •  PDF document")

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget:
            widget.deleteLater()

    def close_current_tab(self):
        if self.tabs.currentIndex() >= 0:
            self.close_tab(self.tabs.currentIndex())

    def with_tab(self, method):
        def call():
            tab = self.tabs.currentWidget()
            if tab:
                getattr(tab, method)()
        return call


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Mupdf")
    
    pixmap = QPixmap(str(ICON_DIR / "pdf-256.png")).scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()
    
    window = PdfReader()
    window.show()
    for argument in sys.argv[1:]:
        if argument.lower().endswith(".pdf") and Path(argument).is_file():
            window.add_pdf(argument)
    splash.finish(window)
    sys.exit(app.exec())
