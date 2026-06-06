---

kanban-plugin: basic

---

## Backlog #grey

- [ ] Figure out navbar (style and behaviour)
- [ ] Componentise EVERYTHING! (so making a page is drag and drop)
- [ ] Make more expressions for Dora mascot (put one at the bottom of the readme that says "My name is Dora and I approve this message."
- [ ] Implement dark mode
- [ ] Contribution guide (incl. code rules, code style guide and setup)
- [ ] Add ability to refresh ALDI cache / Make ALDI cache refresh itself
- [ ] Add stock item to shopping list
- [ ] Look into boot file for checking authorisation (check boot file docs) (there's also PreFetch for auth and stores...)
- [ ] Look into setup of linting: [https://quasar.dev/quasar-cli-vite/linter](https://quasar.dev/quasar-cli-vite/linter)
- [ ] Configure quasar.config.ts
- [ ] Choose style and feel for navbar (e.g. how it hides, how much hides, style of nav items, hover effect, max width, etc)
- [ ] Comb over gitignore
- [ ] Check out all the options under quasar.config.ts (pwa, etc...)
- [ ] Include screenshots and detailed setup instructions in readme, look at popular docker container instructions for inspiration
- [ ] What should /api base do? current throws 500 error for both APIs (dora definitely, guessing same for merchant)
- [ ] UI Feedback for user when search results have been limited due to errors in the web scrapers (e.g. coles encountered an error => "Results are limited due to an error in the search")
- [ ] I did entity ID wrong, it shouldn't be accessible at all in the domain (so not even on a base entity), it's a persistence concern only (but am i bothered to fix this?)
- [ ] Hitting an endpoint that doesn't exist in the API just explodes
- [ ] Look into animations (see quasar config file)
- [ ] Consider simpler "update" action that covers all updates for an entity (could overcomplicate rollbacks with optimistic UI)
- [ ] Set defaults for notify in boot file
- [ ] Create different notification styles
- [ ] Check if API online and report online/offline in UI (relevant for boot file where stores are initialising)
- [ ] API auditing saved into the DB (make a logs table, where all parts of the application can log to, making sure to make a column for "source" e.g. "DAPI") (do this in the middleware for DAPI)
- [ ] Consider making stock item name unique with validation
- [ ] Compare google drive to stock overview for design ideas: [https://drive.google.com/drive/u/0/home](https://drive.google.com/drive/u/0/home)
- [ ] From quasar output: You (or an AE) specified an explicit quasar.config file > devServer > port. It is recommended to use a different devServer > port for each Quasar mode to avoid browser cache issues. Example: ctx.mode.ssr ? 9100 : ...
- [ ] Standardise Event Handler method name. Prefix them with 'On'. E.g., OnBtnClick
- [ ] Look into history in vue router
- [ ] Make sure UI says correct message for days until stocktake alert in the stock item creation form
- [ ] Find a place for system controlled data such as merchants
- [ ] Remove seed data for merchants, should be coming from MAPI only
- [ ] Add session.add_all([x, y, z]) method to persistence, maybe useful for batch add of entities (usage could be add(*entities))
- [ ] Look into bcrypt, see if it's useful for anything
- [ ] Create separate appsettings for development and production? Possibly doesn't matter
- [ ] Generate appsettings on start with defaults, allowing the rest to be configured and set via the options screen
- [ ] Add setters for all config options in config manager
- [ ] Configure root logger in each application and set log path to "logs" folder
- [ ] Find good places to log in the code, and do so (info logging) (SEARCH FOR BEST PRACTICES WITH LOGGING)
- [ ] Cannot easily see if a stock item is on a shopping list from the overview, how to address this?
- [ ] Can a stock item be on multiple shopping lists at the same time? I guess so...but it should only exist on a particular shopping list once
- [ ] Should we be able to refresh a product? It may be possible for a product to become out of sync with the merchant's product
- [ ] Do we want a "delete all data" button?
- [ ] How does out of stock interfere with preferred merchant, stuff already on shopping list, etc
- [ ] Should we bother with compact / expanded view for stock overview?
- [ ] Should "days before next stocktake alert" on the create stock item form be a range picker so we can min max it in the UI or should we just do that in the backend and use validation in front end and backend? We should be preventing inputs like "5000"
- [ ] Look into animations via quasar, see documentation and quasar config file [https://quasar.dev/options/animations](https://quasar.dev/options/animations)
- [ ] Cool modal animation: [https://vuejs.org/examples/#modal](https://vuejs.org/examples/#modal)
- [ ] [[Stock level indicator circle or square shaped]]
- [ ] [[Look into how to make a verification check to ensure newly added properties are added in these locations]]
- [ ] [[Look into this startup API stuff]]
- [ ] Possibly remove merchants from Dora, or at least the get merchants bit, merchant API is in control of this (Atif used the wrong source of truth for available merchants)
- [ ] [[Need some way to  check on  stock levels, so it's not  last updated  but  lasted checked  because you may not need to change stock levels]]
- [ ] Implement "days_until_stocktake_alert" global fallback (if value is zero) - Might want to make this setup by default
- [ ] Show colour somehow for stock level select in q-select for create stock item - can it be componentised?
- [ ] Add better logging, non-existent in most cases
- [ ] Empty string validation
- [ ] Look into spinner for stock item image (quasar has options)


## Important Backlog #orange

- [ ] Add ALDI and IGA logos to product search
- [ ] Changelog: https://github.com/grocy/grocy/blob/master/changelog/72_4.0.2_2023-08-19.md
- [ ] Write a proper readme
- [ ] Stock item page (basic)
- [ ] Move image cache to /cache
- [ ] Move ALDI products by category json to /cache
- [ ] Setup docker compose to make webapp depend on API
- [ ] Choose better icons for nav bar
- [ ] [[Require an API key to hit the backend API]]
- [ ] Put .image_cache under /cache so it gets persisted over docker container instances
- [ ] Only want to print what the persistence context is doing if in debug
- [ ] Don't store the DB in the framework code folder, put it somewhere else and allow user to define that location (potentially)
- [ ] Make system seed data separate to dev test seed data (and make code look better/more organised)
- [ ] Make sure persistence initialisation is being done correctly
- [ ] With bugs starting to pop up, API auditing might be useful to have...
- [ ] Product search is laggy when you have too many results (introduce pagination))
- [ ] [[Product search is very slow, a normal person would not wait for it to finish]]
- [ ] Steal ideas from Mealie and Tandoor for Discount Dora
- [ ] Setup sponsorship button and other Discount Dora settings on GitHub
- [ ] Once Discount Dora is more built up, post it in lots of places to gain traction
- [ ] Make component that switches between card and item (slim and square)


## Bugs #red

- [ ] [[Exception on window resize]] #prerelease
- [ ] [[Null whitespace named stock items could be created]] #prerelease
- [ ] [[Duplicate stock items could be created]] #prerelease
- [ ] Scrollbar for page goes over the titlebar #prerelease
- [ ] Colours look different between chrome and firefox #prerelease


## In Progress #blue

- [ ] [[Stock overview styling]]
- [ ] Lock in colour scheme and apply it everywhere currently possible
- [ ] Swap stock and product search in nav bar (stock should be first)
- [ ] Add a toolbar to the stock overview
- [ ] Styles & themes
- [ ] Bring existing components into new structure (name better and fix code styling)
- [ ] Rename essential link component to dora specific (remove all demo quasar/vue stuff)
- [ ] Get rid of the "Essential links" text on the nav menu
- [ ] Scrollbar (quasar supplied, default browser, my custom shitty one)
- [ ] Visual distinction between the scroll area and the toolbar
- [ ] Detail view (mobile version, splitter vs drawer, q-page-scroller)
- [ ] Sticky toolbar (leave out of scrollable area, use q-page-sticky)
- [ ] Shopping list modal supporting many stock items


## Done #green

**Complete**
- [x] FONT FAMILY! (Part of the logo) - update the readme with this font for the logo/main title
- [x] Test #resolved_bug




%% kanban:settings
```
{"kanban-plugin":"basic","lane-width":400,"new-note-folder":"Discount Dora/Taskboard Notes","new-note-template":"Discount Dora/Templates/Feature Note.md","metadata-keys":[{"metadataKey":"description","label":"Description","shouldHideLabel":true,"containsMarkdown":false}],"tag-colors":[{"tagKey":"#resolved_bug","color":"","backgroundColor":"rgba(214, 4, 4, 0.71)"},{"tagKey":"#prerelease","color":"","backgroundColor":"rgba(34, 225, 173, 0.46)"}]}
```
%%