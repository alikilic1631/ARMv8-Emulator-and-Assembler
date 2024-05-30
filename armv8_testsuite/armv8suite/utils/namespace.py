class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
    @staticmethod
    def from_dict(d: dict):
        return Namespace(**d)
