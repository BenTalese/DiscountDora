import urllib.parse

from pydantic import BaseModel
from session import create_session

# TODO: Learn https://docs.pydantic.dev/2.3/usage/models/
# TODO: Learn https://docs.pydantic.dev/2.3/errors/errors/
class WoolworthsProductOffer(BaseModel, extra='allow'):
    Stockcode: int
    DisplayName: str # 'Lindt Lindor Milk Chocolate Balls 333g'
    IsAvailable: bool
    Name: str # 'Lindt Lindor Milk Chocolate Balls'
    Price: float
    WasPrice: float

    # TODO: Not sure if these are useful and/or crossover with all other merchants
    Barcode: str
    CupPrice: float
    InstoreCupPrice: float
    CupMeasure: str # '100G'
    CupString: str # '$7.21 / 100G'
    InstoreCupString: str # '$7.21 / 100G'
    HasCupPrice: bool
    InstoreHasCupPrice: bool
    InstorePrice: float
    LargeImageFile: str # 'https://cdn0.woolworths.media/content/wowproductimages/large/114682.jpg'
    IsNew: bool
    IsHalfPrice: bool
    IsOnlineOnly: bool
    InstoreWasPrice: float
    IsInStock: bool
    PackageSize: str # '333G'
    InstoreIsAvailable: bool
    Brand: str # 'Lindt'
    Variety: str # 'Mineral Water'

# TODO: This could be on the WoolworthsProductOffer? See remaining from old woolies search file
def search_by_id(product_id: str):
    _Session = create_session()
    _Response = _Session.get(url = f'https://www.woolworths.com.au/api/v3/ui/schemaorg/product/{product_id}')
    return WoolworthsProductOffer.model_construct(**_Response.json()) # TODO: Are the two '**' needed?

def search(search_term: str, max_page_search: int = 0, start_page: int = 1):
    _Session = create_session() # TODO: Investigate optimal lifespan of session, outside or inside this method
    _Session.get(url='https://www.woolworths.com.au')

    _Url = 'https://www.woolworths.com.au/apis/ui/Search/products'
    _Body = {
        'Filters': [],
        'IsSpecial': False,
        'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": search_term})}',
        'PageNumber': start_page,
        'PageSize': 36,
        'SearchTerm': search_term,
        'SortType': "TraderRelevance"
    }

    #_ProductSearchResults = []
    while True:
        _Response = _Session.post(url=_Url, json=_Body)
        _PageSearchResult = _Response.json()

        # NOTE: Things that could be useful: SearchResultsCount, Aggregations and FacetFilters
        # NOTE: Although, probably not common functionality I could use across merchants...
        if _PageSearchResult['Products'] is None:
            break

        # TODO: Figure out if validation would be useful
        # Remove '.model_construct' to get validation
        # Could give defaults to get around unwanted validation...
        for _ProductSearchResult in _PageSearchResult['Products']:
            yield WoolworthsProductOffer.model_construct(**_ProductSearchResult['Products'][0])
            #_ProductSearchResults.append(WoolworthsProductOffer.model_construct(**_ProductSearchResult['Products'][0]))

        #yield _PageSearchResult['Products']

        if _Body['PageNumber'] == max_page_search:
            break

        _Body['PageNumber'] += 1
        # _Search_page = ProductPageSearchResult.parse_obj(response)
        # if _Search_page.Products is None:

if __name__ == '__main__':
    gen = search('Soda', 1)
    for x in gen:
        print(x)
