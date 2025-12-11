# PR Visualizations Dashboard

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

## Deploying to Render

1. Push this repository to GitHub

2. Go to [render.com](https://render.com) and sign up/login

3. Click "New +" → "Web Service"

4. Connect your GitHub repository

5. Configure the service:
   - **Name**: `pr-visualizations` (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

6. Click "Create Web Service"

Render will automatically deploy your app and provide a URL like `https://pr-visualizations.onrender.com`

## Features

- **Dataset Selection**: Choose between Mapper Template PRs, QGIS Plugin PRs, or combined data
- **Year Comparison**: Animated visualization comparing PR activity between years
- **User Comparison**: Track individual contributor activity throughout 2025
- **Custom Aliases**: User-friendly display names for contributors

## Data Files

The dashboard requires the following CSV files in the `data/` directory:
- `all_prs.csv` - Mapper Template repository PRs
- `all_prs_qgis.csv` - QGIS Plugin repository PRs
# git_pr_analysis
