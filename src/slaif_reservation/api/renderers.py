"""Product-branded Browsable API renderer for the existing HTML surface."""

from __future__ import annotations

from rest_framework.renderers import BrowsableAPIRenderer


class SlaifBrowsableAPIRenderer(BrowsableAPIRenderer):  # type: ignore[misc]
    """Browsable API with the SLAIF product identity.

    The customization is structural (template blocks only): the existing
    JSON/HTML renderers, request controls, actions, authentication and
    permissions are retained unchanged.
    """

    template = "web/browsable_api.html"
