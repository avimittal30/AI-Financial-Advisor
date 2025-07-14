from fastapi import FastAPI
from pydantic import BaseModel
from backend.bond_operations import load_and_prepare_bonds, get_bond_recommendations
from backend.genai import get_genai_response

app = FastAPI()

# Load bonds at startup
active_bonds = load_and_prepare_bonds()

class UserPreferences(BaseModel):
    coupon_rate: float
    rating: str
    interest_frequency: str
    redemption_year: int

@app.post("/recommend")
def recommend(user_preferences: UserPreferences):
    """
    Get bond recommendations based on user preferences.
    """
    user_prefs_dict = user_preferences.dict()
    recommendations = get_bond_recommendations(active_bonds, user_prefs_dict)
    
    if not recommendations:
        return {"message": "No suitable bonds found for your preferences."}
        
    top_bond = recommendations[0]
    
    analysis = get_genai_response(top_bond, user_prefs_dict)
    
    return {"analysis": analysis}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

