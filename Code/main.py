from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '' # prevent's pygame from printing out it's welcome message
from pygame import init, display, quit, QUIT, event, Surface, get_error
from pygame.time import Clock
from traceback import format_exc
from logging import error # https://stackoverflow.com/questions/4990718/how-can-i-write-a-try-except-block-that-catches-all-exceptions
from network import Network
from level import Level
from settings import TITLE, WIDTH, HEIGHT, ONLINE, FPS
from GUI.buttonsingleton import ButtonSingleton

def main_init(client : Network | None = None) -> tuple[Surface, Clock, Level, ButtonSingleton]:
    display.set_caption(TITLE)
    window : Surface = display.set_mode((WIDTH, HEIGHT))
    clock : Clock = Clock()
    buttons : ButtonSingleton = ButtonSingleton()
    level : Level = Level(client, buttons)
    return window, clock, level, buttons

def main_run(client : Network | None = None) -> None:

    window, clock, level, buttons = main_init(client)

    while True:

        # remove any already pressed buttons
        events : list[event.Event] = event.get()
        to_remove : list[event.Event] = []

        for e in events:
            if e.type == QUIT:
                to_remove.append(e)
                break
        else:

            for remove in to_remove:
                events.remove(remove)

            # render magenta
            window.fill('magenta')

            # run the loop FPS times every second
            delta_time : float = clock.tick(FPS) / 1000.0 # https://www.reddit.com/r/pygame/comments/k7677j/how_to_make_a_basic_deltatime_system/

            buttons.run()

            # do game level logic
            level.run(delta_time, events)

            display.update()

            continue

        break

    buttons.exit()
    level.clean_up()
        
def main() -> None:
    global ONLINE
    if ONLINE:
        client : Network = Network()
        ONLINE = client.connect()

    successful, failed = init()
    if failed:
        print(f'main.main(): {successful} successful inits and {failed} failed inits.')
        print(f'main.main(): {get_error()}')

    if ONLINE:
        main_run(client)
    else: 
        main_run(None)

    if ONLINE:
        client.disconnect()    
    display.quit()
    quit()

if __name__ == '__main__':
    try:
        main()
    except:
        error(format_exc())
    finally:
        # halt the terminal so errors can be viewed
        input('Press \'Enter\' to the close Console.')
        #input()