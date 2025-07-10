from dotenv import load_dotenv
load_dotenv()

import json
with open('bond_details.json', 'r') as file:
    bond_details = json.load(file)

### Retain only active bonds
active_bonds=[]
from datetime import datetime
from datetime import timedelta
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
# Remove duplicates from active_bonds based on ISIN
unique_bonds = []
seen_isins = set()
for bond in active_bonds:
    isin = bond['ISIN']
    if isin not in seen_isins:
        unique_bonds.append(bond)
        seen_isins.add(isin)
# Update active_bonds to only include unique bonds (remove duplicates based on ISIN)
active_bonds = unique_bonds
len(active_bonds)


from difflib import SequenceMatcher
import re

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


from langchain.tools import tool

user_preferences = {
    'coupon_rate': 7.0,                  # User wants ~7%
    'rating': 'AA',                     # Prefers AA+ or better
    'interest_frequency': 'Quarterly',     # Annual payouts
    'redemption_year': 2028             # Wants bond to mature around 2030
}

def bond_score(bond, user_preferences):
    score = 0
    score += 0.3 * coupon_score(bond['COUPON_RATE'], user_preferences['coupon_rate'])
    score += 0.3 * rating_score(bond['CREDIT_RATING_CREDIT_RATING_AGENCY'].split()[0], user_preferences['rating'])
    score += 0.2 * interest_score(bond['FREQUENCY_OF_THE_INTEREST_PAYMENT'], user_preferences['interest_frequency'])
    score += 0.2 * redemption_score(bond['REDEMPTION'], user_preferences['redemption_year'])
    return score

# List of bond dictionaries


def bond_recommendations(active_bonds, user_preferences):
    '''Recommend bonds based on user preferences.'''
    recommendations = sorted(active_bonds, key=lambda x: bond_score(x, user_preferences), reverse=True)
    return recommendations


### This is the recommended bond
rec=bond_recommendations(active_bonds=active_bonds, user_preferences=user_preferences)[0]


from typing import Dict, Union, List
from langchain_core.tools import tool

import math

### tool to be binded with LLM
@tool
def calculate_coupon_payout(
    investment_amount: float,
    annual_coupon_rate: float,
    horizon_years: float,
    payout_frequency: str = 'quarterly',
    start_date: Union[str, None] = None
) -> Dict[str, Union[float, int, List[Dict]]]:
    """
    Calculate coupon payouts at desired frequency.
    """
    if start_date is None:
        start_date = datetime.now()
    elif isinstance(start_date, str):
        try:
            # Try multiple date formats
            if 'T' in start_date:
                start_date = datetime.fromisoformat(start_date)
            elif '-' in start_date:
                # Handle DD-MM-YYYY format
                try:
                    start_date = datetime.strptime(start_date, '%d-%m-%Y')
                except ValueError:
                    # Handle YYYY-MM-DD format
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                raise ValueError("Unsupported date format")
        except ValueError as e:
            raise ValueError(f"start_date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) or DD-MM-YYYY format. Got: {start_date}")
    
    frequency_map = {
        'monthly': 12,
        'quarterly': 4,
        'semi-annual': 2,
        'semi annual': 2,  # Added for flexibility
        'annual': 1
    }
    
    payout_frequency_lower = payout_frequency.lower()
    if payout_frequency_lower not in frequency_map:
        raise ValueError(f"Invalid frequency. Choose from: {list(frequency_map.keys())}")
    
    payments_per_year = frequency_map[payout_frequency_lower]
    total_payments = int(horizon_years * payments_per_year)
    
    # Convert percentage string to decimal if needed
    if isinstance(annual_coupon_rate, str) and '%' in annual_coupon_rate:
        annual_coupon_rate = float(annual_coupon_rate.replace('%', '')) / 100
    elif annual_coupon_rate > 1:  # Assume it's a percentage if > 1
        annual_coupon_rate = annual_coupon_rate / 100
    
    payout_per_payment = (annual_coupon_rate * investment_amount) / payments_per_year
    total_coupon_income = payout_per_payment * total_payments
    days_between_payments = 365 / payments_per_year
    
    payout_schedule = []
    for i in range(total_payments):
        payout_date = start_date + timedelta(days=int(days_between_payments * (i + 1)))
        payout_schedule.append({
            'payment_number': i + 1,
            'date': payout_date.strftime('%Y-%m-%d'),
            'amount': round(payout_per_payment, 2)
        })
    
    return {
        'investment_amount': investment_amount,
        'annual_coupon_rate': annual_coupon_rate,
        'payout_frequency': payout_frequency,
        'payments_per_year': payments_per_year,
        'payout_per_payment': round(payout_per_payment, 2),
        'total_payments': total_payments,
        'total_coupon_income': round(total_coupon_income, 2),
        'effective_annual_return': round((total_coupon_income / investment_amount) / horizon_years, 4),
        'payout_schedule': payout_schedule
    }


