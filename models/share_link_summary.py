from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, order=True)
class ShareLinkSummary:
    _id: str
    isActive: bool
    title: str
    description: str
    versionFollowing: str  # see ShareLink.VersionFollow
    protection: str  # see ShareLink.Protection
    createdAt: int
    isThumbnailGenerated: Optional[bool]   # non-authoritative; use with suspicion
    thumbnailUrl: str  # non-authoritative; use with suspicion
    custFileName: str  # non-authoritative; use with suspicion
