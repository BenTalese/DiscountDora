"""GET /api/help/food-fact — random food trivia for the help panel.

Originally the spec referenced an external food-fact RSS feed; pulling RSS
from a public list at request time is unreliable (feed shape varies, CORS
on the client, rate-limits). Instead we ship a curated local list and
rotate randomly. Trivia is light, factual, and food-themed — keeps Dora's
personality consistent.

Want more facts? Add lines to FOOD_FACTS below. Keep them under ~140 chars
so they fit the chat bubble without truncation.
"""
import logging
import random
from dataclasses import dataclass

from dora_api.features.routers import HELP_ROUTER
from dora_api.infrastructure.api_response import ok


FOOD_FACTS: tuple[str, ...] = (
    "Honey never spoils. Sealed pots of it from ancient Egyptian tombs are still edible.",
    "Bananas are berries; strawberries are not.",
    "Carrots were originally purple — orange ones were bred in the 17th century.",
    "Apples float because about 25% of their volume is air.",
    "The most stolen food in the world is cheese — about 4% of all cheese made gets nicked.",
    "Watermelons are 92% water, which is exactly the same percentage as a jellyfish.",
    "Pineapples take about two years to grow a single fruit.",
    "Pistachios are technically fruits — specifically, the seed of a drupe.",
    "Saffron is the world's most expensive spice by weight; 75,000 crocus flowers make one pound.",
    "A 'baker's dozen' became thirteen because medieval bakers added an extra loaf to avoid being fined for short-weight bread.",
    "Tomato ketchup was sold as medicine in the 1830s, including for indigestion and jaundice.",
    "Lobsters were once considered food for prisoners and the poor in colonial America.",
    "Mushrooms have more in common genetically with humans than with plants.",
    "Coconut water is so close to human blood plasma it was used as an emergency IV in WWII.",
    "Vanilla is the second-most expensive spice after saffron because the orchids must be hand-pollinated.",
    "The hottest part of a chilli pepper is the membrane that holds the seeds, not the seeds themselves.",
    "Peanuts aren't nuts — they're legumes, more closely related to beans and lentils.",
    "Chocolate was used as currency by the Aztecs; you could buy a turkey for 100 cocoa beans.",
    "Cucumbers are 96% water and were originally cultivated in India over 3,000 years ago.",
    "The bubbles in champagne were originally a defect — early winemakers tried hard to prevent them.",
    "Avocados are toxic to most birds and many mammals, including parrots and horses.",
    "An average cob of corn has exactly 800 kernels, arranged in 16 rows.",
    "Spinach loses up to 90% of its vitamin C within 24 hours of being harvested.",
    "Cashews grow attached to the bottom of a fruit called a cashew apple, which is itself edible.",
    "The fear of cooking is called 'mageirocophobia'.",
)


@dataclass(frozen=True, slots=True)
class FoodFactDto:
    fact: str


@HELP_ROUTER.route("/food-fact", methods=["GET"])
def get_food_fact():
    _Logger = logging.getLogger(__name__)
    fact = random.choice(FOOD_FACTS)
    _Logger.debug("Served food fact: %s", fact[:40])
    return ok(FoodFactDto(fact=fact))
