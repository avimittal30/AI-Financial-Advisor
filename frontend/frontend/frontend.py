import reflex as rx
import httpx
import json
import re
from typing import List, Dict

class State(rx.State):
    """The app state."""
    coupon_rate: float = 0.0
    rating: str = ""
    interest_frequency: str = ""
    redemption_year: int = 2024
    analysis: str = ""
    processing: bool = False
    loading_message: str = "Analyzing bonds..."

    ratings: List[str] = [
        "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
        "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
        "B+", "B", "B-", "CCC", "CC", "C", "D"
    ]
    frequencies: List[str] = ["Annually", "Semi-annually", "Quarterly", "Monthly", "On Maturity"]

    def handle_coupon_rate_change(self, value: str):
        try:
            self.coupon_rate = float(value)
        except (ValueError, TypeError):
            pass

    def handle_redemption_year_change(self, value: str):
        try:
            self.redemption_year = int(value)
        except (ValueError, TypeError):
            pass

    async def get_recommendations(self):
        """Get bond recommendations from the backend."""
        # Validate inputs before making API call
        if self.coupon_rate <= 0:
            self.analysis = "Error: Coupon rate must be greater than 0"
            return
        if not self.rating:
            self.analysis = "Error: Please select a credit rating"
            return
        if not self.interest_frequency:
            self.analysis = "Error: Please select an interest frequency"
            return
        if self.redemption_year < 2024:
            self.analysis = "Error: Redemption year must be 2024 or later"
            return
            
        self.processing = True
        self.analysis = ""
        self.loading_message = "🔍 Searching bond database..."
        try:
            # The API is running on port 8000
            self.loading_message = "🤖 AI is analyzing your preferences..."
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://127.0.0.1:8000/recommend",
                    json={
                        "coupon_rate": self.coupon_rate,
                        "rating": self.rating,
                        "interest_frequency": self.interest_frequency,
                        "redemption_year": self.redemption_year,
                    },
                    timeout=120, # 2 minutes timeout
                )
                response.raise_for_status()
                self.loading_message = "📊 Processing results..."
                data = response.json()
                if "message" in data and not data.get("analysis"):
                    self.analysis = f"No Results: {data['message']}"
                else:
                    self.analysis = data.get("analysis", "No analysis found.")
        except httpx.TimeoutException:
            self.analysis = "Error: Request timed out. The AI analysis is taking too long."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                self.analysis = "Error: Invalid input parameters. Please check your values."
            elif e.response.status_code == 500:
                self.analysis = "Error: Internal server error. Please try again later."
            else:
                self.analysis = f"Error: API request failed with status {e.response.status_code}"
        except httpx.ConnectError:
            self.analysis = "Error: Cannot connect to the API server. Please ensure the backend is running on port 8000."
        except Exception as e:
            self.analysis = f"Error: An unexpected error occurred: {str(e)}"
        finally:
            self.processing = False

    def refresh(self):
        """Clear the form and analysis."""
        self.coupon_rate = 0.0
        self.rating = ""
        self.interest_frequency = ""
        self.redemption_year = 2024
        self.analysis = ""
        self.loading_message = "Analyzing bonds..."

    def _parse_tag(self, tag: str) -> str:
        if not self.analysis:
            return ""
        match = re.search(f"<{tag}>(.*?)</{tag}>", self.analysis, re.DOTALL)
        return match.group(1).strip() if match else ""

    @rx.var
    def bond_description(self) -> str:
        return self._parse_tag("bond_description")

    @rx.var
    def company_name(self) -> str:
        return self._parse_tag("company_name")

    @rx.var
    def instrument_name(self) -> str:
        return self._parse_tag("instrument_name")

    @rx.var
    def analysis_text(self) -> str:
        return self._parse_tag("analysis")

    @rx.var
    def payout_schedule_data(self) -> list[dict]:
        """Parses payout schedule from analysis string."""
        payout_schedule_md = self._parse_tag("payout_schedule")
        if not payout_schedule_md:
            return []

        lines = [line.strip() for line in payout_schedule_md.strip().split('\\n') if line.strip()]
        if len(lines) < 3:  # Header, separator, at least one data row
            return []

        # Parse header
        header_line = lines[0]
        headers = [h.strip().replace(" ", "_").lower() for h in header_line.split('|') if h.strip()]

        data = []
        # Parse data rows
        for line in lines[2:]: # Skip separator line
            values = [v.strip() for v in line.split('|') if v.strip()]
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))
        return data


