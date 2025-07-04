import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import re

# Load and preprocess dataset
df = pd.read_csv("spacex_clean_data.csv")

# Extract payload mass in kg from 'payload_mass'
def extract_kg(payload):
    match = re.search(r"([\d,]+)\s*kg", str(payload))
    if match:
        return float(match.group(1).replace(',', ''))
    return None

df['payload_kg'] = df['payload_mass'].apply(extract_kg)

# Create success column from launch_outcome
df = df[df['launch_outcome'].isin(['Success', 'Failure'])].copy()
df['success'] = df['launch_outcome'].map({'Success': 1, 'Failure': 0})

# Extract booster short name (optional, or just reuse version column)
df['booster'] = df['version,_booster[h]'].astype(str).str.extract(r'(B\d{4}-\d+|F9.*|FH.*)', expand=False)

# Create Dash app
app = dash.Dash(__name__)
launch_sites = df['launch_site'].dropna().unique().tolist()

site_options = [{'label': 'All Sites', 'value': 'ALL'}] + \
               [{'label': site, 'value': site} for site in launch_sites]

app.layout = html.Div([
    html.H1("SpaceX Launch Records Dashboard", style={'textAlign': 'center'}),

    dcc.Dropdown(id='site-dropdown', options=site_options, value='ALL', placeholder="Select a Launch Site"),
    html.Br(),

    dcc.Graph(id='success-pie-chart'),
    html.Br(),

    html.P("Payload range (Kg):"),
    dcc.RangeSlider(id='payload-slider',
                    min=0, max=10000, step=1000,
                    marks={0: '0', 2500: '2500', 5000: '5000', 7500: '7500', 10000: '10000'},
                    value=[0, 10000]),
    dcc.Graph(id='success-payload-scatter-chart')
])

@app.callback(
    Output('success-pie-chart', 'figure'),
    Input('site-dropdown', 'value'))
def update_pie_chart(selected_site):
    if selected_site == 'ALL':
        fig = px.pie(df, names='launch_site', title='Total Success Launches by Site')
    else:
        filtered_df = df[df['launch_site'] == selected_site]
        outcome_counts = filtered_df['launch_outcome'].value_counts().reset_index()
        outcome_counts.columns = ['launch_outcome', 'count']
        fig = px.pie(outcome_counts, names='launch_outcome', values='count',
                     title=f'Success vs. Failure for site {selected_site}')
    return fig

@app.callback(
    Output('success-payload-scatter-chart', 'figure'),
    [Input('site-dropdown', 'value'),
     Input('payload-slider', 'value')])
def update_scatter_chart(site, payload_range):
    filtered_df = df[(df['payload_kg'] >= payload_range[0]) & (df['payload_kg'] <= payload_range[1])]
    if site != 'ALL':
        filtered_df = filtered_df[filtered_df['launch_site'] == site]
    fig = px.scatter(filtered_df, x='payload_kg', y='success', color='booster',
                     title='Payload vs. Outcome for selected site and payload range',
                     labels={'payload_kg': 'Payload Mass (kg)', 'success': 'Launch Outcome'})
    return fig

if __name__ == '__main__':
    app.run(debug=True)

