from pygame.mixer import Sound, get_init, Channel
from settings import MASTER_VOLUME

ALL_SOUNDS = []

def try_sound(file_path : str)-> Sound:
    if get_init():
        sound : Sound = Sound(file_path)
        sound.set_volume(MASTER_VOLUME)
        ALL_SOUNDS.append(sound)
        return sound
    return None

def try_play(sound : Sound, loops : int = 0, maxtime : int = 0, fade_ms : int = 0)-> Channel:
    if get_init():
        return sound.play(loops, maxtime, fade_ms)
    return None

def try_stop(sound : Sound)-> None:
    if get_init():
        sound.stop()

def try_update_all(volume: float = MASTER_VOLUME) -> None:
    if get_init():
        for sound in ALL_SOUNDS:
            sound.set_volume(volume)
            #print(f'updated {sound} to a volume of {volume}')