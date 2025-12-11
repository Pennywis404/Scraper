# -*- coding: utf-8 -*-
import json
from groq import AsyncGroq
from scraper.models import BusinessType


CLASSIFICATION_PROMPT = """Tu es un expert en classification d'entreprises.

Analyse le produit suivant et determine s'il s'agit d'une entreprise B2B (Business-to-Business) ou B2C (Business-to-Consumer).

**Nom:** {name}
**Tagline:** {tagline}
**Description:** {description}

Criteres B2B:
- Cible des entreprises, equipes, ou professionnels
- Outils de productivite pour entreprises
- SaaS pour entreprises
- Solutions d'infrastructure, API, developpement
- Outils de gestion, RH, comptabilite, CRM

Criteres B2C:
- Cible des consommateurs individuels
- Applications personnelles (fitness, dating, divertissement)
- E-commerce grand public
- Reseaux sociaux, jeux, lifestyle

Reponds UNIQUEMENT avec ce format JSON:
{{"classification": "B2B" ou "B2C", "reason": "explication courte en 1 phrase"}}
"""


class ClassifierAgent:
    """Agent that classifies products as B2B or B2C using Groq (Llama 3.1)."""

    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    async def classify(
        self,
        name: str,
        tagline: str,
        description: str
    ) -> tuple[BusinessType, str]:
        """
        Classify a product as B2B or B2C.
        Returns (BusinessType, reason).
        """
        prompt = CLASSIFICATION_PROMPT.format(
            name=name,
            tagline=tagline,
            description=description or tagline,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui repond uniquement en JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150,
            )

            text = response.choices[0].message.content.strip()

            # Clean markdown code blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            result = json.loads(text)
            classification = result.get("classification", "").upper()
            reason = result.get("reason", "")

            if classification == "B2B":
                return BusinessType.B2B, reason
            elif classification == "B2C":
                return BusinessType.B2C, reason
            else:
                return BusinessType.UNKNOWN, f"Classification unclear: {text}"

        except Exception as e:
            return BusinessType.UNKNOWN, f"Error: {str(e)}"

    async def classify_batch(
        self,
        products: list[dict]
    ) -> list[tuple[str, BusinessType, str]]:
        """
        Classify multiple products.
        Returns list of (product_id, BusinessType, reason).
        """
        results = []

        for product in products:
            business_type, reason = await self.classify(
                name=product.get("name", ""),
                tagline=product.get("tagline", ""),
                description=product.get("description", ""),
            )
            results.append((product.get("id"), business_type, reason))

        return results
