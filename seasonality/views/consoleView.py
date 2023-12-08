from .view import View
from ..model import Model


class ConsoleView(View):

    def __init__(self, model: Model) -> None:
        """ Creates a new ConsoleView object with the given model """
        super().__init__(model)

    def render(self) -> None:
        """ Describes the data of the model """
        print(f'\nOriginal: \n{self._model.get_overall_daily_prices()}')
        print(f'\nTrend: \n{self._model.get_overall_daily_trend()}')
        print(f'\nSeasonal: \n{self._model.get_overall_daily_seasonal()}')
        print(f'\nResidual: \n{self._model.get_overall_daily_residual()}')
        print(f'\nAnnual: \n{self._model.get_annual_daily_prices()}')
        print(f'\nAnnual seasonal: \n{self._model.get_annual_daily_seasonal()}')
        print(f'\nAnnual residual: \n{self._model.get_annual_daily_residual()}')
        print(f'\nMonthly seasonal: \n{self._model.get_monthly_seasonal()}')
        print(f'\nWeekdaily seasonal: \n{self._model.get_weekdaily_seasonal()}')
        print(f'\nQuarterly seasonal: \n{self._model.get_annual_quarterly_seasonal()}')
        print(f'\nWeekly seasonal: \n{self._model.get_annual_weekly_seasonal()}')
