---

kanban-plugin: basic

---

## Backlog 💡 #grey

- [ ] I can add/link up a saved product to a stock item
- [ ] I can unlink saved products from a stock item
- [ ] I can easily see which stock item is linked to which products
- [ ] [[I can mark a stock item saved product inactive to omit them from being scraped]]
- [ ] I can mark a stock item/saved product active to include them in deal scraping
- [ ] I can use product features without linking products to stock items (e.g. no usage of stock item features)
- [ ] I have the following options when deleting a stock item: delete, backup and delete, cancel
- [ ] When I delete a stock item, I see an "are you sure?" prompt, which states exactly "this will permanently delete the stock item and remove it from all linked products, recipes, shopping lists, etc"
- [ ] [[I can edit the date a stock item was  opened on  in case the automatic one is incorrect]]
- [ ] [[When marking a stock item as  open , an  opened on date  is recorded automatically]]
- [ ] I get notifications of stock items whose stock level have not changed in the configured amount of time, excluding long-life items
- [ ] I can search for a stock item and have options matching my search pop up. At the end of the list should be a "+" icon or something to indiciate "create new" so I can add stock items quickly that I have not yet created.
- [ ] [[When I link a product to a stock item, if the stock item has no picture it takes the product's picture automatically]]
- [ ] I can flag a stock item as "essential"
- [ ] [[I am warned notified when  essential  stock items are low on stock or out of stock]]
- [ ] [[I can see via the UI exactly, or close enough to, what is wrong at all times if something does error out]]
- [ ] I can see via the logs exactly what is happening at all times during the applications usage
- [ ] I get deletion confirmation when deleting an entity
- [ ] [[I can view nutritional information for a stock item]]
- [ ] [[I can see a tooltip for all buttons when I hover]] #ui_standardisation
- [ ] I can press the enter key to submit my form #ui_standardisation
- [ ] Buttons are always in the same locations where possible #ui_standardisation
- [ ] I am notified about shrinkflation
- [ ] I am notified about artificial sales
- [ ] I can change the visibility of columns in data tables #ui_standardisation
- [ ] [[Setup automation]]
- [ ] [[General UI design and consistency]]
- [ ] Store locator - check out ALDI app for inspiration, also look at woolworths website for mobile and desktop layouts
- [ ] [[I can undo my last action via a button in the toolbar]]
- [ ] I always have same buttons on creation forms: add & close, add & continue #ui_standardisation
- [ ] I get consistent useful form validation #ui_standardisation
- [ ] I get UI feedback consistently when taking actions (e.g. toast, green check transition) #ui_standardisation
- [ ] [[I can integrate and sync with Grocy]]
- [ ] The 404 not found page looks like it belongs in Dora (matches the application)


## Refining ✏️ #orange

- [ ] Font sizes are set correctly (not too small, not too large), and consistent #v200


## Ready Task 🎁 #cyan

- [ ] On navigation, the title of the page animates in


## In Progress ⏩️ #blue

- [ ] [[Main navigation menu]] #v200 #80%
- [ ] I can see the title of the page I'm on #80% #v200
- [ ] When on mobile, scrolling hides the header #v200


## Done ✅ #green

**Complete**
- [x] I can install and run Dora via Docker #v200 #80%


## Archived ⛔️ #black

**Complete**




%% kanban:settings
```
{"kanban-plugin":"basic","new-note-template":"Discount Dora/Templates/Feature Note.md","new-note-folder":"Discount Dora/Feature Notes","lane-width":400,"tag-colors":[{"tagKey":"#80%","color":"","backgroundColor":"rgba(222, 55, 55, 0.79)"},{"tagKey":"#v200","color":"","backgroundColor":"rgba(222, 20, 20, 0.48)"}],"metadata-keys":[{"metadataKey":"description","label":"Description","shouldHideLabel":true,"containsMarkdown":false}]}
```
%%