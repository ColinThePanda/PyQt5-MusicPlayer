from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSlider,
)
from PyQt5.QtGui import QFont, QColor, QWheelEvent
from PyQt5.QtCore import pyqtSignal
import sys
import os
from pathlib import Path

FONT_FAMILY = "Arial"
TITLE_FONT_SIZE = 18
LIST_FONT_SIZE = 12


def get_playlist_list():
    base_dir = get_music_folder()
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]


def get_music_folder():
    """Return the system's default music folder path."""
    return os.path.join(Path.home(), "Music")


DARK_THEME = """
    QWidget {
        background-color: #111111;
        color: #ffffff;
    }
    QListWidget {
        background-color: #1a1a1a;
        border: 2px solid #2281c9;
        border-radius: 5px;
        font-size: 24px;
        outline: none;
    }
    QListWidget::item {
        height: 40px;
        padding: 8px;
        border: none;
        margin: 2px;
    }
    QListWidget::item:selected {
        background-color: #1c5785;
        color: white;
        border: none;
        outline: none;
        border-radius: 5px;
    }
    QPushButton {
        background-color: #1c5785;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #1a6aa3;
    }
    QScrollBar:vertical {
        background: #1a1a1a;
        width: 12px;
        border: none;
    }
    QScrollBar::handle:vertical {
        background: #2281c9;
        min-height: 20px;
        border-radius: 6px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        border: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QSlider::groove:horizontal {
        background: #1a1a1a;
        height: 4px;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #2281c9;
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }
    QSlider::sub-page:horizontal {
        background: #2281c9;
        border-radius: 2px;
    }
"""


class PlaylistWindow(QWidget):
    # Signal that emits the selected playlist name (a string)
    playlist_selected = pyqtSignal(str)

    def __init__(self, playlists):
        super().__init__()
        self.setStyleSheet(DARK_THEME)
        self.playlists = playlists

        self.playlist_list = QListWidget()
        self.populate_list()

        self.playlist_list.setFont(QFont(FONT_FAMILY, LIST_FONT_SIZE))
        self.playlist_list.setUniformItemSizes(True)
        self.playlist_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)

        # Correct connection: use playlist_list, not song_list
        self.playlist_list.itemClicked.connect(self.on_playlist_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.playlist_list)
        self.setLayout(layout)

    def populate_list(self):
        for playlist in self.playlists:
            item = QListWidgetItem(playlist)
            self.playlist_list.addItem(item)

    def on_playlist_clicked(self, item: QListWidgetItem):
        # Emit the selected playlist's name
        selected_playlist = item.text()
        self.playlist_selected.emit(selected_playlist)
