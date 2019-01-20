import random

import plotly
from django.db.models import QuerySet, Count
from pandas import DataFrame
from plotly.graph_objs import Pie, Layout, Scatter, Figure, Annotation

from BaC.settings.base import PLOT_PALETTE


class IsolatePlots(object):
    def __init__(self, queryset):
        """

        :type queryset: QuerySet
        """
        self.queryset = queryset

    def create_pie_plot(self, field, title=None):
        result = self.queryset.values(field).annotate(count=Count(field))
        df = DataFrame([fi for fi in result])
        return plotly.offline.plot({
            "data": [Pie(labels=df.get(field), values=df.get('count'), hoverinfo='label+percent+value',
                         textposition='inside', marker=dict(colors=PLOT_PALETTE))],
            "layout": Layout(title=title, showlegend=False)
        }, show_link=False, output_type='div', include_plotlyjs=False
        )


class GeneMatchPlots(object):
    def __init__(self, queryset):
        """

        :type queryset: QuerySet
        """
        self.queryset = queryset

    @staticmethod
    def _count_by_date_xy(a):
        results = {}
        for match in a:
            x, y = results.setdefault(match['aro_gene__aro_category__category_aro_name'], ([], []))
            x.append(match['result__sample__isolate__collection_date'])
            y.append(match['count'])
        return results

    @staticmethod
    def _add_annotation_on_new_category(annotations, category, date, i, shapes, stacked_y_values):
        if date in annotations:
            annotations[date] = dict(y=stacked_y_values[i], text=annotations[date]['text'] + ', ' + category)
        else:
            annotations[date] = dict(y=stacked_y_values[i], text=category)
            shapes.append({
                'type': 'line', 'x0': date, 'y0': 0, 'x1': date, 'y1': 1, 'opacity': 0.3, 'yref': 'paper'
            })

    @staticmethod
    def _stack_yvalues(annotations, category, cumulative, dates, results, shapes, stacked_y_values):
        total = 0
        index = 0
        new_x = []
        new_y = []
        new_text = []
        for i, date in enumerate(dates):
            if len(results[category][0]) <= index or date != results[category][0][index]:
                stacked_y_values[i] += total
                new_x.append(date)
                new_y.append(stacked_y_values[i])
                new_text.append(total)
            else:
                stacked_y_values[i] += results[category][1][index] + total
                new_x.append(date)
                new_y.append(stacked_y_values[i])
                if total == 0 and i != 0:
                    GeneMatchPlots._add_annotation_on_new_category(annotations, category, date, i, shapes,
                                                                   stacked_y_values)
                if cumulative:
                    total += results[category][1][index]
                index = +1
                new_text.append(total)

        return new_text, new_x, new_y

    @staticmethod
    def _get_plot_data(dates, results, cumulative):
        plot_data = []
        stacked_y_values = [0 for _ in range(0, len(dates))]
        annotations = {}
        shapes = []
        for c, category in enumerate(results):
            new_text, new_x, new_y = GeneMatchPlots._stack_yvalues(annotations, category, cumulative, dates, results,
                                                                   shapes, stacked_y_values)

            results[category] = (new_x, new_y, new_text)
            plot_data.append(Scatter(
                x=results[category][0],
                y=results[category][1],
                text=results[category][2],
                hoverinfo='name',
                mode='lines',
                fill='tonexty',
                name=category,
                line=dict(width=0.5)
            ))

        plot_data.append(Scatter(
            x=[date for date in annotations],
            y=[annotations[date]['y'] for date in annotations],
            text=[annotations[date]['text'] for date in annotations],
            mode='markers',
            hoverinfo='text',
            name='',
            opacity=0,
            marker=dict(size=0, color='black')
        ))
        return plot_data, shapes

    def create_history_plot(self, cumulative=True):
        # Using annotation here to get the count by category and date
        g = [f for f in self.queryset.values('aro_gene__aro_category__category_aro_name',
                                             'result__sample__isolate__collection_date').annotate(
            count=Count('aro_gene__aro_category__category_aro_name'))]

        a = sorted(g, key=lambda k: k['result__sample__isolate__collection_date'])
        all_dates = list(set([c['result__sample__isolate__collection_date'] for c in g]))

        dates = sorted(all_dates)
        # results populated with date (x) and count (y)
        results = self._count_by_date_xy(a)

        plot_data, shapes = self._get_plot_data(dates, results, cumulative=cumulative)

        layout = Layout(
            showlegend=True,
            xaxis=dict(
                type='category',
            ),
            yaxis=dict(
                type='linear',
                range=[1, ],
                dtick=30,
            ),
            shapes=shapes,
            colorway=PLOT_PALETTE,
            hovermode='closest'
        )
        fig = Figure(data=plot_data, layout=layout)
        return plotly.offline.plot(fig, show_link=False, output_type='div', include_plotlyjs=False)
