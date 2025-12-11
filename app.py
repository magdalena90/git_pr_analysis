"""Dash dashboard for PR visualisations."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dcc, html

# User aliases dictionary - map user.login to display names
user_aliases = {
    'Alex-Mackie': 'Alex',
    'DavidMc123': 'David',
    'KBodolai': 'Kristian',
    'SelenaGeo': 'Selena',
    'WillBriggs-SI': 'Will',
    'adamnoach': 'Adam',
    'aneeshnaik': 'Aneesh',
    'anna-fumagalli': 'Anna',
    'euan-si': 'Euan',
    'magdalena90': 'Magda',
    'natborn2': 'Nathan',
    'nestorSag': 'Nestor',
    'oliver-mcf': 'Oliver',
    'rob-webster-space-intelligence': 'Rob',
    'stearp': 'Steph',
    'stuartbrown4': 'Stuart',
    'wietzesuijker': 'Wietze',
}

# Load data
data_dir = Path("data")
df_mapper_template_prs = pd.read_csv(data_dir / "all_prs.csv")
df_qgis_prs = pd.read_csv(data_dir / "all_prs_qgis.csv")

df_mapper_template_prs['source'] = 'mapper_template'
df_qgis_prs['source'] = 'qgis_plugin'


def plot_cumulative_prs(dataset_selection):
    """Create an animated plot showing cumulative PRs throughout the year."""
    # Select dataset
    if dataset_selection == 'mapper_template':
        df = df_mapper_template_prs.copy()
        plot_title_prefix = 'Mapper Template PRs'
    elif dataset_selection == 'qgis_plugins':
        df = df_qgis_prs.copy()
        plot_title_prefix = 'QGIS Plugins PRs'
    elif dataset_selection == 'both':
        df = pd.concat([df_mapper_template_prs, df_qgis_prs], ignore_index=True)
        plot_title_prefix = 'All PRs'
    else:
        raise ValueError("Invalid selection. Choose 'mapper_template', 'qgis_plugins', or 'both'")

    # Preprocess data
    df['merged_at'] = pd.to_datetime(df['merged_at'])
    df_merged = df[df['merged_at'].notna()].copy()
    df_merged['year'] = df_merged['merged_at'].dt.year
    df_merged['day_of_year'] = df_merged['merged_at'].dt.dayofyear
    df_merged['date'] = df_merged['merged_at'].dt.date

    # Calculate cumulative data
    cumulative_data = []
    available_years = sorted(df_merged['year'].unique())

    for year in available_years:
        year_df = df_merged[df_merged['year'] == year].copy()
        year_df = year_df.sort_values('merged_at')

        if len(year_df) == 0:
            continue

        max_day = year_df['day_of_year'].max()
        for day in range(1, max_day + 1):
            cumulative_count = len(year_df[year_df['day_of_year'] <= day])
            cumulative_data.append({
                'day_of_year': day,
                'cumulative_prs': cumulative_count,
                'year': str(year)
            })

    df_cumulative = pd.DataFrame(cumulative_data)

    if len(df_cumulative) == 0:
        return go.Figure()

    # Create figure with animation
    fig = go.Figure()

    # Get unique years
    years = df_cumulative['year'].unique()
    colors = {'2024': '#C26E75', '2025': '#75303B'}
    default_colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']

    # Add initial traces
    for i, year in enumerate(years):
        year_color = colors.get(year, default_colors[i % len(default_colors)])
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='lines',
            name=year,
            line=dict(color=year_color, width=2),
            showlegend=True
        ))
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='markers',
            name=year,
            marker=dict(size=12, color=year_color),
            showlegend=False
        ))

    # Create frames
    frames = []
    max_day = int(df_cumulative['day_of_year'].max())

    for day in range(1, max_day + 1, 2):
        frame_data = []
        for i, year in enumerate(years):
            year_color = colors.get(year, default_colors[i % len(default_colors)])
            year_data = df_cumulative[df_cumulative['year'] == year]
            max_day_for_year = int(year_data['day_of_year'].max())

            year_data_up_to_day = year_data[year_data['day_of_year'] <= day]

            frame_data.append(go.Scatter(
                x=year_data_up_to_day['day_of_year'],
                y=year_data_up_to_day['cumulative_prs'],
                mode='lines',
                name=year,
                line=dict(color=year_color, width=2)
            ))

            if day <= max_day_for_year:
                current_point = year_data_up_to_day[year_data_up_to_day['day_of_year'] == day]
                if len(current_point) == 0:
                    current_point = year_data_up_to_day.iloc[[-1]] if len(year_data_up_to_day) > 0 else year_data_up_to_day
            else:
                current_point = year_data[year_data['day_of_year'] == max_day_for_year]

            if len(current_point) > 0:
                frame_data.append(go.Scatter(
                    x=current_point['day_of_year'],
                    y=current_point['cumulative_prs'],
                    mode='markers',
                    name=year,
                    marker=dict(size=12, color=year_color)
                ))
            else:
                frame_data.append(go.Scatter(x=[], y=[], mode='markers'))

        frames.append(go.Frame(data=frame_data, name=str(day)))

    fig.frames = frames

    fig.update_layout(
        title=f'Cumulative {plot_title_prefix} through the year',
        xaxis_title='Month',
        yaxis_title='Cumulative Number of PRs',
        height=600,
        showlegend=True,
        font=dict(family='Avenir', size=14),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            range=[0, 366],
            tickmode='array',
            tickvals=[1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 365],
            ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Dec'],
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linecolor='#e0e0e0',
            linewidth=1
        ),
        yaxis=dict(
            range=[0, df_cumulative['cumulative_prs'].max() * 1.1],
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linecolor='#e0e0e0',
            linewidth=1
        ),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {'label': 'Play', 'method': 'animate', 'args': [None, {
                    'frame': {'duration': 50, 'redraw': True},
                    'fromcurrent': True,
                    'mode': 'immediate'
                }]},
                {'label': 'Pause', 'method': 'animate', 'args': [[None], {
                    'frame': {'duration': 0, 'redraw': False},
                    'mode': 'immediate'
                }]}
            ]
        }],
        sliders=[{
            'steps': [
                {'args': [[f.name], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}],
                 'label': f'Day {f.name}', 'method': 'animate'}
                for f in fig.frames[::7]
            ],
            'active': 0,
            'x': 0.1,
            'len': 0.9,
            'xanchor': 'left',
            'y': 0,
            'yanchor': 'top'
        }]
    )

    return fig


def plot_cumulative_prs_by_user(dataset_selection, year=2025):
    """Create an animated plot showing cumulative PRs throughout the year for each user."""
    # Select dataset
    if dataset_selection == 'mapper_template':
        df = df_mapper_template_prs.copy()
        plot_title_prefix = 'Mapper Template'
    elif dataset_selection == 'qgis_plugins':
        df = df_qgis_prs.copy()
        plot_title_prefix = 'QGIS Plugins'
    elif dataset_selection == 'both':
        df = pd.concat([df_mapper_template_prs, df_qgis_prs], ignore_index=True)
        plot_title_prefix = 'All'
    else:
        raise ValueError("Invalid selection. Choose 'mapper_template', 'qgis_plugins', or 'both'")

    # Preprocess data
    df['merged_at'] = pd.to_datetime(df['merged_at'])
    df_merged = df[df['merged_at'].notna()].copy()
    df_merged['year'] = df_merged['merged_at'].dt.year
    df_merged['day_of_year'] = df_merged['merged_at'].dt.dayofyear
    df_merged['date'] = df_merged['merged_at'].dt.date

    # Filter for specified year
    df_year = df_merged[df_merged['year'] == year].copy()

    if len(df_year) == 0:
        return go.Figure()

    # Apply user aliases
    df_year['user_display'] = df_year['user.login'].map(user_aliases).fillna(df_year['user.login'])

    # Calculate cumulative data by user
    cumulative_data = []
    users = sorted(df_year['user_display'].unique())

    for user in users:
        user_df = df_year[df_year['user_display'] == user].copy()
        user_df = user_df.sort_values('merged_at')

        if len(user_df) == 0:
            continue

        max_day = user_df['day_of_year'].max()
        for day in range(1, max_day + 1):
            cumulative_count = len(user_df[user_df['day_of_year'] <= day])
            cumulative_data.append({
                'day_of_year': day,
                'cumulative_prs': cumulative_count,
                'user': user
            })

    df_cumulative = pd.DataFrame(cumulative_data)

    if len(df_cumulative) == 0:
        return go.Figure()

    # Create figure with animation
    fig = go.Figure()

    # Get unique users
    users = df_cumulative['user'].unique()

    # Generate distinct colors for each user
    import plotly.express as px
    color_palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2 + px.colors.qualitative.Pastel
    colors = {user: color_palette[i % len(color_palette)] for i, user in enumerate(users)}

    # Add initial traces
    for user in users:
        user_color = colors[user]
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='lines',
            name=user,
            line=dict(color=user_color, width=2),
            showlegend=True,
            hovertemplate=f'<b>{user}</b><br>Cumulative PRs: %{{y}}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='markers',
            name=user,
            marker=dict(size=10, color=user_color),
            showlegend=False,
            hovertemplate=f'<b>{user}</b><br>Cumulative PRs: %{{y}}<extra></extra>'
        ))

    # Create frames
    frames = []
    max_day = int(df_cumulative['day_of_year'].max())

    for day in range(1, max_day + 1, 2):
        frame_data = []
        for user in users:
            user_color = colors[user]
            user_data = df_cumulative[df_cumulative['user'] == user]
            max_day_for_user = int(user_data['day_of_year'].max())

            user_data_up_to_day = user_data[user_data['day_of_year'] <= day]

            frame_data.append(go.Scatter(
                x=user_data_up_to_day['day_of_year'],
                y=user_data_up_to_day['cumulative_prs'],
                mode='lines',
                name=user,
                line=dict(color=user_color, width=2),
                hovertemplate=f'<b>{user}</b><br>Cumulative PRs: %{{y}}<extra></extra>'
            ))

            if day <= max_day_for_user:
                current_point = user_data_up_to_day[user_data_up_to_day['day_of_year'] == day]
                if len(current_point) == 0:
                    current_point = user_data_up_to_day.iloc[[-1]] if len(user_data_up_to_day) > 0 else user_data_up_to_day
            else:
                current_point = user_data[user_data['day_of_year'] == max_day_for_user]

            if len(current_point) > 0:
                frame_data.append(go.Scatter(
                    x=current_point['day_of_year'],
                    y=current_point['cumulative_prs'],
                    mode='markers',
                    name=user,
                    marker=dict(size=10, color=user_color),
                    hovertemplate=f'<b>{user}</b><br>Cumulative PRs: %{{y}}<extra></extra>'
                ))
            else:
                frame_data.append(go.Scatter(x=[], y=[], mode='markers'))

        frames.append(go.Frame(data=frame_data, name=str(day)))

    fig.frames = frames

    fig.update_layout(
        title=f'Cumulative {plot_title_prefix} PRs by User ({year})',
        xaxis_title='Month',
        yaxis_title='Cumulative Number of PRs',
        height=600,
        showlegend=True,
        font=dict(family='Avenir', size=14),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            range=[0, 366],
            tickmode='array',
            tickvals=[1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 365],
            ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Dec'],
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linecolor='#e0e0e0',
            linewidth=1
        ),
        yaxis=dict(
            range=[0, df_cumulative['cumulative_prs'].max() * 1.1],
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linecolor='#e0e0e0',
            linewidth=1
        ),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {'label': 'Play', 'method': 'animate', 'args': [None, {
                    'frame': {'duration': 50, 'redraw': True},
                    'fromcurrent': True,
                    'mode': 'immediate'
                }]},
                {'label': 'Pause', 'method': 'animate', 'args': [[None], {
                    'frame': {'duration': 0, 'redraw': False},
                    'mode': 'immediate'
                }]}
            ]
        }],
        sliders=[{
            'steps': [
                {'args': [[f.name], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}],
                 'label': f'Day {f.name}', 'method': 'animate'}
                for f in fig.frames[::7]
            ],
            'active': 0,
            'x': 0.1,
            'len': 0.9,
            'xanchor': 'left',
            'y': 0,
            'yanchor': 'top'
        }]
    )

    return fig


# Initialize the Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("PR Visualisations Dashboard", style={'textAlign': 'center', 'fontFamily': 'Avenir'}),

    html.Div([
        html.Label("Select Dataset:", style={'fontWeight': 'bold', 'fontFamily': 'Avenir'}),
        dcc.Dropdown(
            id='dataset-dropdown',
            options=[
                {'label': 'Mapper Template PRs', 'value': 'mapper_template'},
                {'label': 'QGIS Plugin PRs', 'value': 'qgis_plugins'},
                {'label': 'All PRs', 'value': 'both'}
            ],
            value='both',
            style={'width': '300px', 'fontFamily': 'Avenir'}
        ),
    ], style={'margin': '20px', 'fontFamily': 'Avenir'}),

    html.Div([
        dcc.Graph(id='year-comparison-graph'),
    ]),

    html.Div([
        dcc.Graph(id='user-comparison-graph'),
    ]),
], style={'fontFamily': 'Avenir'})


@callback(
    Output('year-comparison-graph', 'figure'),
    Input('dataset-dropdown', 'value')
)
def update_year_graph(dataset_selection):
    """Update the year comparison graph based on dataset selection."""
    return plot_cumulative_prs(dataset_selection)


@callback(
    Output('user-comparison-graph', 'figure'),
    Input('dataset-dropdown', 'value')
)
def update_user_graph(dataset_selection):
    """Update the user comparison graph based on dataset selection."""
    return plot_cumulative_prs_by_user(dataset_selection, year=2025)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)

