# **Feedback / Fixes**

Instructions: the following is a mix of UX/UI/behaviour feedback and bug findings. Analyse and generate prompts to get the job done. Before doing anything in each of the prompts, check with me about the impacts and changes that will occur. I may not realise how what I’ve said will change things around the app. I reviewed page by page in isolation half the time. The last thing to review of this document is if I've managed to find and give feedback on all features added to Dora. If not, you should request that I do. Confirm each item before actioning if you suspect there’s any misunderstanding I might have with the app currently. I can’t see/understand the whole context of the code.

# **SPLASH**

- Not sure if this page is following system theme for background, but would be better if it shared the same colouring as the login screen (detached)

# **CANNOT CONNECT SCREEN / INITIAL LOAD SCREEN**

- Same styling as login, splash, etc., ensuring to keep the logo/dora pic animation and location/placement

# **LOGIN / REGISTRATION / FORGOT**

- Password policy feels too restrictive, do minimum of 8 characters, and allow admins to turn the restrictions off.  
- Forgot password screen should match styling of login screen  
- How does sending of the email for forgotten password work? Probably need to get the admin (first login) to set up a sending account. If they skip, disable/hide that "forgot password" button on the login screen. Implementation of this must be flexible (works with multiple email setups, without putting a lot of complexity on Dora's side)  
- Floating dora disappears in mobile view (i like the placement of it in desktop view, maybe in mobile view move it to directly above rather than to the side?)  
- Sign in and create account buttons are not centered properly (either too far to the left, or too wide \- can see it's in line with the right side of the input boxes), same issue on forgot password screen  
- Register text is too small, make it a button same as sign in but another colour, maybe gradient of the dora yellow (match gradient style of login button), "have an account, sign in" should also be a button with same styling)  
- Add a sponsorship / donation / buy me a coffee button in the bottom left that also has an animation. Maybe with a message like "Enjoying Dora?"

# **ONBOARDING**

- Should be same styling as login screen  
- Skip everything button does nothing (no navigation)  
- Getting to the end of onboarding, the finish button does nothing (no navigation)  
- "Show me X" on all the cards at the onboarding finish screen are non-functional (no navigation)  
- Theme choice here should reflect system, light and dark (only), and that translates to system, pesto light and pesto dark \- they can pick others later) \- keep note of the theme option changes mentioned elsewhere in these notes  
- Admin step, fix wording to "Invite other users later"  
- Seed step has Grocy mentioned, probably don't mention that app specifically, and the link also does nothing... should incorporate onto the current page instead of navigating  
- Why does it say "You already have some groups set up. Skipping this leaves them alone; opting in won't create duplicates."? This is first time setup, if it's conflicting with dev data then that's wrong \- assume empty database (apart from system data seeded by migrations)  
- Same issue with "You already have locations. Same deal — opting in here won't double them up."  
- The seed page should probably let you pick and choose all/none or some of the default data  
- Instead of "Skip everything", just say "Skip" \- only persist their choices once they finish  
- Adding a stock item in the onboarding should probably show a slim list of "added" so they can keep track (makes "x added" redundant, move counter to the list)  
- The worst part of using this app will be getting data in \- having a pre-done template might be good, and having the ability to pick what you want from that template would be good (customised). E.g., have a list of common household stock items pre-populated with data, e.g. cheese in the location of fridge, apples \- fridge, ice cream \- freezer, etc), you tick on/off what you want from the starter template. We want people started as soon as possible.  
- Option to tick on/off demo recipe (real recipe \- warn that it requires demo data), demo meal, demo meal plan, etc  
- Do a little celebration animation on finish? Like confetti  
- The "take the tour" page should have more of the key areas with their short succinct summaries, only stock, shopping and alerts mentioned  
- Onboarding should explain to the user the core values and the whole point of Dora, how it is best utilised, and the vision of Dora.  
- Possibly for admin first login, ask what features of Dora they want enabled/disabled (and tell them they can change this later in the admin settings \- need to add this there too)  
- Instead of the "nav to features" at the end of the onboarding, explain the core workflows / features and how to become a power user of the system in as few words as possible. Use pretty diagrams and flowchart looking guides. Point them to go to the guides/help section for each one for a more in-depth explanation. Really show and sell how Dora shines.  
- "How many people do you cook for normally?" \- ties in with cook mode feature for quantity adjustment  
- "Which stores do you (prefer?) to shop at?"  
- Key explanation should be somewhere around what stock items are (simplified, not detailed) and products are (detailed, exact), so milk is the stock item, Vitasoy Oat Milky at Coles is the product. This explanation should surface BEFORE the user is told to add stock items in the onboarding

# **DASHBOARD**

- "Skipped setup wizard..."  
  - continue button does nothing  
  - takes too much space with buttons on own row, could be inlined  
  - welcome message could be added here normally if onboarding is completed  
  - welcome message should be cycled and random, maybe different from all the responses from dora bot (ideas: random phrases based on day of the week, 5 per day, pool of 35-40, in addition to a pool of helpful hints not tied to the day)  
  - Replaces the "Dora says" bubble at the bottom right, but keep the yellow "Dora says", looks nice  
- Dark mode not working  
- How useful is the refresh really? If it's already doing this on navigation to/from the dashboard, remove it  
- Add reordering of cards with dragable rows in the toggle list  
- Alerts navigation is broken (goes to 404). Probably a good idea to build an alerts page with nice UX display of the alerts? Like an "alert control" page. Can get to it from this dashboard card or from the bell in the top right corner.  
- Alert card should be redesigned to be more of a useful summary of the alerts. Picturing two sections, top and bottom. Top is a chart or row of boxes indicating types of alerts, how many of them, and what they're generally about (not sure exactly on this one), like "5 items going expired" or something, or "5 high attention items". Bottom is a sneak peak similar to the current design showing top 3, or 3 different types of alerts. Big-ish button at the bottom or the side "see all" or "see more"  
- A unified “this fortnight” calendar widget might be good to add, which uses different coloured dots on the date squares to indicate when things will happen, combining date data from various areas into one convenient spot. E.g. planned shopping, expiry of items, etc. Clicking on a date square brings up that info plus the meals planned for that day.

# **STOCK OVERVIEW**

