from dataclasses import dataclass, field
from nav_ref import NavRef
from file_summary import FileSummary_CurationLimited


@dataclass(order=True)
class Curation:
    _id: str
    collection: str
    nav: NavRef
    name: str = ""
    slug: str
    description: str = ""
    longDescriptionMd: str = ""
    tags: list[str] = field(default_factory=list, repr=false)
    representativeFile: FileSummary_CurationLimited = None

    # promoted: <- ignore, to be deprecatted here and moved to Organization object
    # keywordRefs: <- ignore, not relavant to Add-On
