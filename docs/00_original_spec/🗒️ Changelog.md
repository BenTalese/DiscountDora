# 2.0.0 🍅 Tomato
```dataviewjs
let dump = dv.page("Feature Boards/!Dump ~ No Area").file.tasks;
let alert = dv.page("Feature Boards/Alerts").file.tasks;
let dash = dv.page("Feature Boards/Dashboard").file.tasks;
let data = dv.page("Feature Boards/Data Management").file.tasks;
let help = dv.page("Feature Boards/Help, Guides & Assistant").file.tasks;
let meal = dv.page("Feature Boards/Meals").file.tasks;
let product = dv.page("Feature Boards/Products").file.tasks;
let recipe = dv.page("Feature Boards/Recipes").file.tasks;
let shopping = dv.page("Feature Boards/Shopping Lists").file.tasks;
let stock = dv.page("Feature Boards/Stock Items").file.tasks;
let option = dv.page("Feature Boards/User & Global Options").file.tasks;

let allTasks = dump
	.concat(alert)
	.concat(dash)
	.concat(data)
	.concat(help)
	.concat(meal)
	.concat(product)
	.concat(recipe)
	.concat(shopping)
	.concat(stock)
	.concat(option);

let tagToFilter = "#v200"
let filteredTasks = allTasks.filter(t => t.text.includes(tagToFilter));

dv.header(2, `${tagToFilter} Features`);
dv.table(["Feature", "Status", "Source"], 
    filteredTasks.map(t => [t.text.replace(tagToFilter, "").trim(), t.completed ? "✅" : "⏳", t.link])
);

```

---

# 2.1.0 🥝 Kiwi
```dataviewjs
let dump = dv.page("Feature Boards/!Dump ~ No Area").file.tasks;
let alert = dv.page("Feature Boards/Alerts").file.tasks;
let dash = dv.page("Feature Boards/Dashboard").file.tasks;
let data = dv.page("Feature Boards/Data Management").file.tasks;
let help = dv.page("Feature Boards/Help, Guides & Assistant").file.tasks;
let meal = dv.page("Feature Boards/Meals").file.tasks;
let product = dv.page("Feature Boards/Products").file.tasks;
let recipe = dv.page("Feature Boards/Recipes").file.tasks;
let shopping = dv.page("Feature Boards/Shopping Lists").file.tasks;
let stock = dv.page("Feature Boards/Stock Items").file.tasks;
let option = dv.page("Feature Boards/User & Global Options").file.tasks;

let allTasks = dump
	.concat(alert)
	.concat(dash)
	.concat(data)
	.concat(help)
	.concat(meal)
	.concat(product)
	.concat(recipe)
	.concat(shopping)
	.concat(stock)
	.concat(option);

let tagToFilter = "#v210"
let filteredTasks = allTasks.filter(t => t.text.includes(tagToFilter));

dv.header(2, `${tagToFilter} Features`);
dv.table(["Feature", "Status", "Source"], 
    filteredTasks.map(t => [t.text.replace(tagToFilter, "").trim(), t.completed ? "✅" : "⏳", t.link])
);

```

---
