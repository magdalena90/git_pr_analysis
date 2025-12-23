# PR Visualisations Dashboard

Interactive Dash dashboard for visualizing Pull Request data from Space Intelligence repositories.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
python app.py
```

3. Open your browser at `http://localhost:8050`

## Features

- **Dataset Selection**: Choose between Mapper Template PRs, Space Intelligence PRs, QGIS Plugin PRs, or all combined
- **Year Comparison**: Animated visualization comparing PR activity between years
- **User Comparison**: Track individual contributor activity throughout 2025
- **Custom Aliases**: User-friendly display names for contributors

## Data Files

The dashboard requires the following CSV file in the `data/` directory:
- `all_prs_detailed_qgis.csv` - Combined PR data from all repositories (Mapper Template, Space Intelligence, and QGIS Plugin)

## Examples

Here are some of the visualisations created with this dashboard

Comparison between number of PRs created in 2024 vs 2025
<img width="1465" height="489" alt="image" src="https://github.com/user-attachments/assets/3038be62-255f-4c28-8aa0-0de28c1e98a5" />

PRs in 2025 by user
<img width="1528" height="487" alt="image" src="https://github.com/user-attachments/assets/1890e1df-d1fe-4388-a2ed-6b41b26ed82e" />


