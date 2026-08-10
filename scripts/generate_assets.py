from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_data"


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    with (DEMO / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    assets = [
        {"name": "customers", "type": "Table", "owner": "Data Platform", "description": "Canonical customer profile table", "certified": "true", "freshness": "1 hour", "columns": "customer_id|email|signup_date|country|segment", "sensitivity": "PII"},
        {"name": "orders", "type": "Table", "owner": "Commerce Analytics", "description": "Customer order transactions", "certified": "true", "freshness": "2 hours", "columns": "order_id|customer_id|amount|created_at|status", "sensitivity": "INTERNAL"},
        {"name": "order_items", "type": "Table", "owner": "Commerce Analytics", "description": "Line items for each order", "certified": "true", "freshness": "2 hours", "columns": "order_id|product_id|quantity|unit_price", "sensitivity": "INTERNAL"},
        {"name": "products", "type": "Table", "owner": "Catalog Team", "description": "Product catalog", "certified": "true", "freshness": "1 day", "columns": "product_id|sku|category|price", "sensitivity": "PUBLIC"},
        {"name": "payments", "type": "Table", "owner": "Finance Analytics", "description": "Payment events and settlement status", "certified": "true", "freshness": "2 hours", "columns": "payment_id|order_id|amount|payment_status", "sensitivity": "CONFIDENTIAL"},
        {"name": "subscriptions", "type": "Table", "owner": "Growth Analytics", "description": "Subscription lifecycle data", "certified": "false", "freshness": "6 hours", "columns": "subscription_id|customer_id|plan|status", "sensitivity": "PII"},
        {"name": "web_events", "type": "Table", "owner": "Product Analytics", "description": "Website behavioral events", "certified": "false", "freshness": "15 minutes", "columns": "event_id|customer_id|event_name|event_time", "sensitivity": "PII"},
        {"name": "support_tickets", "type": "Table", "owner": "Support Ops", "description": "Customer support ticket history", "certified": "true", "freshness": "4 hours", "columns": "ticket_id|customer_id|topic|priority", "sensitivity": "PII"},
        {"name": "daily_revenue", "type": "Table", "owner": "Finance Analytics", "description": "Daily recognized revenue by customer", "certified": "true", "freshness": "2 hours", "columns": "date|customer_id|gross_revenue|net_revenue", "sensitivity": "INTERNAL"},
        {"name": "monthly_revenue", "type": "Table", "owner": "Finance Analytics", "description": "Monthly rollup of recognized revenue", "certified": "true", "freshness": "1 day", "columns": "month|net_revenue|customer_count", "sensitivity": "INTERNAL"},
        {"name": "customer_360", "type": "Table", "owner": "Data Platform", "description": "Joined customer profile and lifecycle view", "certified": "true", "freshness": "3 hours", "columns": "customer_id|segment|lifetime_value|last_order_at", "sensitivity": "PII"},
        {"name": "customer_features", "type": "Table", "owner": "ML Platform", "description": "Feature table for customer models", "certified": "true", "freshness": "6 hours", "columns": "customer_id|orders_30d|visits_30d|tickets_30d", "sensitivity": "PII"},
        {"name": "churn_features", "type": "Table", "owner": "ML Platform", "description": "Churn model training features", "certified": "false", "freshness": "12 hours", "columns": "customer_id|tenure_days|support_count|usage_drop", "sensitivity": "PII"},
        {"name": "marketing_attribution", "type": "Table", "owner": "Marketing Analytics", "description": "Campaign touchpoints mapped to customers", "certified": "false", "freshness": "1 day", "columns": "customer_id|campaign_id|channel|touch_time", "sensitivity": "PII"},
        {"name": "campaign_performance", "type": "Table", "owner": "Marketing Analytics", "description": "Campaign performance rollups", "certified": "true", "freshness": "1 day", "columns": "campaign_id|spend|conversions|revenue", "sensitivity": "INTERNAL"},
        {"name": "inventory_snapshot", "type": "Table", "owner": "Supply Chain", "description": "Current inventory by SKU", "certified": "true", "freshness": "1 hour", "columns": "sku|warehouse|quantity|updated_at", "sensitivity": "INTERNAL"},
        {"name": "refunds", "type": "Table", "owner": "Finance Analytics", "description": "Refund events by order", "certified": "true", "freshness": "4 hours", "columns": "refund_id|order_id|amount|reason", "sensitivity": "CONFIDENTIAL"},
        {"name": "revenue_dashboard", "type": "Dashboard", "owner": "Finance Analytics", "description": "Executive revenue performance dashboard", "certified": "true", "freshness": "2 hours", "columns": "", "sensitivity": "INTERNAL"},
        {"name": "customer_dashboard", "type": "Dashboard", "owner": "CX Analytics", "description": "Customer health and lifecycle dashboard", "certified": "true", "freshness": "3 hours", "columns": "", "sensitivity": "INTERNAL"},
        {"name": "marketing_dashboard", "type": "Dashboard", "owner": "Marketing Analytics", "description": "Campaign and attribution dashboard", "certified": "false", "freshness": "1 day", "columns": "", "sensitivity": "INTERNAL"},
        {"name": "ops_dashboard", "type": "Dashboard", "owner": "Operations", "description": "Inventory and fulfillment dashboard", "certified": "true", "freshness": "1 hour", "columns": "", "sensitivity": "INTERNAL"},
        {"name": "support_dashboard", "type": "Dashboard", "owner": "Support Ops", "description": "Support ticket trends dashboard", "certified": "true", "freshness": "4 hours", "columns": "", "sensitivity": "INTERNAL"},
    ]
    lineage = [
        {"source": "customers", "target": "orders", "relationship_type": "FEEDS"},
        {"source": "orders", "target": "order_items", "relationship_type": "FEEDS"},
        {"source": "products", "target": "order_items", "relationship_type": "FEEDS"},
        {"source": "orders", "target": "payments", "relationship_type": "FEEDS"},
        {"source": "orders", "target": "daily_revenue", "relationship_type": "DERIVED_FROM"},
        {"source": "payments", "target": "daily_revenue", "relationship_type": "FEEDS"},
        {"source": "refunds", "target": "daily_revenue", "relationship_type": "FEEDS"},
        {"source": "daily_revenue", "target": "monthly_revenue", "relationship_type": "DERIVED_FROM"},
        {"source": "daily_revenue", "target": "revenue_dashboard", "relationship_type": "USED_BY"},
        {"source": "monthly_revenue", "target": "revenue_dashboard", "relationship_type": "USED_BY"},
        {"source": "customers", "target": "customer_360", "relationship_type": "DERIVED_FROM"},
        {"source": "orders", "target": "customer_360", "relationship_type": "FEEDS"},
        {"source": "subscriptions", "target": "customer_360", "relationship_type": "FEEDS"},
        {"source": "customer_360", "target": "customer_dashboard", "relationship_type": "USED_BY"},
        {"source": "customer_360", "target": "customer_features", "relationship_type": "DERIVED_FROM"},
        {"source": "web_events", "target": "customer_features", "relationship_type": "FEEDS"},
        {"source": "support_tickets", "target": "customer_features", "relationship_type": "FEEDS"},
        {"source": "customer_360", "target": "churn_features", "relationship_type": "DERIVED_FROM"},
        {"source": "support_tickets", "target": "churn_features", "relationship_type": "FEEDS"},
        {"source": "marketing_attribution", "target": "campaign_performance", "relationship_type": "DERIVED_FROM"},
        {"source": "campaign_performance", "target": "marketing_dashboard", "relationship_type": "USED_BY"},
        {"source": "inventory_snapshot", "target": "ops_dashboard", "relationship_type": "USED_BY"},
        {"source": "support_tickets", "target": "support_dashboard", "relationship_type": "USED_BY"},
    ]
    teams = [
        {"team_name": "Data Platform", "contact": "data-platform@example.com", "description": "Owns core warehouse models"},
        {"team_name": "Finance Analytics", "contact": "finance-data@example.com", "description": "Owns revenue and payments metrics"},
        {"team_name": "ML Platform", "contact": "ml-platform@example.com", "description": "Owns model features and ML datasets"},
        {"team_name": "Marketing Analytics", "contact": "marketing-data@example.com", "description": "Owns campaign reporting"},
    ]
    terms = [
        {"term": "Revenue", "definition": "Net recognized revenue excluding refunds and failed payments", "domain": "Finance", "owner": "Finance Analytics", "maps_to_asset": "daily_revenue"},
        {"term": "Customer", "definition": "A person or account with a canonical row in the customer profile table", "domain": "Core", "owner": "Data Platform", "maps_to_asset": "customers"},
        {"term": "Churn Risk", "definition": "Estimated likelihood that an active customer will stop using the product", "domain": "Growth", "owner": "ML Platform", "maps_to_asset": "churn_features"},
    ]
    models = [
        {"name": "customer_churn_model", "owner": "ML Platform", "trained_on": "churn_features", "description": "Predicts customer churn risk", "certified": "true", "freshness": "1 day", "sensitivity": "PII"},
        {"name": "revenue_forecast_model", "owner": "Finance Analytics", "trained_on": "monthly_revenue", "description": "Forecasts next-quarter revenue", "certified": "true", "freshness": "1 day", "sensitivity": "INTERNAL"},
    ]
    column_lineage = [
        {"source_asset": "customers", "source_column": "customer_id", "target_asset": "orders", "target_column": "customer_id"},
        {"source_asset": "orders", "source_column": "customer_id", "target_asset": "daily_revenue", "target_column": "customer_id"},
        {"source_asset": "customers", "source_column": "customer_id", "target_asset": "customer_360", "target_column": "customer_id"},
        {"source_asset": "customer_360", "source_column": "customer_id", "target_asset": "churn_features", "target_column": "customer_id"},
    ]
    write_csv("assets.csv", assets)
    write_csv("lineage.csv", lineage)
    write_csv("teams.csv", teams)
    write_csv("business_terms.csv", terms)
    write_csv("models.csv", models)
    write_csv("column_lineage.csv", column_lineage)
    print(f"Wrote demo data to {DEMO}")


if __name__ == "__main__":
    main()
