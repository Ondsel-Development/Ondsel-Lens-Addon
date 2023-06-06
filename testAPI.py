from APIClient import APIClient
import unittest
import tempfile
import os
import config  # .gitignored file containing credentials


class APIClientTest(unittest.TestCase):
    def setUp(self):

        self.base_url = config.base_url
        self.username = config.username
        self.password = config.password
        self.access_token = None
        self.api_client = APIClient(self.base_url, self.username, self.password)

    def test_10(self):
        user = self.api_client.get_user()
        self.assertTrue(user["email"] == self.username)
        keys = ["_id", "email", "firstName", "lastName", "createdAt", "updatedAt"]
        for key in keys:
            self.assertIn(key, user.keys())

    def test_15(self):
        result = self.api_client.logout()
        # self.assertIsNone(result)
        # Need to figure out what we can assert about being logged out

    def test_20(self):

        remoteFiles = self.api_client.getModels()
        model = remoteFiles[0]

        keys = [
            "_id",
            "custFileName",
            "uniqueFileName",
            "shouldStartObjGeneration",
            "errorMsg",
            "userId",
            "createdAt",
            "updatedAt",
            "isObjGenerationInProgress",
            "isObjGenerated",
            "isSharedModel",
            "attributes",
            "objUrl",
            "thumbnailUrl",
        ]

        for key in keys:
            self.assertIn(key, model.keys())

    def test_40(self):

        # ModelFunctions

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
        result = self.api_client.uploadFileToServer(fileData, url)

        fileData["uniqueFileName"] = result["uniqueFileName"]

        # Test creating a model on the server
        model = self.api_client.createModel(fileData)
        modelID = model["_id"]
        self.assertIsInstance(modelID, str)

        # Test fetching the model back
        model = self.api_client.getModel(modelID)

        keys = [
            "_id",
            "custFileName",
            "uniqueFileName",
            "shouldStartObjGeneration",
            "errorMsg",
            "userId",
            "createdAt",
            "updatedAt",
            "isObjGenerationInProgress",
            "isObjGenerated",
            "isSharedModel",
            "isSharedModelAnonymousType",
            "objUrl",
            "thumbnailUrl",
        ]

        for key in keys:
            self.assertIn(key, model.keys())

        # Test Regenerating the model
        result = self.api_client.regenerateModelObj(model)

        # test downloading a file
        temp_dir = tempfile.gettempdir()
        fname = os.path.join(temp_dir, fileData["custFileName"])

        result = self.api_client.downloadFileFromServer(result["uniqueFileName"], fname)

        self.assertTrue(os.path.isfile(fname))

        # Test Deleting the model
        #result = self.api_client.deleteModel(model["_id"])

    def test_50(self):
        # Share Functions

        #         # test getting shares
        result = self.api_client.getSharedModels()
        self.assertIsInstance(len(result), int)

        # test getting just one
        share = result[-1]
        shareID = share["_id"]
        result = self.api_client.getSharedModel(shareID)
        # pprint(result)

        keys = [
            "_id",
            "canExportFCStd",
            "canExportOBJ",
            "canExportSTEP",
            "canExportSTL",
            "canUpdateModel",
            "canViewModel",
            "canViewModelAttributes",
            "cloneModelId",
            "createdAt",
            "description",
            "dummyModelId",
            "isActive",
        ]

        for key in keys:
            self.assertIn(key, result.keys())

    # test creating a share

        result = self.api_client.getModels()
        model = result[0]

        shares = self.api_client.getSharedModels(model["_id"])
        self.assertIsInstance(len(shares), int)

        linkprops = {
            "cloneModelId": model["_id"],
            "description": "testcase junk",
            "canViewModel": True,
            "canViewModelAttributes": False,
            "canUpdateModel": False,
            "canExportFCStd": True,
            "canExportSTEP": False,
            "canExportSTL": False,
            "canExportOBJ": True,
            "canDownloadDefaultModel": False,
            "dummyModelId": "",
        }

        result = self.api_client.createSharedModel(linkprops)
        print(result)

        shareID = result["_id"]

    # result = self.api_client.getSharedModels()
    # self.assertIsInstance(len(result), int)

         # test deleting a share
        result = self.api_client.deleteSharedModel(shareID)

    def test_100(self):

        user = self.api_client.get_user()
        props = {"userId": user["_id"]}

        result = self.api_client.getSharedModels(params=props)
        print(len(result))

        for s in result:
            self.api_client.deleteSharedModel(s["_id"])

        models = self.api_client.getModels(params=props)
        print(len(models))
        for model in models:
            print(model["custFileName"])
            result = self.api_client.deleteModel(model["_id"])


if __name__ == "__main__":
    unittest.main()
