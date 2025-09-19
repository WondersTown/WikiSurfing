from pydantic_ai import ModelRetry
from typing import Callable, ParamSpec, TypeVar, TypedDict
import re


R = TypeVar("R")
P = ParamSpec("P")


def value_error_to_retry(func: Callable[[str], R]) -> Callable[[str], R]:
    def wrapper(arg: str) -> R:
        try:
            return func(arg)
        except ValueError as e:
            raise ModelRetry(str(e)) from None

    return wrapper


class _MatchDict(TypedDict):
    start: int
    end: int
    term: str
    href: str
    length: int


def replace_text_with_links(text: str, terms: set[str]) -> str:
    """Replace terms in text with emphasis tags.

    Args:
        text: The input text to process
        terms: Set of terms to wrap in emphasis tags

    Returns:
        Text with matched terms wrapped in <em>term</em> tags

    If overlapping matches are found, prefers the longer match.
    """

    # Find all potential matches with their positions
    matches: list[_MatchDict] = []
    for term in terms:
        # Find all occurrences of this term in the text
        for match in re.finditer(re.escape(term), text, re.IGNORECASE):
            start, end = match.span()
            matches.append(
                _MatchDict(
                    start=start, end=end, term=term, href="", length=end - start
                )
            )

    # Sort matches by start position, then by length (descending) for overlapping cases
    matches.sort(key=lambda x: (x["start"], -x["length"]))

    # Remove overlapping matches, keeping the longer ones
    filtered_matches: list[_MatchDict] = []
    for match in matches:
        # Check if this match overlaps with any already accepted match
        overlaps = False
        for accepted in filtered_matches:
            if not (
                match["end"] <= accepted["start"] or match["start"] >= accepted["end"]
            ):
                # There's an overlap
                if match["length"] > accepted["length"]:
                    # Remove the shorter accepted match
                    filtered_matches.remove(accepted)
                else:
                    # Skip this match as it's shorter
                    overlaps = True
                    break

        if not overlaps:
            filtered_matches.append(match)

    # Sort by start position for processing
    filtered_matches.sort(key=lambda x: x["start"])

    # Apply replacements from right to left to maintain correct positions
    filtered_matches.reverse()

    for match in filtered_matches:
        start = match["start"]
        end = match["end"]

        # Create the replacement emphasis tag
        replacement = f'<em>{text[start:end]}</em>'

        # Replace the text
        text = text[:start] + replacement + text[end:]

    return text
