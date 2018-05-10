import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from ..calculator import Calculator
from ..utils import get_extension, set_chart_style

from .cycletime import CycleTimeCalculator

class ScatterplotCalculator(Calculator):
    """Build scatterplot data for the cycle times: a data frame containing
    only those items in where values are set for `completed_timestamp` and
    `cycle_time`, and with those two columns as the first two, both
    normalised to whole days, and with `completed_timestamp` renamed to
    `completed_date`.
    """

    def run(self):
        cycle_data = self.get_result(CycleTimeCalculator)
        columns = list(cycle_data.columns)
        columns.remove('cycle_time')
        columns.remove('completed_timestamp')
        columns = ['completed_timestamp', 'cycle_time'] + columns

        data = (
            cycle_data[columns]
            .dropna(subset=['cycle_time', 'completed_timestamp'])
            .rename(columns={'completed_timestamp': 'completed_date'})
        )

        data['cycle_time'] = data['cycle_time'].astype('timedelta64[D]')

        return data
    
    def write(self):
        data = self.get_result()

        if self.settings['scatterplot_data']:
            self.write_file(data, self.settings['scatterplot_data'])
        
        if self.settings['scatterplot_chart']:
            self.write_chart(data, self.settings['scatterplot_chart'])

    def write_file(self, data, output_file):
        output_extension = get_extension(output_file)

        file_data = data.copy()
        file_data['completed_date'] = file_data['completed_date'].map(pd.Timestamp.date)

        if output_extension == '.json':
            file_data.to_json(output_file, date_format='iso')
        elif output_extension == '.xlsx':
            file_data.to_excel(output_file, 'Scatter', index=False)
        else:
            file_data.to_csv(output_file, index=False)
        
    def write_chart(self, data, output_file):
        quantiles = self.settings['quantiles']

        chart_data = data.copy()
        chart_data['completed_date'] = chart_data['completed_date'].values.astype('datetime64[D]')
        ct_days = chart_data['cycle_time']

        if len(ct_days.index) < 2:
            print("WARNING: Need at least 2 completed items to draw scatterplot")
            return
        
        fig, ax = plt.subplots()
        fig.autofmt_xdate()

        ax.set_xlabel("Completed date")
        ax.set_ylabel("Cycle time (days)")

        if self.settings['scatterplot_chart_title']:
            ax.set_title(self.settings['scatterplot_chart_title'])

        ax.plot_date(x=chart_data['completed_date'], y=ct_days, ms=5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))

        # Add quantiles
        left, right = ax.get_xlim()
        for quantile, value in ct_days.quantile(quantiles).iteritems():
            ax.hlines(value, left, right, linestyles='--', linewidths=1)
            ax.annotate("%.0f%% (%.0f days)" % ((quantile * 100), value,),
                xy=(left, value),
                xytext=(left, value + 0.5),
                fontsize="x-small",
                ha="left"
            )

        set_chart_style()

        # Write file
        
        fig = ax.get_figure()
        fig.savefig(output_file, bbox_inches='tight', dpi=300)
