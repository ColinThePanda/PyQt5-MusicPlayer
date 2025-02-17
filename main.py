"""
Music Player Application using PyQt5 and Pyglet
Features: Play/Pause, Skip, Shuffle, Volume Control, and Progress Seeking
"""

import os
import sys
import random
from pathlib import Path
from pyglet import media
import pyglet
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QApplication,
    QListWidgetItem, QSlider, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QWheelEvent

# Constants
MUSIC_FOLDER_NAME = "YtSongs"
SUPPORTED_FORMATS = (".mp3", ".wav", ".MP3", ".WAV")
WINDOW_MIN_SIZE = (1000, 412)
FONT_FAMILY = "Arial"
TITLE_FONT_SIZE = 18
LIST_FONT_SIZE = 12
SCROLL_SNAP_INTERVAL = 40

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

def get_music_folder():
    """Return the system's default music folder path."""
    return os.path.join(Path.home(), "Music")

def get_songs_list(music_folder=None):
    """
    Discover audio files in the specified music directory.
    Returns list of full paths to supported audio files
    """
    base_dir = music_folder if music_folder else get_music_folder()
    song_dir = os.path.join(base_dir, MUSIC_FOLDER_NAME)
    
    if not os.path.exists(song_dir):
        return []

    return [
        os.path.join(song_dir, f) 
        for f in os.listdir(song_dir) 
        if f.lower().endswith(SUPPORTED_FORMATS)
    ]

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            ratio = event.x() / self.width()
            value = self.minimum() + ratio * (self.maximum() - self.minimum())
            self.setValue(int(value))
            self.sliderMoved.emit(int(value))
        super().mousePressEvent(event)