def index() -> rx.Component:
    """The welcome page."""
    return rx.container(
        rx.vstack(
            rx.heading("AI Financial Advisor", size="9", color="blue.600"),
            rx.text(
                "Get personalized bond recommendations powered by AI",
                size="5",
                text_align="center",
                color="gray.600",
                max_width="600px"
            ),
            rx.link(
                rx.button(
                    "Get Started",
                    size="4",
                    color_scheme="blue",
                    variant="solid"
                ),
                href="/form",
            ),
            spacing="6",
            justify="center",
            align="center",
            min_height="100vh",
            padding="2rem",
        ),
        max_width="1200px",
        margin="0 auto"
    )

def form() -> rx.Component:
    """The form page to get recommendations."""
    return rx.container(
        rx.vstack(
            # Header section
            rx.vstack(
                rx.heading("Get Bond Recommendations", size="7", color="blue.600"),
                rx.text(
                    "Enter your investment preferences to get AI-powered bond recommendations",
                    size="4",
                    color="gray.600",
                    text_align="center"
                ),
                spacing="2",
                align="center",
                margin_bottom="2rem"
            ),
            
            # Form section
            rx.card(
                rx.vstack(
                    rx.text("Investment Preferences", size="5", weight="bold", color="gray.700"),
                    
                    # Input fields with better styling
                    rx.vstack(
                        rx.vstack(
                            rx.text("Coupon Rate (%)", size="3", weight="medium", color="gray.600"),
                            rx.input(
                                placeholder="e.g., 5.5",
                                type="number",
                                step="0.1",
                                min="0",
                                max="50",
                                value=State.coupon_rate,
                                on_change=State.handle_coupon_rate_change,
                                disabled=State.processing,
                                width="100%"
                            ),
                            spacing="1",
                            width="100%"
                        ),
                        
                        rx.hstack(
                            rx.vstack(
                                rx.text("Credit Rating", size="3", weight="medium", color="gray.600"),
                                rx.select(
                                    State.ratings,
                                    placeholder="Select Rating",
                                    value=State.rating,
                                    on_change=State.set_rating,
                                    disabled=State.processing,
                                    width="100%"
                                ),
                                spacing="1",
                                width="100%"
                            ),
                            rx.vstack(
                                rx.text("Interest Frequency", size="3", weight="medium", color="gray.600"),
                                rx.select(
                                    State.frequencies,
                                    placeholder="Select Frequency",
                                    value=State.interest_frequency,
                                    on_change=State.set_interest_frequency,
                                    disabled=State.processing,
                                    width="100%"
                                ),
                                spacing="1",
                                width="100%"
                            ),
                            spacing="4",
                            width="100%"
                        ),
                        
                        rx.vstack(
                            rx.text("Redemption Year", size="3", weight="medium", color="gray.600"),
                            rx.input(
                                placeholder="e.g., 2030",
                                type="number",
                                min="2024",
                                max="2100",
                                value=State.redemption_year,
                                on_change=State.handle_redemption_year_change,
                                disabled=State.processing,
                                width="100%"
                            ),
                            spacing="1",
                            width="100%"
                        ),
                        
                        spacing="4",
                        width="100%"
                    ),
                    
                    rx.button(
                        rx.cond(
                            State.processing,
                            rx.hstack(
                                rx.spinner(size="3"),
                                rx.text(State.loading_message, size="3"),
                                spacing="2",
                                align="center"
                            ),
                            rx.text("Get Recommendations", size="3")
                        ),
                        on_click=State.get_recommendations,
                        loading=State.processing,
                        disabled=State.processing,
                        size="3",
                        color_scheme="blue",
                        variant="solid",
                        width="100%"
                    ),
                    
                    spacing="4",
                    padding="2rem"
                ),
                width="100%",
                max_width="600px"
            ),
            # Loading overlay when processing
            rx.cond(
                State.processing & ~State.analysis,
                rx.card(
                    rx.vstack(
                        rx.box(
                            rx.spinner(size="3", color="blue.600"),
                            padding="2rem",
                            border_radius="full",
                            background="blue.50",
                            border="2px solid",
                            border_color="blue.200"
                        ),
                        rx.heading(State.loading_message, size="5", color="blue.600"),
                        rx.text(
                            "Please wait while our AI finds the best bond recommendations for you.",
                            size="3",
                            color="gray.600",
                            text_align="center"
                        ),
                        rx.text(
                            "This may take up to 2 minutes.",
                            size="2",
                            color="gray.500",
                            text_align="center"
                        ),
                        spacing="4",
                        align="center",
                        padding="3rem"
                    ),
                    width="100%",
                    max_width="600px",
                    text_align="center"
                )
            ),
            
            # Results section
            rx.cond(
                State.analysis & ~State.processing,
                rx.cond(
                    State.analysis.startswith("Error:") | State.analysis.startswith("No Results:"),
                    # Error display
                    rx.card(
                        rx.vstack(
                            rx.heading("⚠️ Notice", size="5", color="orange.600"),
                            rx.text(State.analysis, color="orange.700", size="4"),
                            spacing="3",
                            padding="2rem"
                        ),
                        width="100%",
                        border_color="orange.300",
                        max_width="800px"
                    ),
                    # Success display
                    rx.card(
                        rx.vstack(
                            rx.heading("✅ Bond Recommendation", size="5", color="green.600", margin_bottom="1rem"),
                            
                            # Bond details section
                            rx.cond(
                                State.bond_description,
                                rx.vstack(
                                    rx.heading("Bond Details", size="4", color="blue.600"),
                                    rx.text(State.bond_description, size="3", line_height="1.6"),
                                    rx.grid(
                                        rx.vstack(
                                            rx.text("Company", size="2", weight="bold", color="gray.600"),
                                            rx.text(State.company_name, size="3", weight="medium"),
                                            spacing="1"
                                        ),
                                        rx.vstack(
                                            rx.text("Instrument", size="2", weight="bold", color="gray.600"),
                                            rx.text(State.instrument_name, size="3", weight="medium"),
                                            spacing="1"
                                        ),
                                        columns="2",
                                        spacing="4",
                                        margin_top="1rem"
                                    ),
                                    spacing="3",
                                    width="100%",
                                    padding="1.5rem",
                                    background="blue.50",
                                    border_radius="md"
                                )
                            ),
                            
                            # Payout schedule section
                            rx.cond(
                                State.payout_schedule_data,
                                rx.vstack(
                                    rx.heading("Payout Schedule", size="4", color="blue.600"),
                                    rx.box(
                                        rx.table.root(
                                            rx.table.header(
                                                rx.table.row(
                                                    rx.table.column_header_cell("Payment #", text_align="center"),
                                                    rx.table.column_header_cell("Date", text_align="center"),
                                                    rx.table.column_header_cell("Amount", text_align="right"),
                                                )
                                            ),
                                            rx.table.body(
                                                rx.foreach(
                                                    State.payout_schedule_data,
                                                    lambda row: rx.table.row(
                                                        rx.table.cell(row["payment_number"], text_align="center"),
                                                        rx.table.cell(row["date"], text_align="center"),
                                                        rx.table.cell(f"₹{row['amount']}", text_align="right", weight="medium"),
                                                    ),
                                                )
                                            ),
                                            variant="surface",
                                            size="2"
                                        ),
                                        overflow_x="auto",
                                        width="100%"
                                    ),
                                    spacing="3",
                                    width="100%"
                                )
                            ),
                            
                            # Analysis section
                            rx.cond(
                                State.analysis_text,
                                rx.vstack(
                                    rx.heading("Investment Analysis", size="4", color="blue.600"),
                                    rx.text(
                                        State.analysis_text,
                                        size="3",
                                        line_height="1.6",
                                        white_space="pre-wrap"
                                    ),
                                    spacing="3",
                                    width="100%",
                                    padding="1.5rem",
                                    background="green.50",
                                    border_radius="md"
                                )
                            ),
                            
                            spacing="6",
                            width="100%"
                        ),
                        width="100%",
                        max_width="900px",
                        padding="2rem"
                    )
                )
            ),
            # Action buttons
            rx.hstack(
                rx.link(
                    rx.button(
                        "← Back to Home",
                        variant="outline",
                        size="3",
                        color_scheme="gray"
                    ),
                    href="/"
                ),
                rx.button(
                    "🔄 Reset Form",
                    on_click=State.refresh,
                    variant="outline",
                    size="3",
                    color_scheme="blue",
                    disabled=State.processing
                ),
                spacing="3",
                justify="center",
                margin_top="2rem"
            ),
            
            spacing="6",
            padding="2rem",
            width="100%",
            max_width="1200px",
            margin="0 auto"
        ),
        width="100%"
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
app.add_page(form, route="/form") 
