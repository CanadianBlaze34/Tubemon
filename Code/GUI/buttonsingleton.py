from __future__ import annotations
from typing import Any, Callable
from pygame import mouse, Surface
from GUI.label import Label
from GUI.slider import Slider
from GUI.button import Button
from logging import error
from traceback import format_exc

class ButtonSingleton:

    def __new__(cls) -> ButtonSingleton:
        # has not been instantiated once before
        if not hasattr(cls, '_instance'):
            # print('Create and run a thread when the first instance is created')
            cls._instance = super().__new__(cls) # object.__new__()

            cls._instance._buttons : dict[str, dict[str, Any]] = {}# Use a dictionary to store button information
            cls._instance._buttons_to_add : list[dict[str, dict[str, Any]]] = [] # Buttons to be added   at the end of the _run loop
            cls._instance._buttons_to_remove  : list[str] = []             # Buttons to be removed at the end of the _run loop

            cls._instance._clicked_position : tuple[int, int] = None # should be a singleton variable
            cls._instance._clicked : bool = False # true when mouse presses in the button and releases in the button

        return cls._instance

    def _add(self) -> None:
        """Add all requested buttons and clear the pending list."""
        for button in self._buttons_to_add:
                self._buttons.update(button)
        self._buttons_to_add.clear()

    def _remove(self) -> None:
        """Remove all requested buttons and clear the pending list."""
        
        for label in self._buttons_to_remove:
            #print(f'ButonSingleton._remove(self): {label}')
            del self._buttons[label]
            #try:
            #except:
            #    error(format_exc())
            #finally:
            #    print(f'ButonSingleton._remove(self): {label}')
            #    raise KeyError


        self._buttons_to_remove.clear()

    def _pressing(self, mp : tuple[int, int], pressing_left_mouse : bool) -> None:
        # save the originally clicked position the mouse button clicked at
        if pressing_left_mouse and not self.clicked_position:
            self.clicked_position = mp

    def _not_pressing(self, pressing_left_mouse : bool) -> None:
        if not pressing_left_mouse:
            self.clicked_position = None # reset 

    def _refresh_states(self) -> None:
        # clicked, entered and exit will only be active for one frame
        # click
        self.clicked = False

    def _update_mouse_states(self, mp : tuple[int, int], pressing_left_mouse : bool) -> None:
        # reset all variable that should only be set once a frame
        self._refresh_states()
        self._pressing(mp, pressing_left_mouse)

    def _update(self) -> None:
        """Update mouse variables, buttons and run all button tasks."""

        mp : tuple[int, int] = mouse.get_pos() # mouse position
        LEFT_MOUSE_BUTTON : int = 0
        pressing_left_mouse : bool = mouse.get_pressed()[LEFT_MOUSE_BUTTON]
        self._update_mouse_states(mp, pressing_left_mouse)
        
        for label_name, items in self._buttons.items():
            # Skip the buttons requested to be removed.
            if label_name in self._buttons_to_remove:
                continue
            
            label = items['label']
            label.update(mp, self.clicked_position, pressing_left_mouse)
            # Run the buttons task
            if items['task'] is not None:
                for index, task in enumerate(items['task']):
                    if task is not None:
                        if type(label) == Button:
                            if index == 0 and label.clicked or\
                               index == 1 and label.entered or\
                               index == 2 and label.exited:
                                    task()

                        elif type(label) == Slider:
                            if label.holding:
                                task()

            #print('update')

        self._not_pressing(pressing_left_mouse)

    def run(self) -> None:
        """update the singleton."""
        self._update()
        self._add()
        self._remove()

    def create(self, label : str, button : Label, tasks : list[Callable] = None, render_order : int = 0) -> None:
        """Create a button with the given label, task, and render order, and add the button to _buttons_to_add.\n
        _buttons_to_add will add all of its items after all tasks are ran.\n
        Args:
            label (str): The label that represents the added buttont.
            task (Callable, optional): The task to be called when the button has been clicked. Defaults to None.
            render_order (int, optional): The order of the buttons to be rendered. Rendered in ascending order. Defaults to 0.
        """ 
        task = []
        if tasks:
            for t in tasks:
                def f_task(tsk = t) : tsk(self)
                task.append( (f_task) if t else None)

        button : dict[str, dict[str, Any]] = {label : {'task' : task, 'render_order' : render_order, 'label' : button}}
        #print('create')
        self._buttons_to_add.append(button)

    def add(self, button : dict[dict[str, Any]]) -> None:
        """Add the button to _buttons_to_add.\n
        _buttons_to_add will add all of its items after all tasks are ran.\n
        Args:
            button (dict[dict[str, Any]]): The button that will be added after all tasks are ran.
        """
        #print('add')
        if button['label'] in self._buttons:
            raise AssertionError
        self._buttons_to_add.append(button)

    def remove(self, *labels : str) -> None:
        """Add the label that represents a button to _buttons_to_remove.\n
        _buttons_to_remove will remove all of the buttons it contains after all tasks are ran.\n
        Args:
            label (str): The label that represents the removed button.
        """
        #print('remove')
        for label in labels:
            self._buttons_to_remove.append(label)

    def remove_all(self) -> None:
        """Add all buttons maintained by the singleton to _buttons_to_remove.\n
        _buttons_to_remove will remove all of the buttons it contains after all tasks are ran."""
        #print('remove all')
        self._buttons_to_remove.extend(self._buttons.keys())

    def draw(self, display_surface : Surface) -> None:
        """Draw all buttons in ascending order of render order"""
        for label, items in sorted(self._buttons.items(), key=lambda x: x[1]['render_order']):
            items['label'].draw(display_surface)

    def get(self, label : str) -> Label:
        return self._buttons[label]

    def exit(self) -> None:
        """Remove all buttons and delete the button singleton."""
        self.remove_all()
        del self
        #print('exit')






