from enum import Enum


class Views(Enum):
    PDF = 1
    CONSOLE = 2


class View:

    def __init__(self) -> None:
        """ Creates a new View object """

    def render(self) -> None:
        """ Renders the view """
        raise NotImplementedError
