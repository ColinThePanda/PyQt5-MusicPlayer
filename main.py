import sys
from PyQt5.QtWidgets import QApplication
from player import MusicPlayerWindow  # Assuming player.py contains your MusicPlayerWindow
# Import the get_songs_list and get_playlist_list functions (modified as above)
from player import get_songs_list  
from playlists import PlaylistWindow  # Adjust import based on your file name

def main():
    app = QApplication(sys.argv)
    
    # Get the list of playlists (each is a folder in your MUSIC_FOLDER_NAME)
    from playlists import get_playlist_list  # or from your module that defines it
    playlists = get_playlist_list()

    # Create the Playlist Selector window
    playlist_window = PlaylistWindow(playlists)
    playlist_window.show()
    
    # When a playlist is selected, load songs and open the player window
    def open_music_player(selected_playlist):
        songs = get_songs_list(selected_playlist)
        if not songs:
            # You could show an error message here if needed
            print(f"No songs found in playlist: {selected_playlist}")
            return
        player = MusicPlayerWindow(songs, selected_playlist)
        player.show()
        # Optionally close the playlist window
        playlist_window.close()

    # Connect the custom signal to our callback
    playlist_window.playlist_selected.connect(open_music_player)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
