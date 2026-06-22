from __future__ import annotations

import uuid

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.assets.selectors import (
    AssetFilterError,
    asset_inventory_queryset,
    get_asset_for_inventory,
    parse_asset_filters,
)


@staff_member_required
def asset_list(request: HttpRequest) -> HttpResponse:
    try:
        filters = parse_asset_filters(request.GET)
    except AssetFilterError as exc:
        return HttpResponseBadRequest(str(exc))

    return render(
        request,
        "assets/asset_list.html",
        {
            "assets": asset_inventory_queryset(filters),
            "filters": filters,
            "kinds": Asset.KIND_CHOICES,
            "parents": Asset.objects.filter(kind=Asset.KIND_MACHINE).order_by("slug"),
            "tags": AssetTag.objects.order_by("slug"),
        },
    )


@staff_member_required
def asset_detail(request: HttpRequest, asset_id: uuid.UUID) -> HttpResponse:
    try:
        asset = get_asset_for_inventory(asset_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc

    return render(request, "assets/asset_detail.html", {"asset": asset})
