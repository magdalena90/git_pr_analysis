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
    'benritchie': 'Ben',
    'stviaene-si': 'Stig',
    'jam3s-in-space': 'James',
    'harryC-space-intelligence': 'Harry',
    'dp-actions[bot]': 'copilot',
    'henryspeir': 'Henry',
}

# Load data
data_dir = Path("data")
df_all_prs = pd.read_csv(data_dir / "all_prs_detailed_qgis.csv")

# Remove copilot entries
df_all_prs = df_all_prs[df_all_prs['user.login'] != 'dp-actions[bot]'].copy()

# Remove rows with additions>30_000 (I suspect these are errors)
df_all_prs = df_all_prs[df_all_prs['additions'] <= 30000].copy()

# Create 'source' column based on base.repo.name
def assign_source(repo_name):
    if repo_name == 'mapper-project-template':
        return 'mapper_template'
    elif repo_name == 'space-intelligence':
        return 'space_intelligence'
    else:
        return 'qgis_plugins'

df_all_prs['source'] = df_all_prs['base.repo.name'].apply(assign_source)


def get_plot_title_prefix(dataset_selection):
    """Generate plot title prefix from selected datasets."""
    if not dataset_selection or len(dataset_selection) == 0:
        return 'No Data'
    
    # Map source values to display names (without 'PRs')
    name_map = {
        'mapper_template': 'Mapper Template',
        'space_intelligence': 'Space Intelligence',
        'qgis_plugins': 'QGIS Plugins'
    }
    
    # Get display names for selected datasets
    display_names = [name_map.get(source, source) for source in dataset_selection]
    
    # Concatenate with ' + ' and add 'PRs' at the end
    if len(display_names) == 1:
        return f'{display_names[0]} PRs'
    else:
        return f'{" + ".join(display_names)} PRs'


def get_weight_label(weight_by):
    """Get the display label for the weight metric."""
    labels = {
        'pr_count': 'PRs',
        'lines_added': 'Lines Added',
        'net_lines': 'Net Lines Added',
        'comments': 'Comments'
    }
    return labels.get(weight_by, 'PRs')


def calculate_weight(df, weight_by):
    """Calculate weight for each row based on the selected metric."""
    if weight_by == 'pr_count':
        return 1
    elif weight_by == 'lines_added':
        return df['additions'].fillna(0)
    elif weight_by == 'net_lines':
        return (df['additions'].fillna(0) - df['deletions'].fillna(0))
    elif weight_by == 'comments':
        return df['review_comment_count'].fillna(0) + 1
    else:
        return 1


