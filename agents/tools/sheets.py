import gspread
from typing import Optional
from urllib.parse import urlparse


class GoogleSheetsExporter:
    """Export data to Google Sheets."""

    # Colors
    COLOR_B2B = {"red": 0.75, "green": 0.93, "blue": 0.75}      # Vert clair
    COLOR_B2C = {"red": 0.96, "green": 0.80, "blue": 0.80}      # Rouge clair
    COLOR_UNKNOWN = {"red": 1, "green": 0.95, "blue": 0.75}     # Jaune
    COLOR_HEADER = {"red": 0.1, "green": 0.1, "blue": 0.15}     # Noir/bleu foncé

    def __init__(self, credentials: dict, spreadsheet_id: Optional[str] = None):
        """Initialize with service account credentials."""
        self.gc = gspread.service_account_from_dict(credentials)
        self.spreadsheet_id = spreadsheet_id
        self._spreadsheet = None

    def _get_spreadsheet(self, spreadsheet_id: Optional[str] = None):
        """Get or create spreadsheet reference."""
        sid = spreadsheet_id or self.spreadsheet_id
        if not sid:
            raise ValueError("No spreadsheet_id provided")

        if self._spreadsheet is None or spreadsheet_id:
            self._spreadsheet = self.gc.open_by_key(sid)

        return self._spreadsheet

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url if url.startswith("http") else f"https://{url}")
            domain = parsed.netloc or parsed.path
            return domain.replace("www.", "")
        except:
            return url

    def _format_date(self, date_str: str) -> str:
        """Format date string to YYYY-MM-DD."""
        if not date_str:
            return ""
        if "T" in date_str:
            return date_str.split("T")[0]
        return date_str


    def _style_worksheet(
        self,
        worksheet,
        num_rows: int,
        num_cols: int,
        products: list[dict],
        color_name_col: bool = True
    ):
        """Apply professional styling to worksheet."""

        # Header style
        col_letter = chr(ord('A') + num_cols - 1)
        worksheet.format(f"A1:{col_letter}1", {
            "backgroundColor": self.COLOR_HEADER,
            "textFormat": {
                "bold": True,
                "fontSize": 11,
                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
            },
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE"
        })

        # Data cells style
        if num_rows > 1:
            worksheet.format(f"A2:{col_letter}{num_rows}", {
                "textFormat": {"fontSize": 10},
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "CLIP"
            })

        # Add filter
        worksheet.set_basic_filter(f"A1:{col_letter}{num_rows}")

        # Freeze header
        worksheet.freeze(rows=1)

        # Color the Name column (column A) based on business type
        if color_name_col and products:
            for i, p in enumerate(products, start=2):
                business_type = p.get("business_type", "UNKNOWN")

                if business_type == "B2B":
                    color = self.COLOR_B2B
                elif business_type == "B2C":
                    color = self.COLOR_B2C
                else:
                    color = self.COLOR_UNKNOWN

                worksheet.format(f"A{i}", {
                    "backgroundColor": color,
                    "textFormat": {"bold": True, "fontSize": 10}
                })

    def export_b2b_products(
        self,
        products: list[dict],
        spreadsheet_id: Optional[str] = None,
        worksheet_name: str = "B2B Products"
    ) -> int:
        """
        Export B2B products to dedicated sheet.
        Green color on Name column.
        """
        if not products:
            return 0

        spreadsheet = self._get_spreadsheet(spreadsheet_id)

        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=len(products) + 10,
                cols=10
            )

        # Headers: Name, Tagline, Website, Classification, Type, Date
        headers = ["Name", "Tagline", "Website", "Classification", "Type", "Date"]

        # Prepare rows
        rows = [headers]
        for p in products:
            rows.append([
                p.get("name", ""),
                p.get("tagline", ""),
                p.get("website", "") or "",
                p.get("classification_reason", ""),
                p.get("business_type", "B2B"),
                self._format_date(p.get("created_at", "") or ""),
            ])

        # Update data (value_input_option RAW to interpret formulas)
        worksheet.update(rows, "A1", value_input_option="USER_ENTERED")

        # Apply styling
        self._style_worksheet(
            worksheet,
            num_rows=len(products) + 1,
            num_cols=6,
            products=products,
            color_name_col=False
        )

        return len(products)

    def export_other_products(
        self,
        products: list[dict],
        spreadsheet_id: Optional[str] = None,
        worksheet_name: str = "Startup Tracker"
    ) -> int:
        """
        Export B2C and UNKNOWN products to Startup Tracker.
        Red for B2C, Yellow for UNKNOWN on Name column.
        """
        if not products:
            return 0

        spreadsheet = self._get_spreadsheet(spreadsheet_id)

        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=len(products) + 10,
                cols=10
            )

        # Headers: Name, Tagline, Website, Classification, Type, Date
        headers = ["Name", "Tagline", "Website", "Classification", "Type", "Date"]

        # Prepare rows
        rows = [headers]
        for p in products:
            rows.append([
                p.get("name", ""),
                p.get("tagline", ""),
                p.get("website", "") or "",
                p.get("classification_reason", ""),
                p.get("business_type", "UNKNOWN"),
                self._format_date(p.get("created_at", "") or ""),
            ])

        # Update data (value_input_option to interpret formulas)
        worksheet.update(rows, "A1", value_input_option="USER_ENTERED")

        # Apply styling
        self._style_worksheet(
            worksheet,
            num_rows=len(products) + 1,
            num_cols=6,
            products=products,
            color_name_col=False
        )

        return len(products)

    def export_all_to_tracker(
        self,
        all_products: list[dict],
        spreadsheet_id: Optional[str] = None
    ) -> dict:
        """
        Export all products split into two sheets:
        - B2B Products: Only B2B startups (green Name)
        - Startup Tracker: B2C and UNKNOWN (red/yellow Name)

        Returns dict with counts for each sheet.
        """
        # Split products by type
        b2b_products = [p for p in all_products if p.get("business_type") == "B2B"]
        other_products = [p for p in all_products if p.get("business_type") != "B2B"]

        # Sort by date (most recent first)
        b2b_products.sort(key=lambda x: x.get("created_at", "") or "", reverse=True)
        other_products.sort(key=lambda x: x.get("created_at", "") or "", reverse=True)

        # Export to respective sheets
        b2b_count = self.export_b2b_products(b2b_products, spreadsheet_id)
        other_count = self.export_other_products(other_products, spreadsheet_id)

        return {
            "b2b_exported": b2b_count,
            "other_exported": other_count,
            "total": b2b_count + other_count
        }

    def export_indie_products(
        self,
        products: list,
        spreadsheet_id: Optional[str] = None,
        worksheet_name: str = "Indie Hackers"
    ) -> int:
        """
        Export Indie Hackers products to dedicated sheet.
        Columns: Name, Tagline, Revenue, Stripe, Website
        """
        if not products:
            return 0

        spreadsheet = self._get_spreadsheet(spreadsheet_id)

        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=len(products) + 10,
                cols=10
            )

        # Headers
        headers = ["Name", "Tagline", "Revenue", "Stripe Verified", "URL"]

        # Prepare rows
        rows = [headers]
        for p in products:
            # Handle both dict and dataclass
            if hasattr(p, "to_dict"):
                p = p.to_dict()

            rows.append([
                p.get("name", ""),
                p.get("tagline", ""),
                p.get("revenue", ""),
                "Yes" if p.get("stripe_verified") else "No",
                p.get("url", ""),
            ])

        # Update data
        worksheet.update(rows, "A1", value_input_option="USER_ENTERED")

        # Apply styling (reuse existing method)
        self._style_worksheet(
            worksheet,
            num_rows=len(products) + 1,
            num_cols=5,
            products=[],  # No color coding
            color_name_col=False
        )

        return len(products)
