"""Official management links. No authentication, account APIs or billing actions."""

from __future__ import annotations
from dataclasses import dataclass
import webbrowser


@dataclass(frozen=True)
class SubscriptionGuide:
    platform: str
    title: str
    url: str
    instructions: str


GUIDES = {
    "web": SubscriptionGuide(
        "web", "ChatGPT web", "https://chatgpt.com/",
        "Sign into the original ChatGPT account. Check Settings for billing "
        "and subscription management; verify the current plan there.",
    ),
    "google": SubscriptionGuide(
        "google", "Google Play",
        "https://play.google.com/store/account/subscriptions",
        "Use the Google account that purchased ChatGPT on Android; check its "
        "subscription and next charge in Google Play.",
    ),
    "apple": SubscriptionGuide(
        "apple", "Apple App Store",
        "https://support.apple.com/en-us/118428",
        "Follow Apple's official subscription-management steps using the "
        "Apple Account that purchased ChatGPT.",
    ),
}


def guide_for(platform: str) -> SubscriptionGuide:
    try:
        return GUIDES[platform]
    except KeyError as exc:
        raise ValueError("Platform must be web, google or apple") from exc


def open_official_page(platform: str) -> bool:
    """Opens a hard-coded official URL only after explicit user action."""
    return bool(webbrowser.open(guide_for(platform).url))