def plot_cumulative_prs(dataset_selection, weight_by='pr_count'):
    """Create an animated plot showing cumulative PRs throughout the year."""
    # Select dataset - dataset_selection is now a list
    if not dataset_selection or len(dataset_selection) == 0:
        return go.Figure()
    
    # Filter data based on selected sources
    df = df_all_prs[df_all_prs['source'].isin(dataset_selection)].copy()
    plot_title_prefix = get_plot_title_prefix(dataset_selection)

    # Preprocess data
    df['merged_at'] = pd.to_datetime(df['merged_at'])
    df_merged = df[df['merged_at'].notna()].copy()
    df_merged['year'] = df_merged['merged_at'].dt.year
    df_merged['day_of_year'] = df_merged['merged_at'].dt.dayofyear
    df_merged['date'] = df_merged['merged_at'].dt.date
    
    # Add weight column
    df_merged['weight'] = calculate_weight(df_merged, weight_by)

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
            cumulative_count = year_df[year_df['day_of_year'] <= day]['weight'].sum()
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
            mode='markers+text',
            name=year,
            marker=dict(size=12, color=year_color),
            text=[],
            textposition='middle right',
            textfont=dict(color=year_color, size=12, family='Avenir'),
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
                    mode='markers+text',
                    name=year,
                    marker=dict(size=12, color=year_color),
                    text=[year],
                    textposition='middle right',
                    textfont=dict(color=year_color, size=12, family='Avenir')
                ))
            else:
                frame_data.append(go.Scatter(x=[], y=[], mode='markers+text', text=[]))

        frames.append(go.Frame(data=frame_data, name=str(day)))

    fig.frames = frames

    weight_label = get_weight_label(weight_by)
    fig.update_layout(
        title=f'Cumulative {plot_title_prefix} through the year',
        xaxis_title='Month',
        yaxis_title=f'Cumulative {weight_label}',
        height=600,
        showlegend=True,
        font=dict(family='Space Grotesk', size=14),
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
                    'frame': {'duration': 100, 'redraw': True},
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


def plot_cumulative_prs_by_user(dataset_selection, year=2025, weight_by='pr_count'):
    """Create an animated plot showing cumulative PRs throughout the year for each user."""
    # Select dataset - dataset_selection is now a list
    if not dataset_selection or len(dataset_selection) == 0:
        return go.Figure()
    
    # Filter data based on selected sources
    df = df_all_prs[df_all_prs['source'].isin(dataset_selection)].copy()
    
    # Get plot title without 'PRs' suffix for user comparison
    title_parts = get_plot_title_prefix(dataset_selection)
    # Remove ' PRs' from the end to add it back in the final title
    plot_title_prefix = title_parts.replace(' PRs', '')

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
    
    # Add weight column
    df_year['weight'] = calculate_weight(df_year, weight_by)

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
            cumulative_count = user_df[user_df['day_of_year'] <= day]['weight'].sum()
            cumulative_data.append({
                'day_of_year': day,
                'cumulative_prs': cumulative_count,
                'user': user
            })

    df_cumulative = pd.DataFrame(cumulative_data)

    if len(df_cumulative) == 0:
        return go.Figure()

    # Identify top 7 users by final cumulative value
    n = 7
    final_values = df_cumulative.groupby('user')['cumulative_prs'].max().sort_values(ascending=False)
    top_n_users = set(final_values.head(n).index)

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
        show_text = user in top_n_users
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='markers+text' if show_text else 'markers',
            name=user,
            marker=dict(size=10, color=user_color),
            text=[],
            textposition='middle right' if show_text else None,
            textfont=dict(color=user_color, size=10, family='Avenir') if show_text else None,
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
                show_text = user in top_n_users
                frame_data.append(go.Scatter(
                    x=current_point['day_of_year'],
                    y=current_point['cumulative_prs'],
                    mode='markers+text' if show_text else 'markers',
                    name=user,
                    marker=dict(size=10, color=user_color),
                    text=[user] if show_text else [],
                    textposition='middle right' if show_text else None,
                    textfont=dict(color=user_color, size=14, family='Avenir') if show_text else None,
                    hovertemplate=f'<b>{user}</b><br>Cumulative PRs: %{{y}}<extra></extra>'
                ))
            else:
                frame_data.append(go.Scatter(x=[], y=[], mode='markers', text=[]))

        frames.append(go.Frame(data=frame_data, name=str(day)))

    fig.frames = frames

    weight_label = get_weight_label(weight_by)
    fig.update_layout(
        title=f'Cumulative {plot_title_prefix} PRs by User ({year})',
        xaxis_title='Month',
        yaxis_title=f'Cumulative {weight_label}',
        height=600,
        showlegend=True,
        font=dict(family='Space Grotesk', size=14),
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
                    'frame': {'duration': 160, 'redraw': True},
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


def plot_cumulative_reviews_by_user(dataset_selection, year=2025):
    """Create an animated plot showing cumulative reviews throughout the year for each user."""
    import ast
    
    # Select dataset
    if not dataset_selection or len(dataset_selection) == 0:
        return go.Figure()
    
    # Filter data based on selected sources
    df = df_all_prs[df_all_prs['source'].isin(dataset_selection)].copy()
    
    # Get plot title without 'PRs' suffix
    title_parts = get_plot_title_prefix(dataset_selection)
    plot_title_prefix = title_parts.replace(' PRs', '')

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

    # Parse requested_reviewers and expand rows
    review_records = []
    for _, row in df_year.iterrows():
        reviewers_str = row['requested_reviewers']
        if pd.isna(reviewers_str) or reviewers_str == '[]':
            continue
        
        try:
            reviewers_list = ast.literal_eval(reviewers_str)
            if isinstance(reviewers_list, list) and len(reviewers_list) > 0:
                for reviewer_dict in reviewers_list:
                    if isinstance(reviewer_dict, dict) and 'login' in reviewer_dict:
                        review_records.append({
                            'reviewer_login': reviewer_dict['login'],
                            'merged_at': row['merged_at'],
                            'day_of_year': row['day_of_year'],
                            'date': row['date']
                        })
        except (ValueError, SyntaxError):
            continue
    
    if len(review_records) == 0:
        return go.Figure()
    
    df_reviews = pd.DataFrame(review_records)
    
    # Apply user aliases
    df_reviews['user_display'] = df_reviews['reviewer_login'].map(user_aliases).fillna(df_reviews['reviewer_login'])
    
    # Calculate cumulative data by reviewer
    cumulative_data = []
    users = sorted(df_reviews['user_display'].unique())

    for user in users:
        user_df = df_reviews[df_reviews['user_display'] == user].copy()
        user_df = user_df.sort_values('merged_at')

        if len(user_df) == 0:
            continue

        max_day = user_df['day_of_year'].max()
        for day in range(1, max_day + 1):
            cumulative_count = len(user_df[user_df['day_of_year'] <= day])
            cumulative_data.append({
                'day_of_year': day,
                'cumulative_reviews': cumulative_count,
                'user': user
            })

    df_cumulative = pd.DataFrame(cumulative_data)

    if len(df_cumulative) == 0:
        return go.Figure()

    # Identify top 7 users by final cumulative value
    n = 7
    final_values = df_cumulative.groupby('user')['cumulative_reviews'].max().sort_values(ascending=False)
    top_n_users = set(final_values.head(n).index)

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
            hovertemplate=f'<b>{user}</b><br>Cumulative Reviews: %{{y}}<extra></extra>'
        ))
        show_text = user in top_n_users
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='markers+text' if show_text else 'markers',
            name=user,
            marker=dict(size=10, color=user_color),
            text=[],
            textposition='middle right' if show_text else None,
            textfont=dict(color=user_color, size=10, family='Avenir') if show_text else None,
            showlegend=False,
            hovertemplate=f'<b>{user}</b><br>Cumulative Reviews: %{{y}}<extra></extra>'
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
                y=user_data_up_to_day['cumulative_reviews'],
                mode='lines',
                name=user,
                line=dict(color=user_color, width=2),
                hovertemplate=f'<b>{user}</b><br>Cumulative Reviews: %{{y}}<extra></extra>'
            ))

            if day <= max_day_for_user:
                current_point = user_data_up_to_day[user_data_up_to_day['day_of_year'] == day]
                if len(current_point) == 0:
                    current_point = user_data_up_to_day.iloc[[-1]] if len(user_data_up_to_day) > 0 else user_data_up_to_day
            else:
                current_point = user_data[user_data['day_of_year'] == max_day_for_user]

            if len(current_point) > 0:
                show_text = user in top_n_users
                frame_data.append(go.Scatter(
                    x=current_point['day_of_year'],
                    y=current_point['cumulative_reviews'],
                    mode='markers+text' if show_text else 'markers',
                    name=user,
                    marker=dict(size=10, color=user_color),
                    text=[user] if show_text else [],
                    textposition='middle right' if show_text else None,
                    textfont=dict(color=user_color, size=14, family='Avenir') if show_text else None,
                    hovertemplate=f'<b>{user}</b><br>Cumulative Reviews: %{{y}}<extra></extra>'
                ))
            else:
                frame_data.append(go.Scatter(x=[], y=[], mode='markers', text=[]))

        frames.append(go.Frame(data=frame_data, name=str(day)))

    fig.frames = frames

    fig.update_layout(
        title=f'Cumulative {plot_title_prefix} Reviews by User ({year})',
        xaxis_title='Month',
        yaxis_title='Cumulative Reviews',
        height=600,
        showlegend=True,
        font=dict(family='Space Grotesk', size=14),
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
            range=[0, df_cumulative['cumulative_reviews'].max() * 1.1],
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
                    'frame': {'duration': 160, 'redraw': True},
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
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap']
app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("PR Visualisations Dashboard", style={'textAlign': 'center', 'fontFamily': 'Space Grotesk'}),

    html.Div([
        html.Div([
            html.Label("Select Dataset:", style={'fontWeight': 'bold', 'fontFamily': 'Avenir', 'marginBottom': '10px', 'display': 'block'}),
            html.Div([
                dcc.Checklist(
                    id='dataset-mapper',
                    options=[{'label': ' Mapper Template PRs', 'value': 'mapper_template'}],
                    value=['mapper_template'],
                    style={'display': 'inline-block', 'marginRight': '20px', 'fontFamily': 'Avenir'}
                ),
                dcc.Checklist(
                    id='dataset-space',
                    options=[{'label': ' Space Intelligence PRs', 'value': 'space_intelligence'}],
                    value=['space_intelligence'],
                    style={'display': 'inline-block', 'marginRight': '20px', 'fontFamily': 'Avenir'}
                ),
                dcc.Checklist(
                    id='dataset-qgis',
                    options=[{'label': ' QGIS Plugin PRs', 'value': 'qgis_plugins'}],
                    value=['qgis_plugins'],
                    style={'display': 'inline-block', 'fontFamily': 'Avenir'}
                ),
            ]),
        ], style={'display': 'inline-block', 'marginRight': '40px', 'fontFamily': 'Avenir', 'verticalAlign': 'top'}),

        html.Div([
            html.Label("Weight By:", style={'fontWeight': 'bold', 'fontFamily': 'Avenir'}),
            dcc.Dropdown(
                id='weight-dropdown',
                options=[
                    {'label': 'PR Count', 'value': 'pr_count'},
                    {'label': 'Number of Lines Added', 'value': 'lines_added'},
                    {'label': 'Net Number of Lines Added', 'value': 'net_lines'},
                    {'label': 'Number of Comments', 'value': 'comments'}
                ],
                value='pr_count',
                style={'width': '350px', 'fontFamily': 'Avenir'}
            ),
        ], style={'display': 'inline-block', 'fontFamily': 'Avenir'}),
    ], style={'margin': '20px', 'fontFamily': 'Avenir'}),

    html.Div([
        dcc.Graph(id='year-comparison-graph'),
    ]),

    html.Div([
        dcc.Graph(id='user-comparison-graph'),
    ]),

    html.Div([
        dcc.Graph(id='reviews-comparison-graph'),
    ]),
], style={'fontFamily': 'Avenir'})


