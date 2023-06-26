import requests
import json
import uuid
import os

class CustomAuthenticationError(Exception):
    pass

class CustomConnectionError(Exception):
    pass

class APIClient:
    def __init__(self, email, password, api_url, lens_url, access_token=None, user=None):
        self.base_url = api_url
        self.lens_url = lens_url

        if access_token == None:
            self.email = email
            self.password = password
            self.access_token = None
            self.user = None
        else:
            self.email = None
            self.password = None
            self.access_token = access_token
            self.user = user

    def authRequired(func):
        def wrapper(self, *args, **kwargs):
            if not self.access_token:
                self._authenticate()

            result = func(self, *args, **kwargs)

            return result

        return wrapper

    def _authenticate(self):
        endpoint = "authentication"

        payload = {
            "strategy": "local",
            "email": self.email,
            "password": self.password,
        }

        headers = {"Content-Type": "application/json"}
        try:
            data = self._post(endpoint, headers=headers, data=json.dumps(payload))
            self.access_token = data["accessToken"]
            self.user = data["user"]
        except requests.exceptions.RequestException as e:
            raise CustomConnectionError("Connection Error")

        except CustomAuthenticationError as e:
            raise CustomAuthenticationError("Authentication Error")

        except Exception as e:
            raise e


    def _delete(self, endpoint, headers={}, params=None):

        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Accept"] = "application/json"

        try:
            response = requests.delete(
                f"{self.base_url}/{endpoint}", params=params, headers=headers
            )
        except requests.exceptions.RequestException as e:
            # Handle connection error
            print(f"Connection Error: {e}")

        if response.status_code == 200:
            return response.json()
        else:
            # Handle API error cases
            callData = {
                "endpoint": endpoint,
                "headers": headers,
                "params": params,
            }
            self._dump_response(response, callData)
            raise Exception(
                f"API request failed with status code {response.status_code}"
            )

    def _request(self, endpoint, headers={}, params=None):

        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Accept"] = "application/json"
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=headers, params=params)
        except requests.exceptions.RequestException as e:
            # Handle connection error
            print(f"Connection Error: {e}")

        if response.status_code == 200:
            return response.json()
        else:
            callData = {
                "endpoint": endpoint,
                "headers": headers,
                "params": params,
            }
            self._dump_response(response, callData)
            raise Exception(
                f"API request failed with status code {response.status_code}"
            )

    def _post(self, endpoint, headers={}, params=None, data=None, files=None):

        if endpoint != "authentication":
            headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Accept"] = "application/json"
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}", headers=headers, data=data, files=files
            )
        except requests.exceptions.RequestException as e:
            # Handle connection error
            print(f"Connection Error: {e}")
            return

        if response.status_code in [201, 200]:
            return response.json()
        elif response.status_code == 401:
            raise CustomAuthenticationError("Not Authenticated")
        else:
            callData = {
                "endpoint": endpoint,
                "headers": headers,
                "data": data,
                "files": files,
            }
            self._dump_response(response, callData)
            raise Exception(
                f"API request failed with status code {response.status_code}"
            )

    def _update(self, endpoint, headers={}, data=None, files=None):

        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Accept"] = "application/json"

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, data=data, files=files
            )
        except requests.exceptions.RequestException as e:
            # Handle connection error
            print(f"Connection Error: {e}")

        if response.status_code in [201, 200]:
            return response.json()
        else:
            callData = {
                "endpoint": endpoint,
                "headers": headers,
                "data": data,
                "files": files,
            }
            self._dump_response(response, callData)
            raise Exception(
                f"API request failed with status code {response.status_code}"
            )

    def _download(self, url, filename):
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            # Handle connection error
            print(f"Connection Error: {e}")
            print(f"URL: {url}")
            print(f"Filename: {filename}")
            return None

        if response.status_code == 200:
            # Save file to workspace directory under the user name not the unique name
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            # Handle API error cases
            callData = {"url": url, "filename": filename}
            self._dump_response(response, callData)
            raise Exception(
                f"API request failed with status code {response.status_code}"
            )

    def _dump_response(self, response, callData):
        print("XXXXXX Call Data XXXXXX")
        for key, value in callData.items():
            print(key, value)
        print("XXXXXXXXXXXXXXXXXXXXXXX")

        print(response)
        print(f"Status code: {response.status_code}")

        # Access headers
        print(f"Content-Type: {response.headers['Content-Type']}")

        # Access response body as text
        print(f"Response body (text): {response.text}")

        if response.headers["Content-Type"] == "application/json":
            # Access response body as JSON
            print(f"Response body (JSON): {response.json()}")

    @authRequired
    def get_base_url(self):
        return self.lens_url

    # User/Authentication fuctions

    @authRequired
    def get_user(self):
        return self.user

    @authRequired
    def logout(self):

        endpoint = "authentication"
        result = self._delete(endpoint)
        return result

    # Model Functions

    @authRequired
    def getModels(self, params=None):

        paginationparams = {"$limit": 50, "$skip": 0, "isSharedModel": "false"}

        endpoint = "models"
        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}

        result = self._request(endpoint, params=params)
        files = result["data"]

        return files

    @authRequired
    def getModel(self, modelId):
        endpoint = f"models/{modelId}"

        result = self._request(endpoint)
        return result

    @authRequired
    def createModel(self, fileName, fileUpdatedAt, uniqueName):
        print("Creating the model...")
        endpoint = "models"

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "custFileName": fileName,
            "uniqueFileName": uniqueName,
            "shouldStartObjGeneration": True,
            "errorMsg": "",
            "fileUpdatedAt" : fileUpdatedAt
        }

        result = self._post(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def regenerateModelObj(self, fileId, fileUpdatedAt, uniqueFileName):
        print(f"Regenerating the model OBJ... {fileUpdatedAt}")
        endpoint = f"models/{fileId}"

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "uniqueFileName": uniqueFileName,
            "shouldStartObjGeneration": True,
            "fileUpdatedAt" : fileUpdatedAt
        }

        result = self._update(endpoint, headers=headers, data=json.dumps(payload))

    @authRequired
    def deleteModel(self, _id):
        endpoint = f"/models/{_id}"

        result = self._delete(endpoint)
        return result

    #  Upload Functions

    @authRequired
    def uploadFileToServer(self, uniqueName, filename):
        print(filename)
        # files to be uploaded needs to have a unique name generated with uuid (use str(uuid.uuid4()) ) : test.fcstd -> c4481734-c18f-4b8c-8867-9694ae2a9f5a.fcstd
        endpoint = "upload"

        if not os.path.isfile(filename):
            raise FileNotFoundError

        with open(filename, "rb") as f:
            fileWithUniqueName = (
                uniqueName,
                f,
                "application/octet-stream",
            )

            files = {"file": fileWithUniqueName}
            result = self._post(endpoint, files=files)
            return result


    @authRequired
    def downloadFileFromServer(self, uniqueName, filename):
        endpoint = f"/upload/{uniqueName}"
        print(filename)

        response = self._request(endpoint)
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)
        print(response)

        self._download(response["url"], filename)

    # Shared Model Functions

    @authRequired
    def getSharedModels(self, params=None):
        endpoint = "shared-models"

        headers = {
            "Content-Type": "application/json",
        }

        paginationparams = {"$limit": 50, "$skip": 0}

        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}

        result = self._request(endpoint, headers, params)
        return result["data"]

    @authRequired
    def createSharedModel(self, params):
        endpoint = "shared-models"

        headers = {
            "Content-Type": "application/json",
        }

        result = self._post(endpoint, headers, data=json.dumps(params))
        return result

    @authRequired
    def getSharedModel(self, shareID):
        endpoint = f"shared-models/{shareID}"

        result = self._request(endpoint)
        return result

    @authRequired
    def updateSharedModel(self, fileData):
        endpoint = f"shared-models/{fileData['_id']}"
        headers = {
            "Content-Type": "application/json",
        }

        result = self._update(endpoint, headers=headers, data=json.dumps(fileData))

        return result

    @authRequired
    def deleteSharedModel(self, ShareModelID):
        endpoint = f"shared-models/{ShareModelID}"

        result = self._delete(endpoint)
        return result


class APIHelper:
    def __init__(self):
        pass

    @staticmethod
    def getFilter(objName):

        if objName == "models":
            return {
                "$limit": None,
                "$skip": None,
                "_id": None,
                "userId": None,
                "custFileName": None,
                "uniqueFileName": None,
                "createdAt": None,
                "updatedAt": None,
                "isSharedModel": None,
                "sharedModelId": None,
                "isSharedModelAnonymousType": None,
            }
        elif objName == "shared-Mode":
            return {
                "$limit": None,
                "$skip": None,
                "_id": None,
                "userId": None,
                "cloneModelId": None,
                "isActive": None,
                "deleted": None,
            }

    @staticmethod
    def filterFilter(data):

        if isinstance(data, dict):
            return {
                key: APIHelper.filterFilter(value)
                for key, value in data.items()
                if value is not None and APIHelper.filterFilter(value)
            }
        elif isinstance(data, list):
            return [
                APIHelper.filterFilter(item)
                for item in data
                if item is not None and APIHelper.filterFilter(item)
            ]
        else:
            return data
