"""
style.py
--------
ONE unified dark/teal theme, used across the entire app (auth screens AND
the dashboard) so the visual identity is consistent everywhere, plus
reusable UI components: logo, header banner, footer, and decorative
background icons (original SVG line-art -- heartbeat, dumbbell, footprint,
droplet, DNA helix, question mark) that sit faintly behind the content,
similar in spirit to the blurred gym-photo backdrop in the reference
mockup, but as original vector art (no stock photography needed/bundled).

IMPORTANT: every HTML string passed to st.markdown(..., unsafe_allow_html=True)
is run through textwrap.dedent().strip() first, or built as a single
flush (no-newline) string. Without this, the natural indentation of a
multi-line string written inside a Python function can make Streamlit's
markdown parser treat the block as a *code block* instead of raw HTML.
Keep that pattern if you add more HTML snippets here.

Usage in app.py:
    from style import inject_custom_css, hero_header, render_footer, risk_badge

    inject_custom_css()          # once, right after st.set_page_config(...)
    hero_header("Title", "Subtitle")   # top of a page
    render_footer()                    # bottom of a page
"""

import textwrap
import streamlit as st


# ---------------------------------------------------------------------------
# Palette -- single dark/teal theme used everywhere
# ---------------------------------------------------------------------------
BG = "#0A0F1C"
CARD = "#111A2C"
CARD_BORDER = "rgba(45, 217, 206, 0.22)"
TEAL = "#2DE0D4"
TEAL_DARK = "#1AB8B0"
PURPLE = "#6C5CE7"
DANGER = "#FF6B6B"
WARNING = "#FDCB6E"
SUCCESS = "#2DE0D4"
TEXT = "#E8EEF7"
MUTED = "#8B96AC"


