import inspect
from dataclasses import dataclass, field
from data_models.nav_ref import NavRef
from data_models.file_summary import FileSummary_CurationLimited
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

    @classmethod
    def from_json(cls, json_data):      
        ''' makes forgiving of extra fields '''
        return cls(**{
            k: v for k, v in json_data.items() 
            if k in inspect.signature(cls).parameters
        })

