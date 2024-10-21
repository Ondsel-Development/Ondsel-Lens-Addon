import Utils

from PySide import QtCore
from PySide.QtGui import QStyledItemDelegate, QStyle

logger = Utils.getLogger(__name__)


class WorkspaceListDelegate(QStyledItemDelegate):
    def getOrganizationText(self, workspaceData):
        organizationData = workspaceData.get("organization")
        if organizationData:
            organizationName = organizationData.get("name")
            if organizationName:
                return f"({organizationName})"
            else:
                logger.debug("No 'name' in organization'")
        else:
            logger.debug("No 'organization' in workspaceData")
        return ""

    def paint(self, painter, option, index):
        # Get the data for the current index
        workspaceData = index.data(QtCore.Qt.DisplayRole)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        # Set up font for the name (bold)
        name_font = painter.font()
        name_font.setBold(True)

        # Set up font for the type (normal)
        type_font = painter.font()
        type_font.setBold(False)

        # Draw the name
        name_rect = QtCore.QRect(
            option.rect.left() + 20,
            option.rect.top(),
            option.rect.width() - 20,
            option.rect.height() // 3,
        )
        painter.setFont(name_font)
        painter.drawText(
            name_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            workspaceData["name"],
        )

        # Calculate the width of the name text
        name_width = painter.fontMetrics().boundingRect(workspaceData["name"]).width()

        # Draw the organization in parentheses TODO : name and not the id.

        type_text = self.getOrganizationText(workspaceData)
        type_rect = QtCore.QRect(
            option.rect.left() + 20 + name_width + 5,
            option.rect.top(),
            option.rect.width() - 20,
            option.rect.height() // 3,
        )
        painter.setFont(type_font)
        painter.drawText(
            type_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, type_text
        )

        # Adjust the height of the item
        item_height = option.rect.height() // 3
        name_rect.setHeight(item_height)
        type_rect.setHeight(item_height)

        # Draw the description
        desc_rect = QtCore.QRect(
            option.rect.left() + 20,
            type_rect.bottom(),
            option.rect.width() - 20,
            item_height,
        )
        painter.drawText(
            desc_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            workspaceData["description"],
        )

        # Draw the button
        # button_rect = QtCore.QRect(
        #     option.rect.right() - 80,  # Adjust position as needed
        #     option.rect.top() + 10,    # Adjust position as needed
        #     70, 30                      # Width and height of the button
        # )
        # painter.save()
        # painter.setPen(QtCore.Qt.NoPen)
        # painter.setBrush(QtCore.Qt.lightGray)  # Button color
        # painter.drawRoundedRect(button_rect, 5, 5)
        # painter.restore()

        # # Draw button text
        # painter.setFont(type_font)
        # painter.drawText(
        #     button_rect,
        #     QtCore.Qt.AlignCenter,
        #     "Enter"
        # )

    def sizeHint(self, option, index):
        return QtCore.QSize(100, 60)  # Adjust the desired width and height

    # def editorEvent(self, event, model, option, index):
    #     # Check if the event is a mouse button release
    #     if event.type() == QtCore.QEvent.MouseButtonRelease:
    #         # Define the button rect same as in the paint method
    #         button_rect = QtCore.QRect(
    #             option.rect.right() - 80,
    #             option.rect.top() + 10,
    #             70, 30
    #         )
    #         # Check if the click was within the button rect
    #         if button_rect.contains(event.pos()):
    #             # Handle button click here
    #             logger.debug("Button clicked for item:", index.row())
    #             return True  # Event was handled
    #     return super(WorkspaceListDelegate, self).editorEvent(event, model,
    #                                                           option, index)
