from PySide.QtGui import QCursor
from PySide.QtWidgets import QApplication
from PySide.QtCore import Qt


from delegates.promotion_delegate import PromotionDelegate
from models.promotion import PromotionListModel, Promotion
from qflowview.qflowview import QFlowView
from APIClient import fancy_handle, API_Call_Result


class OndselPromotionsView(QFlowView):
    def __init__(self, parent=None):
        super(OndselPromotionsView, self).__init__(parent)
        self.parent = parent
        self.promotionListModel = PromotionListModel()
        self.setItemDelegate(PromotionDelegate)
        self.setModel(self.promotionListModel)
        self.ondsel_org = None
        self.get_ondsel_and_promotions()

    def get_ondsel_and_promotions(self):
        promotions = []
        def get_promoted_items():
            nonlocal promotions
            ondsel_org = self.parent.api.getOndselOrganization()
            self.ondsel_org = ondsel_org
            promotions_dicts = ondsel_org["curation"]["promoted"] or []
            for promo in promotions_dicts:
                new_promo = Promotion.from_json(promo)
                new_promo.curation.parent = (
                    self.parent
                )  # this gives live api access to the item delegate's curation
                promotions.append(new_promo)

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        api_result = fancy_handle(get_promoted_items)
        if api_result == API_Call_Result.OK:
            self.promotionListModel.promotion_list = promotions
            self.parent.form.ondselStartStatusLabel.setText("")
            self.promotionListModel.layoutChanged.emit() # TODO: needed?

        elif api_result == API_Call_Result.DISCONNECTED:
            self.parent.form.ondselStartStatusLabel.setText("off-line")
            self.promotionListModel.promotion_list = []
            self.promotionListModel.layoutChanged.emit()

        else:
            # because search is public, .NOT_LOGGED_IN will never happen
            self.parent.form.ondselStartStatusLabel.setText("unexpected error")
            self.promotionListModel.promotion_list = []
            self.promotionListModel.layoutChanged.emit()
        QApplication.restoreOverrideCursor()
