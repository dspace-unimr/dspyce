class RestObjectNotFoundError(FileNotFoundError):
    """ DSpaceObject not found. """
    def __init__(self, *args, **kwargs):
        pass