# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import unittest
from PySide2.QtCore import Qt
from LinkModel import ShareLinkModel
from APIClient import APIClient
import pprint
import os
import time
import config

"""
These unittests are currently hitting the server.
Useful for developing but really should be rewritten to mock the server response
and only test the data model.

Also, an assert here and there wouldn't hurt.
"""


class TestLinkModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = config.base_url
        cls.lens_url = config.lens_url
        cls.username = config.username
        cls.password = config.password
        cls.access_token = None
        cls.api_client = APIClient(
            cls.username, cls.password, cls.base_url, cls.lens_url
        )

        testfile = "testshape.FCStd"

        url, basename = os.path.split(testfile)

        created_time = os.path.getctime(testfile)
        modified_time = os.path.getmtime(testfile)

        fileData = {
            "custFileName": basename,
            "isFolder": False,
            "versions": [basename],
            "currentVersion": basename,
            "createdAt": created_time,
            "updatedAt": modified_time,
            "status": "Untracked",
            "shouldStartObjGeneration": True,
        }
        result = cls.api_client.uploadFileToServer(fileData, url)

        fileData["uniqueFileName"] = result["uniqueFileName"]

        # Test creating a model on the server
        model = cls.api_client.createModel(fileData)
        cls.modelID = model["_id"]

    @classmethod
    def tearDownClass(cls):
        pass
        # result = cls.api_client.deleteModel(cls.modelID)

    def setUp(self):
        self.base_url = config.base_url
        self.username = config.username
        self.password = config.password
        self.access_token = None

    def tearDown(self):
        pass

    def test_00(self):
        # test initial state

        sharemodel = ShareLinkModel(self.modelID, self.api_client)

        self.assertTrue(sharemodel.rowCount() == 0)
        sharemodel.dump()

    def test_10(self):
        # create a share link data model.
        sharemodel = ShareLinkModel(self.modelID, self.api_client)

        link = {
            "cloneModelId": self.modelID,
            "description": "test link",
            "canViewModel": True,
            "canViewModelAttributes": False,
            "canUpdateModel": False,
            "canExportFCStd": False,
            "canExportSTEP": False,
            "canExportSTL": False,
            "canExportOBJ": False,
            "dummyModelId": "",  # self.modelID,
            "canDownloadDefaultModel": True,
        }

        # create a share link
        result = sharemodel.add_new_link(link)
        print(sharemodel.rowCount())
        self.assertTrue(sharemodel.rowCount() == 1)

        # delete the link
        result = sharemodel.delete_link(result["_id"])
        self.assertTrue(sharemodel.rowCount() == 0)

    def test_20(self):
        # test update.
        pass


if __name__ == "__main__":
    unittest.main()