def _md(html: str):
    """Dedent + strip, then render as raw HTML. Use for every HTML snippet."""
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Logo -- original heartbeat-pulse badge. Flush single-line string (no
# newlines/indentation) so it can never be mistaken for a markdown code block.
# ---------------------------------------------------------------------------
LOGO_SVG_LARGE = (
    '<svg width="42" height="42" viewBox="0 0 46 46" xmlns="http://www.w3.org/2000/svg">'
    '<defs><linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" stop-color="#2DE0D4"/><stop offset="100%" stop-color="#1AB8B0"/>'
    '</linearGradient></defs>'
    '<circle cx="23" cy="23" r="22" fill="url(#logoGrad)"/>'
    '<circle cx="23" cy="23" r="22" fill="none" stroke="white" stroke-opacity="0.25" stroke-width="1.5"/>'
    '<path d="M8 24 h6 l3 -9 l4 18 l3 -13 l2.5 4 h11.5" fill="none" stroke="#05201D" '
    'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="35" cy="12" r="2.6" fill="#05201D"/></svg>'
)
LOGO_SVG_SMALL = LOGO_SVG_LARGE.replace('width="42" height="42"', 'width="24" height="24"')

# ---------------------------------------------------------------------------
# Decorative background icons (original line-art, baked-in low opacity).
# Tiled/positioned behind the whole app to echo the mockup's photographic
# backdrop, without using any actual photo.
# ---------------------------------------------------------------------------
DUMBBELL_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNjAiIGhlaWdodD0iMTYwIiB2aWV3Qm94PSIwIDAgMTYwIDE2MCI+CjxnIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzJERTBENCIgc3Ryb2tlLXdpZHRoPSI1IiBzdHJva2UtbGluZWNhcD0icm91bmQiIG9wYWNpdHk9IjAuMDkiPgo8cmVjdCB4PSIyMCIgeT0iNjAiIHdpZHRoPSIxOCIgaGVpZ2h0PSI0MCIgcng9IjQiLz4KPHJlY3QgeD0iMTAiIHk9IjY4IiB3aWR0aD0iMTAiIGhlaWdodD0iMjQiIHJ4PSIzIi8+CjxyZWN0IHg9IjEyMiIgeT0iNjAiIHdpZHRoPSIxOCIgaGVpZ2h0PSI0MCIgcng9IjQiLz4KPHJlY3QgeD0iMTQwIiB5PSI2OCIgd2lkdGg9IjEwIiBoZWlnaHQ9IjI0IiByeD0iMyIvPgo8bGluZSB4MT0iMzgiIHkxPSI4MCIgeDI9IjEyMiIgeTI9IjgwIi8+CjwvZz48L3N2Zz4="
HEARTBEAT_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMTIwIiB2aWV3Qm94PSIwIDAgMjAwIDEyMCI+CjxwYXRoIGQ9Ik0xMCA2MCBINTUgTDcwIDIwIEw5NSAxMDAgTDExNSA0NSBMMTI4IDYwIEgxOTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzJERTBENCIgc3Ryb2tlLXdpZHRoPSI1IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIG9wYWNpdHk9IjAuMDkiLz4KPC9zdmc+"
FOOTPRINT_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iMTYwIiB2aWV3Qm94PSIwIDAgMTIwIDE2MCI+CjxnIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMDkiPgo8ZWxsaXBzZSBjeD0iNjAiIGN5PSIxMDAiIHJ4PSIzMiIgcnk9IjQ4Ii8+CjxjaXJjbGUgY3g9IjQwIiBjeT0iMzUiIHI9IjEwIi8+CjxjaXJjbGUgY3g9IjYwIiBjeT0iMjUiIHI9IjExIi8+CjxjaXJjbGUgY3g9IjgxIiBjeT0iMjgiIHI9IjEwIi8+CjxjaXJjbGUgY3g9Ijk4IiBjeT0iNDAiIHI9IjgiLz4KPC9nPjwvc3ZnPg=="
DROPLET_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iMTYwIiB2aWV3Qm94PSIwIDAgMTIwIDE2MCI+CjxwYXRoIGQ9Ik02MCAxMCBDNjAgMTAgMjAgNzAgMjAgMTA1IEE0MCA0MCAwIDAgMCAxMDAgMTA1IEMxMDAgNzAgNjAgMTAgNjAgMTAgWiIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4wOSIvPgo8L3N2Zz4="
QUESTION_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNDAiIGhlaWdodD0iMTYwIiB2aWV3Qm94PSIwIDAgMTQwIDE2MCI+Cjx0ZXh0IHg9IjcwIiB5PSIxMjAiIGZvbnQtc2l6ZT0iMTQwIiBmb250LWZhbWlseT0iUG9wcGlucywgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjcwMCIgZmlsbD0iIzJERTBENCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC4wOSI+PzwvdGV4dD4KPC9zdmc+"
DNA_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgMTQwIDIwMCI+CjxnIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzZDNUNFNyIgc3Ryb2tlLXdpZHRoPSI0IiBvcGFjaXR5PSIwLjA4Ij4KPHBhdGggZD0iTTIwIDEwIEMyMCA2MCAxMjAgNjAgMTIwIDExMCBDMTIwIDE2MCAyMCAxNjAgMjAgMTkwIi8+CjxwYXRoIGQ9Ik0xMjAgMTAgQzEyMCA2MCAyMCA2MCAyMCAxMTAgQzIwIDE2MCAxMjAgMTYwIDEyMCAxOTAiLz4KPGxpbmUgeDE9IjI4IiB5MT0iMzUiIHgyPSIxMTIiIHkyPSIzNSIvPgo8bGluZSB4MT0iMzYiIHkxPSI2MCIgeDI9IjEwNCIgeTI9IjYwIi8+CjxsaW5lIHgxPSIzNiIgeTE9IjE0MCIgeDI9IjEwNCIgeTI9IjE0MCIvPgo8bGluZSB4MT0iMjgiIHkxPSIxNjUiIHgyPSIxMTIiIHkyPSIxNjUiLz4KPC9nPjwvc3ZnPg=="

# Original word-cloud background (fitness-related words, varied size/rotation/
# opacity) -- same visual idea as a stock "word cloud" poster, but generated
# as original vector art so it can be freely embedded/tiled at any size.
WORDCLOUD_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NDAiIGhlaWdodD0iNjQwIiB2aWV3Qm94PSIwIDAgNjQwIDY0MCI+PHRleHQgeD0iNDI0IiB5PSI2OSIgZm9udC1zaXplPSIyMCIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iNzAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE4IiB0cmFuc2Zvcm09InJvdGF0ZSgwIDQyNCA2OSkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldFTExORVNTPC90ZXh0Pjx0ZXh0IHg9IjUzOSIgeT0iMjM5IiBmb250LXNpemU9IjE2IiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI4MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTEiIHRyYW5zZm9ybT0icm90YXRlKDAgNTM5IDIzOSkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPk1PVElPTjwvdGV4dD48dGV4dCB4PSIxMTIiIHk9IjU4NCIgZm9udC1zaXplPSIyMiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iOTAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjExIiB0cmFuc2Zvcm09InJvdGF0ZSg0IDExMiA1ODQpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5XT1JLT1VUPC90ZXh0Pjx0ZXh0IHg9IjYxNiIgeT0iODMiIGZvbnQtc2l6ZT0iMjIiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjcwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xIiB0cmFuc2Zvcm09InJvdGF0ZSg0IDYxNiA4MykiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkhFQUxUSFk8L3RleHQ+PHRleHQgeD0iMzE2IiB5PSI0NDkiIGZvbnQtc2l6ZT0iMjAiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjkwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xNSIgdHJhbnNmb3JtPSJyb3RhdGUoMCAzMTYgNDQ5KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+U1RSRU5HVEg8L3RleHQ+PHRleHQgeD0iNDAxIiB5PSIxMTkiIGZvbnQtc2l6ZT0iMjIiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjkwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xNyIgdHJhbnNmb3JtPSJyb3RhdGUoLTkwIDQwMSAxMTkpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5oYWJpdDwvdGV4dD48dGV4dCB4PSI1MjgiIHk9IjU2NCIgZm9udC1zaXplPSIyMiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE4IiB0cmFuc2Zvcm09InJvdGF0ZSg0IDUyOCA1NjQpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TVFJFTkdUSDwvdGV4dD48dGV4dCB4PSIzOTAiIHk9IjMyNiIgZm9udC1zaXplPSI0NCIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iOTAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE4IiB0cmFuc2Zvcm09InJvdGF0ZSgtOCAzOTAgMzI2KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+aGFiaXQ8L3RleHQ+PHRleHQgeD0iMTQwIiB5PSI1NDQiIGZvbnQtc2l6ZT0iMTYiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjgwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xMiIgdHJhbnNmb3JtPSJyb3RhdGUoNCAxNDAgNTQ0KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+VklUQUxJVFk8L3RleHQ+PHRleHQgeD0iNTkxIiB5PSI2MDYiIGZvbnQtc2l6ZT0iMTYiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjgwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xMyIgdHJhbnNmb3JtPSJyb3RhdGUoLTQgNTkxIDYwNikiIHRleHQtYW5jaG9yPSJtaWRkbGUiPmZpdDwvdGV4dD48dGV4dCB4PSI2MTMiIHk9IjQ4NyIgZm9udC1zaXplPSI0NCIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE4IiB0cmFuc2Zvcm09InJvdGF0ZSgwIDYxMyA0ODcpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5nb2FsczwvdGV4dD48dGV4dCB4PSI4MiIgeT0iMzM3IiBmb250LXNpemU9IjE2IiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI4MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTMiIHRyYW5zZm9ybT0icm90YXRlKDkwIDgyIDMzNykiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkJBTEFOQ0U8L3RleHQ+PHRleHQgeD0iNDMiIHk9IjQ5MiIgZm9udC1zaXplPSIzMCIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iNzAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjEyIiB0cmFuc2Zvcm09InJvdGF0ZSgtNCA0MyA0OTIpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5maXQ8L3RleHQ+PHRleHQgeD0iMjQzIiB5PSIzMTQiIGZvbnQtc2l6ZT0iMTYiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjgwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xNyIgdHJhbnNmb3JtPSJyb3RhdGUoMCAyNDMgMzE0KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QkFMQU5DRTwvdGV4dD48dGV4dCB4PSIxMDIiIHk9IjE5MCIgZm9udC1zaXplPSI0NCIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE0IiB0cmFuc2Zvcm09InJvdGF0ZSg5MCAxMDIgMTkwKSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Q0FSRElPPC90ZXh0Pjx0ZXh0IHg9IjU4MyIgeT0iMzA1IiBmb250LXNpemU9IjM2IiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI5MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMiIgdHJhbnNmb3JtPSJyb3RhdGUoNCA1ODMgMzA1KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+RU5FUkdZPC90ZXh0Pjx0ZXh0IHg9IjE3NCIgeT0iMTA0IiBmb250LXNpemU9IjIyIiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI5MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTIiIHRyYW5zZm9ybT0icm90YXRlKDAgMTc0IDEwNCkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkNBUkRJTzwvdGV4dD48dGV4dCB4PSI1MTYiIHk9IjIwNiIgZm9udC1zaXplPSIxNiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iNzAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjEzIiB0cmFuc2Zvcm09InJvdGF0ZSg4IDUxNiAyMDYpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5HT0FMUzwvdGV4dD48dGV4dCB4PSI0MjgiIHk9IjQyMyIgZm9udC1zaXplPSIzNiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE1IiB0cmFuc2Zvcm09InJvdGF0ZSgwIDQyOCA0MjMpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5DQVJESU88L3RleHQ+PHRleHQgeD0iMTMyIiB5PSIzNjgiIGZvbnQtc2l6ZT0iMjAiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjkwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xMSIgdHJhbnNmb3JtPSJyb3RhdGUoMCAxMzIgMzY4KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+U1RBTUlOQTwvdGV4dD48dGV4dCB4PSI0MDUiIHk9IjE3MiIgZm9udC1zaXplPSIyMiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iOTAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjIiIHRyYW5zZm9ybT0icm90YXRlKDggNDA1IDE3MikiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldPUktPVVQ8L3RleHQ+PHRleHQgeD0iMjkxIiB5PSI1MTAiIGZvbnQtc2l6ZT0iMzAiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjcwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xNSIgdHJhbnNmb3JtPSJyb3RhdGUoMCAyOTEgNTEwKSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+c2xlZXA8L3RleHQ+PHRleHQgeD0iMTEzIiB5PSIyODciIGZvbnQtc2l6ZT0iMjYiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjcwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xNCIgdHJhbnNmb3JtPSJyb3RhdGUoLTkwIDExMyAyODcpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5GSVRORVNTPC90ZXh0Pjx0ZXh0IHg9IjI0OCIgeT0iMjE5IiBmb250LXNpemU9IjMwIiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI5MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTgiIHRyYW5zZm9ybT0icm90YXRlKC04IDI0OCAyMTkpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5oeWRyYXRlPC90ZXh0Pjx0ZXh0IHg9IjIyNCIgeT0iNTUwIiBmb250LXNpemU9IjIyIiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTQiIHRyYW5zZm9ybT0icm90YXRlKDkwIDIyNCA1NTApIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5wcm9ncmVzczwvdGV4dD48dGV4dCB4PSI1MDMiIHk9IjI4NSIgZm9udC1zaXplPSIyNiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE3IiB0cmFuc2Zvcm09InJvdGF0ZSgtOCA1MDMgMjg1KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+RklUTkVTUzwvdGV4dD48dGV4dCB4PSI1MTAiIHk9IjM3MiIgZm9udC1zaXplPSIxNiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iNzAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE4IiB0cmFuc2Zvcm09InJvdGF0ZSgwIDUxMCAzNzIpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5nb2FsczwvdGV4dD48dGV4dCB4PSIxMDgiIHk9IjQyNSIgZm9udC1zaXplPSIzMCIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iNzAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjE0IiB0cmFuc2Zvcm09InJvdGF0ZSg5MCAxMDggNDI1KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Rk9DVVM8L3RleHQ+PHRleHQgeD0iMTk0IiB5PSIxNTAiIGZvbnQtc2l6ZT0iMjAiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjgwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xMiIgdHJhbnNmb3JtPSJyb3RhdGUoMCAxOTQgMTUwKSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+c2xlZXA8L3RleHQ+PHRleHQgeD0iNDEiIHk9IjM0IiBmb250LXNpemU9IjIwIiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTUiIHRyYW5zZm9ybT0icm90YXRlKDAgNDEgMzQpIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5FTkVSR1k8L3RleHQ+PHRleHQgeD0iMjM2IiB5PSI0OCIgZm9udC1zaXplPSIyMiIgZm9udC1mYW1pbHk9IlBvcHBpbnMsIEFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iOTAwIiBmaWxsPSIjMkRFMEQ0IiBvcGFjaXR5PSIwLjEyIiB0cmFuc2Zvcm09InJvdGF0ZSg4IDIzNiA0OCkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkZPQ1VTPC90ZXh0Pjx0ZXh0IHg9IjI4NSIgeT0iNTc3IiBmb250LXNpemU9IjMwIiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTgiIHRyYW5zZm9ybT0icm90YXRlKDQgMjg1IDU3NykiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkdPQUxTPC90ZXh0Pjx0ZXh0IHg9IjQ4OSIgeT0iNjE3IiBmb250LXNpemU9IjMwIiBmb250LWZhbWlseT0iUG9wcGlucywgQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtd2VpZ2h0PSI5MDAiIGZpbGw9IiMyREUwRDQiIG9wYWNpdHk9IjAuMTQiIHRyYW5zZm9ybT0icm90YXRlKC05MCA0ODkgNjE3KSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+c2xlZXA8L3RleHQ+PHRleHQgeD0iNTM5IiB5PSI0ODMiIGZvbnQtc2l6ZT0iMTYiIGZvbnQtZmFtaWx5PSJQb3BwaW5zLCBBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjcwMCIgZmlsbD0iIzJERTBENCIgb3BhY2l0eT0iMC4xIiB0cmFuc2Zvcm09InJvdGF0ZSgtOTAgNTM5IDQ4MykiIHRleHQtYW5jaG9yPSJtaWRkbGUiPlNUUkVOR1RIPC90ZXh0Pjwvc3ZnPg=="

# Plain (full-opacity) inline icons used for the ANIMATED floating background
# elements -- opacity here is controlled by the .bg-float-icon CSS class
# instead of being baked into the SVG, so they fade in/out consistently
# with the float animation.
_ICON_DUMBBELL_INLINE = (
    '<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg" width="100%">'
    '<g fill="none" stroke="#2DE0D4" stroke-width="6" stroke-linecap="round">'
    '<rect x="20" y="60" width="18" height="40" rx="4"/><rect x="10" y="68" width="10" height="24" rx="3"/>'
    '<rect x="122" y="60" width="18" height="40" rx="4"/><rect x="140" y="68" width="10" height="24" rx="3"/>'
    '<line x1="38" y1="80" x2="122" y2="80"/></g></svg>'
)
_ICON_DROPLET_INLINE = (
    '<svg viewBox="0 0 120 160" xmlns="http://www.w3.org/2000/svg" width="100%">'
    '<path d="M60 10 C60 10 20 70 20 105 A40 40 0 0 0 100 105 C100 70 60 10 60 10 Z" fill="#2DE0D4"/></svg>'
)
_ICON_HEARTBEAT_INLINE = (
    '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg" width="100%">'
    '<path d="M10 60 H55 L70 20 L95 100 L115 45 L128 60 H190" fill="none" stroke="#2DE0D4" '
    'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)
_ICON_FOOTPRINT_INLINE = (
    '<svg viewBox="0 0 120 160" xmlns="http://www.w3.org/2000/svg" width="100%">'
    '<g fill="#6C5CE7"><ellipse cx="60" cy="100" rx="32" ry="48"/><circle cx="40" cy="35" r="10"/>'
    '<circle cx="60" cy="25" r="11"/><circle cx="81" cy="28" r="10"/><circle cx="98" cy="40" r="8"/></g></svg>'
)
_ICON_DNA_INLINE = (
    '<svg viewBox="0 0 140 200" xmlns="http://www.w3.org/2000/svg" width="100%">'
    '<g fill="none" stroke="#6C5CE7" stroke-width="5">'
    '<path d="M20 10 C20 60 120 60 120 110 C120 160 20 160 20 190"/>'
    '<path d="M120 10 C120 60 20 60 20 110 C20 160 120 160 120 190"/>'
    '<line x1="28" y1="35" x2="112" y2="35"/><line x1="36" y1="60" x2="104" y2="60"/>'
    '<line x1="36" y1="140" x2="104" y2="140"/><line x1="28" y1="165" x2="112" y2="165"/></g></svg>'
)


def inject_custom_css():
    """The single theme for the whole app -- call once per page load."""
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {TEXT}; }}
        h1, h2, h3, h4, h5, h6, .hero-title, .auth-heading {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
            color: {TEXT} !important;
        }}
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4 {{
            color: {TEXT} !important;
        }}

        /* Remove the default white Streamlit toolbar band + top decoration bar */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}
        header[data-testid="stHeader"] * {{ color: {TEXT} !important; fill: {TEXT} !important; }}
        div[data-testid="stDecoration"] {{ display: none !important; }}
        div[data-testid="stToolbar"] {{ background: transparent !important; }}

        .stApp {{
            background-color: {BG};
            background-image:
                radial-gradient(circle at 12% 8%, rgba(45,224,212,0.18) 0%, transparent 42%),
                radial-gradient(circle at 88% 92%, rgba(108,92,231,0.18) 0%, transparent 42%),
                url("data:image/svg+xml;base64,{DUMBBELL_B64}"),
                url("data:image/svg+xml;base64,{HEARTBEAT_B64}"),
                url("data:image/svg+xml;base64,{FOOTPRINT_B64}"),
                url("data:image/svg+xml;base64,{DROPLET_B64}"),
                url("data:image/svg+xml;base64,{DNA_B64}");
            background-repeat: no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat;
            background-position:
                0 0, 0 0,
                6% 78%, 62% 6%, 92% 70%, 4% 18%, 90% 30%;
            background-size:
                auto, auto,
                200px 200px, 300px 180px, 150px 200px, 140px 186px, 170px 242px;
            background-attachment: fixed, fixed, fixed, fixed, fixed, fixed, fixed;
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0D1424 0%, #0A0F1C 100%);
            border-right: 1px solid rgba(45, 224, 212, 0.12);
            z-index: 100 !important;
        }}
        section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: rgba(45, 224, 212, 0.06);
            border: 1px solid rgba(45, 224, 212, 0.12);
            border-radius: 10px;
            padding: 0.4rem 0.6rem;
            margin-bottom: 0.35rem;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: rgba(45, 224, 212, 0.16);
            border: 1px solid {TEAL};
        }}

        /* The little arrow that re-opens a collapsed sidebar sits at the very
           top-left of the viewport by default -- our fixed full-width header
           (z-index 999999) was rendering on top of it and blocking clicks.
           Force it above everything and keep it clear of the header. */
        div[data-testid="stSidebarCollapsedControl"],
        button[data-testid="stSidebarCollapsedControl"],
        div[data-testid="collapsedControl"] {{
            z-index: 1000001 !important;
            position: fixed !important;
            top: 14px !important;
            left: 14px !important;
            opacity: 1 !important;
            visibility: visible !important;
            background: {CARD} !important;
            border: 1px solid {CARD_BORDER} !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stSidebarCollapsedControl"] * {{ color: {TEAL} !important; }}

        /* Hero banner */
        .hero-banner {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            background: {CARD};
            border: 1px solid {CARD_BORDER};
            padding: 1.4rem 1.8rem;
            border-radius: 20px;
            margin-bottom: 1.6rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35), 0 0 30px rgba(45,224,212,0.06);
        }}
        .hero-logo {{
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(45, 224, 212, 0.10);
            border-radius: 14px;
            padding: 6px;
        }}
        .hero-text-block {{ display: flex; flex-direction: column; }}
        .hero-title {{ font-size: 1.7rem; margin: 0; color: {TEXT} !important; line-height: 1.15; }}
        .hero-subtitle {{ font-size: 0.9rem; color: {MUTED}; margin-top: 0.2rem; }}

        /* Footer */
        .app-footer {{
            margin-top: 3rem;
            padding: 1.4rem 1.6rem;
            border-radius: 16px;
            background: {CARD};
            border: 1px solid {CARD_BORDER};
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.6rem;
            color: {TEXT};
            font-size: 0.85rem;
        }}
        .app-footer .footer-brand {{ display: flex; align-items: center; gap: 0.5rem; font-weight: 600; }}
        .app-footer .footer-links a {{ color: {TEAL}; text-decoration: none; margin-left: 1rem; font-weight: 500; }}
        .app-footer .footer-links a:hover {{ text-decoration: underline; }}
        .app-footer .footer-disclaimer {{ width: 100%; margin-top: 0.6rem; font-size: 0.75rem; color: {MUTED}; }}

        /* Cards / forms */
        div[data-testid="stForm"], .custom-card {{
            background: {CARD};
            border: 1px solid {CARD_BORDER};
            border-radius: 18px;
            padding: 1.6rem 1.6rem 1.1rem 1.6rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35), 0 0 24px rgba(45,224,212,0.05);
        }}

        /* Inputs -- everywhere, not just inside forms */
        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        div[data-baseweb="select"] > div, .stDateInput input {{
            background-color: #0D1524 !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 12px !important;
            color: {TEXT} !important;
        }}
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: {MUTED} !important; }}
        .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
            border: 1px solid {TEAL} !important;
            box-shadow: 0 0 0 3px rgba(45,224,212,0.15) !important;
        }}
        label, .stMarkdown p, .stCaption, div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMetricLabel"], p, span, .stMarkdown {{ color: {TEXT}; }}
        .stCaption, small {{ color: {MUTED} !important; }}

        /* Metrics */
        div[data-testid="stMetric"] {{
            background: {CARD};
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
            padding: 0.9rem 1rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        }}
        div[data-testid="stMetricValue"] {{ color: {TEAL} !important; }}

        /* Buttons */
        .stButton > button, .stFormSubmitButton > button {{
            background: linear-gradient(120deg, {TEAL} 0%, {TEAL_DARK} 100%) !important;
            color: #05201D !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 0.6rem 1.4rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.02em;
            box-shadow: 0 8px 22px rgba(45,224,212,0.30) !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 10px 26px rgba(45,224,212,0.45) !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{ gap: 1.4rem; border-bottom: 1px solid rgba(255,255,255,0.08); }}
        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            color: {MUTED} !important;
            font-weight: 600;
            padding: 0.5rem 0.1rem;
            border-radius: 0;
        }}
        .stTabs [aria-selected="true"] {{ color: {TEAL} !important; border-bottom: 2px solid {TEAL} !important; }}

        /* Dataframes / expanders */
        div[data-testid="stExpander"], div[data-testid="stDataFrame"] {{
            background: {CARD};
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-left: 0.4rem;
        }}
        .badge-low {{ background: rgba(45,224,212,0.15); color: {TEAL}; border: 1px solid rgba(45,224,212,0.4); }}
        .badge-medium {{ background: rgba(253,203,110,0.15); color: {WARNING}; border: 1px solid rgba(253,203,110,0.4); }}
        .badge-high {{ background: rgba(255,107,107,0.15); color: {DANGER}; border: 1px solid rgba(255,107,107,0.4); }}

        /* Auth-specific */
        .auth-topbar {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.7rem;
            margin: 2.4rem 0 2rem 0;
            color: {MUTED};
            font-weight: 800;
            letter-spacing: 0.08em;
            font-size: 1.15rem;
            text-transform: uppercase;
        }}
        .auth-topbar span {{ color: {TEXT}; }}
        .auth-heading {{ font-size: 2.1rem; font-weight: 800; color: {TEXT}; line-height: 1.15; margin-bottom: 0.3rem; }}
        .auth-heading .accent {{ color: {TEAL}; }}
        .auth-subtext {{ color: {MUTED}; font-size: 0.95rem; margin-bottom: 1.4rem; }}
        .auth-footnote {{ text-align: center; color: {MUTED}; font-size: 0.85rem; margin-top: 1.1rem; }}
        .auth-footnote a {{ color: {TEAL}; text-decoration: none; font-weight: 600; }}
        .auth-footnote a:hover {{ text-decoration: underline; }}

        div.block-container {{ padding-top: 2rem; }}

        /* --- Background animation --- */
        @keyframes pulseGlow {{
            0%   {{ opacity: 0.55; transform: scale(1); }}
            50%  {{ opacity: 1;    transform: scale(1.12); }}
            100% {{ opacity: 0.55; transform: scale(1); }}
        }}
        @keyframes floatUpDown {{
            0%   {{ transform: translateY(0px) rotate(0deg); }}
            50%  {{ transform: translateY(-18px) rotate(4deg); }}
            100% {{ transform: translateY(0px) rotate(0deg); }}
        }}
        @keyframes drift {{
            0%   {{ background-position: 0% 0%; }}
            50%  {{ background-position: 3% 2%; }}
            100% {{ background-position: 0% 0%; }}
        }}

        .bg-glow {{
            position: fixed;
            border-radius: 50%;
            filter: blur(60px);
            pointer-events: none;
            z-index: 0;
            animation: pulseGlow 7s ease-in-out infinite;
        }}
        .bg-glow.one {{
            top: -80px; left: -80px; width: 320px; height: 320px;
            background: radial-gradient(circle, rgba(45,224,212,0.28) 0%, transparent 70%);
            animation-delay: 0s;
        }}
        .bg-glow.two {{
            bottom: -100px; right: -100px; width: 380px; height: 380px;
            background: radial-gradient(circle, rgba(108,92,231,0.24) 0%, transparent 70%);
            animation-delay: 2s;
        }}
        .bg-glow.three {{
            top: 40%; right: 8%; width: 220px; height: 220px;
            background: radial-gradient(circle, rgba(45,224,212,0.16) 0%, transparent 70%);
            animation-delay: 4s;
        }}

        .bg-float-icon {{
            position: fixed;
            pointer-events: none;
            z-index: 0;
            opacity: 0.22;
            animation: floatUpDown 6s ease-in-out infinite;
        }}
        .bg-float-icon.i1 {{ top: 12%;  left: 5%;  animation-duration: 7s;  animation-delay: 0s; }}
        .bg-float-icon.i2 {{ top: 70%;  left: 8%;  animation-duration: 8s;  animation-delay: 1.2s; }}
        .bg-float-icon.i3 {{ top: 18%;  right: 6%; animation-duration: 6.5s; animation-delay: 0.6s; }}
        .bg-float-icon.i4 {{ top: 62%;  right: 9%; animation-duration: 7.5s; animation-delay: 2s; }}
        .bg-float-icon.i5 {{ top: 88%;  right: 30%; animation-duration: 9s;  animation-delay: 1.6s; }}

        /* Animated word-cloud layer (original artwork), slowly drifting */
        .bg-wordcloud {{
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background-image: url("data:image/svg+xml;base64,{WORDCLOUD_B64}");
            background-repeat: repeat;
            background-size: 560px 560px;
            animation: wordDrift 90s linear infinite;
        }}
        @keyframes wordDrift {{
            0%   {{ background-position: 0px 0px; }}
            100% {{ background-position: 560px 560px; }}
        }}

        .stApp > div:first-child {{ position: relative; z-index: 1; }}

        /* Streamlit wraps the app in containers that sometimes set
           transform/contain, which makes `position: fixed` descendants
           anchor to THAT wrapper instead of the real browser viewport --
           this is why a fixed header can end up only spanning the main
           content area instead of going over the sidebar. Neutralize it. */
        .stApp,
        div[data-testid="stAppViewContainer"],
        section.main,
        div[data-testid="stMain"],
        div.block-container {{
            transform: none !important;
            contain: none !important;
            filter: none !important;
            perspective: none !important;
            will-change: auto !important;
        }}

        /* ---- Full-width header & footer that span OVER the sidebar ---- */
        .hero-banner {{
            position: fixed !important;
            top: 0 !important; left: 0 !important; right: 0 !important;
            width: 100vw !important;
            z-index: 999999 !important;
            border-radius: 0;
            margin-bottom: 0;
        }}
        .app-footer {{
            position: fixed !important;
            bottom: 0 !important; left: 0 !important; right: 0 !important;
            width: 100vw !important;
            z-index: 999998 !important;
            border-radius: 0;
            margin-top: 0;
        }}
        /* Push page content below the fixed header, and the sidebar's own
           content below it too, and leave room above the fixed footer. */
        div.block-container {{ padding-top: 6.5rem; padding-bottom: 6rem; }}
        section[data-testid="stSidebar"] > div {{ padding-top: 5.5rem; padding-bottom: 6rem; }}

        /* Chat input: theme it dark, and sit it just above the footer */
        div[data-testid="stChatInput"], div[data-testid="stBottomBlockContainer"],
        .stChatFloatingInputContainer {{
            background: {CARD} !important;
            border-top: 1px solid {CARD_BORDER} !important;
            bottom: 68px !important;
            z-index: 998 !important;
        }}
        div[data-testid="stChatInput"] textarea, div[data-testid="stChatInput"] input {{
            background-color: #0D1524 !important;
            color: {TEXT} !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 12px !important;
        }}
    </style>
    """
    st.markdown(textwrap.dedent(css), unsafe_allow_html=True)

    decor = (
        '<div class="bg-wordcloud"></div>'
        '<div class="bg-glow one"></div>'
        '<div class="bg-glow two"></div>'
        '<div class="bg-glow three"></div>'
        f'<div class="bg-float-icon i1" style="width:70px;">{_ICON_DUMBBELL_INLINE}</div>'
        f'<div class="bg-float-icon i2" style="width:60px;">{_ICON_DROPLET_INLINE}</div>'
        f'<div class="bg-float-icon i3" style="width:80px;">{_ICON_HEARTBEAT_INLINE}</div>'
        f'<div class="bg-float-icon i4" style="width:55px;">{_ICON_FOOTPRINT_INLINE}</div>'
        f'<div class="bg-float-icon i5" style="width:65px;">{_ICON_DNA_INLINE}</div>'
    )
    st.markdown(decor, unsafe_allow_html=True)


def hero_header(title: str, subtitle: str = ""):
    """Top banner with logo + title + subtitle, used on dashboard pages."""
    html = (
        f'<div class="hero-banner">'
        f'<div class="hero-logo">{LOGO_SVG_LARGE}</div>'
        f'<div class="hero-text-block">'
        f'<div class="hero-title">{title}</div>'
        f'<div class="hero-subtitle">{subtitle}</div>'
        f'</div></div>'
    )
    _md(html)


def render_footer(session_token: str = None):
    """Standard footer shown at the bottom of every page. If session_token is
    given, the About/Privacy/Contact links carry it along so a logged-in user
    doesn't get logged out just from navigating to one of these pages."""
    suffix = f"&session={session_token}" if session_token else ""
    html = (
        f'<div class="app-footer">'
        f'<div class="footer-brand">{LOGO_SVG_SMALL} Health &amp; Fitness Digital Twin</div>'
        f'<div class="footer-links">'
        f'<a href="?page=about{suffix}" target="_self">About</a>'
        f'<a href="?page=privacy{suffix}" target="_self">Privacy</a>'
        f'<a href="?page=contact{suffix}" target="_self">Contact</a>'
        f'</div>'
        f'<div class="footer-disclaimer">'
        f'⚠️ Educational project. Predictions and risk scores are AI-generated estimates, '
        f'not medical advice — always consult a qualified professional for health decisions.'
        f'</div></div>'
    )
    _md(html)