@callback(
    Output('year-comparison-graph', 'figure'),
    Input('dataset-mapper', 'value'),
    Input('dataset-space', 'value'),
    Input('dataset-qgis', 'value'),
    Input('weight-dropdown', 'value')
)
def update_year_graph(mapper_checked, space_checked, qgis_checked, weight_by):
    """Update the year comparison graph based on dataset and weight selection."""
    # Combine all checked datasets
    dataset_selection = []
    if mapper_checked:
        dataset_selection.extend(mapper_checked)
    if space_checked:
        dataset_selection.extend(space_checked)
    if qgis_checked:
        dataset_selection.extend(qgis_checked)
    return plot_cumulative_prs(dataset_selection, weight_by)


@callback(
    Output('user-comparison-graph', 'figure'),
    Input('dataset-mapper', 'value'),
    Input('dataset-space', 'value'),
    Input('dataset-qgis', 'value'),
    Input('weight-dropdown', 'value')
)
def update_user_graph(mapper_checked, space_checked, qgis_checked, weight_by):
    """Update the user comparison graph based on dataset and weight selection."""
    # Combine all checked datasets
    dataset_selection = []
    if mapper_checked:
        dataset_selection.extend(mapper_checked)
    if space_checked:
        dataset_selection.extend(space_checked)
    if qgis_checked:
        dataset_selection.extend(qgis_checked)
    return plot_cumulative_prs_by_user(dataset_selection, year=2025, weight_by=weight_by)


@callback(
    Output('reviews-comparison-graph', 'figure'),
    Input('dataset-mapper', 'value'),
    Input('dataset-space', 'value'),
    Input('dataset-qgis', 'value')
)
def update_reviews_graph(mapper_checked, space_checked, qgis_checked):
    """Update the reviews comparison graph based on dataset selection."""
    # Combine all checked datasets
    dataset_selection = []
    if mapper_checked:
        dataset_selection.extend(mapper_checked)
    if space_checked:
        dataset_selection.extend(space_checked)
    if qgis_checked:
        dataset_selection.extend(qgis_checked)
    return plot_cumulative_reviews_by_user(dataset_selection, year=2025)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=True)

