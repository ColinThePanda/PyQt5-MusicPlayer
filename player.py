import os
import sys
import random
from pyglet import media
import pyglet
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QApplication,
    QListWidgetItem,
    QScrollBar,
    QSlider,
    QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QWheelEvent
from pathlib import Path

def get_music_folder():
    """Return the system's default music folder path."""
    return os.path.join(Path.home(), "Music")

def get_playlist_path(playlist):
    return os.path.join(os.path.join(get_music_folder(), 'YtSongs'), playlist)

def get_songs_list(playlist, music_folder=None):
    songs = []
    playlist_dir = get_playlist_path(playlist)

    if os.path.exists(playlist_dir):
        for file in os.listdir(playlist_dir):
            if file.lower().endswith(('.mp3', '.wav')):
                songs.append(os.path.join(playlist_dir, file))
    return songs

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

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = self.minimum() + ((event.x() / self.width()) * (self.maximum() - self.minimum()))
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
            self.sliderPressed.emit()
        super().mousePressEvent(event)

class MusicPlayerWindow(QWidget):
    def __init__(self, songs, playlist):
        super().__init__()
        self.playlist = get_playlist_path(playlist)
        self.songs = songs
        self.songs_dict = {os.path.basename(s).lower(): s for s in songs}
        self.media_player = media.Player()
        self.current_song_index = -1
        self.is_paused = False
        self.seeking = False
        self.played_first_song = False

        # Window setup
        self.setWindowTitle("Music Player")
        self.setStyleSheet(DARK_THEME)
        self.setMinimumSize(1000, 412)

        # UI components
        self.title_label = QLabel("Music Player")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        
        self.song_list = QListWidget()
        self.song_list.setFont(QFont("Arial", 12))
        self.song_list.setUniformItemSizes(True)
        
        # Populate song list
        for song in songs:
            item = QListWidgetItem(os.path.basename(song).rsplit('.', 1)[0])
            item.setSizeHint(QSize(-1, 40))
            self.song_list.addItem(item)

        # Progress bar components
        self.progress_slider = ClickableSlider(Qt.Horizontal)
        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_slider.setRange(0, 100)
        self.current_time_label = QLabel("00:00")
        self.total_duration_label = QLabel("00:00")
        self.current_time_label.setFont(QFont("Arial", 12))
        self.total_duration_label.setFont(QFont("Arial", 12))

        # Volume components
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_label = QLabel("Volume")
        self.volume_label.setFont(QFont("Arial", 12))

        # Create buttons
        self.pause_button = QPushButton("Play")
        self.skip_button = QPushButton("Skip")
        self.shuffle_button = QPushButton("Shuffle")

        # Setup layouts
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()

        # Control layout
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.skip_button)
        control_layout.addWidget(self.shuffle_button)

        control_layout.addWidget(self.current_time_label)
        control_layout.addWidget(self.progress_slider)
        control_layout.addWidget(self.total_duration_label)

        #control_layout.addStretch()
        control_layout.addWidget(self.volume_label)
        control_layout.addWidget(self.volume_slider)

        # Main layout
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.song_list)
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)

        # Connect signals
        self.song_list.itemClicked.connect(self.on_song_clicked)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.skip_button.clicked.connect(self.skip_song)
        self.shuffle_button.clicked.connect(self.shuffle_playlist)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.progress_slider.sliderPressed.connect(self.start_seeking)
        self.progress_slider.sliderReleased.connect(self.stop_seeking)
        self.progress_slider.sliderMoved.connect(self.update_time_during_seek)

        # Pyglet integration
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_pyglet)
        self.timer.start(100)

        # Configure scroll bar
        scroll_bar = self.song_list.verticalScrollBar()
        scroll_bar.setSingleStep(60)
        scroll_bar.setPageStep(60)
        scroll_bar.valueChanged.connect(self.snap_scroll_value)
        self.song_list.wheelEvent = self.custom_wheel_event

    def custom_wheel_event(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        steps = delta / 120.0
        scroll_step = 1
        new_value = self.song_list.verticalScrollBar().value() - int(round(steps * scroll_step))
        snapped_value = round(new_value / scroll_step) * scroll_step
        self.song_list.verticalScrollBar().setValue(snapped_value)
        event.accept()

    def snap_scroll_value(self, value):
        snap_interval = 1
        snapped_value = round(value)
        if value != snapped_value:
            sb = self.song_list.verticalScrollBar()
            sb.blockSignals(True)
            sb.setValue(snapped_value)
            sb.blockSignals(False)

    def start_seeking(self):
        self.seeking = True

    def stop_seeking(self):
        self.seeking = False
        if self.media_player.source:
            self.media_player.seek(self.progress_slider.value())

    def update_time_during_seek(self, position):
        self.current_time_label.setText(self.format_time(position))

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def update_pyglet(self):
        pyglet.app.platform_event_loop.step(0.001)
        if self.media_player.source and self.media_player.playing and not self.seeking:
            current_time = self.media_player.time
            self.progress_slider.setValue(int(current_time))
            self.current_time_label.setText(self.format_time(current_time))
        if not self.media_player.playing and not self.is_paused and self.current_song_index != -1:
            old_index = self.current_song_index
            self.skip_song()
            if old_index != self.current_song_index:
                self.update_current_indicator()

    def update_current_indicator(self):
        for i in range(self.song_list.count()):
            item = self.song_list.item(i)
            item.setBackground(QColor(26, 26, 26))
            item.setForeground(Qt.white)
        
        if 0 <= self.current_song_index < self.song_list.count():
            current_item = self.song_list.item(self.current_song_index)
            current_item.setBackground(QColor(28, 87, 133))
            current_item.setForeground(Qt.white)
            self.song_list.setCurrentRow(self.current_song_index)
            self.song_list.scrollToItem(current_item)

    def on_song_clicked(self, item):
        songs_lowercase = [song.lower() for song in self.songs]
        song_name = item.text().lower()
        try:
            song_index = songs_lowercase.index((os.path.join(self.playlist, song_name).lower() + ".mp3").lower())
        except:
            song_index = songs_lowercase.index((os.path.join(self.playlist, song_name).lower() + ".wav").lower())
        try:
            self.current_song_index = song_index
            self.play_song(self.songs[song_index])
        except ValueError:
            return

    def play_song(self, song_path):
        self.played_first_song = True
        self.media_player.pause()
        self.media_player = media.Player()
        source = media.load(song_path)
        self.media_player.queue(source)
        self.media_player.play()
        self.is_paused = False
        self.pause_button.setText("Pause")

        # Set up progress bar
        duration = source.duration
        self.progress_slider.setMaximum(int(duration))
        self.total_duration_label.setText(self.format_time(duration))
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")

        @self.media_player.event
        def on_eos():
            self.progress_slider.setValue(0)
            self.current_time_label.setText("00:00")
            self.update_current_indicator()
        
        self.media_player.push_handlers(on_eos)
        self.update_current_indicator()

    def play_first_song(self):
        if self.songs:
            self.current_song_index = 0
            self.play_song(self.songs[0])

    def toggle_pause(self):
        if self.media_player.playing:
            self.media_player.pause()
            self.is_paused = True
            self.pause_button.setText("Resume")
        elif not self.played_first_song:
            self.play_first_song()
            self.is_paused = False
            self.pause_button.setText("Pause")
        else:
            self.media_player.play()
            self.is_paused = False
            self.pause_button.setText("Pause")

    def restart_song(self):
        if self.current_song_index != -1:
            self.play_song(self.songs[self.current_song_index])

    def skip_song(self):
        if self.current_song_index == -1:
            return
        old_index = self.current_song_index
        if self.current_song_index < len(self.songs) - 1:
            self.current_song_index += 1
        else:
            self.current_song_index = 0
        if old_index != self.current_song_index:
            self.play_song(self.songs[self.current_song_index])

    def shuffle_playlist(self):
        current_song = self.songs[self.current_song_index] if self.current_song_index != -1 else None
        random.shuffle(self.songs)
        self.song_list.clear()
        for song in self.songs:
            item = QListWidgetItem(os.path.basename(song).rsplit('.', 1)[0])
            item.setSizeHint(QSize(-1, 40))
            self.song_list.addItem(item)
        self.current_song_index = 0
        self.play_first_song()

    def set_volume(self, value):
        self.media_player.volume = value / 100.0

def main():
    app = QApplication(sys.argv)
    songs = get_songs_list(get_music_folder())
    if not songs:
        print("No songs found in 'Songs' directory.")
        msg = QLabel("No songs found in 'Songs' directory!\nCreate a 'Songs' folder with audio files.")
        msg.setStyleSheet("font-size: 16px; color: white;")
        msg.setAlignment(Qt.AlignCenter)
        msg.show()
        sys.exit(app.exec_())
    else:
        window = MusicPlayerWindow(songs)
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()