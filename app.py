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

app.config.suppress_callback_exceptions = True

external_stylesheets = [
    'https://codepen.io/unicorndy/pen/GRJXrvP.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('Space_Corrected.csv').drop(columns=['Detail'])

df['Location'].loc[
    df.Location == 'LP-41, Kauai, Pacific Missile Range Facility'
    ] = 'LP-41, Kauai, Pacific Missile Range Facility, USA'
df['Location'].loc[
    df.Location == 'Launch Plateform, Shahrud Missile Test Site'
    ] = 'Launch Plateform, Shahrud Missile Test Site, Iran'
df['Location'].loc[
    df.Location == 'Stargazer, Base Aerea de Gando, Gran Canaria'
    ] = 'Stargazer, Base Aerea de Gando, Gran Canaria, Spain'
df['Location'].loc[
    df.Location == 'Vertical Launch Area, Spaceport America, New Mexico'
    ] = 'Vertical Launch Area, Spaceport America, New Mexico, USA'

lat_long = pd.read_csv('LatLong.csv')
lat_long = lat_long.rename(columns={
    'Unnamed: 0': 'Location',
    '0': 'Lat',
    '1': 'Long'})
df = df.merge(lat_long, on='Location')
df.fillna(5, inplace=True)

countries = list(np.unique(df['Location'].apply(
    lambda loc: loc.split(',')[-1][1:])))
countries_dicts = []
for c in countries:
    d = {}
    d['label'] = c
    d['value'] = c
    countries_dicts.append(d)

app.layout = html.Div(
    [
        html.Div(
            className='four columns',
            children=[
                html.Div(
                    className='row',
                    children=[
                        html.H1('Dash - SPACE MISSIONS'),
                        html.P(
                            'Visualizing space missions ' +
                            'across the world since 1957 with Plotly - Dash'),
                        html.P('Select a location from the dropdown below.'),
                        dcc.Dropdown(
                            id='countries',
                            options=countries_dicts,
                            value='Select a location',
                            style={
                                'background-color': '#111111'
                            }
                        ),
                        html.Div(id='status-container'),
                    ]
                ),
                html.Div(
                    className='row',
                    children=[
                        html.Div(id='company-pie')
                    ]
                )
            ],
            style={
                'margin-top': '50px',
                'border-right': '1px solid #444444'
            }
        ),
        html.Div(
            className='five columns',
            children=[
                html.Div(
                    className='row',
                    children=[
                        html.Div(id='mission-map'),
                    ],
                    style={
                        'margin-top': '50px'
                    }
                ),
                html.Div(
                    className='row ts',
                    children=[
                        html.Div(id='country-time-series')
                    ],
                )
            ],
            style={
                'margin-top': '50px',
                'border-right': '1px solid #444444'
            }
        ),
        html.Div(
            className='three columns',
            children=[
                html.Div(
                    children=[
                        html.Div(id='country-dist')
                    ]
                )
            ]
        )
    ]
)


@app.callback(
    dash.dependencies.Output('dd-output-container', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_country_output(value):
    return html.H3(value)


@app.callback(
    dash.dependencies.Output('status-container', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_statuses(value):
    n_df = df[df.Location.str.contains(value)]

    n_df['Country'] = np.repeat(
        list(np.unique(
            n_df['Location'].apply(
                lambda loc: loc.split(',')[-1][1:]
                )))[0], len(n_df))

    df_rockets = n_df.drop_duplicates(subset=' Rocket')
    fig = px.bar(
        df_rockets,
        x=' Rocket',
        y='Country',
        color='Status Rocket',
        orientation='h',
        color_discrete_sequence=px.colors.sequential.Magma[2:],
        title="Status of Country's Rockets")
    fig.update_layout(
        barmode='stack',
        height=250,
        template='plotly_dark')
    return html.Div(
        dcc.Graph(id='rocket-statuses', figure=fig)
    )


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
                        title="Mission Companies",
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
        n_df['Status Mission'].str.contains('Success')]
    df_failed = n_df[
        n_df['Status Mission'].str.contains('Failure')]
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
        name='Successful',
        marker=dict(color=px.colors.sequential.Magma[8]))
    fig.add_scatter(
        x=failure_dates.index,
        y=failure_dates.values,
        mode='lines',
        name='Failed',
        marker=dict(color=px.colors.sequential.Magma[4]))
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        title='Number of Successful and Failed Space Missions Per Year',
        xaxis_title='Year',
        yaxis_title='Number of Space Missions',
        legend=dict(
            yanchor='bottom',
            xanchor='left'
        )
        )

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
                height=950,
                title='Space Race Leading Countries')
            )

    fig.update_layout(template='plotly_dark')

    return html.Div(
        dcc.Graph(id='dist-bar', figure=fig),
        style={
            'margin-top': '25px'
        }
    )


@app.callback(
    dash.dependencies.Output('mission-map', 'children'),
    [dash.dependencies.Input('countries', 'value')]
)
def update_map(value):
    df_filtered = df[df.Location.str.contains(value)]

    statuses = np.unique(df_filtered['Status Mission'])

    df_filtered['Status Mission'] = pd.Categorical(
        df_filtered['Status Mission'])
    df_filtered['Code'] = df_filtered['Status Mission'].cat.codes

    fig = go.Figure()

    col_scale = px.colors.sequential.Magma[4:4+len(statuses)]

    for s, c in zip(statuses, col_scale):
        n_df = df_filtered[df_filtered['Status Mission'] == s]
        fig.add_trace(go.Scattergeo(
            lon=n_df['Long'],
            lat=n_df['Lat'],
            text=n_df['Location'],
            marker=dict(
                color=c,
                symbol=n_df['Code'],
                size=10
            ),
            showlegend=True,
            name=s
        ))

    fig.update_geos(projection_type='orthographic')
    fig.update_layout(
        template='plotly_dark',
        height=400,
        width=600,
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 20
        },
        title='Geographical Locations of Missions'
    )
    fig.update_layout(legend={
        'itemsizing': 'constant',
        'xanchor': 'left'
        })
    return html.Div(
        dcc.Graph(id='world-map', figure=fig)
    )


if __name__ == '__main__':
    app.run_server(debug=True)
