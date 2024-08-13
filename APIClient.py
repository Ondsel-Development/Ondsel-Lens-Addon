from enum import Enum
import os

import requests
import json
import urllib

import Utils
from models.curation import Curation

logger = Utils.getLogger(__name__)


class APIClientException(Exception):
    pass


class APIClientAuthenticationException(APIClientException):
    pass


class APIClientConnectionError(APIClientException):
    pass


class APIClientRequestException(APIClientException):
    pass


class ConnStatus(Enum):
    LOGGED_OUT = 1  # no connection, user logged out
    CONNECTED = 2  # connection, user logged in
    DISCONNECTED = 3  # no connection, user logged in


OK = requests.codes.ok
CREATED = requests.codes.created
UNAUTHORIZED = requests.codes.unauthorized


class APIClient:
    def __init__(
        self,
        email,
        password,
        api_url,
        lens_url,
        source,
        version,
        access_token=None,
        user=None,
    ):
        self.base_url = api_url
        self.lens_url = lens_url
        self.source = source
        self.version = version

        if access_token is None:
            self.email = email
            self.password = password
            self.access_token = None
            self.user = None
            self.status = ConnStatus.LOGGED_OUT
        else:
            self.email = None
            self.password = None
            self.access_token = access_token
            self.user = user
            self.status = ConnStatus.CONNECTED

    def getNameUser(self):
        if self.user and "name" in self.user:
            return self.user["name"]

        return ""

    def logout(self):
        self.email = None
        self.password = None
        self.access_token = None
        self.user = None
        self.status = ConnStatus.LOGGED_OUT

    def is_logged_in(self):
        """Whether a user is logged in.

        The user may be disconnected."""
        return self.access_token is not None and self.user is not None

    def disconnect(self):
        self.status = ConnStatus.DISCONNECTED

    def is_connected(self):
        """Whether a user is connected.

        This implies that the user is logged in."""
        return self.is_logged_in() and self.status == ConnStatus.CONNECTED

    def authRequired(func):
        def wrapper(self, *args, **kwargs):
            if not self.access_token:
                self.authenticate()

            result = func(self, *args, **kwargs)

            return result

        return wrapper

    def authenticate(self):
        endpoint = "authentication"

        payload = {
            "strategy": "local",
            "email": self.email,
            "password": self.password,
        }

        headers = self._set_content_type()
        data = self._post(endpoint, headers=headers, data=json.dumps(payload))
        self.access_token = data["accessToken"]
        self.user = data["user"]
        self.status = ConnStatus.CONNECTED

    def _raiseException(self, response, **kwargs):
        "Raise a generic exception based on the status code"
        # dumps only when debugging is enabled
        self._dump_response(response, **kwargs)
        raise APIClientRequestException(
            f"API request failed with status code {response.status_code}: "
            + response.json()["message"]
        )

    def _set_default_headers(self, headers):
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Accept"] = "application/json"
        headers["X-Lens-Source"] = self.source
        headers["X-Lens-Version"] = self.version

        return headers

    def _set_content_type(self):
        headers = {"Content-Type": "application/json"}
        return headers

    def _delete(self, endpoint, headers={}, params=None):
        headers = self._set_default_headers(headers)

        try:
            response = requests.delete(
                f"{self.base_url}/{endpoint}", params=params, headers=headers
            )
        except requests.exceptions.RequestException as e:
            raise APIClientConnectionError(e)

        if response.status_code == OK:
            self.status = ConnStatus.CONNECTED
            return response.json()
        else:
            self._raiseException(
                response, endpoint=endpoint, headers=headers, params=params
            )

    def _request(self, endpoint, headers={}, params=None):
        headers = self._set_default_headers(headers)
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=headers, params=params
            )
        except requests.exceptions.RequestException as e:
            raise APIClientConnectionError(e)

        if response.status_code == OK:
            self.status = ConnStatus.CONNECTED
            return response.json()
        elif response.status_code == UNAUTHORIZED:
            raise APIClientAuthenticationException("Not authenticated")
        else:
            self._raiseException(
                response, endpoint=endpoint, headers=headers, params=params
            )

    def _post(self, endpoint, headers={}, params=None, data=None, files=None):
        headers = self._set_default_headers(headers)
        if endpoint == "authentication":
            headers.pop("Authorization")
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}", headers=headers, data=data, files=files
            )
        except requests.exceptions.RequestException as e:
            raise APIClientConnectionError(e)

        # only _post makes a distinction between the general error and
        # unauthorized because _authenticate makes use of post and unauthorized
        # should be handled differently for the _authenticate function (for
        # example give the user another try to log in).
        if response.status_code in [CREATED, OK]:
            self.status = ConnStatus.CONNECTED
            return response.json()
        elif response.status_code == UNAUTHORIZED:
            raise APIClientAuthenticationException("Not authenticated")
        else:
            self._raiseException(
                response, endpoint=endpoint, headers=headers, data=data, files=files
            )

    def _update(self, endpoint, headers={}, data=None, files=None):
        headers = self._set_default_headers(headers)

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, data=data, files=files
            )
        except requests.exceptions.RequestException as e:
            raise APIClientConnectionError(e)

        if response.status_code in [CREATED, OK]:
            self.status = ConnStatus.CONNECTED
            return response.json()
        else:
            self._raiseException(
                response, endpoint=endpoint, headers=headers, data=data, files=files
            )

    def _download(self, url, filename):
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            raise APIClientException(e)

        if response.status_code == OK:
            # Save file to workspace directory under the user name not the unique name
            with open(filename, "wb") as f:
                f.write(response.content)
            self.status = ConnStatus.CONNECTED
            return True
        else:
            self._raiseException(response, url=url, filename=filename)

    def _dump_response(self, response, **kwargs):
        # # make a dictionary out of the keyword arguments
        # callData = {f"{k}": v for k, v in kwargs.items}
        logger.debug("XXXXXX Call Data XXXXXX")
        for key, value in kwargs.items():
            logger.debug(f"{key} {value}")
        logger.debug("XXXXXXXXXXXXXXXXXXXXXXX")

        logger.debug(response)
        logger.debug(f"Status code: {response.status_code}")

        # Access headers
        logger.debug(f"Content-Type: {response.headers['Content-Type']}")

        # Access response body as text
        logger.debug(f"Response body (text): {response.text}")

        if response.headers["Content-Type"].startswith("application/json"):
            # Access response body as JSON
            logger.debug(f"Response body (JSON): {response.json()}")

    @authRequired
    def get_base_url(self):
        return self.lens_url

    # User/Authentication fuctions

    @authRequired
    def get_user(self):
        return self.user

    # @authRequired
    # def logout(self):
    #     endpoint = "authentication"
    #     result = self._delete(endpoint)
    #     return result

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
        models = result["data"]

        return models

    @authRequired
    def getModel(self, modelId):
        endpoint = f"models/{modelId}"

        result = self._request(endpoint)
        return result

    @authRequired
    def createModel(self, fileId):
        logger.debug("Creating the model...")
        endpoint = "models"

        headers = self._set_content_type()
        payload = {
            "fileId": fileId,
            "shouldStartObjGeneration": True,
            "createSystemGeneratedShareLink": False,
        }

        result = self._post(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def regenerateModelObj(self, modelId, fileId):
        logger.debug("Regenerating the model OBJ... ")
        endpoint = f"models/{modelId}"

        headers = self._set_content_type()
        payload = {
            # "shouldCommitNewVersion": True,
            "fileId": fileId,
            "shouldStartObjGeneration": True,
            # "createSystemGeneratedShareLink": False,
        }

        result = self._update(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def deleteModel(self, _id):
        endpoint = f"/models/{_id}"

        result = self._delete(endpoint)
        return result

    # File Objects functions

    @authRequired
    def getFiles(self, params=None):
        paginationparams = {"$limit": 50, "$skip": 0, "isSystemGenerated": "false"}
        endpoint = "file"
        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}

        result = self._request(endpoint, params=params)
        files = result["data"]

        return files

    @authRequired
    def createFile(self, fileName, fileUpdatedAt, uniqueName, directory, workspace):
        logger.debug(f"Creating file {fileName} in dir {directory}")
        endpoint = "file"

        headers = self._set_content_type()
        payload = {
            "custFileName": fileName,
            "shouldCommitNewVersion": True,
            "version": {
                "uniqueFileName": uniqueName,
                # "message": "Initial commit from the Ondsel Lens addon",
                "message": "Initial commit",
                "fileUpdatedAt": fileUpdatedAt,
            },
            "directory": directory,
            "workspace": workspace,
        }

        result = self._post(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def updateFileObj(
        self, fileId, fileUpdatedAt, uniqueFileName, directory, workspace, message
    ):
        logger.debug(f"updatingFileObj {fileId} in dir {directory}")
        endpoint = f"file/{fileId}"

        headers = self._set_content_type()
        payload = {
            "shouldCommitNewVersion": True,
            "version": {
                "uniqueFileName": uniqueFileName,
                "fileUpdatedAt": fileUpdatedAt,
                "message": message,
            },
            "directory": directory,
            "workspace": workspace,
        }

        result = self._update(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def setVersionActive(self, fileId, versionId):
        logger.debug("setVersionActive")
        endpoint = f"file/{fileId}"

        headers = self._set_content_type()
        payload = {
            "shouldCheckoutToVersion": True,
            "versionId": versionId,
        }

        result = self._update(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def deleteFile(self, fileId):
        endpoint = f"file/{fileId}"

        result = self._delete(endpoint)
        return result

    #  Upload Functions

    @authRequired
    def uploadFileToServer(self, uniqueName, filename):
        logger.debug(f"upload: {filename}")
        # files to be uploaded need to have a unique name generated with uuid
        # (use str(uuid.uuid4()) ) : test.fcstd ->
        # c4481734-c18f-4b8c-8867-9694ae2a9f5a.fcstd
        # Note that this is not a hash but a random identifier.
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
    def downloadFileFromServer(self, uniqueFileName, pathFile):
        endpoint = f"/upload/{uniqueFileName}"

        response = self._request(endpoint)
        directory = os.path.dirname(pathFile)
        os.makedirs(directory, exist_ok=True)

        return self._download(response["url"], pathFile)

    @authRequired
    def downloadObjectFileFromServer(self, objUrl, pathFile):
        directory = os.path.dirname(pathFile)
        os.makedirs(directory, exist_ok=True)

        return self._download(objUrl, pathFile)

    # Shared Model Functions

    @authRequired
    def getSharedModels(self, params=None):
        endpoint = "shared-models"

        headers = self._set_content_type()
        paginationparams = {"$limit": 50, "$skip": 0}

        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}
        if "pin" in params:
            if params["pin"] == "":
                del params["pin"]

        result = self._request(endpoint, headers, params)
        return result["data"]

    @authRequired
    def createSharedModel(self, params):
        endpoint = "shared-models"

        headers = self._set_content_type()
        result = self._post(endpoint, headers, data=json.dumps(params))
        return result

    @authRequired
    def getSharedModel(self, shareID):
        endpoint = f"shared-models/{shareID}"

        result = self._request(endpoint)
        return result

    @authRequired
    def updateSharedModel(self, sharedModelData):
        endpoint = f"shared-models/{sharedModelData['_id']}"
        if "pin" in sharedModelData:
            if sharedModelData["pin"] == "":
                del sharedModelData["pin"]
        if "dummyModelId" in sharedModelData:
            if sharedModelData["dummyModelId"] is None:
                del sharedModelData["dummyModelId"]
        if "isSystemGenerated" in sharedModelData:
            if sharedModelData["isSystemGenerated"]:
                del sharedModelData["isActive"]
            del sharedModelData["isSystemGenerated"]

        headers = self._set_content_type()
        result = self._update(
            endpoint, headers=headers, data=json.dumps(sharedModelData)
        )

        return result

    @authRequired
    def deleteSharedModel(self, ShareModelID):
        endpoint = f"shared-models/{ShareModelID}"

        result = self._delete(endpoint)
        return result

    # Workspace functions.
    @authRequired
    def getWorkspaces(self, params=None):
        paginationparams = {"$limit": 50, "$skip": 0}
        endpoint = "workspaces"
        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}

        result = self._request(endpoint, params=params)
        workspaces = result["data"]

        return workspaces

    @authRequired
    def getWorkspace(self, workspaceID):
        endpoint = f"workspaces/{workspaceID}"

        result = self._request(endpoint)
        return result

    @authRequired
    def createWorkspace(self, name, description, organizationId):
        logger.debug("Creating the workspace...")
        endpoint = "workspaces"

        headers = self._set_content_type()
        payload = {
            "name": name,
            "description": description,
            "organizationId": organizationId,
        }

        result = self._post(endpoint, headers=headers, data=json.dumps(payload))

        return result

    @authRequired
    def updateWorkspace(self, workspaceData):
        endpoint = f"workspaces/{workspaceData['_id']}"

        headers = self._set_content_type()
        result = self._update(endpoint, headers=headers, data=json.dumps(workspaceData))

        return result

    @authRequired
    def deleteWorkspace(self, WorkspaceID):
        endpoint = f"workspaces/{WorkspaceID}"

        result = self._delete(endpoint)
        return result

    # Directory Functions
    @authRequired
    def getDirectories(self, params=None):
        paginationparams = {"$limit": 50, "$skip": 0}
        endpoint = "directories"
        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}

        result = self._request(endpoint, params=params)
        directories = result["data"]

        return directories

    @authRequired
    def getDirectory(self, directoryID):
        endpoint = f"directories/{directoryID}"

        result = self._request(endpoint)
        return result

    @authRequired
    def createDirectory(self, name, idParentDir, nameParentDir, workspace):
        logger.debug("Creating the directory...")
        endpoint = "directories"

        headers = self._set_content_type()
        payload = {
            "name": name,
            "workspace": workspace,
            "parentDirectory": {
                "_id": idParentDir,
                "name": nameParentDir,
            },
        }

        return self._post(endpoint, headers=headers, data=json.dumps(payload))

    @authRequired
    def updateDirectory(self, directoryData):
        endpoint = f"directories/{directoryData['_id']}"

        headers = self._set_content_type()
        result = self._update(endpoint, headers=headers, data=json.dumps(directoryData))

        return result

    @authRequired
    def deleteDirectory(self, directoryID):
        endpoint = f"directories/{directoryID}"

        result = self._delete(endpoint)
        return result

    @authRequired
    def uploadPrefs(
        self,
        orgId,
        uniqueFileNameUserConfig,
        fileNameUserConfig,
        uniqueFileNameSystemConfig,
        fileNameSystemConfig,
    ):
        endpoint = "preferences"

        orgData = self.getOrganization(orgId)

        prefId = orgData.get("preferencesId")

        if prefId:
            endpoint = f"preferences/{prefId}"
            payloadHeader = "shouldCommitNewVersion"
            payloadHeaderValue = True
            message = "Update preferences"
        else:
            endpoint = "preferences"
            payloadHeader = "organizationId"
            payloadHeaderValue = orgId
            message = "Initial commit perferences"

        headers = self._set_content_type()
        payload = {
            payloadHeader: payloadHeaderValue,
            "version": {
                "files": [
                    {
                        "fileName": fileNameUserConfig,
                        "uniqueFileName": uniqueFileNameUserConfig,
                        "additionalData": {
                            "message": message,
                        },
                        "additionalKeysToSave": {},
                    },
                    {
                        "fileName": fileNameSystemConfig,
                        "uniqueFileName": uniqueFileNameSystemConfig,
                        "additionalData": {},
                        "additionalKeysToSave": {},
                    },
                ],
            },
        }

        if prefId:
            return self._update(endpoint, headers=headers, data=json.dumps(payload))
        else:
            return self._post(endpoint, headers=headers, data=json.dumps(payload))

    @authRequired
    def getOrganization(self, orgId):
        endpoint = f"organizations/{orgId}"

        return self._request(endpoint)

    @authRequired
    def downloadPrefs(self, prefId):
        if prefId:
            endpoint = f"preferences/{prefId}"
            return self._request(endpoint)
        else:
            return None

    @authRequired
    def getOrganizations(self, params=None):
        paginationparams = {"$limit": 50, "$skip": 0}
        endpoint = "organizations"
        if params is None:
            params = paginationparams
        else:
            params = {**params, **paginationparams}

        result = self._request(endpoint, params=params)
        organizations = result["data"]

        return organizations

    @authRequired
    def getSecondaryRefs(self, orgSecondaryReferencesId):
        endpoint = f"org-secondary-references/{orgSecondaryReferencesId}"

        result = self._request(endpoint)
        return result

    def get_search_results(self, search_text, target=None):
        params = {"text": urllib.parse.quote_plus(search_text)}
        if target is not None:
            params["target"] = target
        result = self._request("keywords", params=params)
        data = result["data"]
        scored_items = data[0]["sortedMatches"]
        curations = []
        for item in scored_items:
            new_curation = Curation.from_json(item["curation"])
            curations.append(new_curation)
        return curations


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
