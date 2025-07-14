# AI Financial Advisor

AI Powered Bond Selector Agent that suggests fixed income instruments based on user's preferences.

## Features

- 🤖 **AI-Powered Analysis**: Uses advanced language models to analyze bonds and provide personalized recommendations
- 📊 **Comprehensive Bond Database**: Access to 1900+ active bonds with detailed information
- 💰 **Payout Calculations**: Automatic calculation of coupon payments and schedules
- 🎨 **Modern UI**: Clean, responsive interface built with Reflex
- 🔍 **Smart Filtering**: Intelligent bond matching based on coupon rate, credit rating, frequency, and redemption year
- ⚡ **Fast API**: RESTful backend with FastAPI for high performance

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AI-Financial-Advisor
   ```

2. **Install backend dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**:
   ```bash
   cd frontend
   pip install -r requirements.txt
   cd ..
   ```

4. **Set up environment variables**:
   ```bash
   export GROQ_API_KEY="your-groq-api-key-here"
   ```
   *Note: The app will run without the API key, but AI analysis features will be limited.*

### Running the Application

#### Option 1: Using the Startup Script (Recommended)
```bash
python start_app.py
```

#### Option 2: Manual Start
1. **Start the backend** (in one terminal):
   ```bash
   python app.py
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   reflex run
   ```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Usage

1. **Navigate to the application** at http://localhost:3000
2. **Click "Get Started"** to access the bond recommendation form
3. **Fill in your preferences**:
   - **Coupon Rate**: Desired interest rate (e.g., 6.5%)
   - **Credit Rating**: Preferred bond rating (AAA, AA+, etc.)
   - **Interest Frequency**: How often you want payments (Annual, Semi-annual, Quarterly, Monthly)
   - **Redemption Year**: When you want the bond to mature
4. **Click "Get Recommendations"** to receive AI-powered analysis
5. **Review the results** including bond details, payout schedule, and investment analysis

## API Endpoints

### GET /health
Health check endpoint that returns system status and number of loaded bonds.

### POST /recommend
Get bond recommendations based on user preferences.

**Request Body**:
```json
{
  "coupon_rate": 6.5,
  "rating": "AAA",
  "interest_frequency": "Quarterly",
  "redemption_year": 2030
}
```

**Response**:
```json
{
  "analysis": "Detailed AI analysis with bond details, payout schedule, and recommendations"
}
```

## Technology Stack

- **Backend**: FastAPI, Python
- **Frontend**: Reflex (Python-based web framework)
- **AI/ML**: LangChain, Groq API
- **Data Processing**: Pandas, JSON
- **API Client**: httpx

## Project Structure

```
AI-Financial-Advisor/
├── app.py                 # FastAPI backend application
├── backend/
│   ├── bond_operations.py # Bond data processing and scoring
│   └── genai.py          # AI analysis and recommendation engine
├── frontend/
│   └── frontend/
│       └── frontend.py   # Reflex frontend application
├── bond_details.json     # Bond database (1900+ bonds)
├── requirements.txt      # Backend dependencies
├── start_app.py         # Convenient startup script
└── test_integration.py  # Integration tests

```

## Key Features Implemented

### Backend Improvements
- ✅ **CORS Configuration**: Proper cross-origin resource sharing setup
- ✅ **Input Validation**: Pydantic models with comprehensive validation
- ✅ **Error Handling**: Graceful error handling with meaningful messages
- ✅ **Health Monitoring**: Health check endpoint for system status
- ✅ **Bond Scoring**: Intelligent scoring algorithm for bond recommendations

### Frontend Improvements
- ✅ **Modern UI**: Clean, responsive design with proper styling
- ✅ **Form Validation**: Client-side validation with user-friendly error messages
- ✅ **Loading States**: Proper loading indicators during API calls
- ✅ **Error Display**: Clear error messaging and handling
- ✅ **Results Presentation**: Well-formatted display of bond details and analysis
- ✅ **Navigation**: Smooth navigation between pages

### Integration
- ✅ **API Integration**: Seamless communication between frontend and backend
- ✅ **Data Parsing**: Proper parsing of AI responses with structured data
- ✅ **Environment Configuration**: Proper handling of environment variables
- ✅ **Dependency Management**: Clear dependency requirements

## Testing

Run the integration tests to verify the system:

```bash
python test_integration.py
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**: Ensure all dependencies are installed
2. **API connection errors**: Verify the backend is running on port 8000
3. **No AI analysis**: Check that GROQ_API_KEY is set correctly
4. **Port conflicts**: Ensure ports 3000 and 8000 are available

### Getting Help

- Check the health endpoint: http://localhost:8000/health
- Review the console output for detailed error messages
- Ensure all requirements are installed correctly

## License

This project is for educational and demonstration purposes.
