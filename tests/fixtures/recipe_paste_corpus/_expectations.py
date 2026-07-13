"""Ground-truth minimum-shape assertions for each corpus fixture.

Each entry is intentionally LOOSE — the parser only needs to satisfy the
declared minimums. Pinning exact ``(qty, unit, text)`` tuples per row
would make every parser tweak break dozens of tests; loose fences catch
regressions without over-constraining. Add fixtures + entries as we grow
the corpus.

Field semantics (all optional — the test asserts a field only when the
entry declares it non-None):

    name_contains      — substring the extracted recipe name must
                         include (case-insensitive). Guards against
                         grabbing a nav crumb instead of the recipe
                         title.
    servings           — expected integer servings/yield.
    prep_minutes,
    cook_minutes,
    total_minutes      — meta-block times from the fixture. ``None``
                         when the fixture doesn't publish that field
                         (e.g. Simply Recipes gives total-only). The
                         parser may store total in ``cook_time_minutes``
                         when prep is absent; the test tolerates that
                         (see the per-field mapping in
                         ``test_parse_recipe_from_text.py``).
    min_ingredients    — lower bound on ingredient count. Loose so a
                         parser tweak that finds one extra never breaks
                         the fence.
    min_steps          — lower bound on structured step count.
    first_ingredient_contains
                       — substring the FIRST extracted ingredient's
                         raw_text must contain. This is the strongest
                         "did the parser find the right block?" signal —
                         if we grab the pre-story text as ingredients,
                         this will fail immediately.
    notes              — free-form explanation for future readers of
                         why this fixture is shaped the way it is (e.g.
                         "sub-sections", "no Ingredients header",
                         "footer noise interleaved"). Not asserted.

Time tolerances: the test allows ±2 minutes on each numeric time field
to absorb rounding when a site expresses total as "1 hr" and the parser
sums prep + cook to 65 min.
"""

