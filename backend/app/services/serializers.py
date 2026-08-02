from app.models import Transaction


def serialize_transaction(txn: Transaction, merchant_name: str) -> dict:
    return {
        "id": txn.id,
        "merchant_name": merchant_name,
        "amount": float(txn.amount),
        "posted_date": txn.posted_date.isoformat(),
        "expected_amount": float(txn.expected_amount) if txn.expected_amount is not None else None,
        "deviation_pct": txn.deviation_pct,
        "is_drift": txn.is_drift,
    }
