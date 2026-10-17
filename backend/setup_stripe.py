import os
from pathlib import Path

import stripe
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

PRODUCT_ID = "tlg_full_access"
LOOKUP_KEY = "tlg_full_access_40"
AMOUNT = 4000


def get_or_create_product():
    for p in stripe.Product.list(active=True).auto_paging_iter():
        if p.to_dict().get("metadata", {}).get("emergent_product_id") == PRODUCT_ID:
            return p
    return stripe.Product.create(
        name="The Lord's Gym - Full Access", tax_code="txcd_10302000",
        description="Full access to the assessment platform and training videos",
        metadata={"managed_by": "emergent", "emergent_product_id": PRODUCT_ID},
    )


def ensure_price(product):
    existing = stripe.Price.list(lookup_keys=[LOOKUP_KEY], active=True, limit=1).data
    if existing and existing[0].unit_amount == AMOUNT:
        return existing[0]
    if existing:
        stripe.Price.modify(existing[0].id, active=False)
    return stripe.Price.create(product=product.id, unit_amount=AMOUNT, currency="usd",
                               lookup_key=LOOKUP_KEY, transfer_lookup_key=True)


if __name__ == "__main__":
    prod = get_or_create_product()
    price = ensure_price(prod)
    print(prod.id, price.id, price.unit_amount)
