"""On-demand merchant data-provider health check.

The merchant API already runs this daily on a cron via APScheduler, but the
settings UI needs a way to ask "are these working right now?" without waiting
for the next scheduled tick.

We do a single light search per provider against any merchant it supports.
Results update each provider's in-memory `is_healthy` flag (same field the
GET `/api/health/data-providers` endpoint reads).
"""
import logging

from flask import jsonify

from merchant_api.infrastructure.configuration_manager import \
    CONFIGURATION_MANAGER
from merchant_api.infrastructure.merchant_data_providers import \
    MERCHANT_DATA_PROVIDERS
from merchant_api.routers import HEALTH_ROUTER


@HEALTH_ROUTER.route("data-providers/check", methods=["POST"])
def run_data_provider_health_check():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Ad-hoc data-provider health check requested.")
    _Merchants = CONFIGURATION_MANAGER.get_all_merchants()
    _Results = []

    for _Provider in MERCHANT_DATA_PROVIDERS:
        try:
            _SupportedMerchant = next(
                (m for m in _Merchants if _Provider.is_merchant_supported(m)),
                None,
            )
            if _SupportedMerchant is None:
                # A provider with no enabled merchant just stays at its last
                # known state — we can't probe it without a target.
                _Results.append({
                    "base_url": _Provider.base_url,
                    "is_healthy": _Provider.is_healthy,
                    "skipped": True,
                })
                continue

            _Offers = _Provider.search_by_term('Chocolate Ice Cream', _SupportedMerchant, 1)
            _Provider.is_healthy = bool(_Offers)
        except Exception:
            _Provider.is_healthy = False
            _Logger.exception(
                "Data provider '%s' failed during ad-hoc health check.",
                _Provider.base_url,
            )

        _Results.append({
            "base_url": _Provider.base_url,
            "is_healthy": _Provider.is_healthy,
            "skipped": False,
        })

    return jsonify(_Results), 200
