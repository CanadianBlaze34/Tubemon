from time import time
from typing import Any, Callable

class Timer:
    
    def __init__(self, duration : float, task : Callable = None) -> None:
        self.duration   : float    = duration
        self.start_time : float    = time()
        self.task       : Callable = task
    
    def complete(self) -> bool:
        return time() - self.start_time >= self.duration

    def complete_task(self) -> bool:
        
        # not enough time has passed
        if time() - self.start_time < self.duration:
            return False

        # complete the task only once
        if self.task:
            self.task()
            self.task = None
            
        return True

    def complete_task_return(self) -> Any:
        
        # not enough time has passed
        if time() - self.start_time < self.duration:
            return None

        # complete the task and save it into itself 
        # to return the value of the task
        if type(self.task) == Callable:
            self.task = self.task()

        return self.task
            

    # TODO:
    # timer : Timer = Timer(duration, function_on_finish)
    # would need an update, or thread(preferably another process) or
    # call complete and if the time is greater than the duration, do the task