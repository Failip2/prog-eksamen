import pygame.mixer
import random
import general as g
from collections import deque

DIRECTORY_PATH = "assets/sfx/music/"

class SoundsManager:
    def __init__(self, num_sfx_channels=16):
        if pygame.mixer.get_init():
            pygame.mixer.quit()
            
        total_channels = 5 + num_sfx_channels
        pygame.mixer.init(frequency=44100, size=-16, channels=total_channels, buffer=2048)
        pygame.mixer.set_num_channels(total_channels)
        
        self.sounds = {}
        self.sfx_channels = [pygame.mixer.Channel(i) for i in range(5, 5+num_sfx_channels)]
        self.channel_usage = deque(self.sfx_channels, maxlen=num_sfx_channels)

    def createSound(self, soundName, soundDir):
        self.sounds[soundName] = pygame.mixer.Sound(soundDir)
        self.sounds[soundName].set_volume(0.5)

    def playSound(self, soundName, allow_overlap=True):
        if soundName not in self.sounds:
            return

        # First check all channels for availability
        for channel in self.sfx_channels:
            if not channel.get_busy():
                channel.play(self.sounds[soundName])
                self.channel_usage.append(channel)
                return
        
        # If all busy and overlap allowed
        if allow_overlap:
            try:
                channel = self.channel_usage.popleft()
                channel.stop()
                channel.play(self.sounds[soundName])
                self.channel_usage.append(channel)
            except (IndexError, pygame.error):
                self.sfx_channels[0].play(self.sounds[soundName])

class MusicWithQueue:
    def __init__(self):
        self.music_channel = pygame.mixer.Channel(0)
        self.music_channel.set_volume(0.2)
        self.soundArray = [pygame.mixer.Sound(f) 
                          for f in g.getAllFilesInDir(f"{DIRECTORY_PATH}main", ".mp3")]

    def playMusic(self):
        if not self.music_channel.get_busy() and self.soundArray:
            self.music_channel.play(random.choice(self.soundArray))

# Initialize with 16 SFX channels (total 21 channels)
sound_manager = SoundsManager(num_sfx_channels=16)

# Sound creation remains the same

# Create sound effects
sfx_mapping = {
    "ak47": "assets/sfx/sounds/ak47.mp3",
    "zombie": "assets/sfx/sounds/zombie.mp3",
    "zomb_hit": "assets/sfx/sounds/zomb_hit.mp3",
    "bullet_wall": "assets/sfx/sounds/bullet_wall.mp3",
    "zomb_death": "assets/sfx/sounds/zomb_death.wav"
}

for name, path in sfx_mapping.items():
    sound_manager.createSound(name, path)

# Usage example remains the same