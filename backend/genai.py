from langchain.tools import tool
from typing import Dict, Union, List
from datetime import datetime, timedelta
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

groq_api_key = os.getenv('GROQ_API_KEY')
if groq_api_key:
    os.environ['GROQ_API_KEY'] = groq_api_key

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
            if 'T' in start_date:
                start_date = datetime.fromisoformat(start_date)
            elif '-' in start_date:
                try:
                    start_date = datetime.strptime(start_date, '%d-%m-%Y')
                except ValueError:
                    try:
                        start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    except ValueError:
                        start_date = datetime.strptime(start_date, '%m-%d-%Y')
            else:
                raise ValueError("Unsupported date format")
        except ValueError as e:
            raise ValueError(f"start_date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) or DD-MM-YYYY format. Got: {start_date}")

    frequency_map = {
        'monthly': 12,
        'quarterly': 4,
        'semi-annual': 2,
        'semi annual': 2,
        'annual': 1
    }

    payout_frequency_lower = payout_frequency.lower()
    if payout_frequency_lower not in frequency_map:
        raise ValueError(f"Invalid frequency. Choose from: {list(frequency_map.keys())}")

    payments_per_year = frequency_map[payout_frequency_lower]
    total_payments = int(horizon_years * payments_per_year)

    if isinstance(annual_coupon_rate, str) and '%' in annual_coupon_rate:
        annual_coupon_rate = float(annual_coupon_rate.replace('%', '')) / 100
    elif annual_coupon_rate > 1:
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

def get_genai_response(bond, user_preference):
    try:
        # llm = ChatOpenAI(model='gpt-4o')
        if not os.getenv('GROQ_API_KEY'):
            return "API configuration error: GROQ_API_KEY not found. Please set the environment variable and restart the application."
        
        llm = ChatGroq(model='deepseek-r1-distill-llama-70b')
        llm_with_tools = llm.bind_tools([calculate_coupon_payout])

        class AgentState(TypedDict):
            messages: List

        def call_llm(state: AgentState) -> AgentState:
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": state["messages"] + [response]}

        def call_tool(state) -> AgentState:
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

        graph = workflow.compile()

        today_str = datetime.today().strftime("%d-%m-%Y")

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

                      The final response should be in the following format:
                      <bond_description>
                      <company_name>
                      <instrument_name>
                      <payout_schedule>
                      <analysis>
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
        return final_state['messages'][-1].content
        
    except Exception as e:
        return f"AI analysis error: {str(e)}. The system encountered an issue while generating the analysis."
