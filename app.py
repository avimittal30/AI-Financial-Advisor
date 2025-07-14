from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.bond_operations import load_and_prepare_bonds, get_bond_recommendations
from backend.genai import get_genai_response

app = FastAPI(title="AI Financial Advisor API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load bonds at startup
try:
    active_bonds = load_and_prepare_bonds()
    print(f"Loaded {len(active_bonds)} active bonds")
except Exception as e:
    print(f"Error loading bonds: {e}")
    active_bonds = []

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bonds_loaded": len(active_bonds),
        "message": "AI Financial Advisor API is running"
    }

class UserPreferences(BaseModel):
    coupon_rate: float = Field(gt=0, le=50, description="Coupon rate as a percentage")
    rating: str = Field(min_length=1, description="Credit rating")
    interest_frequency: str = Field(min_length=1, description="Interest payment frequency")
    redemption_year: int = Field(ge=2024, le=2100, description="Redemption year")

@app.post("/recommend")
def recommend(user_preferences: UserPreferences):
    """
    Get bond recommendations based on user preferences.
    """
    try:
        user_prefs_dict = user_preferences.model_dump()
        
        # Validate that we have bonds loaded
        if not active_bonds:
            raise HTTPException(status_code=500, detail="Bond data not available")
        
        recommendations = get_bond_recommendations(active_bonds, user_prefs_dict)
        
        if not recommendations:
            return {"message": "No suitable bonds found for your preferences.", "analysis": ""}
            
        top_bond = recommendations[0]
        
        # Validate required fields in the bond
        required_fields = ['COUPON_RATE', 'CREDIT_RATING_CREDIT_RATING_AGENCY', 'FREQUENCY_OF_THE_INTEREST_PAYMENT', 'REDEMPTION']
        missing_fields = [field for field in required_fields if not top_bond.get(field)]
        if missing_fields:
            raise HTTPException(status_code=500, detail=f"Bond data incomplete, missing: {missing_fields}")
        
        analysis = get_genai_response(top_bond, user_prefs_dict)
        
        return {"analysis": analysis}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

