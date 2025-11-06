
class AveragedStack():
    """ A stack that holds a maximum number of elements (max_stack_len).
        New elements are added after being averaged over average_len inputs.
        
        Used for smoothing sensor readings over time.
    """
    def __init__(self, max_stack_len=10, average_len=5, init_value=None):
        self.maxlen = max_stack_len
        self.stack = []
        self.input_stack = []
        self.average_len = average_len

        if init_value is not None:
            for _ in range(max_stack_len):
                self.add(init_value)

    def add(self, value):
        self.input_stack.append(value)
        if len(self.input_stack) > self.average_len:
            new_value = sum(self.input_stack) / self.average_len
            self.input_stack = []
            self.stack.append(new_value)
            if len(self.stack) > self.maxlen:
                self.stack.pop(0)

    def average(self):
        if not self.stack:
            return None
        return sum(self.stack) / len(self.stack)
    
    def clear(self):
        self.stack = []
        self.input_stack = []

    def min(self):
        if not self.stack:
            return None
        return min(self.stack)
    
    def max(self):
        if not self.stack:
            return None
        return max(self.stack)

__oneof_log = {}
def oneof(func, n: int = 3, *args, **kwargs):
    """ Pass calls to a function one of n times, returns latest values otherwise. """
    global __oneof_log

    #make key with function and arguments
    funkey = str(func) + str(args) + str(kwargs)

    if not funkey in __oneof_log:
        # inits to n so first call runs the function
        __oneof_log[funkey] = {"counter": n, "last_value": None}

    __oneof_log[funkey]["counter"] += 1
    if __oneof_log[funkey]["counter"] >= n:
        __oneof_log[funkey]["last_value"] = func(*args, **kwargs)
        __oneof_log[funkey]["counter"] = 0
        print(f"oneof: called function {func.__name__}()")

    return __oneof_log[funkey]["last_value"]