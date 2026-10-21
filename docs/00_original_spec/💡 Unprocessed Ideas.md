**Misc**
- The toolbar buttons on the stock item overview (or anywhere really) are separated by concern with a separator, e.g.
	- Overview actions: Add, search/locate, stock-take filter, show/hide filters
	- Selection buttons: Deselect, add to shopping list, locate
- Option to only include low stock stock items in deal search - *would this even be useful??*
- When searching, display which products are already linked to a stock item
- What about keeping track of space? Small, medium and large sizes of items maybe?
	- Could attach a number to each size and you can assign a total to each shelf/location?
	- E.g. small = 1, medium = 2, large = 4
	- Above idea probably overcomplicated. How about instead, each "location" can have a storage metric if no "shelves" present, otherwise each shelf tracks its storage status. A "storage status" will be similar to stock level, a system-defined set of options to pick.

- I can flag recipes as healthy or unhealthy (possibly a 5 star rating system)
- I can filter and sort recipes by how healthy they are 
- Importing recipes auto-links ingredients to stock items and flags the ones that failed to be identified (e.g. stock item actually doesn't exist)
- Not every ingredient must be linked to a stock item, but all ingredients are still accounted for in the system 

- Something useful is to be able to setup reminders to use things, e.g. I open a jar of Thai curry paste, I should use it with a couple months (could be a button "remind me" which opens a modal to select date for reminder)

**----- FROM KEEP NOTES -----**
Move page nav to main top bar? (but user button...? just merge them?)
Split view when clicking on a stock item?

Toolbar
Filter area (collapsible)
Main working area

For each stock item (order):
Stock level - Change stock level
Add to shopping cart
Picture
Name
Stock location

With less showing, i can remove the "headers" on each card to make it look less ugly

Next alert date??
Stock group?? (can filter by but don't need to see it)

Primary light  
Primary  
Primary dark  
  
Secondary light  
Secondary  
Secondary dark  
  
Accent light  
Accent  
Accent dark  
  
The quick action section or the non action area on each stock item card is coloured different  
  
Can a stock item be active/unchecked on multiple shopping lists simultaneously? No, but you should be able to have multiple products for the same stock item selected on the shopping list  
Actually yes I think? ALDI shopping list, Woolworths shopping list, I get ice cream X at ALDI and Y at Woolworths
**----- FROM KEEP NOTES -----**

**Recipes**
- Sometimes you want to just say "mince of any kind"
- Ingredients usually are described as "amount" + "name" + "prep adjective", e.g. "3 carrots diced"

**Stock Locations**
- Stock items can have many stock locations
- A stock location has shelves
- A stock item can specify the shelf of the stock location it is on, e.g. "Pantry - 3rd Shelf"
- Stock locations do not require the shelf to be specified
- Stock items not on a shelf are on the "zero" shelf
- StockLocationShelf?
	- int ShelfNumber?
- A stock item card will have a "search" button, which will locate the stock item


**Stock Map**
- For a stock item you can click "show on map" if using the map feature, to show you where the stock item is kept
	- If stock item in more than one location, additional prompt to ask which location to show
- Stock locations shown on the stock overview will be buttons IF they are placed on the stock map, otherwise they are just text
- Clicking or tapping on the stock location button will open the stock map and highlight/select this stock item
- Selecting a stock item on the stock map will display a similar UI to the stock overview, where you can see it's name, stock levels, etc. Consider this the detail view for stock items on the stock map
- The detail view on the stock map will be shown from the bottom of the screen, like a banner across the screen

**Meal Planner**
- I think meals will need to be viewed via an overview like stock items, but should not be on the same view
	- Can the meal planner view be merged with this? Could the meals just be a list on the side you can drag in?
- Meal planner could be drag and drop, where you see "in-stock meals in a list on the left and you can drag them
	- Maybe when you drag, you set the meal to being in the "planned" state?
- Meal tracking - in-stock / planning
- Left pane has searchable/filterable list of meals in the system
- Meals are greyed out if they have zero available servings
- Tracking properties on meals:
	- total_servings
	- available_servings / allocated_servings
	- requested_servings / planned_servings
- Each meal on the left pane has a set of +/- buttons to increase or decrease the number of available servings
- The right pane is a UI for tracking when meals are planned for
- You can drag and drop meals from the left pane to the right pane
- When dropping a meal, it prompts you for "how many to allocate?"
- Each slot on the right side where a meal is will display:
	- Which meal is allocated
	- How many of that meal is allocated and available
	- How many of that meal is allocated and required
	- Likely can display this as: # / # e.g. 4/6
- Check outlook calendar views for ideas
- Meals - in stock tracking is "# of servings"
- Kanban style board for meal planning with each day as a column and top to bottom is early to late in the day? Linear list? Can switch between views?
- Don't lock people into using the planner in a certain way, what if people just want a simple list view where they can track the number of meals they have in stock?
	- Based off this thought, could make the meal planner pop up in a split view on the right side by clicking a button in the toolbar (show planner), movable by dragging the splitter bar
	- Clicking the toolbar button should hide the planner
	- This way it can be used, or not at all




Bulk add with autofill, will bring up ones that errored
Bulk remove
Quick add product for DD, scans url you provide

Shopping list reminder (every X days since item was added) (per item basis, items groupedif sending reminder on same day)
Also reminder for specific day