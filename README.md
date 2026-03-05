# Azure Mood App

A web application for tracking and visualizing your mood through an intuitive calendar interface.

## Product Vision

To empower users to map their inner lives through an elegant, intuitive calendar interface.

## Setup & Run

1. Clone the repository
   ```bash
   git clone https://github.com/swe-students-spring2026/2-web-app-azure_falcons.git
   cd 2-web-app-azure_falcons
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables
   
   Copy `.env.example` to `.env` and fill in your MongoDB credentials:
   ```bash
   cp .env.example .env
   ```
   
   Required variables:
   ```
   MONGO_URI
   MONGO_DB
   ```

5. Run the application
   ```bash
   python run.py
   ```

6. Open in browser: http://127.0.0.1:5000

## User Stories

See our [Product Backlog](https://github.com/orgs/swe-students-spring2026/projects/39/views/1).

## Task Boards

See our [Projects Page](https://github.com/orgs/swe-students-spring2026/projects).