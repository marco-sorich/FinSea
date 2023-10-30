from .model import Model
from .views.pdfView import PdfView
from .views.consoleView import ConsoleView
from .views.view import Views


class Analyzer:

    def __init__(self, symbol: str, max_num_of_years: int) -> None:
        """
        Creates an Analyzer object for the given symbol and maximum number of years to analyze.
        """
        self.__model = Model(symbol, max_num_of_years)

    def calc(self) -> None:
        """
        Calculates the seasonality for the given symbol and maximum number of years to analyze.
        """
        self.__model.calc()

    def render(self, view: Views, file_name: str = '', ann_conf_band: bool = True) -> None:
        """
        Renders the seasonality for the given symbol and maximum number of years to analyze.
        """
        if view == Views.PDF:
            self.__view = PdfView(self.__model, file_name, ann_conf_band=("ci", 95)) if ann_conf_band else PdfView(self.__model, file_name, ann_conf_band=None)
        elif view == Views.CONSOLE:
            self.__view = ConsoleView(self.__model)
        else:  # pragma: no cover
            raise ValueError('Unknown view type')

        self.__view.render()
