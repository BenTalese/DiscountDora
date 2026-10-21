Splitter makes sense because drawer content should probably be "for all pages"

"Back to top" button would be nice, but won't work for desktop on stock item page if i use a splitter - doesn't feel super valuable anyways

The toolbar at the top should probably always be visible? So it should be outside the splitter container

Splitter won't work well on mobile, probably has to be a pop up slideable modal thing (full size modal)

Hiding header screws with custom scrollbar... SHOULD BE USING SCROLLAREA FROM QUASAR

Could combine drawer + scrollarea to get pagescroller to work (feels wrong to use drawer for page specific content)

A concern i have is if it will feel jarring to have the layout change when you click on a stock item - google drive has a button to show the area, selection doesn't do it

Maybe it'd be nice (if i go down this path) to have the detail panel disappear if multiple are selected (might actually work better for mobile compatibility)


What seems to make sense right now:
- Scroll area (for quasar non-janky custom scrollbar that works with header reveal) with padding on top and bottom, maybe also a border, to make it look clean
- Splitter for detail view (because it's page specific, passing props around to make drawer content work for specific pages feels dirty)
- Sacrifice the scroll to top button, or make my own (put in toolbar)

But looking back over chatgpt convo, drawer also looks not so bad with composables...

Everything hinges on splitter vs drawer...
It feels like scroll area was not intended for the purpose i'm thinking of...
If i don't use scrollarea for the entire page, how will the toolbar stay at the top? - sticky component

Google drive "rounded card with generous margins" look for the side panel looks great btw, could copy that - put content inside of a div, inside of the splitter/drawer and style that

Splitter approach - "to top" button doesn't work, header reveal doesn't work
Drawer approach - it all works

Header reveal - problem with custom scrollbar, scroll area, splitter - literally has to be a plain scrollable page (but only want for mobile so factor that in there)
Splitter
Scroll area
Sticky toolbar - only if not using splitter or scroll area
Scroller - only if not using splitter or scroll area (make own toolbar button - can't be that hard)
Infinite scroll - idk if this will just work inside a splitter
Drawer

Header reveal - if on mobile
Custom scroller button in toolbar - if on desktop
	Else use quasar built-in
Plain page + scroll area - if on desktop
Drawer + scroll area (draggable IF on desktop)