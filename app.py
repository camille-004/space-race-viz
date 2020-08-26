# pylint:disable=E1101

import numpy as np
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

app = dash.Dash(__name__)
external_stylesheets = [
    'assets/styles.css', 'https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('Space_Corrected.csv').drop(columns=['Detail'])

countries = list(np.unique(df['Location'].apply(
    lambda loc: loc.split(',')[-1][1:])))
countries.remove('New Mexico')
countries_dicts = []
for c in countries:
    d = {}
    d['label'] = c
    d['value'] = c
    countries_dicts.append(d)

app.layout = html.Div([
    dcc.Dropdown(
        id='countries',
        options=countries_dicts,
        value='Select a location'
    ),
    html.Div(id='dd-output-container'),
    html.Div(id='table-container'),
    html.Div(id='company-pie'),
    html.Div(id='country-time-series'),
    html.Div(id='country-dist')
])


def generate_table(df, max_rows=5):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df.columns[2:]])] +

        # Body
        [html.Tr([
            html.Td(df.iloc[i][col]) for col in df.columns[2:]
        ]) for i in range(min(len(df), max_rows))]
    )


@app.callback(
    dash.dependencies.Output('dd-output-container', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_country_output(value):
    return html.H1(value)


@app.callback(
    dash.dependencies.Output('table-container', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def display_table(value):
    if value is None:
        return generate_table(df)
    n_df = df[df.Location.str.contains(value)]
    return generate_table(n_df)


@app.callback(
    dash.dependencies.Output('company-pie', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_pie(value):
    n_df = df[df.Location.str.contains(value)]

    companies = list(n_df['Company Name'].value_counts().index)
    value_counts = list(n_df['Company Name'].value_counts().values)

    fig = go.Figure(data=[go.Pie(
        labels=companies,
        values=value_counts,
        textinfo='percent',
        hole=0.3)],
                    layout=go.Layout(
                        title="Companies",
                        width=600,
                        height=300
                    ))
    fig.update_traces(marker=dict(
        colors=px.colors.sequential.Magma))
    fig.update_layout(template='plotly_dark')
    return html.Div(
        dcc.Graph(id='pie-chart', figure=fig)
    )


@app.callback(
    dash.dependencies.Output('country-time-series', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_ts(value):
    n_df = df[df.Location.str.contains(value)]

    n_df['Datum'] = pd.to_datetime(n_df['Datum'], utc=True)
    df_successful = n_df[
        n_df['Status Mission'] == 'Success']
    df_failed = n_df[
        n_df['Status Mission'] == 'Failure']
    successful_dates = pd.DatetimeIndex(
        df_successful['Datum']).to_period(
            'Y').value_counts().sort_index().to_timestamp()
    failure_dates = pd.DatetimeIndex(
        df_failed['Datum']).to_period(
            'Y').value_counts().sort_index().to_timestamp()

    fig = go.Figure()
    fig.update_layout(template='plotly_dark')
    fig.add_scatter(
        x=successful_dates.index,
        y=successful_dates.values,
        mode='lines',
        name='Successful Missions',
        marker=dict(color=px.colors.sequential.Magma[8]))
    fig.add_scatter(
        x=failure_dates.index,
        y=failure_dates.values,
        mode='lines',
        name='Failed Missions',
        marker=dict(color=px.colors.sequential.Magma[4]))
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        title='Number of Successful and Failed Space Missions Per Year',
        xaxis_title='Year',
        yaxis_title='Number of Space Missions',
        width=600,
        height=450)

    return html.Div(
        dcc.Graph(id='time-series', figure=fig)
    )


@app.callback(
    dash.dependencies.Output('country-dist', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_dist(value):
    if value is None:
        return html.Div()

    countries = list(np.unique(df['Location'].apply(
        lambda loc: loc.split(',')[-1][1:])))
    num_countries = {}

    for c in countries:
        num_countries[c] = len(df[df.Location.str.contains(c)])
    df_dict = {
        'Country': list(num_countries.keys()),
        'Number': list(num_countries.values())}
    n_df = pd.DataFrame.from_dict(df_dict).sort_values(
        by='Number', ascending=True).reset_index().drop(
            columns=['index'])

    colors = [px.colors.sequential.Magma[3], ] * len(countries)

    idx = n_df.loc[n_df['Country'] == value].index[0]
    colors[idx] = px.colors.sequential.Magma[5]
    fig = go.Figure(data=[
        go.Bar(
            x=n_df['Number'],
            y=n_df['Country'],
            orientation='h',
            marker_color=colors,
            )],
            layout=go.Layout(
                height=600,
                width=600,
                title='Leading Countries in the Space Race')
            )

    fig.update_layout(template='plotly_dark')

    return html.Div(
        dcc.Graph(id='dist-bar', figure=fig)
    )


if __name__ == '__main__':
    app.run_server(debug=True)