class MusicPlayerWindow(QWidget):
    def __init__(self, songs):
        super().__init__()
        self.songs = songs
        self.current_song_index = -1
        self.media_player = media.Player()
        self.is_paused = False
        self.seeking = False
        self.played_first_song = False

        self.initializeUI()
        self.connectSignals()
        self.setupAudioTimer()

    def initializeUI(self):
        """Set up all UI components and layouts"""
        self.setWindowTitle("Music Player")
        self.setStyleSheet(DARK_THEME)
        self.setMinimumSize(*WINDOW_MIN_SIZE)

        # Create UI components
        self.title_label = QLabel("Music Player")
        self.song_list = QListWidget()
        self.progress_slider = ClickableSlider(Qt.Horizontal)
        self.volume_slider = ClickableSlider(Qt.Horizontal)
        self.current_time_label = QLabel("00:00")
        self.total_duration_label = QLabel("00:00")
        self.volume_label = QLabel("Volume")

        self.configureUIComponents()
        self.populateSongList()
        self.createControlButtons()
        self.setupLayouts()

    def configureUIComponents(self):
        """Configure visual properties of UI elements"""
        # Title label
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont(FONT_FAMILY, TITLE_FONT_SIZE, QFont.Bold))

        # Song list
        self.song_list.setFont(QFont(FONT_FAMILY, LIST_FONT_SIZE))
        self.song_list.setUniformItemSizes(True)
        self.song_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)

        # Progress slider
        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_slider.setRange(0, 100)

        # Time labels
        self.current_time_label.setFont(QFont(FONT_FAMILY, LIST_FONT_SIZE))
        self.total_duration_label.setFont(QFont(FONT_FAMILY, LIST_FONT_SIZE))

        # Volume controls
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_label.setFont(QFont(FONT_FAMILY, LIST_FONT_SIZE))

    def createControlButtons(self):
        """Initialize and style control buttons"""
        self.pause_button = QPushButton("Play")
        self.skip_button = QPushButton("Skip")
        self.shuffle_button = QPushButton("Shuffle")

    def populateSongList(self):
        """Fill song list with discovered audio files"""
        for song in self.songs:
            item = QListWidgetItem(os.path.basename(song).rsplit('.', 1)[0])
            item.setData(Qt.UserRole, song)  # Store full path
            item.setSizeHint(QSize(-1, SCROLL_SNAP_INTERVAL))
            self.song_list.addItem(item)

    def setupLayouts(self):
        """Arrange UI components in layouts"""
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()

        # Add Buttons
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.skip_button)
        control_layout.addWidget(self.shuffle_button)

        # Add Progress Slider
        control_layout.addWidget(self.current_time_label)
        control_layout.addWidget(self.progress_slider)
        control_layout.addWidget(self.total_duration_label)

        # Add Volume Slider
        control_layout.addWidget(self.volume_label)
        control_layout.addWidget(self.volume_slider)

        # Main layout
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.song_list)
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)

    def connectSignals(self):
        """Connect UI signals to their handler functions"""
        self.song_list.itemClicked.connect(self.handleSongClick)
        self.pause_button.clicked.connect(self.togglePlayback)
        self.skip_button.clicked.connect(self.playNextSong)
        self.shuffle_button.clicked.connect(self.shufflePlaylist)
        self.volume_slider.valueChanged.connect(self.updateVolume)
        self.progress_slider.sliderPressed.connect(lambda: setattr(self, 'seeking', True))
        self.progress_slider.sliderReleased.connect(self.handleSeekRelease)

    def setupAudioTimer(self):
        """Initialize timer for audio progress updates"""
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.updatePlaybackState)
        self.audio_timer.start(100)

    def handleSongClick(self, item):
        """Handle song selection from list"""
        song_path = item.data(Qt.UserRole)
        self.current_song_index = self.songs.index(song_path)
        self.playSong(song_path)

    def playSong(self, song_path):
        """Start playing the specified audio file"""
        try:
            source = media.load(song_path)
        except Exception as e:
            print(f"Error loading song: {e}")
            return

        self.played_first_song = True
        self.media_player.pause()
        self.media_player = media.Player()
        self.media_player.queue(source)
        self.media_player.play()
        
        # Update UI state
        self.is_paused = False
        self.pause_button.setText("Pause")
        self.updateSongProgress(source.duration)
        self.updateCurrentSongHighlight()

        # Set end-of-song handler
        self.media_player.push_handlers(on_eos=self.handleSongEnd)

    def updateSongProgress(self, duration):
        """Update progress controls for new song"""
        self.progress_slider.setMaximum(int(duration))
        self.progress_slider.setValue(0)
        self.total_duration_label.setText(self.formatTime(duration))
        self.current_time_label.setText("00:00")

    def handleSongEnd(self):
        """Automatically play next song when current ends"""
        self.progress_slider.setValue(0)
        self.playNextSong()

    def togglePlayback(self):
        """Toggle between play/pause states"""
        if not self.played_first_song:
            self.playFirstSong()
            return

        if self.media_player.playing:
            self.media_player.pause()
            self.is_paused = True
            self.pause_button.setText("Resume")
        else:
            self.media_player.play()
            self.is_paused = False
            self.pause_button.setText("Pause")

    def playNextSong(self):
        """Advance to next song in playlist"""
        if not self.songs:
            return

        new_index = (self.current_song_index + 1) % len(self.songs)
        self.current_song_index = new_index
        self.playSong(self.songs[new_index])

    def shufflePlaylist(self):
        """Randomize playlist order using original behavior"""
        random.shuffle(self.songs)
        self.song_list.clear()
        
        # Repopulate list with shuffled songs
        for song in self.songs:
            item = QListWidgetItem(os.path.basename(song).rsplit('.', 1)[0])
            item.setData(Qt.UserRole, song)
            item.setSizeHint(QSize(-1, 40))
            self.song_list.addItem(item)
        
        # Play first song in shuffled playlist
        self.current_song_index = 0
        self.playSong(self.songs[0])

    def updatePlaybackState(self):
        """Update progress bar and handle automatic song advancement"""
        pyglet.app.platform_event_loop.step(0.001)
        
        if self.media_player.source and not self.seeking:
            current_time = self.media_player.time
            self.progress_slider.setValue(int(current_time))
            self.current_time_label.setText(self.formatTime(current_time))

    def handleSeekRelease(self):
        """Handle user finishing progress bar interaction"""
        self.seeking = False
        if self.media_player.source:
            self.media_player.seek(self.progress_slider.value())

    def updateVolume(self, value):
        """Adjust playback volume"""
        self.media_player.volume = value / 100.0

    def updateCurrentSongHighlight(self):
        """Visual indicator for currently playing song"""
        for i in range(self.song_list.count()):
            item = self.song_list.item(i)
            item.setBackground(QColor(26, 26, 26))
            item.setForeground(Qt.white)
        
        if 0 <= self.current_song_index < self.song_list.count():
            current_item = self.song_list.item(self.current_song_index)
            current_item.setBackground(QColor(28, 87, 133))
            self.song_list.setCurrentItem(current_item)

    def formatTime(self, seconds):
        """Convert seconds to mm:ss format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def playFirstSong(self):
        """Play the first song in the playlist"""
        if self.songs:
            self.current_song_index = 0
            self.playSong(self.songs[0])

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    
    songs = get_songs_list()
    if not songs:
        error_msg = QLabel("No songs found!\nCreate a 'YtSongs' folder with audio files.")
        error_msg.setStyleSheet("font-size: 16px; color: white;")
        error_msg.setAlignment(Qt.AlignCenter)
        error_msg.show()
    else:
        player = MusicPlayerWindow(songs)
        player.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()