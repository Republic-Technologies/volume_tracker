# GitHub Pages Deployment Guide

This guide will help you deploy the DOCT Volume Tracker dashboard to GitHub Pages.

## Prerequisites

- A GitHub repository (already set up)
- GitHub Pages enabled in your repository settings

## Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select:
   - **Source**: `GitHub Actions`
4. Save the settings

## Step 2: Update Homepage URL (Optional)

If you want to use a custom domain or your repository has a different name, update the `homepage` field in `dashboard/package.json`:

```json
"homepage": "https://yourusername.github.io/volume_tracker"
```

Replace `yourusername` with your GitHub username and `volume_tracker` with your repository name.

## Step 3: Push to GitHub

1. Add all files:
```bash
git add .
```

2. Commit the changes:
```bash
git commit -m "Add React dashboard for DOCT Volume Tracker"
```

3. Push to GitHub:
```bash
git push origin main
```

## Step 4: Automatic Deployment

Once you push, the GitHub Actions workflow (`.github/workflows/deploy-dashboard.yml`) will automatically:
1. Build the React app
2. Deploy it to GitHub Pages

You can monitor the deployment progress in the **Actions** tab of your GitHub repository.

## Step 5: Access Your Dashboard

After the workflow completes (usually 2-3 minutes), your dashboard will be available at:
- `https://yourusername.github.io/volume_tracker/`

## Manual Deployment (Alternative)

If you prefer to deploy manually:

1. Install dependencies:
```bash
cd dashboard
npm install
```

2. Install gh-pages:
```bash
npm install --save-dev gh-pages
```

3. Deploy:
```bash
npm run deploy
```

## Troubleshooting

### Dashboard shows blank page
- Check that the JSON files are in `dashboard/public/`
- Verify the homepage URL in `package.json` matches your repository
- Check browser console for errors

### Build fails
- Make sure all dependencies are installed: `npm install` in the dashboard directory
- Check the Actions tab for specific error messages

### Data not updating
- Verify the GitHub Actions workflow is copying JSON files to `dashboard/public/`
- Check that the cache-busting in `dataLoader.js` is working

## Notes

- The dashboard will automatically rebuild and redeploy whenever you push changes to the `dashboard/` directory
- The JSON data files (`trades.json` and `depth_chart.json`) are updated by the daily scrape workflow and copied to `dashboard/public/` automatically

