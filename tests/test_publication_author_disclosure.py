import unittest
import re

from site_generation import render_listing_author_list


AUTHOR_MAP = {
    "alice smith": "alice-smith",
    "bob jones": "bob-jones",
    "carol ng": "carol-ng",
    "dan wu": "dan-wu",
    "eve stone": "eve-stone",
}


class RenderListingAuthorListTests(unittest.TestCase):
    def test_returns_plain_markup_when_author_count_is_at_cutoff(self) -> None:
        html = render_listing_author_list(
            "Alice Smith, Bob Jones, Carol Ng, Dan Wu",
            AUTHOR_MAP,
            visible_authors=4,
        )

        self.assertNotIn("see more...", html)
        self.assertNotIn("author-disclosure__extra", html)
        self.assertIn('/members/alice-smith/', html)
        self.assertIn('/members/dan-wu/', html)

    def test_adds_disclosure_markup_when_author_count_exceeds_cutoff(self) -> None:
        html = render_listing_author_list(
            "Alice Smith, Bob Jones, Carol Ng, Dan Wu, Eve Stone",
            AUTHOR_MAP,
            visible_authors=4,
        )

        self.assertIn('class="author-disclosure"', html)
        self.assertRegex(html, r'class="author-disclosure__extra"[^>]*hidden')
        self.assertIn('class="author-disclosure__button"', html)
        self.assertIn('see more...', html)

    def test_keeps_member_links_in_visible_and_hidden_authors(self) -> None:
        html = render_listing_author_list(
            "Alice Smith, Bob Jones, Carol Ng, Dan Wu, Eve Stone",
            AUTHOR_MAP,
            visible_authors=4,
        )

        self.assertIn('/members/alice-smith/', html)
        self.assertIn('/members/eve-stone/', html)

    def test_keeps_hidden_authors_in_dom_for_text_search(self) -> None:
        html = render_listing_author_list(
            "Alice Smith, Bob Jones, Carol Ng, Dan Wu, Eve Stone",
            AUTHOR_MAP,
            visible_authors=4,
        )

        self.assertRegex(
            html,
            re.compile(
                r'class="author-disclosure__extra"[^>]*hidden[^>]*>.*Eve Stone',
                re.DOTALL,
            ),
        )


if __name__ == "__main__":
    unittest.main()
