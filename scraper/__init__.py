from scraper.client import ProductHuntClient
from scraper.models import Product, BusinessType

# Lazy import for Playwright-dependent modules (not available on Streamlit Cloud)
def __getattr__(name):
    if name in ("IndieHackersClient", "IndieProduct"):
        from scraper.indiehackers import IndieHackersClient, IndieProduct
        globals()["IndieHackersClient"] = IndieHackersClient
        globals()["IndieProduct"] = IndieProduct
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ProductHuntClient",
    "Product",
    "BusinessType",
    "IndieHackersClient",
    "IndieProduct",
]