- Navigation to this page has a noticeable delay between 1 to 3 seconds. Why is this so slow? Investigate and report. I seem to get lag of about 1 second on every other page. The page change feels not snappy at all. It's just worst on this particular screen. Alerts button also feels slow. \- Update... at some point after the "animations" DS4 addition, something has changed. It no longer feels laggy like it used to. What happened?  
- The highlighting rules feel weird at the moment. E.g. "essential" highlights and puts a red dot.  
- Data export should be based on the current filtered items, not all items (for both csv and pdf)  
- Stock item detail view should only appear on mobile, and on mobile the drawer view should not appear when selecting the row. This locks navigation to row selection.  
- Stock item detail view should be the same between the standalone view and the drawer view.  
- Stock level change button should be first in the row, and should be a big coloured button without text (basically copy what I had before \- look at main branch or my componentise branch \- making any improvements you can spot). I want it to be the focus \- quick stock level update.  
- Clicking or tapping a stock item row opens the detail view (whether that be mobile view (new page) or desktop view (side drawer)) \- google drive style UX \- only concern i have is someone trying to tap or click a button and missing, then clicking the row... is this an issue or it it fine with correctly made buttons?  
- Only in mobile view, holding on a stock item row enters multi-select mode (google drive UX)  
- Add a "scan mode" button that allows you to pick an action that will be performed on scanned items, for example "open details", "mark out of stock", "mark well-stocked", etc. Possibly incorporate into stocktake mode?  
- Can show/hide images of stock items (save preference)  
- The stock item "chip" is a bad idea. It doesn't make sense in its usages across the app, and it looks too messy/too much detail squished together.  
- I don't like the "low/ok/mid", remove.  
- The highlight around the "chip" should move to the whole row item outline  
- Rows feel a bit small, make them a smidge taller  
- Name of stock item should be a bit more emphasised (larger text or bold or something)  
- What are the current highlighting/outline colour rules? This should be hashed out and refined.  
- Location chip should show the main zone, not "right shelf"  
- The red "status" indicator inside the "chip"is visual noise, remove. It does not provide any additional information not already visible. Essential items can be filtered to and this info is not necessary in this view.  
- The shopping cart icon inside the "chip" feels unnecessary, the main shopping list button should cover everything (it's multi-purpose). Check my original notes for the shopping list functionality on the stock overview page. Clarify the design with me. Current one feels completely wrong and uesless.  
  - I can foresee lots of complexity in the behaviour of the shopping cart button. It needs to account for many factors. Number of shopping lists, presence of products, etc. For example, no products linked means add to list based on list logic. If products present, present with choice modal of which product (if more than one). Many branching paths.  
- The "on x lists" chip is unnecessary, information overdose.  
- Expiry button should be moved to the other buttons on the right  
- If no expiry, its not a dropdown, it opens a date picker  
- If expiry set, expiry button should have \+1 day, \+7 days, \+14 days and clear.  
- Update the “number of recipes” chip to be “number of upcoming planned meals” which is much more useful to see. This can be combined with stock level by the user to determine if something needs to go on the shopping list. This may even be a useful metric to be alerted on. “Milk is low in stock and on 5 planned meals”. Issue with this though is we need to distinguish between “going to cook” and “already cooked” so the correct information is given. Are meals already being allocated to meal plans? If not we should do this. Should also allow the user to define how many will be used, for example if more than one person eating that meal.  
- The ellipses options on the "chip" are all fluff/noise (can find all this easily elsewhere) \- remove.  
- To avoid "selection" colour interfering with status colour for the rows, actively selected can fill the row instead of change outline colour.  
- Top area needs some serious tidy up and polish. Things are all over the place and ugly.  
  - Counts should be minified and moved to the bottom of the page as a sticky footer (add space between the footer and the scrollable area). Add more counts in (well stocked, sufficient stock, flagged, auto add, needs attention, whatever else is useful)  
  - Across the top should be all the buttons, all together (new item, export, bulk select, etc)  
  - Add a filter button that shows filters, hidden by default  
  - Used in a recipe is a useless filter, remove  
  - Remove counts from stock level filters and change to a dropdown filter, any level the default  
  - Can't see end of placeholder text in search filter, shorten it  
  - Keep search filter separate to other filters (not hidden with others)  
  - Filter button changes based on filter state  
  - Export button doesn't need the ellipses, use a different icon  
  - All buttons should be the same width and height. This is app wide I feel for toolbar buttons. Make a standard toolbar with a standard toolbar button. Same goes for filters. There are base types, and each should look and feel the same. For example, the export button is different to the other buttons next to it. Of course there can be additional styling where necessary, such as the stock take button glowing for attention, but this is the exception and with a purpose.  
  - The glow of the stocktake button is not obvious enough. I almost didn't see it.  
- Add stock item modal  
  - No way to specify stock group  
  - No way to mark some other fields  
  - Location suffers same fate here as elsewhere. “Left shelf” means nothing on its own.  
  - Add to list in bulk select does not confirm WHICH list if theres more than one.

# **STOCK ITEM DETAIL**

- Clear expiry button not obvious enough, add cross mark next to expiry detail to clear it  
- Is there any relationship between expiry and open? Do they impact each other in any way?  
- No way to set "essential" that I can see? Might be missing it?  
- No way to set stock group. Stock groups feel like a forgotten feature with no connection throughout the app. Is there any value in doing so?  
  - What else in the app is like this? Field exists but no way to set it/interact with it  
- Open the split-view at 50%, so it's in the middle of the screen  
- Set a minimum/maximum splitter distance so the window on either side is not squished to an unusable or ugly state. There appears to be a max set, the min could be the same (neat).  
- Unlink product button causes an exception (kaboom)  
- In some themes, the tab buttons are hardly visible. They should be theme aware.  
- Stock level is shown twice. Remove the one next to the stock item name heading.  
- Move the delete button to the bottom left, below the tabs, or top right inline with the header, whichever makes more sense.  
- Restock makes no sense here, remove. Makes more sense for a shopping list finalisation.  
- Move "opened" button to where opened info is displayed (so its together. Do same with expiry.  
- Find deals is an odd button to always show. Move it to be in the linked products tab and only show it if there's no products, e.g. "Find products" or "link existing" product.  
- How does show QR code and register barcode work? Are they different features?  
- Overview could be single column of details, looks a bit messy now, could be neater/tidier.  
- Location can be updated directly, does not need a separate dropdown to its info display  
- Is “notes” just fluff/noise? What value does it bring to the user you think?  
- No way to add product of choice to shopping list, just the cheapest. Better design is to highlight/style the cheaper option and give each product a list add button.  
- Not sold on the preferred merchant / preferred product behaviour. Need to flesh this out and decide on value to the user vs fluff / noise.  
- Remove recipe from favourites does nothing.  
- Clicking recipes does not navigate correctly, just fails and goes to the recipes overview page.  
- None of the recipe actions do anything, except cook button.  
- Deleting stock item does not work. Server error. “sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed”  
- Swap into list for substitutes feels like a weird feature. Would it even get used?  
- After removing stock item chip design, I feel it’s still handy to see the stock level indicator and the chip highlighting/outline for substitutes. Can’t see anything else being useful outside of name and stock level state.  
- The shopping lists tab feels lack luster. The go-to link icon on the right of the shopping list feels unnecessary, you can’t actually click on it. (primary) in plain text looks boring and unimaginative.  
- The history tab as-is feels unuseful. Maybe if it had a bit more data/info in it…maybe? I’d need to be convinced. Maybe there’s some value I’m not seeing.  
- Cannot edi unless i change the stock item namet, it's supplying all fields (it should be a PATCH, not a PUT, need to only supply changed fields \- different from original, careful with this) "A stock item with the name 'Barilla Pasta' already exists."

# **STOCKTAKE MODE**

- Doesn’t need a refresh button  
- Top of the queue info text feels like…obvious information  
- Text on the page feels small all over. Then again, app does feel like it suffers from this. Is this standard text size?  
- The keyboard shortcuts on the buttons looks tacky. Move this to an instructional section on the stocktake landing page.  
- Skip button should be as big as the others  
- What are the current rules for items getting to the stock take list? Let’s review this.  
- Problem I can see is using the buttons doesn’t ever prompt you to add items to the shopping list. Should probably ask you at some point (either upon marking something down a level, or out of stock, or at the end “here were the items you marked as out/etc would you like to add them all to your shopping list?) Could use the “complete” screen? This would remove the need for a shopping list button during the stocktake.  
- Stock level change doesn’t display the colours. It should be the same as the stock item overview, not just text.  
- Colour could be different between still correct and change level? Maybe the standard button colour?  
- Skip shortcut should be 4  
- Shopping list button doesn’t seem to be aware of that item’s state on any shopping list. Also when I click it i get two toasts at the same time. “0 added, 1 already on list” and “brazil nuts added to your primary list”.

# **PRODUCT SEARCH**

- There’s been a misunderstanding with merchants and merchant data providers from previous prompts. A merchant is a company with stores such as “ALDI” and “Coles”. They happen to have websites which are “providing” the data of their products. There’s also other websites that provide this data. This is evident on the manage merchants page where the two ideas have been conflated.  
- The connection health to providers could look cleaner \- make it a dropdown button with a meaningful icon that changes colour. Green till 1 provider drops, then it goes yellow, then orange, then red when nothing is healthy. Place it next to the show/hide filters button.  
- The search bar does not match styling of others and in fact cannot show text in dark mode (white on white). Search bars should be consistent.  
- The loading area during search is not theme aware.  
- Again the green chips in pesto theme (specifically dark mode) are too hard to read for the connections and stores.  
- Bad UX toggling stores all on/off as the chip expands and the button moves around. Could be better if there’s a dash to show they are excluded? Or move the button to the front?  
- There should be a disclaimer somewhere that the product search tries its best to be as accurate as it can, however it’s at the mercy of the data provided by…the data providers. Should be said in the most plain english possible. Data provider is my own terminology.  
- The bottom of the product card is not theme aware  
- Cannot save products: Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted  
- Quick add to shopping list button same issue: Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted  
- Link to a stock item same issue: Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted Extra inputs are not permitted (also does this save the product simultaneously? It should.  
- I liked the old design more with the save button being bigger and in the middle of the product card  
- The % off label could be a bit more obvious, or maybe the styling of the cards could be better in general with highlighting?  
- Size/weight doesn’t make any sense to be a filter. How can you accurately implement this without complicated logic? If we do keep it, it should instead be a one at a time “greater than”, “less than” or “exact” filter with metric choices. That then needs to be calculated per product to see if it matches. E.g. the filter says greater than 500ml, a product that says 1L satisfies this. But then “5 PACK” makes no sense for this unit so it should be displayed anyways.  
- Per unit max price behaviour is off. Entering any number yields no effect on the filtering. Entering letters is allowed which is wrong. Ctrl+a delete clearing the input then filters everything out and you have to click clear filters button.  
- Seems the entering input then clearing filters out all products on all inputs incorrectly. Empty should be the same as filter off.  
- In-stock, specials only and half price quick filters seem useful. Are there any other quick filters that would bring value to this screen? Let’s assess.  
- It’s not obvious when a filter is applied. Cannot see how many of how many are visible. No styling to the clear filters button to indicate there are active filters.  
- The dora picture (displayed before search and when no product matches search) is not centred over the background box. This is also visible on the dashboard greeting card at the top.  
- The state of the page seems to be remembered after navigating away, but only partially (state of filters for example). Does it make sense to keep state between pages or to refresh on navigation? Let’s assess and fix this for each screen.  
- Clear ranges button should be clear filters.  
- How does the relevancy filter work? Is it working well?  
- Whatever icon is being used for the very first loading pulse when you load the web app, use that for every place there is loading (for consistency). Here it should be used for the search loading. Any more interesting animations we can use? Let’s plan/prototype.  
- The filter labels and the filter inputs feel a bit messy/hard to read/not designed well. Improve this. The app should not look like a professional polished well designed app, not like a uni student’s first app. That goes for any and all UI elements.  
- Do a performance analysis of the code. This screen takes considerable time with all merchants enabled. We do not want to be blocked for being considered a bot, but 20-30s per search does feel crap. Is there any way to improve this? Some ideas I have: concurrent search, or present results as they are retrieved, or combination of.  
- Do an analysis of the code for likelihood of getting blocked by providers. Any way to ensure this does not happen? What if we have multiple concurrent users searching? I am concerned this feature would become blocked.  
- The link button would be better as the logo of the merchant, or perhaps the image of the merchant. What do you think?  
- Add to compare button almost invisible on some images, maybe move it to the bottom of the card.  
- Comparison feature feels useless without some sort of sorting, highlighting or some way to make comparison easier than reading a table of info.  
- Attribute header in comparison feels unnecessary, leave that header blank.

# **MY PRODUCTS**

- Should not be a prerequisite to link a product to a stock item for adding to shopping cart. The features should be standalone usable. E.g. a user only wishes to use products side of things. (This should be obviously noted in the instructions/guides/etc so people don't feel like they have to use everything \- they can use as much of the app as they want). To make this happen, I propose the following rule: if a product is added to the shopping list, and no linked stock item is already on the list, the product displays on its own line (and the UI shows it is just a product). If later a stock item is linked, the stock item is automatically added to the shopping list and the product is then nested under it (as the UI currently displays). If a stock item is removed from the shopping list, its products are too removed (same as deleting a stock item). If a product is removed from the shopping list, a modal pops up to ask if the stock item should also be removed.  
- No way to add custom products, for example if something is not available via the merchant API due to the store not being supported (not one of the major 4).  
- Cannot mark products inactive: Extra inputs are not permitted  
- Buttons aren't that many, can move to the card and remove ellipses?  
- Instead of current linking info/button, change to be same placement as the "save product" button on the search page. Grey broken link for unlinked, green connected link for linked. Clicking it shows modal to link if unlinked. Clicking it unlinks if linked. Still separately show which item is linked to.  
- Consider changes to shopping cart button on other screens. Can be componentised?  
- No way to remove a saved product  
- Not sure what styling shows products are inactive. Maybe a button with a search icon, grey if inactive, blue if active?  
- Filter clear button is different to other screens with its behaviour, appearing if filters enabled, hidden otherwise. Each screen should be the same with its filter behaviour.  
- % off chip is a little small/hard to read. Same goes for other info on the product. There's plenty of space on the card to use.  
- Why is unlink modal cancel button yellow? Should componentise and keep consistent where possible. I think it's usually red?  
- No way to deselect all in bulk select mode.  
- Bulk select button and area is different in styling to other screens. Should be consistent. Looks not so great in stock page. Looks better here (keep in mind im testing in dark mode \- pesto).  
- Bulk select "select inactive" would be a good button to add.  
- Bulk select "select low stock on deal" also good button.  
- Bulk select "select out of stock on deal" also good button.  
- Bulk select "essential low stock on deal" also good button. Are my buttons making sense? Better way to do it?  
- Stock items without products button could be more obvious when there's more than zero. Should grab attention, not be obscured.  
- Refresh button again? Why? I can't think of anywhere in the app I'd need a refresh button. This isn't the type of app to be kept open in long sessions.  
- Bulk select button should be part of the toolbar, not its own area with info that is learnt then not needed to be shown again.  
- Open stock item button on card no necessary, can click on stock item name.  
- Info at the top of the page is so hidden and tiny, not noticeable. Move to be consistent with stock page design, as the sticky footer.  
- As a general design idea, should filter button be active by default (filters shown) on desktop, and hidden/disabled on mobile?

# **PRODUCT HISTORY**

- Feels like a major feature, hidden away a bit.  
- Can select products but no change occurs on the page.  
- Product card here feels squished a bit, can't see full placeholder text for notify under. Does this feature work as intended? Verify.  
- Formatting of number input for notify under doesn't seem right. Should format to a decimal, no? Let's do what is standard for a price input.  
- The %off and other text is so tiny.  
- Why is %off chip colouring feeling different to elsewhere? Is it or is it just my imagination? Componentise and standardise.  
- The hover bubble is not theme aware, white text on white background in dark mode.  
- I see manage alerts button that is context aware for this screen. This is good, but would be good to manage in a central area as well (alert control) where you can have granular control over all alerts. Ensure alerts of different types have their own unique styling and icons to clearly differentiate them.  
- Price history graph does not extend all the way to the edge of the box. Hidden info thats not  displayed yet? Bug? What am i missing?  
- If kept as own page, what do you think of making it similar to the stock item detail view, where on desktop if you click on it on the my products page, it shows in drawer mode on the right? Might be a risky idea considering how much is on the page. Might need its own specifically designed view for this. If we do a separate design, could use the my products page as the selectors of what is displayed in the price history chart. Would be better shown from the bottom I think rather than the right side because of the direction of the graph. Quasar has a special component for this I think, a type of dialogue that takes full width and drags up from the bottom. Thoughts?

# **RECIPES OVERVIEW**

- Should be called "Cookbook" anywhere the page itself is mentioned  
- Same issue with page info at the top, should be a componentised sticky footer. Consistency\!  
- "Missing" filter is offset weirdly compared to other filters (looks out of place), same as "free from" filter.  
- Filters should work the same here as on other pages in terms of shown/hidden/active/clear/etc.  
- Getting same filter issues as other screens such as deleting input filters incorrectly where it should be same as blank.  
- Cuisine and category should not be lumped together as the same filter. Also they are not  tags.  
- Should it be recipe “tags”, or specifically “dietary tags”  
- Can tags be condensed into one filter, clicking specific ones toggles between must have, must not have, and neutral (green \+, red \-, grey). Clicking/tapping changes between state and does not close the dropdown (like multi-select behaviour).  
- I think there should be a settings page for recipe tags. Seed the default ones (what we have now) and let the user add/edit/remove them.  
- Stock item filter should be multi-select as well.  
- Can we style the rows in the stock item filter to reflect stock level?  
- Any useful filters we're missing? Any value gaps?  
- "Folder" grouping not obvious, almost missed it. Number as well is tiny.  
- Edit button feels useless here when you just click/tap on the recipe card itself for same effect.  
- Delete button can be in the recipe detail view, same as mark made.  
- "Mark made" everywhere sounds odd... make it "Mark Cooked". Update anywhere relevant...componentise\! Consistency\!  
- Duplicate feels like a rarely used button, move to detail view.  
- Should “duplicate” be…”new version”... or “manage versions”?  
- With so few buttons, can move to the card itself and ditch the ellipses.  
- Recipes should have an image and display that image if available. People eat with their eyes.  
- Recipe comparison tool in its current state feels useless. Is there any way to make this more useful? Would people actually use this? I feel they wouldn't. If not, let's remove it.  
- Recipe comparison chips are not theme aware or colour choice is bad in dark mode pesto. The white on grey colour is not readable.  
- Formatting of comparison looks awkward/bad. E.g. prep+cook time is very far from the info, and the info is on 2 lines. 2, new line, min.  
- Would the design look nicer if the sections/groupings were in a rounded box as the background?  
- Nice addition with budget feature would be to add a recipe estimated cost, based on data available from products linked to stock items and historic shopping list/receipt reconciliation data. This feels like it could then be fed from recipes into meal planning, then meal plans into shopping list budgets. All the features can connect together nicely. Something key to keep in mind though is some people may not want to know how many dollars they are eating. This is only a feature for the budget conscious. It should be an option to turn off (all budget/money related features outside the very basic product search information). Budget information does not impact the core flow of Dora. It’s an add-on.  
- Cuisine/category should not be multi-select. You’re either after Italian, or Asian.  
- New recipe modal…  
  - Crammed and ugly formatting. Looks all over the place.  
  - Inconsistent with add stock item modal, cannot click out of it to cancel adding.  
  - Must keep in mind how servings are affected by the auto-adjust feature. Probably no change to this modal however.  
  - Why is cuisine and category a different thing? They’re even filtered together on the overview. Should it not just be cuisine? Why was it done this way? Was this from my original spec notes somewhere?  
  - What is the expected input for instructions? The modal doesn’t tell you. Is it flexible? Can it be flexible (e.g. for copy \+ paste)?  
  - Nutrition information in its current state feels like it’s just noise/useless.   
  - Nutrition information in its current state feels like it’s just noise/useless. Again like price information, should be opt-in otherwise hidden. It also needs to be less free-form. What nutritional information is useful to note down on recipes? I feel it'd be good to provide the option of linking stock items to items in a nutritional facts DB, configurable in settings, which can then be a source to estimate nutritional info of meals. Setting for nutritional info maybe that is off (hidden), simple (just energy/kal which can be compared/sorted for recipes), and complex (nutritional db). Simple can be a number typed in, complex is auto mode (you don't touch anything). My concern with this all though is the complexity in being accurate with quantities in recipes and translating that to accurate nutritional info conversions. If this is too difficult, maybe just stick to "off" and "simple" (number input for kcal).  
  - There's a lot of dietary tags, would be better configured (can toggle, or add/edit/delete)  
  - "Tags reflect what the recipe was tagged with — a planning aid,..." could shorten beginning to "Tags are a planning aid,..."  
  - Formatting of ingredients being added is off (stock item input is off-centre for some reason)  
  - Should unit be freeform? If it stays that way it should give a hint (ml/g/etc) of some sort. Took me a bit to realise what I should enter.  
  - Modal not consistent with others, cannot click out to escape  
- No way to import recipes from urls from the overview. Good or bad idea?  
- Create recipe button in different placement to where other pages have the “create x” button. This should be consistent across every page.   
- Would a filter “planned in” be useful? Where you can see recipes included in future/current meal plans (not before today).  
  - Idea I just had for dashboard “next up to cook”, maybe shows the next 3 recipes that need cooking based off meal plans and amount in stock, etc. Allows you to navigate to those specific recipes and also tells you at a glance if they are ready to cook or missing ingredients.  
- The allocation logic seems to not be working?  
- Is there much value in seeing the number of cooked meals on this page? Is it clutter? Maybe it could be simplified? What if the user doesn’t want to use meal plans and just want to track what’s in stock? Also, should it be like stock overview where you can easily change how many are in stock from the overview?  
  - I feel like it’d be nice to see the number in stock which is editable, and the number of allocated meals (which only shows if there is allocations at all \- usage of the meal planner feature) in its own box. Neutral if available is \>= allocated. Red if \< allocated.  
  - Could use the left side of the card? See next note about using space better  
- Could the bottom of the card be better used? Rather than just “cook now”?  
- Probably want filters based on meal count? Filter to only in stock, order by, etc.  
- Filter “order by last made” or something 

# **RECIPE DETAIL**

- Category should be like dietary tags \- filterable dropdown select with toggleable options in settings, or add/edit/delete.  
- Cuisine should be same as category in regards to above point.  
- Stock item picker should be a filterable dropdown select (there could be up to 100\)  
- Cannot save recipe for same reason cant save stock item \- its updating name when i didn't change it  
- Why is nutrition a separate dropdown field (collapsed)? It feels out of place in its current state. If we change how nutrition is working from how it is currently, maybe a separate area. Guess it depends what happens with nutrition info.  
- Again shopping cart button on stock item row that could be componentised with behaviour standardised.  
- Wasnt't obvious I can edit the title to change the name of the recipe. This is different behaviour to other screens (e.g. stock item has its own field for name). Keep it consistent. If we go with changing the title, then it should have styling to indicate it can be changed.  
- Don't like that I don't get prevented from saving the recipe if I haven't filled out one of the stock items. Filled out other bits but left stock item empty. It just ate the row silently instead of giving validation errors. Should force me to fill it out or delete that line.  
- The cookable now box of info is not theme aware (missing is impossible to read in dark mode, and cookable (green) is too bright of a green like other areas mentioned. Could just be this theme, unsure.) Well-stocked chip has same issue.  
- The double chip of out-of-stock and missing looks odd. Maybe highlight the row instead? Looks quite weird currently. Also without “missing”, so e.g. well-stocked, it looks really odd because theres a space for “missing” but its not there. It just looks odd.  
- What’s the point of “notes” for ingredients? What purpose does this serve?  
- What about multi-part recipes? Should this be supported? If so how? My first thoughts are allowing for multiple recipe sections (e.g. sauce, meat), or linking recipes together: Lasanga depends on/is made up of bechamel sauce recipe, nepoetana sauce recipe, lasanga mince recipe. Now sure how this would look like and which is better/worse in terms of UX.  
- Recipe source should be a separate field  
- Should recipe importer mention which websites are more/less likely to work?  
- Should not be able to get to cook mode if the recipe edits save does not succeed.  
- Weird navigation: recipe detail \-\> cook mode \-\> exit \-\> recipe overview  
- Unsaved changes modal (presented by start cook mode) has no "cancel", also clicking out of the modal closes and navigates anyways  
- I wonder if it would be good to see substitutes are available/in-stock as a separate "status"? Could be presented in a few areas I think. Does this overcomplicate the UX though?  
- Mentions the substitutes graph but this is a deleted feature.  
- Why does selecting a substitute completely swap and edit the recipe? This is wrong. Substituting is a temporary thing. Should also probably display for this cook mode only (the selected substitutes).  
- Mark made \-\> should be mark cooked  
- Can't click out of the delete confirmation to cancel  
- Mark made should be a bigger button maybe? Also delete should not be so close to it.  
- Export to csv feels weird, remove feature here.  
- Export/print can be moved outside the ellipses and remove the ellipses.  
- Buttons feel all over the place, should they just be across the top? Maybe some across the top? Not sure. Even weirder that the buttons move to the bottom in mobile/slim view.  
- I feel like "start cook mode" should prompt a confirmation if it's not "ready to cook now"  
- Optional field of "tools required" or something to that effect, where you can list out what you need. E.g. food processor, frypan, 5L pot, etc. This is again a configurable dropdown of options (premade defaults) changable in settings. There can then be a inclusion/exclusion filter on recipe overview.  
- Personal notes about the recipe would be good. These should display during cook mode somewhere useful (perhaps under all steps section?)  
- I don’t see any way to create versions of recipes (as per my original feature notes)  
- Don’t like wording “meals on hand”, change to “available meals”  
- Is it normal the red strike through cursor (not allowed) flashes when clicking add or remove meals?  
- The log cook button is really bugging me. Can’t say exactly why. At first I thought this is useless, but maybe there is some value in it. It’s just really bugging me. Maybe if it was with the other buttons instead (just part of the toolbar)?

# **COOK MODE**

- Allow easy setting of stock level (using something in cooking decreases how much is in stock). Probably add this as the finish of cook mode, update stock levels of used stock items like a check list "update any stock levels?" and even a quick way to "add to shopping list" straight after you finish cooking  
- How many are we cooking for today? \- Feature that auto-adjusts quantities based on number of people, this is set to a default (see onboarding) and can be adjusted easily (zero friction) per cooking session  
- Ingredients should be grouped by location (base location only, fridge, pantry, etc, don’t worry about sub areas for grouping)  
- Add tools section and highlight similar to ingredients per step (see below). Don’t show tools if none added to recipe.  
- How do sub-steps work in recipes? How are they added? How are they displayed/handled in cook mode? If we’re handling sub-steps, can this also support hints per step? Shown like a footer on the current step?  
- Ingredients UI design looks horrible currently  
- Stock level is not relevant at this point (we have decided to cook…)  
- Timer component is not theme aware, cannot see in dark mode. Cannot see reset button either.  
- Timer has no sound that plays? The toast feels insufficient to alert the user. Maybe instead of a toast it should be the timer component changes in some way (styling). Also would be nice if the timer component was a bar that fills up.  
- Some quantities display poorly. E.g. 2 scoops is displayed as “2scoops”. I think there should be an inclusion list of units that get put directly after the quantity. “ml, g, etc..”  
- The ticking behaviour with the steps and the ingredients feels odd. How is this calculated? What if ingredient A is used between steps 1, 2 and 3? I think instead we can highlight what ingredients are used in a step. Do we need to tick off ingredients?  
- Ticking feels unnecessary for both ingredients and steps. Move to highlighting only I think.  
- Voice button is not obvious enough. Hidden feature. Also name it more clearly… what does “enable voice” mean? Can have a bit of fun with it maybe, this is your digital sous chef.  
- The cook mode page feels a little boring and basic with the styling. Could look much better.  
- Finished cooking modal…  
  - Again, clicking out does not cancel and close modal (go back to cooking)  
  - Feels a little boring for finishing such a challenging task. Where’s the hooray? Where’s the congrats?  
  - Update stock levels of everything?? I should be presented with the ability to mark stock item levels individually, and to stock levels of my choosing. This removes the need for the toggle “add to shopping list?” There should be a shopping list button to allow me to add each.  
  - How many meals cooked should start at zero. Make it optional.

# **MEAL PLANS**

- Make into a more useful tool... picturing a really easy quick flow of a sequential meal plan builder that allows you to pick your meals for a week (build a new plan or pick from existing) \-\> then get a list of required stock \-\> build a shopping list from what is in stock \-\> email or print plan and shopping list  
- Meal plans can be like templates, you can pick from your "templates" which are built meal plans and can allocate them to weeks, can even rotate a month of plans (each month is the same) which can then tie into auto-adding of out-of-stock or low-stock items to the shopping list  
- Icon for the page should use the one that was for meals page. I think that icon works better than a calendar. What do you think? Any other options that better fit?  
- Instead of a warning symbol, maybe a chef’s hat? For shortfall banner.  
- Allocation seems to be broken. Allocating a meal does not affect x unallocated of x on hand.  
- “Generate shopping list for this week” button showed toast “Nothing to add \- you have…” but with a subtitle of “I’m a notification\!”. I don’t want to see anything like demo / example / placeholder stuff anywhere in the app. This is unacceptable for a polished professional app.  
- Full ingredient demand uses different colouring for stock level than everywhere else in the app. Consistency\!  
- Drag/drop should likely be disabled for mobile view. No way it could work I say…  
- Anywhere you can drag/drop, there should be a tap/click menu. Drag/drop is a power user option. Offer both and let the user pick how to use the app.  
- Name of meal plan feels useless, unless we make it template based (which makes sense, then the template has a name). Meal plan instances should not have a name though. They’re just “week starting X”  
- Date picker feels wrong for creating a new meal plan.  
  - I can pick any day (how does this even work? Feels totally wrong)  
  - I can pick dates in the past…again, odd  
  - I think instead, it should show options to pick from upcoming weeks (including the current week). Options should be greyed out or not shown if there’s an active plan for that week.  
- Based off what I’ve said above, feels like there will need to be meal plan template management functionality. Some basic thoughts to build off…  
  - Can save meal plans as templates  
  - Meal plans can be created from templates (not linked at all to the instance)  
  - Probably just a button in the toolbar in meal planner allows you to view and manage meal plan templates  
- Maybe instead of creating with modal (because the current one feels awkward (e.g. why would you add meals via here when you can search/drag and drop/etc on the main page) there’s a dropdown of weeks and you can see from the dropdown the status of meal plans on those weeks (whether they have one or not). You can apply a meal plan template (warns you will lose the current plan if any meals are assigned) (note: how does applying a template work if some days are in the past? Just make those meals not counted and read-only right?). This replaces the “active plan” dropdown.  
  - For design, I’m picturing a custom calendar widget for this as the week picker where the active week highlights (colour/fill the squares), only the first day in each row displays any text (the date but only DD, for example 25th May is “25”. Month at the top banner. The status of individual days in the calendar is marked with underline under the day squares. The squares are rounded boxes and that’s it (minimalist look maybe? Futuristic? Hard to describe). Help me design this well\!  
  - This widget I picture being on the right above the shopping info.  
  - Current day should be marked.  
- Building on the points above…main working area might be good as a scrollable carousel, where scrolling reveals the previous or next week. There should be an up arrow above the area to click previous and down arrow below to go next. This should come with a nice smooth animation. The calendar widget should change with it.  
- Below the main working area can be two areas where meals can be selected from. One is “the favourites” which is most frequently picked meals on a plan. Other is “haven't had in a while…” which is a rotation of meals not had in a while, like reminders. This feature might be reusable on the recipe overview but based on “last made”, different metric. You can drag meals from here as well onto the week plan.  
- The main working area might need to be a bit more centred? Not sure… maybe fine where it is?  
- The current “all recipes” area feels inadequate. It should be filterable and vertical because it's a list, and it can hold hundreds of recipes. Picturing it on the left of the main working area.  
- Need some sort of method to add recipes/meals onto the days without drag and drop.  
- I should be able to ask Dorabot to assist with meal planning. Some examples: I want to have an Italian week. I want Tuesday to be healthy. I want a low calorie plan (ask user to enable nutritional facts and fill out enough data, or try and guess)  
- Meal plans should be able to be made recurring. Switching between recurring and non recurring should not stuff with historical plans. Perhaps once a week passes, it locks to read-only entirely?  
- How can recurring and editing coexist? Perhaps once an edit is made to a future week it is treated as its own plan and when occurrence setting is change or disabled that week is untouched (treated as different).  
- It is absolutely essential to ensure the UX works for both groups of people: those who batch cook (store meals) and those who cook only fresh. This statement must reflect in all facets of the app but it most heavily impacts recipes and meal planning. For example, the system should not feel overbearing for those who cook on the day, and it should also feel useful and informative for those who like to prep and plan ahead. Part of this likely means renaming the UI in cook mode to say “how many meals did you save?” For example   
- Currently the meal cards on days do not fit properly (icons or text go beyond the card). Perhaps expand the size of the card and wrap the text?  
- Issue with current design is if I refresh the page, it goes to the earliest dated plan instead of refreshing the current plan page.  
- Right now it’s thursday 8am AEST, and I can see wednesday is still active/droppable, but when I drop I get an exception. Not sure logging is working properly everywhere throughout the app, likely needs an audit… this is all I can find from this exception:  
  - 2026-06-04 07:44:33,038 INFO	\[dora\_api.infrastructure.middleware\] \[req=024bde90-07e8-4112-bb96-7edfff7605f4\] \[user=b97ff390-a110-4013-bee4-ba24edecf27f\] → PATCH /api/meal-plans/a1ab75a5-178f-48cf-a38b-27502e9b00de  
  - 2026-06-04 07:44:33,038 DEBUG   \[dora\_api.infrastructure.middleware\] \[req=024bde90-07e8-4112-bb96-7edfff7605f4\] \[user=b97ff390-a110-4013-bee4-ba24edecf27f\] Incoming request | method=PATCH path=/api/meal-plans/a1ab75a5-178f-48cf-a38b-27502e9b00de endpoint=MEAL\_PLAN\_ROUTER.update\_meal\_plan ip=127.0.0.1  
  - 2026-06-04 07:44:33,038 DEBUG   \[dora\_api.infrastructure.middleware\] \[req=024bde90-07e8-4112-bb96-7edfff7605f4\] \[user=b97ff390-a110-4013-bee4-ba24edecf27f\] body: {'entries': \[{'recipe\_id': '784ec655-23c1-4491-ae54-90e6913e4b6d', 'scheduled\_for': '2026-06-04', 'servings': 2, 'slot': 'Dinner'}, {'recipe\_id': '7a207f0e-1efd-4d32-b01e-aace9cd51b5c', 'scheduled\_for': '2026-06-05', 'servings': 3, 'slot': 'Dinner'}, {'recipe\_id': '5a3f7e13-1fca-466a-9221-3ee2009099b4', 'scheduled\_for': '2026-06-06', 'servings': 4, 'slot': 'Dinner'}, {'recipe\_id': '5a3f7e13-1fca-466a-9221-3ee2009099b4', 'scheduled\_for': '2026-06-03', 'servings': 1, 'slot': 'Dinner'}\]}  
  - 2026-06-04 07:44:33,044 INFO	\[dora\_api.infrastructure.middleware\] \[req=024bde90-07e8-4112-bb96-7edfff7605f4\] \[user=b97ff390-a110-4013-bee4-ba24edecf27f\] ← 400 PATCH /api/meal-plans/a1ab75a5-178f-48cf-a38b-27502e9b00de (6.2ms)  
- Hovering over stock items should reveal which meal(s) they are coming from (they highlight the same). Not sure how to solve that for mobile view, maybe just a lost feature?  
- Should be able to see the shopping list status of each stock item (if already on a list, etc)  
- Should be able to individually add items to a shopping list, or add all in one go  
- Generate shopping list? Is this what this button does? Is this what it should do? Perhaps it’s add or generate? Perhaps everywhere you can add an item to a shopping list, you have the options of to existing or new?  
- Does the “needs x” of a stock item in the shopping info area work properly? Worried about it not adding up correctly for everything  
- When I add a meal to a day, no matter what it’s always “Dinner”. What was this supposed to be? It should not be related to the recipe’s time of day, that’s just a suggestion. If I want ice cream for breakfast, I will have it.  
- The fact there’s an “edit entries” button shows there is a gap with the current main working area.  
- Delete plan should just become “clear week”  
- Some elements on the page are not theme aware, e.g. “Create a meal plan to get started.” card, day headers  
- Don’t need this exported as csv…remove that button  
- With the new carousel design, don’t need the title “Week of…”  
- The colouring and iconography feels so conflicting on this page, between the recipe list, the shortfall banner and the meals planned on the days. Perhaps there’s too much going on in this regard?  
  - How many meals on hand is a bit hidden, could be better displayed at the end of the chip with its own colour separation (divide the chip), and make the number bigger maybe? Might just be an issue with the font size in general.  
  - Do I need to know if something is cookable now on this page? This is the planner, not the cookbook. Suggest meals I can cook now and the green highlighting with a checkmark feel like they don’t belong.  
- With the earlier design ideas, I am concerned with squishing the main working area too much. Perhaps the recipes/meals to select/drag should be combined in the column to the right? Not sure if that then pushes important info in the right out of sight. It’s kind of an issue in general with the page. There’s a lot that is horizontally displayed that could be better shown vertically. Not saying it’s wrong as horizontal, but it feels it could be better vertical POSSIBLY: shortfall, recipes/meals  
- Is the shortfall banner needed? It’s showing information twice.  
- Could the time of day be made into rows instead of displaying on the meal cards?  
- If I drag eggs onto morning breakfast twice it should see they are the same recipe ID and increase the count  
- I shouldn't have to drag one by one to increase the count of a meal  
- Times of day should be configurable, and come with preconfigured defaults.

# **SHOPPING LISTS**

- Being able to set a planned shopping day per list would be useful. Optional of course.  
- Shopping day alert would be good to have.  
- I think this view could be combined with the details view. The overview page doesn't add much value in my eyes, just adds more navigation.  
  - For desktop, right panel can have all shopping lists ordered by planned shop date/finalised shop date, then by creation date as a fallback  
  - For mobile view, move this to be a dropdown at the top of the page.  
  - The current detail shown for the primary list can be moved to a top info area of the current shopping list in view  
  - Archived lists also show in the same list  
  - The picked list when navigating to the shopping lists page should be based on today's date (I think? Any friction from this?)  
- The “primary list” functionality feels not quite right…not sure what would be better.

# **SHOPPING LIST DETAILS VIEW**

- Drag and drop is an index off somehow (wrong items being swapped)

# **SHOPPING MODE**

- Handy to see substitutes quickly if something in store is unavailable. This is more complex than just “is there another linked product to this stock item. Could also be what are the substitute stock items and their products that are related.  
- Shopping mode should allow you to optionally add or edit pricing information as you go. The shopping list in dora BECOMES the receipt.  
- Need to close the loop in dora: completing a shopping list (after review) should allow you to quickly restock all items, with the option to change individual levels if needed (e.g. move all to well-stocked and then tweak to sufficient for a couple items). This is an attempt to complete “P2-01/02”, treating the shopping list as the receipt. No need for scanning or unreliable OCR.  
- I have not sighted it yet but the undo functionality of a done shopping list sounds bad. Undo should probably only be in certain situations. This needs a thorough review. We don’t want accidental bad data.

# **REPORTS**

- ?

# **WASTE**

- ?

# **SETTINGS**

- Theme should be split into type (system, light, dark) selection and theme (pesto, lemon, etc) selection separately, the light/dark buttons removed from the theme cards, and the colours shown on the cards change depending on whether light or dark is selected (system is calculated if possible otherwise just use light) so only one set of colours per theme is showing (the relevant ones)  
- No way to set/update a profile picture. Should also display this on the menu bar for the user profile button. Keep displaying the current icon if no profile picture set.

# **ALERTS**

- An alert control screen feels like it’s missing  
- The number of alerts doesn't seem to add up to the number bubble (e.g. i see 6, but when i click the bell there's 10\)  
- I feel alerts could be smarter with the priority and what's actually an alert.  
- Users should be able to opt in/out of different types of alerts. Dora is as quiet or noisy as they want it to be.  
- Add alert type and functionality for “no planned meals for next week”

# **HELP**

- Ensure there is detailed help for every part of the app, documenting every piece of functionality  
- Ensure there is detailed guides  
- Ensure there is Q & A / FAQ section  
- Ensure help is easily navigable and sections are obvious to find  
- Where applicable there are pieces of UI or diagrams or screenshots (I can provide) for clarity around features. The features should just sink in.

# **DORA BOT**

- Some text does not change size as per the user settings (is this expected?)  
- The basic/ai chip is a bit squished/small  
- Make basic/AI chip a toggle slider button, with the AI side disabled if unavailable. This allows a per user preference of which chat to use. Style it in a cool looking way, like a slanted thick slider. When you slide, the chat does a pulse glow (only once) in the theme's colour. AI mode on is colourful, AI mode off is dull glow.  
- Something funky is happening with the Dorabot animations (e.g. hover) since the animation DS4 task was completed. It flashes a bit. It felt perfect before.  
- Don't need the "Hi I'm Dora. Click me..." speech bubble on every login. Once it is acknowledged, it doesn't pop up again for that user  
- Users should be able to turn the bot off completely in settings  
- Let’s call Dorabot “D.O.R.A.” \- Delicious Organised Restock Assistant…or anything better we can come up with.

# **MOBILE VIEW**

# **DATA**

- Don't like it being alongside the major pages in the main menu. It should be under settings, "My Data".  
- Can export to multiple formats (json, csv, what else is a valuable format if any?)  
- The formatting of this page looks so ugly. No margins on some things, spacing feels weird, and worst offender is the data to tick on/off is not inline with the checkbox. Looks really unprofessional.  
- The font size/type usage is bad (for headings). This especially hurts the optional section that is collapsed. Does it need to be collapsed at all? Makes no sense. It’s the main part of the page.  
- Could perhaps use the horizontal space a bit better and make it look nicer at the same time? Use cards with checkboxes?  
- This bit at the top feels like useless fluff: (breadcrumb) Data/Backup & restore \- and Backup, import, export and barcode tools for your Dora data.  
- Import feels awkward. There should be template sheets generated from the live schema that the user can pick between to download, fill out, then upload. What format though…csv?  
- Export and print tab feels unnecessary? I don’t think users would ever go here.  
- What’s the point of the scan tab under QR codes in this area? Feels like a feature that’s only useful in stock overview, etc.  
- Is it still barcodes and QR? Should it be renamed to QR codes?

# **NO AREA / MISC**

- 404 page is not in theme with the app (default quasar one)  
- Undo cross-app seems off, e.g. dashboard push expiry, then go to stock item and clear its expiry  
- Long loading areas are given a loading ghost effect \- not sure exactly what it's called but it's meant to mimic the layout while it's loading \- this should replace things like stock item detail view showing "Stock Item" while it's still loading  
- Main menu button hover (inactive) has double outline (incorrect feeling), where as active has single outline (correct)  
- Settings is shown in both main menu and the user dropdown button \- remove from main menu  
- I need a full systems QA test document to manually go through every single featuer in detail and test (DO THIS LAST so it captures the final product)  
- Default text size in some areas feels way too small (like some hovers). The change between small medium and large text size is also not much difference. I was expecting 75%, 100%, 150% scaling  
- The button colours in pesto for some buttons feel too bright and I can't read the text. Notice this particularly on the green ones like add buttons. Should be darker.  
- Would be a nice-to-have if the QR codes had the dora logo on them (in the middle) \- the D/D simple one.  
- Remind me to provide the real ALDI and IGA logos  
- Let’s rename everywhere to Dashy Dora (anywhere Discount is used…can’t be that many).  
- Would the main menu bar look better without the bottom border?  
- How useful is the command palette feature really? Let’s assess.  
- QR code scanning should bring up a modal of quick actions on that item.  
- For the general UI design, it should be consistent.  
- For the general UI design, surely it can feel a little more unique? Quasar surely exposes some form of base customisation that can be used, plus some tweaking with custom css? It looks just okay currently, not polished feeling or unique. I’m not a good designer so can’t say for sure what it is lacking.  
- I’d like a way to know how people are using my app. I know some companies track where their users go and what they do (e.g. which features get hit the most).  
- Why is the .local folder so messy? Data folder feels unnecessary, and logs are in two different locations. I feel like either keep as data (how it was before, instead of .local) or move folders up into .local. What’s the reasoning behind all this?  
- Are the logs rolling? Not sure they are rolling properly. The Current dapi log file is 46539 lines long and spans from 2026-06-04 to 2026-05-28 (likely when the .local folder move happened if I had to guess)  
- A lot of text isn't visible in either light/dark mode (mostly dark mode is crap \- as if text is not switching)  
- Command palette (ctrl \+ k) doesnt work with some stuff like create stock item

 

# **NEW FEATURE IDEAS**

- Push notifications/alerts to certain individuals, like how Alexa can. For example, user "A" sees stock item is low or out, they can click/tap "notify user" which allows them to instantly or in some amount of time notify either themself (self-reminder) or user "B" of this. Can similarly send a shopping list to another user via their registered email (share shopping list). A notification/alert would appear for the user(s) that "user 'A' has shared a shopping list with you"  
- Can we make this “gameified”? People like the addictiveness of games and gamifying can be successful, for example apps that reward you for not looking at your phone.

# **Technical Considerations** 

- Looking at my kivy P2P test branch, does this have any home in the current app? My vision was for standalone no server installs to link and communicate (syncing data).  
- I want to ensure there is single sources of truth for the front end data and operations (business logic). The more that's in the backend the better.

