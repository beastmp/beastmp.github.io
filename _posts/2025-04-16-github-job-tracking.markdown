---
layout: posts
title:  "Job Tracking"
date:   2025-04-16 12:00:00 +0000
tags: ["javascript"]
author_profile: true
author: Michael Palmer
categories: work
highlight_home: false
tagline: "A JavaScript project."
header:
  overlay_image: https://opengraph.githubassets.com/1/beastmp/job-tracking
  teaser: https://opengraph.githubassets.com/1/beastmp/job-tracking
  caption: "GitHub Repository: [job-tracking](https://github.com/beastmp/job-tracking)"
description: "A JavaScript project."
---

# Job Search Tracking Application

A full-stack MERN application for tracking job applications with LinkedIn data enrichment and email integration.

## Features

- Track job applications (title, company, location, status, etc.)
- Update application status (Applied, Interview, Offer, Rejected, Saved)
- Enrich job data from LinkedIn job listings
- Import job applications from emails
- Export data to Excel
- Dashboard with application statistics and visualizations
- Responsive design for desktop and mobile

## Technologies Used

- **Frontend**: React, React Router, Bootstrap, Chart.js
- **Backend**: Node.js, Express
- **Database**: MongoDB
- **APIs**: Email IMAP integration

## Security Features

- Encrypted storage of email credentials
- Environment-based configuration
- Secure API handling with rate limiting
- TLS/SSL support for email connections

## Setup Instructions

### Prerequisites

- Node.js (v18+) and npm installed
- MongoDB database (local or MongoDB Atlas)
- Email account with IMAP access (for email integration)

### Initial Setup

1. Clone the repository:
   ```
   git clone https://github.com/beastmp/job-tracking.git
   cd job-tracking
   ```

2. Install dependencies for both backend and frontend:
   ```
   cd backend && npm install
   cd ../frontend && npm install
   ```

3. Configure environment variables (see Security Configuration below)

### Security Configuration

The application requires proper environment variables configuration. **Never commit real credentials to your repository.**

1. Create a `.env.example` file in the backend directory (a template is provided)

2. Create your actual `.env` file based on the example:
   ```
   cp backend/.env.example backend/.env
   ```

3. Edit the `.env` file with your actual credentials:
   ```
   PORT=5000
   MONGODB_URI=mongodb+srv://username:password@cluster.example.mongodb.net/?retryWrites=true&w=majority

   # Generate a secure encryption key using:
   # node -e "console.log(require('crypto').randomBytes(16).toString('hex'))"
   ENCRYPTION_KEY=your_32_character_random_key
   ```

4. For production deployment, make sure to use proper secrets management (never hardcode credentials)

### Starting the Application

#### Development Mode

1. Start the backend server:
   ```
   cd backend
   npm run dev
   ```

2. In a separate terminal, start the frontend:
   ```
   cd frontend
   npm start
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

#### Production Mode

For production deployment, follow the instructions in the [SECURITY_SETUP.md](./docs/SECURITY_SETUP.md) document.

## Email Integration

The application can connect to email accounts to automatically import job applications:

1. Use the Email Integration section in the application
2. Provide your email address, IMAP server details, and password
3. Email credentials are encrypted before being stored in the database
4. For Gmail, use an app-specific password rather than your main password

**Important**: Review the [SECURITY_SETUP.md](./docs/SECURITY_SETUP.md) guide for secure email integration.

## LinkedIn Data Enrichment

The application includes LinkedIn job data enrichment functionality:

- Rate-limited to comply with LinkedIn's terms of service
- Used only for enriching job application data that the user has already manually added
- Not used for automated scraping or bulk data collection

## Deployment Options

This MERN stack application can be deployed using various services:

1. **Render**: All-in-one platform for both frontend and backend
2. **Vercel + MongoDB Atlas**: Vercel for frontend/serverless functions, MongoDB Atlas for database
3. **Railway**: Simple deployment with GitHub integration
4. **AWS Elastic Beanstalk + MongoDB Atlas**: Enterprise-grade hosting
5. **Heroku + MongoDB Atlas**: Simple deployment with good free tier

For detailed deployment instructions, see [SECURITY_SETUP.md](./docs/SECURITY_SETUP.md).

## Security Considerations

Before deploying to production:

1. Ensure all environment variables are properly set
2. Generate a secure random encryption key
3. Use HTTPS in production
4. Configure proper CORS settings
5. Implement rate limiting
6. Use secure MongoDB connection settings

## License

[MIT License](LICENSE)

---


> This post is automatically generated from my [GitHub repository](https://github.com/beastmp/job-tracking).  
> Last updated: 2025-04-17

