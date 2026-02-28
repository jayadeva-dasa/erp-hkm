"""
API package for HKM app.

This file ensures Python treats `hkm.api` as a package so routes like
`hkm.api.v1.guest_house.*` resolve correctly. Dashboard APIs (eagle_view,
category_analytics, asset_reco, chart_of_accounts, daily_sales_report) live in
hkm_dashboard.api.
"""

__all__ = ["v1"]

