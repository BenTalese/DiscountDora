---

kanban-plugin: basic

---

## Backlog 💡 #grey

- [ ] I can view all of my saved products #overview
- [ ] [[I can see the price history of a product by merchant]] #overview
- [ ] I can remove a merchant product from my saved products #overview
- [ ] I get a deletion confirmation (unsaving) if a saved product is linked to something already in Dora #overview
- [ ] [[I can manually add product offers to saved scraped products]] #overview
- [ ] [[I can resave an unsaved product if I accidentally unsaved it]] #overview
- [ ] I can see historical pricing data for saved products #overview
- [ ] I can see all relevant product information #overview
- [ ] [[I can see the current deal of a product]] #overview
- [ ] I can create my own products for manual tracking #custom_products
- [ ] I can edit & update my own custom products #custom_products
- [ ] I can easily see which of my saved products are custom products #custom_products
- [ ] I can manually add product offers to my custom products #custom_products
- [ ] I can create my own custom merchants #custom_products
- [ ] I can delete my own custom products #custom_products
- [ ] Products from scrape results are locked down (readonly) while custom products are editable #custom_products
- [ ] I can visually distinguish readonly products from custom products #custom_products
- [ ] [[I can view the current deals like a catalogue]] #overview
- [ ] [[I can add a product directly to the shopping cart from my saved products]] #overview
- [ ] I can receive the product deals email to my registered email on the day I specify #deals_email
- [ ] I can see a section for "on your shopping list" #deals_email
- [ ] I can see a section for "half price deals" #deals_email
- [ ] I can see how much a product is for currently #deals_email
- [ ] I can see how much a product is reduced by (exact savings) #deals_email
- [ ] I can see the original price for a product #deals_email
- [ ] I can see the discount percentage for a product #deals_email
- [ ] I can see the per unit price for a product #deals_email
- [ ] I can order the deal sections via my preferences in Dora #deals_email
- [ ] I can see highlighting for products on half-price #deals_email
- [ ] I can save a scraped product to "my products" #product_search
- [ ] I can remove a scraped product from "my products" from the product search #product_search
- [ ] [[I can sort product results by relevancy, name, price, etc]] #filters #product_search
- [ ] I can search for products by their stockcode #product_search
- [ ] I can see a product's information including: brand, merchant, image, price, weight/size, availability, stockcode, name #product_search
- [ ] I can click/tap on a product to visit its page from the merchant's website #product_search
- [ ] I can filter products by availability #filters #product_search
- [ ] I can filter products by merchant, and can filter to multiple merchants (multi-select) #filters #product_search
- [ ] I can filter products I have already saved #filters #product_search
- [ ] I can sort products by price high -> low and low -> high #filters #product_search
- [ ] I can search products from Amazon #product_search
- [ ] [[I can see immediate UI feedback on the search if there's no internet connection]] #product_search
- [ ] I can control how many results I get per merchant #product_search
- [ ] I can see metadata about search such as page number, product count, etc #product_search
- [ ] The loading spinner tells me search may take some time depending on number of merchants to search #product_search
- [ ] [[I can see which merchants are currently available (see connection status)]] #product_search
- [ ] I see UI feedback if I tap or hover on a disabled merchant. A merchant would be disabled if unavailable or disabled via the configurator. #product_search
- [ ] [[I can quick-add a product so that it also creates the stock item and links them together]] #product_search
- [ ] [[I can add a product to the shopping cart directly from the product search]] #product_search
- [ ] I don't get confirmation prompt when unsaving product if it isn't tied to anything #product_search
- [ ] I don't get confirmation prompt when unsaving product if it isn't tied to anything #overview
- [ ] [[I can sort products by  Unit Price (High to Low)  and  Unit Price (Low to High)]] #filters #product_search
- [ ] I can add notes to products (e.g. "I don't like this one") #detail_view
- [ ] [[The ALDI cache rebuilds itself periodically, keeping it up to date, triggered by my search]] #product_search
- [ ] Can we scrape individual store data for product location? Could be manual input we allow, but would people bother adding that info per product? Probably not #product_search
- [ ] [[I can add products to a comparison tool and compare their details]]
- [ ] Wherever I see a product, I can click to see that product's information (or navigate to its webpage)
- [ ] I can optionally (user preference) see the source of a product on product search cards (e.g. SaveOnGroceries or Coles) #product_search
- [ ] I can choose how many products are retrieved per page #product_search
- [ ] I get UI feedback when saving a product, e.g. a toast/quasar notify #product_search
- [ ] [[I can un-save un-favourite a product]]
- [ ] The search results have an algorithm to sort by 'Relevance'. This should also be the default. #product_search
- [ ] [[Deals are highlighted more prominently depending on the % off]]
- [ ] I can always see the % off a deal is, unless the product is full price
- [ ] [[I can filter to half price or better deals]] #filters
- [ ] I can see an "on your shopping list" deal section, which is deals for merchant products linked to stock items on a shopping list #deals_email
- [ ] I can "see similar deals" when a product is out of stock, or all products for a stock item are out of stock
- [ ] I can view the product offer email in my browser for compatibility #deals_email
- [ ] [[I can assign products to categories (e.g. freezer, fruit, meat)]]
- [ ] I can sort products by % off #filters
- [ ] I can sort products by amount off #filters
- [ ] [[I can receive a compact simplified deals email]] #deals_email
- [ ] [[I can at a glance see pricing trend information on a product]]
- [ ] I can link a stock item to a product from the products page
- [ ] I can query and create historical reports for pricing data
- [ ] [[I can translate between units of measurement]]
- [ ] The screen for no products found is in theme with the Dora styling - maybe use mascot instead of banana #product_search
- [ ] I am told I have no internet connection and am prevented from searching when this is so #product_search
- [ ] Searching times out in a time frame that makes sense #product_search


## Refining ✏️ #orange



## Ready Task 🎁 #cyan

- [ ] I can cancel the search at any time without refreshing the browser tab #product_search


## In Progress ⏩️ #blue



## Done ✅ #green

**Complete**
- [x] I can search and browse products of merchants matching the term I have searched for #product_search #v200
- [x] I can do a fresh search and see products I have previously saved #product_search #v200
- [x] I can search products from IGA #product_search #v200
- [x] I can search products from Coles #product_search #v200
- [x] I can search products from Woolworths #product_search #v200
- [x] I can search products from ALDI #product_search #v200
- [x] I can see UI feedback for when my search results are loading #product_search #v200


## Archived ⛔️ #black

**Complete**
- [x] [[I can filter products by price range]] #product_search
- [x] [[I can filter products by weight range]] #product_search #filters
- [x] Add toggle option for suggested product deals (related to search products) (Archived: what the hell was I talking about??)




%% kanban:settings
```
{"kanban-plugin":"basic","new-note-template":"Discount Dora/Templates/Feature Note.md","new-note-folder":"Discount Dora/Feature Notes","lane-width":400,"tag-colors":[{"tagKey":"#80%","color":"","backgroundColor":"rgba(222, 55, 55, 0.79)"},{"tagKey":"#filters","color":"","backgroundColor":"rgba(201, 181, 46, 0.64)"},{"tagKey":"#custom_products","color":"","backgroundColor":"rgba(2, 158, 158, 0.72)"},{"tagKey":"#deals_email","color":"","backgroundColor":"rgba(60, 145, 14, 0.73)"}],"metadata-keys":[{"metadataKey":"description","label":"Description","shouldHideLabel":true,"containsMarkdown":false}]}
```
%%