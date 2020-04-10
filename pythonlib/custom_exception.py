# Base Exception Class
class CommonException(Exception):
    """Custom invocation of Exception that can be used as the base for custom exceptions"""
    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return repr(self.message)