def risk_badge(level: str) -> str:
    cls = {"Low": "badge-low", "Medium": "badge-medium", "High": "badge-high"}.get(level, "badge-medium")
    return f'<span class="badge {cls}">{level}</span>'


def auth_topbar(brand: str = "HEALTH &amp; FITNESS DIGITAL TWIN"):
    html = f'<div class="auth-topbar">{LOGO_SVG_SMALL}<span>{brand}</span></div>'
    _md(html)


def auth_heading(title_plain: str, title_accent: str, subtitle: str):
    html = (
        f'<div class="auth-heading">{title_plain} <span class="accent">{title_accent}</span></div>'
        f'<div class="auth-subtext">{subtitle}</div>'
    )
    _md(html)


def auth_footnote(text: str):
    _md(f'<div class="auth-footnote">{text}</div>')


# Kept for backwards compatibility with earlier versions of app.py that
# imported a separate auth theme function -- now it's the same unified theme.
def inject_auth_theme():
    inject_custom_css()


# ---------------------------------------------------------------------------
# Plotly dark theme -- makes every chart match the black/teal dashboard look.
# Call style_chart(fig) right before st.plotly_chart(fig, ...).
# ---------------------------------------------------------------------------
CHART_COLORWAY = ["#2DE0D4", "#6C5CE7", "#FDCB6E", "#FF6B6B", "#74B9FF"]


def style_chart(fig):
    """Apply the dark/teal theme to a Plotly figure. Returns the same fig."""
    fig.update_layout(
        paper_bgcolor="#0D1524",
        plot_bgcolor="#0D1524",
        font=dict(color=TEXT, family="Inter, sans-serif"),
        title_font=dict(color=TEXT, family="Poppins, sans-serif", size=16),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        colorway=CHART_COLORWAY,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)",
                    linecolor="rgba(255,255,255,0.15)", color=MUTED),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)",
                    linecolor="rgba(255,255,255,0.15)", color=MUTED),
    )
    return fig