from .view import View
from ..model import Model


class ConsoleView(View):

    def __init__(self, model: Model) -> None:
        """ Creates a new ConsoleView object with the given self.__model and file path """
        self.__model = model
        super().__init__()

    def render(self) -> None:
        """ Describes the data of the model """
        print(f'\nOriginal: \n{self.__model.get_original().head()}')
        print(f'\nTrend: \n{self.__model.get_trend().head()}')
        print(f'\nSeasonal: \n{self.__model.get_seasonal().head()}')
        print(f'\nResidual: \n{self.__model.get_residual().head()}')
        print(f'\nAnnual: \n{self.__model.get_annual().head()}')
        print(f'\nAnnual seasonal: \n{self.__model.get_annual_seasonal().head()}')
        print(f'\nAnnual residual: \n{self.__model.get_annual_residual().head()}')
        print(f'\nMonthly seasonal: \n{self.__model.get_monthly_seasonal().head()}')
        print(f'\nWeekdaily seasonal: \n{self.__model.get_weekdaily_seasonal().head()}')
        print(f'\nQuarterly seasonal: \n{self.__model.get_quarterly_seasonal().head()}')
        print(f'\nWeekly seasonal: \n{self.__model.get_weekly_seasonal().head()}')
