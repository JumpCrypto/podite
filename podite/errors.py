class PodPathError(Exception):
    def __init__(self, message: str, name, ty, val=None):
        if isinstance(name, list):
            self.path = name
        else:
            self.path = [name]
        self.ty = ty
        self.val = val
        self.message = message
        super().__init__(message)

    def __str__(self):
        path = ".".join(self.path[::-1])
        if self.val is not None:
            return f"{self.message}\n Path: {path}\n Type: {self.ty}, Val: {type(self.val)}({self.val})"
        else:
            return f"{self.message}\n Path: {path}\n Type: {self.ty}"
