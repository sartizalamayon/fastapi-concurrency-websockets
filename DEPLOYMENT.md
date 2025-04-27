# Deployment Guide for Render

This guide will walk you through deploying the Bistro92 High-Concurrency API to [Render](https://render.com/), a cloud platform for hosting web applications.

## Prerequisites

1. A [Render account](https://dashboard.render.com/register) (free tier is sufficient to start)
2. Your code in a Git repository (e.g., GitHub, GitLab, Bitbucket)

## Deployment Steps

### 1. Push Your Code to a Git Repository

Ensure your code is pushed to a Git repository that Render can access, such as a public GitHub repository or a private one you've connected to Render.

### 2. Create a New Web Service on Render

1. Log in to your Render dashboard
2. Click on the "New +" button and select "Web Service"
3. Connect your repository by selecting it from the list of available repositories
4. Configure your web service:
   - **Name**: `bistro92-api` (or any name you prefer)
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --workers 4`
5. Select a plan (the free plan works for testing)
6. Click "Create Web Service"

### 3. Create a PostgreSQL Database

1. From your Render dashboard, click "New +" and select "PostgreSQL"
2. Configure your database:
   - **Name**: `bistro92-db` (or any name you prefer)
   - Select a plan (the free plan is sufficient for testing)
3. Click "Create Database"
4. Note the "Internal Database URL" - you'll need this in the next step

### 4. Configure Environment Variables

1. Navigate to your web service dashboard
2. Click on the "Environment" tab
3. Add the following environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: The "Internal Database URL" from your PostgreSQL database

### 5. Automatic Deployment

Render will automatically deploy your application whenever you push changes to your repository. You can monitor the deployment progress in the "Events" tab of your web service.

## Testing Your Deployment

Once your deployment is complete:

1. Click on the URL provided by Render for your web service
2. You should see a response like `{"status":"ok","message":"Bistro92 API is running"}`
3. Visit `https://your-service-url.onrender.com/docs` to access the API documentation

## Troubleshooting

### Database Connection Issues

If you're experiencing database connection issues, check:

1. The `DATABASE_URL` environment variable is set correctly
2. Your database service is running
3. The application logs for specific error messages

### Application Crashes

If your application is crashing on startup:

1. Check the application logs in the Render dashboard
2. Ensure all required environment variables are set
3. Verify that the `gunicorn` start command is correct

## Using with Custom Domains

To use your API with a custom domain:

1. Go to your web service dashboard
2. Click on "Settings" and then "Custom Domain"
3. Follow the instructions to add and verify your domain

## Migrating from SQLite

When moving from a local SQLite database to PostgreSQL on Render:

1. The application code has been updated to handle both types of databases
2. The first time your app starts on Render, it will create the necessary tables
3. You may need to seed your data or transfer it from your local SQLite database

Note that the free PostgreSQL instance on Render has a 1GB storage limit, which should be sufficient for most small to medium-sized applications. 