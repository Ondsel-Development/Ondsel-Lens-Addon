import inspect
from dataclasses import dataclass

from models.curation import Curation
from PySide.QtCore import Qt, QAbstractListModel
from models.user_summary import UserSummary


@dataclass(order=True)
class Notation:
    updatedAt: int
    message: str
    historicUser: UserSummary

    def __post_init__(self):
        self.historicUser = UserSummary(**self.historicUser)


@dataclass(order=True)
class Promotion:
    notation: Notation
    curation: Curation

    def __post_init__(self):
        self.notation = Notation(**self.notation)
        self.curation = Curation(**self.curation)

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


class PromotionListModel(QAbstractListModel):

    PromotionRole = Qt.UserRole + 1 # TODO: verify this behavior

    def __init__(self, *args, promotions=None, **kwargs):
        super(PromotionListModel, self).__init__(*args, **kwargs)
        self.promotion_list = promotions or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.prommotion_list[index.row()].curation.name
        elif role == self.PromotionRole:
            return self.promotion_list[index.row()]

    def rowCount(self, index):
        return len(self.promotion_list)
