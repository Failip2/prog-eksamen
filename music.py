import pygame.mixer
import random
import general as g

DIRECTORY_PATH = "assets/sfx/music/"

class SoundsManager:
    def __init__(self):
        self.sounds = {}
    

    def createSound(self, soundName, soundDir):
        self.sounds[soundName] = pygame.mixer.Sound(soundDir)

    def playSound(self, soundName):
        self.sounds[soundName].play()
        return


class MusicWithQueue:

    def __init__(self, channel) -> None:
        self.channel = channels[channel]
        self.channel.set_volume(0.2)
        self.channelKeyName = list(channels.keys())[list(channels.values()).index(self.channel)]
        self.soundArray = self.defineMusicArray(self.channelKeyName)
        self.PLAY_MUSIC = False

    def defineMusicArray(self, channelKeyName):
        arr = []
        for filename in g.getAllFilesInDir(DIRECTORY_PATH+channelKeyName, ".mp3"):
                arr.append(pygame.mixer.Sound(filename))
        return arr
    
    def playMusic(self):
        if self.channel.get_busy():
            return
        self.PLAY_MUSIC = True
        self.channel.play(self.soundArray[0])
        self.soundArray.append(self.soundArray.pop(self.soundArray.index(self.soundArray[0])))
        return self
    
    def checkForSoundPlaying(self):
        if not self.PLAY_MUSIC:
            return
        if self.channel.get_sound() == None:
            self.playMusic()
    
    def stopMusic(self):
        self.PLAY_MUSIC = False
        self.channel.stop()
        return


def getRandomMusic(musicArr):
    print(musicArr)
    return musicArr[random.randint(0,len(musicArr)-1)]


pygame.mixer.init(frequency = 44100, size = -16, channels = 4, buffer = 2**12)

sound_manager = SoundsManager()

sound_manager.createSound("ak47", "assets/sfx/sounds/ak47.mp3")
sound_manager.createSound("zombie", "assets/sfx/sounds/zombie.mp3")

channels = {
    "main": pygame.mixer.Channel(0),
    "arena": pygame.mixer.Channel(1),
    "tutorial": pygame.mixer.Channel(2),
    "3": pygame.mixer.Channel(3),
    "4": pygame.mixer.Channel(4)
}