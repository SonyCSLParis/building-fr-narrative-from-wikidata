# -*- coding: utf-8 -*-
""" Plotly figures to be used for visualisations """

import plotly.express as px

def get_fig_hist_plotly(df_input=None, x_data=None, y_data=None, nbins=None,
                        tickangle=0, title=None, width=None, height=None):
    """ Plotly figure """
    fig = px.histogram(data_frame=df_input, x=x_data, y=y_data,
                       width=width, height=height, nbins=nbins)
    fig.update_xaxes(tickangle=tickangle, categoryorder="total descending")
    fig.update_layout(title_text=title, title_x=0.5)
    return fig
