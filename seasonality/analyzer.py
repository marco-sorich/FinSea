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

    def render(
            self,
            view: Views,
            file_name: str = '',
            ann_conf_band: bool = True,
            no_overall_daily_prices_plot: bool = False,
            no_overall_daily_trend_plot: bool = False,
            no_overall_daily_residual_plot: bool = False,
            no_annual_daily_prices_plot: bool = False,
            no_annual_daily_seasonal_plot: bool = False,
            no_annual_daily_redisdual_plot: bool = False,
            no_annual_weekly_seasonal_plot: bool = False,
            no_annual_monthly_seasonal_plot: bool = False,
            no_annual_quarterly_seasonal_plot: bool = False,
            no_weekdaily_seasonal_plot: bool = True,
            page_width: int = 210,
            page_height: int = 297
    ) -> None:
        """
        Renders the seasonality for the given symbol and maximum number of years to analyze.
        """
        if view == Views.PDF:
            conf_band = ("ci", 95) if ann_conf_band else None
            self.__view = PdfView(
                self.__model,
                file_name,
                ann_conf_band=conf_band,
                no_overall_daily_prices_plot=no_overall_daily_prices_plot,
                no_overall_daily_trend_plot=no_overall_daily_trend_plot,
                no_overall_daily_residual_plot=no_overall_daily_residual_plot,
                no_annual_daily_prices_plot=no_annual_daily_prices_plot,
                no_annual_daily_seasonal_plot=no_annual_daily_seasonal_plot,
                no_annual_daily_redisdual_plot=no_annual_daily_redisdual_plot,
                no_annual_weekly_seasonal_plot=no_annual_weekly_seasonal_plot,
                no_annual_monthly_seasonal_plot=no_annual_monthly_seasonal_plot,
                no_annual_quarterly_seasonal_plot=no_annual_quarterly_seasonal_plot,
                no_weekdaily_seasonal_plot=no_weekdaily_seasonal_plot,
                page_width=page_width,
                page_height=page_height
            )
        elif view == Views.CONSOLE:
            self.__view = ConsoleView(self.__model)
        else:  # pragma: no cover
            raise ValueError('Unknown view type')

        self.__view.render()
