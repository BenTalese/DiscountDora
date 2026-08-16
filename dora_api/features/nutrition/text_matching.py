"""Shared food-name text handling for the nutrition feature.

Two consumers need the *same* notion of "these two words are the same word":
`recipe_rollup` matching a recipe's "3 cloves" against a dataset portion's
"clove", and `suggestions` matching a stock item's "Bananas" against a
catalogue's "Banana, raw". A second, subtly-different de-pluraliser in the
newer file would make the two disagree about the same pantry, so it lives here
once (R-002).
"""

# Deliberately tiny. These are the words that carry no identifying information
# in a food name, so counting them would let "Beans, of the garden" look like a
# better match for "beans" than "Beans, snap, raw". Anything with actual
# culinary meaning ("raw", "fresh", "dried") is NOT here — those distinguish
# real dataset rows from each other and must keep scoring.
STOPWORDS = frozenset({"a", "an", "the", "of", "and", "or", "with", "in"})


def singular(word: str) -> str:
    """Crude de-pluralisation, applied to both sides of a match so recipe
    wording ("3 cloves") meets dataset wording ("clove"). Words shorter than
    four letters are left alone — stripping the s off "oz" or "cos" changes
    what they mean."""
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxzo":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokens(text: str) -> set[str]:
    """A food name reduced to its comparable words.

    Non-letters become separators, because catalogue names are punctuation-
    heavy ("Chicken, broilers or fryers, breast") and stock-item names are not
    ("chicken breast"). Digits go the same way: "Milk 2%" and "Milk, 2% fat"
    should meet on `milk`, and a stray number is never what makes two foods the
    same thing.
    """
    cleaned = "".join(c if c.isalpha() else " " for c in (text or "").lower())
    return {
        singular(word) for word in cleaned.split()
        if word and word not in STOPWORDS
    }


def normalised(text: str) -> str:
    """The whole name as one comparable string — used only for the exact-match
    case, where word order still matters."""
    cleaned = "".join(c if c.isalpha() else " " for c in (text or "").lower())
    return " ".join(singular(word) for word in cleaned.split() if word)
