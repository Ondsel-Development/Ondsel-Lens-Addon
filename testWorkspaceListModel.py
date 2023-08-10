# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************
import unittest
from unittest.mock import patch, MagicMock
from PySide2.QtCore import Qt, QModelIndex
from DataModels import WorkspaceListModel
import os


class TestWorkspaceListModel(unittest.TestCase):
    def setUp(self):
        self.model = WorkspaceListModel(filename="junk.json")

    def tearDown(self):
        # Delete the workspaceListFile after running the tests
        if os.path.exists("junk.json"):
            os.remove("junk.json")

    def test_rowCount(self):
        # Test initial row count
        self.assertEqual(self.model.rowCount(), 0)

        # Test row count after adding workspaces
        self.model.addWorkspace("Workspace 1", "Description 1", "local", "url1")
        self.assertEqual(self.model.rowCount(), 1)

    def test_data(self):
        # Test data retrieval
        self.model.addWorkspace("Workspace 1", "Description 1", "local", "url1")
        index = self.model.index(0)
        data = self.model.data(index, Qt.DisplayRole)
        expected_data = {
            "name": "Workspace 1",
            "description": "Description 1",
            "type": "local",
            "url": "url1",
        }
        self.assertEqual(data, expected_data)

    def test_updateData(self):
        # Test updating data
        workspaces = [
            {
                "name": "Workspace 1",
                "description": "Description 1",
                "type": "local",
                "url": "url1",
            },
            {
                "name": "Workspace 2",
                "description": "Description 2",
                "type": "local",
                "url": "url2",
            },
        ]
        self.model.updateData(workspaces)
        self.assertEqual(self.model.rowCount(), 2)


if __name__ == "__main__":
    unittest.main()
