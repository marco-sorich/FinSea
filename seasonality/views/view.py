from enum import Enum

from ..model import Model


class Views(Enum):
    PDF = 1
    CONSOLE = 2


class View:

    def __init__(self, model: Model) -> None:
        self._model = model
        """ Creates a new View object """

    def render(self) -> None:
        """ Renders the view """
        raise NotImplementedError