from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import os
os.environ['GROQ_API_KEY']=os.getenv('GROQ_API_KEY')
# llm=ChatOpenAI(model='gpt-4o')
llm=ChatGroq(model='deepseek-r1-distill-llama-70b')
llm_with_tools=llm.bind_tools([calculate_coupon_payout])


bond=rec
user_preference=user_preferences
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage


from typing import TypedDict
class AgentState(TypedDict):
    messages: List

def call_llm(state:AgentState)->AgentState:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


def call_tool(state)->AgentState:
    # Find the last tool call message
    last_msg = state["messages"][-1]
    if not hasattr(last_msg, "tool_calls"):
        return state

    new_messages = state["messages"][:]
    for tool_call in last_msg.tool_calls:
        if tool_call["name"] == "calculate_coupon_payout":
            args = tool_call["args"]
            result = calculate_coupon_payout.invoke(args)
            new_messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=str(result)
                )
            )
    return {"messages": new_messages}


from langgraph.graph import StateGraph, END
from datetime import datetime

today_str = datetime.today().strftime("%d-%m-%Y")  # Or "%Y-%m-%d" if you prefer


workflow = StateGraph(AgentState)
workflow.add_node("llm", call_llm)
workflow.add_node("tool", call_tool)
workflow.set_entry_point("llm")

def should_continue(state):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tool"
    return END



workflow.add_conditional_edges("llm", should_continue)
workflow.add_edge("tool", "llm")

# Compile the graph
graph = workflow.compile()

prompt = f"""You are an investment advisor that recommends suitable fixed income bonds to users according to their preferences. 
You have access to a tool that calculates payouts at desired frequency.

Here is the bond information:
{bond}

Here are the user preferences:
{user_preference}

Today's date is: {today_str}

Please:
1. For Bond details, please extract Bond Description, company name and name of the instrument
2. From the bond info, extract the frequency of interest payment from the field FREQUENCY_OF_THE_INTEREST_PAYMENT. 
Use only one of the following standard values: "monthly", "quarterly", "semi-annual", "semin annual", or "annual". 
3. Extract redemption year from bond information to calulate horizon to be used by the tool. The horizon should be calculated as difference between redemption date and the date today.
to calculate coupon payments using the tool.
4. Calculate the coupon payments using this frequency 
5. Show the payouts in a tabular format
6. Provide an analysis to the user to show how this bond aligns with the user's preferences

In the final response, do **not** list the steps or explain what was done.  Just show the final table of payouts and 
provide a comprehensive analysis on how the bond aligns with the user's preferences.


"""

messages = [
    SystemMessage(content=(
        "You are a financial advisor who helps users understand their bond investments. "
        "You have access to a tool called `calculate_coupon_payout` which calculates coupon payouts "
        "based on investment amount, interest rate, payout frequency, and investment duration. "
        
    )),
    HumanMessage(content=prompt)
]

final_state = graph.invoke({"messages": messages})
print(final_state['messages'][-1].content)

