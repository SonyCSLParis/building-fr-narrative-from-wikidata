""" Plotly figures to be used for visualisations """

import plotly.express as px

def get_fig_hist_plotly(df=None, x=None, y=None, nbins=None,
                        tickangle=0, title=None, width=None, height=None):
    """ Plotly figure """
    fig = px.histogram(data_frame=df, x=x, y=y, width=width, height=height, nbins=nbins)
    fig.update_xaxes(tickangle=tickangle, categoryorder="total descending")
    fig.update_layout(title_text=title, title_x=0.5)
    return fig
