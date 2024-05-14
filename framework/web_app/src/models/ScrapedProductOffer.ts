import { Product } from "./Product"

export type ScrapedProductOffer = {
    brand: string | null
    image: string
    is_available: boolean
    is_saved: boolean
    is_saved_product_active?: boolean
    merchant_name: string
    merchant_stockcode: string
    name: string
    price_difference: number
    price_now: number
    price_per_cup: string | null
    price_was: number
    size: string
    size_unit: string
    size_value: number
    web_url: string
}
