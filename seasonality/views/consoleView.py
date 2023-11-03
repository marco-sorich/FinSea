from .view import View
from ..model import Model


class ConsoleView(View):

    def __init__(self, model: Model) -> None:
        """ Creates a new ConsoleView object with the given model """
        super().__init__(model)

    def render(self) -> None:
        """ Describes the data of the model """
        print(f'\nOriginal: \n{self._model.get_overall_daily_prices().head()}')
        print(f'\nTrend: \n{self._model.get_overall_daily_trend().head()}')
        print(f'\nSeasonal: \n{self._model.get_overall_daily_seasonal().head()}')
        print(f'\nResidual: \n{self._model.get_overall_daily_residual().head()}')
        print(f'\nAnnual: \n{self._model.get_annual_daily_prices().head()}')
        print(f'\nAnnual seasonal: \n{self._model.get_annual_daily_seasonal().head()}')
        print(f'\nAnnual residual: \n{self._model.get_annual_daily_residual().head()}')
        print(f'\nMonthly seasonal: \n{self._model.get_monthly_seasonal().head()}')
        print(f'\nWeekdaily seasonal: \n{self._model.get_weekdaily_seasonal().head()}')
        print(f'\nQuarterly seasonal: \n{self._model.get_annual_quarterly_seasonal().head()}')
        print(f'\nWeekly seasonal: \n{self._model.get_annual_weekly_seasonal().head()}')
