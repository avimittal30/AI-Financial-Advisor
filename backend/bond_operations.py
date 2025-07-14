from dotenv import load_dotenv
from difflib import SequenceMatcher
import re
import json
from typing import Dict, Union, List
from datetime import datetime, timedelta

load_dotenv()

def load_and_prepare_bonds():
    with open('bond_details.json', 'r') as file:
        bond_details = json.load(file)

    ### Retain only active bonds
    date_format = "%d-%m-%Y"
    current_date = datetime.now()
    active_bonds = [bond for bond in bond_details if datetime.strptime(bond['REDEMPTION'], date_format) > current_date + timedelta(days=380)]

    ## Retain only selected details for the bond.
    selected_fields = [
        'COMPANY',
        'id',
        'ISIN',
        'NAME_OF_THE_INSTRUMENT',
        'DESCRIPTION_IN_NSDL',
        'ISSUE_PRICE',
        'FACEVALUE',
        'DATE_OF_ALLOTMENT',
        'REDEMPTION',
        'COUPON_RATE',
        'FREQUENCY_OF_THE_INTEREST_PAYMENT',
        'DEFAULTED_IN_REDEMPTION',
        'CREDIT_RATING_CREDIT_RATING_AGENCY'
    ]

    # Create a new list of dicts with only the selected fields for each bond
    active_bonds = [
        {field: bond.get(field, None) for field in selected_fields}
        for bond in active_bonds
    ]

    ## Remove duplicates based on ISIN
    unique_bonds = []
    seen_isins = set()
    for bond in active_bonds:
        isin = bond['ISIN']
        if isin not in seen_isins:
            unique_bonds.append(bond)
            seen_isins.add(isin)
    active_bonds = unique_bonds
    return active_bonds

def rating_score(bond_rating, user_rating):
    return 1.0 if bond_rating == user_rating else 0.5 if bond_rating.startswith(user_rating[0]) else 0

def interest_score(bond_freq, user_freq):
    return 1.0 if user_freq.lower() in bond_freq.lower() else 0

def extract_coupon_value(coupon_str):
    match = re.search(r"(\d+(\.\d+)?)%", coupon_str)
    return float(match.group(1)) if match else 0.0

def coupon_score(bond_coupon, user_coupon):
    bond_coupon_val = extract_coupon_value(bond_coupon)
    return max(0, 1 - abs(bond_coupon_val - user_coupon) / user_coupon)

def redemption_score(bond_redemption, user_year):
    bond_year = int(bond_redemption.split('-')[-1])
    return max(0, 1 - abs(bond_year - user_year) / 10)  # normalize over 10 years

def bond_score(bond, user_preferences):
    score = 0
    score += 0.3 * coupon_score(bond['COUPON_RATE'], user_preferences['coupon_rate'])
    score += 0.3 * rating_score(bond['CREDIT_RATING_CREDIT_RATING_AGENCY'].split()[0], user_preferences['rating'])
    score += 0.2 * interest_score(bond['FREQUENCY_OF_THE_INTEREST_PAYMENT'], user_preferences['interest_frequency'])
    score += 0.2 * redemption_score(bond['REDEMPTION'], user_preferences['redemption_year'])
    return score

def get_bond_recommendations(active_bonds, user_preferences):
    '''Recommend bonds based on user preferences.'''
    recommendations = sorted(active_bonds, key=lambda x: bond_score(x, user_preferences), reverse=True)
    return recommendations
