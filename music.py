# Loke har skrevet music.py

import pygame.mixer
import random
import general as g
from collections import deque

# Directory path for music files
DIRECTORY_PATH = "assets/sfx/music/"

class SoundsManager:
    def __init__(self, num_sfx_channels=16):
        # Reinitialize the mixer to ensure a clean state
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        
        # Initialize the mixer with the specified number of channels
        total_channels = 5 + num_sfx_channels
        pygame.mixer.init(frequency=44100, size=-16, channels=total_channels, buffer=2048)
        pygame.mixer.set_num_channels(total_channels)
        
        # Dictionary to store sound effects
        self.sounds = {}
        # List of channels for sound effects
        self.sfx_channels = [pygame.mixer.Channel(i) for i in range(5, 5+num_sfx_channels)]
        # Deque to manage channel usage for sound effects
        self.channel_usage = deque(self.sfx_channels, maxlen=num_sfx_channels)

    def createSound(self, soundName, soundDir, volume=0.5):
        # Load the sound from the specified directory and set its volume
        self.sounds[soundName] = pygame.mixer.Sound(soundDir)
        self.sounds[soundName].set_volume(volume)

    def playSound(self, soundName, allow_overlap=True):
        # Check if the sound exists in the dictionary
        if soundName not in self.sounds:
            return

        # First check all channels for availability
        for channel in self.sfx_channels:
            if not channel.get_busy():
                # Play the sound on the available channel
                channel.play(self.sounds[soundName])
                self.channel_usage.append(channel)
                return
        
        # If all channels are busy and overlap is allowed
        if allow_overlap:
            try:
                # Reuse the least recently used channel
                channel = self.channel_usage.popleft()
                channel.stop()
                channel.play(self.sounds[soundName])
                self.channel_usage.append(channel)
            except (IndexError, pygame.error):
                # Fallback to the first channel if an error occurs
                self.sfx_channels[0].play(self.sounds[soundName])

class MusicWithQueue:
    def __init__(self):
        # Initialize the music channel
        self.music_channel = pygame.mixer.Channel(0)
        self.music_channel.set_volume(0.2)
        # Load all music files from the directory
        self.soundArray = [pygame.mixer.Sound(f) 
                          for f in g.getAllFilesInDir(DIRECTORY_PATH, ".mp3")]
        
        # Set up a custom event for when music ends
        self.MUSIC_END = pygame.USEREVENT + 1
        self.music_channel.set_endevent(self.MUSIC_END)
        self.current_song = None

    def playMusic(self):
        # Only queue a new song if none is currently playing
        if not self.music_channel.get_busy() and self.soundArray:
            self.current_song = random.choice(self.soundArray)
            self.music_channel.play(self.current_song)

    def handle_event(self, event):
        # Handle the custom music end event
        if event.type == self.MUSIC_END:
            self.playMusic()

# Initialize the sound manager with 16 SFX channels (total 21 channels)
sound_manager = SoundsManager(num_sfx_channels=16)

# Mapping of sound effect names to their file paths and volumes
sfx_mapping = {
    "ak47": ("assets/sfx/sounds/ak47.mp3", 0.5),
    "zombie": ("assets/sfx/sounds/zombie.mp3", 0.3),
    "zomb_hit": ("assets/sfx/sounds/zomb_hit.mp3", 0.5),
    "bullet_wall": ("assets/sfx/sounds/bullet_wall.mp3", 0.5),
    "zomb_death": ("assets/sfx/sounds/zomb_death.wav", 0.5)
}

# Create sound effects based on the mapping
for name, v in sfx_mapping.items():
    path, vol = v
    sound_manager.createSound(name, path, volume=vol)