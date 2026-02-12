from pydantic import BaseModel

from framework.merchant_api.domain.enumerations.supported_merchant import SupportedMerchant


class Merchant(BaseModel):
    is_enabled: bool
    name: SupportedMerchant
