import inspect
from dataclasses import dataclass, field
from models.nav_ref import NavRef
from models.file_summary import FileSummary_CurationLimited
from typing import Optional


@dataclass(order=True)
class Curation:
    _id: str
    collection: str
    nav: NavRef
    name: str = ""
    slug: str = ""
    description: str = ""
    longDescriptionMd: str = ""
    tags: list[str] = field(default_factory=list, repr=False)
    representativeFile: Optional[FileSummary_CurationLimited] = None
    # promoted: <- ignore, to be deprecatted here and moved to Organization object
    # keywordRefs: <- ignore, not relavant to Add-On

    def __post_init__(self):
        self.nav = NavRef(**self.nav)
        if self.representativeFile:
            self.representativeFile = FileSummary_CurationLimited(
                **self.representativeFile
            )

    def get_thumbnail_url(self):
        url = None
        if self.representativeFile:
            url = (
                self.representativeFile.thumbnailUrlCache
            )  # defaults to None if missing
        else:
            # todo: get better defaults for the different target collections. A generic head, for example, for a user.
            match self.nav.target:
                case "workspaces":
                    if self.orgname != None:
                        url = None
                    else:
                        url = None
                case "organizations":
                    url = None
                case "users":
                    url = None
                case "shared-models":
                    url = None
                case "models":
                    url = None
                case "ondsel":
                    url = None
        return url

    @classmethod
    def from_json(cls, json_data):
        """makes forgiving of extra fields"""
        return cls(
            **{
                k: v
                for k, v in json_data.items()
                if k in inspect.signature(cls).parameters
            }
        )
