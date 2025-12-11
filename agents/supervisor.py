# -*- coding: utf-8 -*-
"""
Supervisor orchestrates the full workflow:
1. Scrape Product Hunt
2. Store in Supabase
3. Classify with Groq (Llama 3.3)
4. Export to Google Sheets (B2B Products + Startup Tracker)
"""

from typing import Callable, Optional
from datetime import datetime

from scraper import ProductHuntClient, Product
from database import LaunchesRepository
from agents.worker import ClassifierAgent
from agents.tools.sheets import GoogleSheetsExporter


class WorkflowSupervisor:
    """Orchestrates the complete scraping and classification workflow."""

    def __init__(
        self,
        scraper: ProductHuntClient,
        repository: LaunchesRepository,
        classifier: Optional[ClassifierAgent] = None,
        sheets_exporter: Optional[GoogleSheetsExporter] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.scraper = scraper
        self.repository = repository
        self.classifier = classifier
        self.sheets_exporter = sheets_exporter
        self.on_status = on_status or (lambda x: None)

    def _emit(self, message: str):
        """Emit a status message."""
        self.on_status(message)

    async def run(
        self,
        limit: int = 50,
        date: Optional[datetime] = None,
        spreadsheet_id: Optional[str] = None,
        skip_classification: bool = False,
        skip_export: bool = False,
    ) -> dict:
        """
        Run the complete workflow.

        Args:
            limit: Max number of products to scrape
            date: Specific date to scrape (None = today)
            spreadsheet_id: Google Sheets ID for export

        Returns:
            Summary stats
        """
        stats = {
            "scraped": 0,
            "stored": 0,
            "classified": 0,
            "b2b_count": 0,
            "b2c_count": 0,
            "exported": 0,
            "errors": [],
        }

        try:
            # Step 1: Scrape
            self._emit("Lancement du scraping Product Hunt...")

            if date:
                products = await self.scraper.get_posts_by_date(date, limit)
            else:
                products = await self.scraper.get_today_posts(limit)

            stats["scraped"] = len(products)
            self._emit(f"Lancement OK - {len(products)} produits trouves")

            # Step 2: Store in database
            self._emit("Envoi vers la base de donnees...")

            stored = await self.repository.insert_products(products)
            stats["stored"] = stored
            self._emit(f"Donnees scrappees - {stored} produits enregistres")

            # Step 3: Classify (optional)
            if not skip_classification and self.classifier:
                self._emit("Classification B2B/B2C en cours...")

                unclassified = await self.repository.get_unclassified()
                classifications = await self.classifier.classify_batch(unclassified)

                for product_id, business_type, reason in classifications:
                    await self.repository.update_classification(
                        product_id, business_type, reason
                    )
                    if business_type.value == "B2B":
                        stats["b2b_count"] += 1
                    elif business_type.value == "B2C":
                        stats["b2c_count"] += 1

                stats["classified"] = len(classifications)
                self._emit(
                    f"Classement fait - {stats['b2b_count']} B2B, {stats['b2c_count']} B2C"
                )
            else:
                self._emit("Classification ignoree (skip_classification=True)")

            # Step 4: Export to Google Sheets (optional)
            if not skip_export and spreadsheet_id and self.sheets_exporter:
                self._emit("Export vers Google Sheets...")

                all_products = await self.repository.get_all()
                export_result = self.sheets_exporter.export_all_to_tracker(
                    all_products,
                    spreadsheet_id=spreadsheet_id,
                )
                stats["exported"] = export_result["total"]
                stats["b2b_exported"] = export_result["b2b_exported"]
                stats["other_exported"] = export_result["other_exported"]
                self._emit(
                    f"Export termine - {export_result['b2b_exported']} B2B, "
                    f"{export_result['other_exported']} autres"
                )
            elif skip_export:
                self._emit("Export ignore (skip_export=True)")
            else:
                self._emit("Pas de spreadsheet_id fourni, export ignore")

            self._emit("Workflow termine avec succes!")

        except Exception as e:
            stats["errors"].append(str(e))
            self._emit(f"Erreur: {str(e)}")

        return stats