EXPECTATIONS: dict[str, dict] = {
    # ── Class A: explicit headers ────────────────────────────────────

    # AllRecipes — "Prep Time:\n10 mins\nCook Time:\n25 mins\n..." split
    # across two-line pairs; ingredients under an "Ingredients" header
    # with the "1/2x 1x 2x" scaling widget noise; directions under
    # "Directions"; stop at "Nutrition Facts (per serving)".
    "allrecipes1": {
        "name_contains": "tuna",
        "servings": 4,
        "prep_minutes": 10,
        "cook_minutes": 25,
        "total_minutes": 35,
        "min_ingredients": 6,
        "min_steps": 4,
        "first_ingredient_contains": "noodles",
        "notes": "Clean Class A; 8 ingredients, 5 steps.",
    },
    "allrecipes2": {
        "name_contains": "honey garlic chicken",
        "servings": 6,
        "prep_minutes": 10,
        "cook_minutes": 180,   # 3 hrs
        "total_minutes": 190,  # 3 hrs 10 mins
        "min_ingredients": 12,
        "min_steps": 4,
        "first_ingredient_contains": "honey",
        "notes": "Slow-cooker recipe with hours-scale cook time.",
    },
    "allrecipes3": {
        "name_contains": "catfish",
        "servings": 2,
        "prep_minutes": 20,
        "cook_minutes": 10,
        "total_minutes": 30,
        "min_ingredients": 6,
        "min_steps": 5,
        "first_ingredient_contains": "buttermilk",
        "notes": "Photo captions + photographer credits interleaved "
                 "with steps — parser needs to filter them out.",
    },

    # Half Baked Harvest — inline "Prep Time 25 minutes minutes" on one
    # line (double "minutes" is HBH's own formatting quirk); ingredients
    # with "▢" bullets; instructions under "Instructions".
    "halfbakedharvest1": {
        "name_contains": "zucchini",  # Zucchini Cheddar Chicken Noodle Casserole
        "servings": 6,
        "prep_minutes": 25,
        "cook_minutes": 30,
        "total_minutes": 55,
        "min_ingredients": 12,
        "min_steps": 4,
        "first_ingredient_contains": "butter",
        "notes": "Long story preamble; recipe card starts around line 134.",
    },
    "halfbakedharvest2": {
        "name_contains": "latte",  # Iced Cinnamon Honey Latte — "Fiesta Steak Fajitas" at top is a related-post link, NOT the recipe title
        "servings": 2,
        "prep_minutes": 5,
        "cook_minutes": None,  # not given; only prep + total (both 5)
        "total_minutes": 5,
        "min_ingredients": 5,
        "min_steps": 3,
        "first_ingredient_contains": "milk",
        "notes": "No cook time — total = prep. Header nav mentions a "
                 "'Fiesta Steak Fajitas' related-post link at line 47 "
                 "that the parser must NOT pick as the title; real title "
                 "is at the breadcrumb (line 35) and recipe card (line 118).",
    },
    "halfbakedharvest3": {
        "name_contains": "peanut butter",  # No Bake Chocolate Peanut Butter Cookie Bars
        "servings": 20,
        "prep_minutes": 10,
        "cook_minutes": None,
        "total_minutes": 130,  # 2 hours hours 10 minutes minutes
        "min_ingredients": 7,
        "min_steps": 4,
        "first_ingredient_contains": "peanut butter",
        "notes": "Total time spans hours + minutes; no-bake so no cook time.",
    },

    # RecipeTin Eats — "Prep: 15 minutes mins" / "Cook: 25 minutes mins"
    # / "Servings5" (no space); ingredients with "▢" bullets and
    # sub-section headers ending in ":" (e.g. "Portuguese chicken
    # seasoning:"); instructions numbered under "Instructions".
    "recipetineats1": {
        "name_contains": "portuguese",  # Nando's Portuguese Chicken and Rice
        "servings": 5,
        "prep_minutes": 15,
        "cook_minutes": 25,
        "total_minutes": None,
        "min_ingredients": 15,
        "min_steps": 6,
        "first_ingredient_contains": "chicken",
        "notes": "Multi-section ingredients (chicken seasoning / rice / "
                 "garnishes); also has an 'Rice resting: 10 minutes' line "
                 "the parser can ignore.",
    },
    "recipetineats2": {
        "name_contains": "meatball",  # Italian Meatballs
        "servings": 4,
        "prep_minutes": 20,
        "cook_minutes": 20,
        "total_minutes": 40,
        "min_ingredients": 15,
        "min_steps": 10,
        "first_ingredient_contains": "bread",
        "notes": "Sub-sections: Meatballs / Sauce; steps include an "
                 "abbreviated + full recipe split.",
    },
    "recipetineats3": {
        "name_contains": "mapo tofu",
        "servings": 4,
        "prep_minutes": 20,
        "cook_minutes": 25,
        "total_minutes": None,
        "min_ingredients": 15,
        "min_steps": 10,
        "first_ingredient_contains": "peppercorns",  # First ▢ line is "1 tbsp whole pink Sichuan peppercorns"
        "notes": "Multi-section (Blanched tofu / Golden pork / etc); "
                 "first bulleted line is a lone 'Sichuan peppercorns' "
                 "with no sub-section header above it — the parser is "
                 "honest to grab it as the first ingredient. "
                 "Servings line reads 'Servings4 – 5 people (or 1 Nagi)'.",
    },

    # Sally's Baking — "Author: Sally McKenney Prep Time: 4 hours ...
    # Cook Time: 30 minutes Total Time: 8 hours ... Yield: 1 9-inch pie"
    # ALL ON ONE LINE. Ingredients under "Ingredients" with unmarked
    # sub-section headers (Crust / Custard Filling / Whipped Cream).
    "sallysbaking1": {
        "name_contains": "banana cream",  # Homemade Banana Cream Pie
        "servings": 1,   # Yield: 1 9-inch pie — parser grabs "1" plausibly
        "prep_minutes": 240,  # 4 hours
        "cook_minutes": 30,
        "total_minutes": 480,  # 8 hours
        "min_ingredients": 12,
        "min_steps": 8,
        "first_ingredient_contains": "pie crust",
        "notes": "All meta on ONE line — challenging inline extraction. "
                 "Yield=1 is a pie count, not servings; parser is honest "
                 "to grab '1' since that's literally what the fixture says.",
    },
    "sallysbaking2": {
        "name_contains": "double chocolate",  # Favorite Double Chocolate Chip Cookies
        "servings": 20,   # "Yield: 20-22 cookies" — parser grabs 20
        "prep_minutes": 195,  # 3 hours, 15 minutes (includes chilling)
        "cook_minutes": 12,
        "total_minutes": 210,  # 3 hours, 30 minutes
        "min_ingredients": 9,
        "min_steps": 6,
        "first_ingredient_contains": "butter",
        "notes": "Same inline-meta shape as sallysbaking1. Yield in cookies.",
    },

    # Simply Recipes — "Prep Time:\n35 mins\nCook Time:\n35 mins\n..."
    # two-line split; ingredients under "Ingredients"; steps under
    # "Directions"; stop at "Nutrition Facts (per serving)".
    "simplyrecipes1": {
        "name_contains": "lasagna",  # Creamy, Herby Sheet Pan Lasagna
        "servings": 8,
        "prep_minutes": 35,
        "cook_minutes": 35,
        "total_minutes": 70,  # 1 hr 10 mins
        "min_ingredients": 12,
        "min_steps": 6,
        "first_ingredient_contains": "spinach",
        "notes": "Also has a 'Note:' preamble between meta and ingredients "
                 "the parser should skip.",
    },
    "simplyrecipes2": {
        "name_contains": "cowgirl",  # Dump-and-Bake Cowgirl Casserole
        "servings": 8,
        "prep_minutes": 10,
        "cook_minutes": 30,
        "total_minutes": 55,  # includes 15 min resting
        "min_ingredients": 8,
        "min_steps": 5,
        "first_ingredient_contains": "nonstick",
        "notes": "Extra 'Resting time: 15 mins' line between prep and total.",
    },
    "simplyrecipes3": {
        "name_contains": "pasta",  # Quick 4-Ingredient Pasta
        "servings": 4,
        "prep_minutes": None,  # not listed on this fixture
        "cook_minutes": None,
        "total_minutes": 25,
        "min_ingredients": 6,
        "min_steps": 5,
        "first_ingredient_contains": "salt",
        "notes": "Total-only meta (no prep, no cook). First ingredient is "
                 "'Salt and freshly ground black pepper' — parser is honest "
                 "to grab that as-is.",
    },

    # Taste.com.au — compact vertical meta ("Prep\n10m\nCook\n1h 05m\n
    # Serves\n4"); ingredients count baked into the "Ingredients (14)"
    # header line; method uses "Step 1" / "Step 2" markers, each
    # followed by a prose paragraph and a photo caption alt-text.
    "taste.com.au1": {
        "name_contains": "shepherd",  # Classic Shepherd's Pie
        "servings": 4,
        "prep_minutes": 10,
        "cook_minutes": 65,  # 1h 05m
        "total_minutes": None,  # not given as a separate field
        "min_ingredients": 10,
        "min_steps": 4,
        "first_ingredient_contains": "olive oil",
        "notes": "'Step 1' style markers, not numbered '1.'. Meta values "
                 "live on lines separate from labels ('Prep\\n10m\\n').",
    },
    "taste.com.au2": {
        "name_contains": "massaman",  # Thai massaman beef curry
        "servings": 4,
        "prep_minutes": 10,
        "cook_minutes": 100,  # 1h 40m
        "total_minutes": None,
        "min_ingredients": 19,
        "min_steps": 3,
        "first_ingredient_contains": "vegetable oil",
        "notes": "Same taste.com.au chrome as fixture1, but the method is "
                 "followed by a video carousel ('01:01' timecode, 11x 'Next "
                 "video thumbnail', a video title + 'more' link) that a naive "
                 "collector grabs as ~16 junk steps. Also leaks the Coles "
                 "price widget ('Estimate based on...', 'Fulfilled by "
                 "coles-logo') into ingredients. Both are filtered now.",
    },

    # Woolworths — vertical meta ("Prep\nPreparation time is 10minutes\n
    # 10m\n..."); every ingredient line appears TWICE consecutively in
    # slightly different formats (short + expanded), so a naive collector
    # would over-count. Method uses "Step 1 of N" markers.
    "woolworths1": {
        "name_contains": "cottage pie",  # Cheesy sweet potato cottage pie topping
        "servings": 8,
        "prep_minutes": 10,
        "cook_minutes": 25,
        "total_minutes": None,
        "min_ingredients": 5,   # stated as 6; loose fence at 5
        "min_steps": 3,
        "first_ingredient_contains": "sweet potato",
        "notes": "Every ingredient line duplicated in a second format "
                 "('1.50kg gold sweet potatoes' then '1.50kilograms gold "
                 "sweet potatoes'). Parser may de-dup or accept dupes; "
                 "loose fence tolerates both.",
    },
    "woolworths2": {
        "name_contains": "bourguignon",  # Correctly-spelled breadcrumb wins over the fixture's body typo
        "servings": 6,
        "prep_minutes": 10,
        "cook_minutes": 265,  # 4hr 25m
        "total_minutes": None,
        "min_ingredients": 11,   # stated as 13; loose fence at 11
        "min_steps": 3,
        "first_ingredient_contains": "olive oil",
        "notes": "Same double-line ingredient shape as woolworths1. "
                 "Fixture body has the typo 'bourguinon' (missing 'g') "
                 "at lines 11, 14; the breadcrumb at line 9 spells it "
                 "correctly. Parser wins the breadcrumb via Strategy 1 "
                 "(breadcrumb detection).",
    },

    # ── Class B: no explicit section headers (Smitten Kitchen) ────────

    # smittenkitchen1 — Deb's classic shape: no "Ingredients" or
    # "Instructions" headers. Meta is a "Yield: ..." line inline
    # ("Yield: The original recipe suggest 24 but I got 34."). Ingredient
    # sub-sections are bare "Sauce" / "Meatballs" lines (no colon!)
    # followed by unbulleted lines. Instructions are prose paragraphs
    # starting with verb prefixes ("Make sauce:", "Make meatballs:").
    # Footer stops at "Print Recipe" — everything after (Related /
    # comments / Reply form) is noise.
    "smittenkitchen1": {
        "name_contains": "scallion meatballs",
        "servings": 24,   # "Yield: The original recipe suggest 24 but I got 34"
        "prep_minutes": None,
        "cook_minutes": None,
        "total_minutes": None,
        "min_ingredients": 10,   # ~14 real ingredients across 2 sections
        "min_steps": 3,
        "first_ingredient_contains": "sugar",   # first ingredient is "1/2 cup dark brown sugar"
        "notes": "CLASS B — no headers. Sub-sections 'Sauce' and "
                 "'Meatballs' are bare lines (no colon). Instructions "
                 "start with 'Make sauce:' / 'Make meatballs:' verb "
                 "prefixes. Footer starts at 'Print Recipe'.",
    },
    # smittenkitchen2 — same shape but slightly cleaner: "Serves 6 to 8
    # as a tapa, 2 as a light main dish." followed immediately by
    # unbulleted ingredients then NUMBERED steps ("1. Heat 2
    # tablespoons..."). No sub-sections.
    "smittenkitchen2": {
        "name_contains": "tortilla",   # Potato Tortilla with Artichokes and Red Peppers
        "servings": 6,
        "prep_minutes": None,
        "cook_minutes": None,
        "total_minutes": None,
        "min_ingredients": 6,   # ~8 ingredients
        "min_steps": 4,
        "first_ingredient_contains": "olive oil",   # "About 4 tablespoons olive oil, plus more if needed"
        "notes": "CLASS B — no 'Ingredients' header but instructions "
                 "ARE numbered (1. 2. 3.), which is a helpful anchor "
                 "for the ingredient/instruction boundary.",
    },
    # smittenkitchen3 — small structured tell: "    Servings: 4 Time: 45
    # minutes Source: Smitten Kitchen" on ONE line (like Sally's inline
    # meta but shorter). Ingredients are unbulleted; instructions are
    # unnumbered prose paragraphs starting after them.
    "smittenkitchen3": {
        "name_contains": "chili",   # Skillet Turkey Chili
        "servings": 4,
        "prep_minutes": None,
        "cook_minutes": None,
        "total_minutes": 45,
        "min_ingredients": 8,   # ~11 ingredients including "To serve: ..." line
        "min_steps": 2,   # 2 prose paragraphs
        "first_ingredient_contains": "olive oil",
        "notes": "CLASS B — inline meta line, unnumbered prose steps. "
                 "Last 'ingredient' is 'To serve: ...' which is really "
                 "garnish suggestions; parser is fine to keep it as-is.",
    },
}
