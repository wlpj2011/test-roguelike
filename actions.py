class Action:
    pass

class EscapeAction:
    pass

class MovementAction:
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy
