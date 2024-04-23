# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import unittest
from PySide.QtCore import Qt, QModelIndex
from DataModels import FileListModel


class TestFileListModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Run once before all tests
        cls.files = [
            {
                "_id": "r45zef415zef1515",
                "custFileName": "part1.fcstd",
                "uniqueFileName": "23ef23e-f23zefe-23zz-ef123.fcstd",
                "created": "2023-01-01",
                "localUrl": "something/something/",
                "isFolder": True,
                "versions": [
                    "part1.fcstd",
                    "part1-01012023-154023.fcbak",
                    "part1-01022023-101021.fcbak",
                ],
                "currentVersion": "part1.fcstd",
            },
        ]

    @classmethod
    def tearDownClass(cls):
        # Run once after all tests
        pass

    def setUp(self):
        # Run before each test
        self.model = FileListModel(self.files)

    def tearDown(self):
        # Run after each test
        pass

    def test_rowCount(self):
        # Test initial row count
        self.assertEqual(self.model.rowCount(), 1)

        # Test row count after updating data
        files = [
            {
                "_id": "r45zef415zef1515",
                "custFileName": "part1.fcstd",
                "uniqueFileName": "23ef23e-f23zefe-23zz-ef123.fcstd",
                "created": "2023-01-01",
                "localUrl": "something/something/",
                "isFolder": True,
                "versions": [
                    "part1.fcstd",
                    "part1-01012023-154023.fcbak",
                    "part1-01022023-101021.fcbak",
                ],
                "currentVersion": "part1.fcstd",
            },
            {
                "_id": "abc123",
                "custFileName": "part2.fcstd",
                "uniqueFileName": "xyz789",
                "created": "2023-01-02",
                "localUrl": "something/something/else/",
                "isFolder": False,
                "versions": ["part2.fcstd", "part2-01012023-154023.fcbak"],
                "currentVersion": "part2.fcstd",
            },
        ]
        self.model.updateData(files)
        self.assertEqual(self.model.rowCount(), 2)

    def test_data(self):
        # Test data retrieval
        index = self.model.index(0)
        data = self.model.data(index, Qt.DisplayRole)
        expected_data = {
            "_id": "r45zef415zef1515",
            "custFileName": "part1.fcstd",
            "uniqueFileName": "23ef23e-f23zefe-23zz-ef123.fcstd",
            "created": "2023-01-01",
            "localUrl": "something/something/",
            "isFolder": True,
            "versions": [
                "part1.fcstd",
                "part1-01012023-154023.fcbak",
                "part1-01022023-101021.fcbak",
            ],
            "currentVersion": "part1.fcstd",
        }
        self.assertEqual(data, expected_data)

    # Add more tests for other methods if needed


if __name__ == "__main__":
    unittest.main()
