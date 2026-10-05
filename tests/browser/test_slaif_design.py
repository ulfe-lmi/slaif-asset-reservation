"""Real role/surface visual and layout qualification of the SLAIF design."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)

CUSTOM = Path(__file__).resolve().parents[1] / "fixtures/branding/custom"
WIDTHS = (1440, 1024, 768, 390)


@pytest.fixture
def visual_records():
    member = User.objects.create_user(
        email="visual-member@example.com", password="synthetic-pass", display_name="Research member"
    )
    staff = User.objects.create_superuser(
        email="visual-staff@example.com", password="synthetic-pass", display_name="Lab operator"
    )
    other = User.objects.create_user(email="visual-other@example.com", password="synthetic-pass")
    machine = Asset.objects.create(
        slug="visual-compute",
        name="Compute workstation",
        kind="machine",
        active=True,
        reservable=False,
        verification_required=False,
    )
    asset = Asset.objects.create(
        slug="visual-gpu",
        name="GPU research device",
        kind="gpu",
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
        description="A shared device for scheduled research sessions.",
        capabilities={"memory_gb": 24},
    )
    tag = AssetTag.objects.create(slug="research", name="Research")
    asset.tags.add(tag)
    policy = ReservationPolicy.objects.create(
        name="default",
        asset=None,
        active=True,
        min_duration_minutes=1,
        max_duration_minutes=2880,
        booking_horizon_days=7,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=8,
        purpose_required=False,
    )
    now = timezone.now()
    reservation = Reservation.objects.create(
        asset=asset,
        requested_by_user=member,
        source="web",
        status="confirmed",
        start_at=now + timedelta(hours=3),
        end_at=now + timedelta(hours=5),
        effective_end_at=now + timedelta(hours=5),
        purpose="Research session",
    )
    Reservation.objects.create(
        asset=asset,
        requested_by_user=other,
        source="web",
        status="confirmed",
        start_at=now + timedelta(hours=7),
        end_at=now + timedelta(hours=8),
        effective_end_at=now + timedelta(hours=8),
        purpose="Private other-owner fixture",
    )
    blackout = MaintenanceBlackout.objects.create(
        asset=asset,
        start_at=now + timedelta(days=2),
        end_at=now + timedelta(days=2, hours=2),
        reason="Planned device maintenance",
        active=True,
        created_by=staff,
    )
    event = AuditEvent.objects.create(
        occurred_at=now,
        actor_user=staff,
        action=AuditEvent.ACTION_POLICY_CREATED,
        target_type="reservation_policy",
        target_id=policy.id,
        correlation_id=policy.id,
        source="admin",
        metadata={},
    )
    issued = issue_api_token(
        owner=member,
        name="Research integration",
        scopes=["availability:read", "reservations:read"],
        lifetime_days=7,
    )
    # Only the token row/prefix is used; no plaintext response is rendered/captured.
    token = issued.token
    return {
        "member": member,
        "staff": staff,
        "asset": asset,
        "policy": policy,
        "reservation": reservation,
        "blackout": blackout,
        "event": event,
        "token": token,
    }


def login(page: Page, base: str, email: str) -> None:
    if page.locator(".nav-form").count():
        toggle = page.get_by_role("button", name="Menu", exact=True)
        if toggle.is_visible() and toggle.get_attribute("aria-expanded") == "false":
            toggle.click()
        page.get_by_role("button", name="Logout", exact=True).click()
        page.wait_for_url(base + "/login/")
    page.goto(base + "/login/")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill("synthetic-pass")
    page.get_by_role("button", name="Log in", exact=True).click()
    page.wait_for_url(base + "/")


def inspect_surface(page: Page, output_path, name: str, width: int, theme: str) -> None:
    page.wait_for_function("document.fonts.status === 'loaded'")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), name
    assert "Django" not in page.locator("body").inner_text(), name
    assert "Django" not in page.title(), name
    assert page.locator("h1").count() > 0, name
    # Every declared help relationship must resolve to actual DOM help.
    assert page.evaluate("""() =>
        Array.from(document.querySelectorAll('[aria-describedby]')).every(el =>
          el.getAttribute('aria-describedby').split(/\\s+/).every(id =>
            !!document.getElementById(id)))"""), name
    page.wait_for_function(
        "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)"
    )
    # Measure the actual painted foreground against its nearest opaque ancestor.
    # These UI surfaces have solid backgrounds; no screenshot pixel matching is used.
    contrast_failures = page.evaluate(r"""() => {
      const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
      const lum = a => a.slice(0,3).map(x => {
        x /= 255; return x <= .04045 ? x / 12.92 : ((x+.055)/1.055)**2.4;
      }).reduce((v,x,i) => v + x*[.2126,.7152,.0722][i], 0);
      return [...document.querySelectorAll(
        'h1,h2,h3,label,.help,.choice-help,button,a.button,.nav-toggle,' +
        '.site-footer span,.site-footer a,a.admin-brand,#changelist-filter a'
      )].filter(el => el.checkVisibility() && !el.matches(':disabled') &&
          el.getAttribute('aria-disabled') !== 'true' && [...el.childNodes].some(n =>
          n.nodeType === Node.TEXT_NODE && n.textContent.trim())).flatMap(el => {
        const cs = getComputedStyle(el); let bg = null;
        for (let parent = el; parent; parent = parent.parentElement) {
          const c = rgb(getComputedStyle(parent).backgroundColor);
          if (c.length === 3 || c[3] === 1) { bg = c; break; }
        }
        if (!bg) bg = [255,255,255];
        const fg = rgb(cs.color);
        if (fg.length === 4) for (let i=0; i<3; i++)
          fg[i] = fg[i]*fg[3] + bg[i]*(1-fg[3]);
        const a = lum(fg), b = lum(bg);
        const ratio = (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
        const large = parseFloat(cs.fontSize) >= 24 ||
          (parseFloat(cs.fontSize) >= 18.66 && parseInt(cs.fontWeight) >= 700);
        return ratio + .01 < (large ? 3 : 4.5) ?
          [{text:el.textContent.trim().slice(0,65),ratio,fg:cs.color,bg}] : [];
      });
    }""")
    assert not contrast_failures, (name, contrast_failures)
    focus_failure = page.evaluate("""() => {
      const controls = document.querySelectorAll(
        'a[href],button,input:not([type=hidden]),select,textarea,[role=combobox]');
      for (const el of controls) {
        if (!el.checkVisibility() || el.matches(':disabled') ||
            el.getAttribute('aria-disabled') === 'true' ||
            el.classList.contains('select2-hidden-accessible')) continue;
        el.focus();
        if (el !== document.activeElement) return {
          tag:el.tagName, id:el.id, classes:el.className, tabIndex:el.tabIndex};
      }
      return null;
    }""")
    assert focus_failure is None, (name, focus_failure)
    # Focus checks can scroll long forms. Capture their intended initial layout,
    # including the sticky administration sidebar, from the top of the document.
    page.evaluate("window.scrollTo(0, 0)")
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(resolve))")
    page.screenshot(path=f"{output_path}/{theme}-{width}-{name}.png", full_page=True)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("theme", ["default", "custom"])
@pytest.mark.parametrize("width", WIDTHS)
def test_all_role_surfaces(
    page: Page, live_server, output_path, visual_records, theme: str, width: int
) -> None:
    data = visual_records
    base = live_server.url
    page.set_viewport_size({"width": width, "height": 1000 if width >= 768 else 844})
    with override_settings(BRANDING_DIR=str(CUSTOM) if theme == "custom" else None):
        for name, path in [
            ("landing", "/"),
            ("login", "/login/"),
            ("admin-login", "/admin/login/"),
        ]:
            page.goto(base + path)
            assert "Private other-owner fixture" not in page.locator("body").inner_text()
            inspect_surface(page, output_path, name, width, theme)
        page.goto(base + "/")
        page.get_by_role("link", name="Administration", exact=True).first.click()
        assert "/admin/login/" in page.url
        login(page, base, data["member"].email)
        if width <= 1024:
            page.get_by_role("button", name="Menu", exact=True).focus()
            page.keyboard.press("Enter")
            assert page.get_by_role("link", name="Assets", exact=True).is_visible()
            inspect_surface(page, output_path, "navigation", width, theme)
            page.keyboard.press("Escape")
            assert (
                page.get_by_role("button", name="Menu", exact=True).get_attribute("aria-expanded")
                == "false"
            )
        member_pages = [
            ("dashboard", "/"),
            ("assets", "/assets/"),
            ("asset-detail", f"/assets/{data['asset'].id}/"),
            ("reserve", f"/assets/{data['asset'].id}/reserve/"),
            ("reservations", "/reservations/"),
            ("reservation", f"/reservations/{data['reservation'].id}/"),
            ("profile", "/profile/"),
            ("tokens", "/tokens/"),
            ("token-create", "/tokens/new/"),
        ]
        for name, path in member_pages:
            page.goto(base + path)
            assert "Private other-owner fixture" not in page.locator("body").inner_text()
            inspect_surface(page, output_path, name, width, theme)
        login(page, base, data["staff"].email)
        staff_pages = [
            ("manage", "/manage/"),
            ("policies", "/manage/policies/"),
            ("policy", f"/manage/policies/{data['policy'].id}/"),
            ("policy-form", f"/manage/policies/{data['policy'].id}/edit/"),
            ("blackouts", "/manage/blackouts/"),
            ("blackout", f"/manage/blackouts/{data['blackout'].id}/"),
            ("blackout-form", "/manage/blackouts/new/"),
            ("managed-reservations", "/manage/reservations/"),
            ("managed-reservation", f"/manage/reservations/{data['reservation'].id}/"),
            ("audit", "/manage/audit/"),
            ("audit-detail", f"/manage/audit/{data['event'].id}/"),
            ("admin", "/admin/"),
            ("admin-users", "/admin/accounts/user/"),
            ("admin-user", f"/admin/accounts/user/{data['member'].id}/change/"),
            ("admin-user-add", "/admin/accounts/user/add/"),
            ("admin-password", f"/admin/accounts/user/{data['member'].id}/password/"),
            ("admin-token", f"/admin/accounts/apitoken/{data['token'].id}/change/"),
            ("admin-assets", "/admin/assets/asset/"),
            ("admin-asset", f"/admin/assets/asset/{data['asset'].id}/change/"),
            ("admin-group", "/admin/auth/group/add/"),
            ("admin-policy", f"/admin/reservations/reservationpolicy/{data['policy'].id}/change/"),
        ]
        for name, path in staff_pages:
            page.goto(base + path)
            inspect_surface(page, output_path, name, width, theme)
        page.goto(base + "/manage/audit/")
        assert page.get_by_role("link", name="Export CSV", exact=True).is_visible()
