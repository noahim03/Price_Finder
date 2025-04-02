# Product Price Tracker

A full-stack web application that tracks and displays product prices over time. Users can input product names, and the app will fetch and monitor their current prices.

## Features

- Search for products by name
- View current product prices
- Track price history with interactive charts
- View search history with timestamps
- Refresh product prices on demand

## Technology Stack

### Backend
- Python Flask
- SQLAlchemy for database management
- SQLite for data storage
- RESTful API design

### Frontend
- React with TypeScript
- Material-UI for styling
- Recharts for data visualization
- Axios for API requests

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd price_tracker/backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the Flask application:
   ```
   python wsgi.py
   ```

   The backend server will start at http://localhost:5000

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd price_tracker/frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

   The frontend application will start at http://localhost:3000

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Enter a product name in the search box
3. View the current price
4. Check the price history chart for price trends
5. Use the "Refresh" button to update prices
6. Switch to the "Search History" tab to view your search history

## Notes

This application uses a mock price service for demonstration purposes. In a real-world scenario, you would integrate with actual product APIs or implement web scraping functionality to get real prices.

## Project Structure

```
price_tracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── price_service.py
│   │   └── routes.py
│   ├── instance/
│   ├── config.py
│   ├── requirements.txt
│   └── wsgi.py
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   │   ├── PriceHistoryChart.tsx
    │   │   ├── ProductList.tsx
    │   │   ├── ProductSearch.tsx
    │   │   └── SearchHistoryList.tsx
    │   ├── services/
    │   │   └── api.ts
    │   ├── types/
    │   │   └── index.ts
    │   ├── App.tsx
    │   └── index.tsx
    ├── package.json
    └── tsconfig.json
``` 