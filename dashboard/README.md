# DOCT Volume Tracker Dashboard

A React-based dashboard for visualizing and analyzing DOCT trading data.

## Features

- **Alerts Section**: Automatically detects large trades (>1.5 standard deviations) in the past 5 days compared to the baseline of the past 14 days
- **Depth Chart Table**: Displays all order book depth chart entries
- **Trades Table**: 
  - Pagination (10, 50, or 100 trades per page)
  - Sorting by date (descending) and time (descending)
  - Filters for buyer, seller, date range, exchange, and volume range
- **Analysis Visualizations**:
  - Order Book Depth Chart: Visualizes buy walls (bids) and sell walls (asks) at different price levels
  - Volume Over Time: Line chart showing aggregate volume with date range and exchange filtering
  - Buyer/Seller Breakdown: Bar charts showing top buyers and sellers by volume

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure `trades.json` and `depth_chart.json` are in the `public/` directory

3. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Building for Production

To build for production (e.g., for GitHub Pages):

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Deployment to GitHub Pages

1. Install `gh-pages` package:
```bash
npm install --save-dev gh-pages
```

2. Add to `package.json` scripts:
```json
"homepage": "https://yourusername.github.io/doct-volume-tracker",
"predeploy": "npm run build",
"deploy": "gh-pages -d build"
```

3. Deploy:
```bash
npm run deploy
```

## Technologies Used

- React 18
- Recharts for data visualization
- date-fns for date handling
- CSS for styling

