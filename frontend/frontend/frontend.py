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
        self.processing = True
        self.analysis = ""
        try:
            # The API is running on port 8000
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
                data = response.json()
                self.analysis = data.get("analysis", "No analysis found.")
        except httpx.HTTPError as e:
            self.analysis = f"An API error occurred: {e}"
        except Exception as e:
            self.analysis = f"An unexpected error occurred: {e}"
        finally:
            self.processing = False

    def refresh(self):
        """Clear the form and analysis."""
        self.coupon_rate = 0.0
        self.rating = ""
        self.interest_frequency = ""
        self.redemption_year = 2024
        self.analysis = ""

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
            rx.heading("AI Financial Advisor", size="9"),
            rx.link(
                rx.button("Get Started"),
                href="/form",
            ),
            spacing="5",
            justify="center",
            align="center",
            min_height="100vh",
        )
    )

def form() -> rx.Component:
    """The form page to get recommendations."""
    return rx.container(
        rx.vstack(
            rx.heading("Get Bond Recommendations", size="7"),
            rx.hstack(
                rx.input(placeholder="Coupon Rate (e.g., 5.5)", type="number", on_change=State.handle_coupon_rate_change),
                rx.select(
                    State.ratings,
                    placeholder="Select Rating",
                    on_change=State.set_rating,
                ),
                rx.select(
                    State.frequencies,
                    placeholder="Select Frequency",
                    on_change=State.set_interest_frequency,
                ),
            ),
            rx.input(
                placeholder="Redemption Year (e.g., 2030)",
                type="number",
                on_change=State.handle_redemption_year_change
            ),
            rx.button(
                "Get Recommendations",
                on_click=State.get_recommendations,
                is_loading=State.processing,
            ),
            rx.cond(
                State.analysis,
                rx.card(
                    rx.vstack(
                        rx.cond(
                            State.bond_description,
                            rx.vstack(
                                rx.heading("Bond Details", size="5"),
                                rx.text(State.bond_description, as_="p"),
                                rx.hstack(rx.text("Company:", weight="bold"), rx.text(State.company_name)),
                                rx.hstack(rx.text("Instrument:", weight="bold"), rx.text(State.instrument_name)),
                                spacing="2",
                                align_items="start",
                                width="100%"
                            )
                        ),
                        rx.cond(
                            State.payout_schedule_data,
                            rx.vstack(
                                rx.heading("Payout Schedule", size="5"),
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("Payment Number"),
                                            rx.table.column_header_cell("Date"),
                                            rx.table.column_header_cell("Amount"),
                                        )
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            State.payout_schedule_data,
                                            lambda row: rx.table.row(
                                                rx.table.cell(row["payment_number"]),
                                                rx.table.cell(row["date"]),
                                                rx.table.cell(row["amount"]),
                                            ),
                                        )
                                    ),
                                    variant="surface",
                                ),
                                align_items="start",
                                width="100%"
                            )
                        ),
                        rx.cond(
                            State.analysis_text,
                            rx.vstack(
                                rx.heading("Analysis", size="5"),
                                rx.text(State.analysis_text, as_="p"),
                                align_items="start",
                                width="100%"
                            )
                        ),
                        spacing="4"
                    ),
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.button("Refresh", on_click=State.refresh),
                rx.button("Feedback"),  # Placeholder for feedback functionality
            ),
            spacing="4",
            padding_top="5vh",
            width="100%",
        ),
        center_content=True,
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
app.add_page(form, route="/form") 
