# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

from DataModels import ShareLinkModel, VersionModel

from PySide.QtCore import Qt

if __name__ == "__main__":
    # Test the ShareLinkModel
    # Create a test dataset
    data = [
        {
            "shortName": "FirstShareLink",
            "url": "https://example.com/v1",
            "created": "2023-01-01",
            "active": True,
        },
        {
            "shortName": "SecondShareLink",
            "url": "https://example.com/v2",
            "created": "2023-02-01",
            "active": False,
        },
        {
            "shortName": "ThirdShareLink",
            "url": "https://example.com/v3",
            "created": "2023-03-01",
            "active": True,
        },
    ]
    # Create the model
    model = ShareLinkModel(data)

    # Verify the model's data
    for row in range(model.rowCount()):
        for column in range(model.columnCount(None)):
            index = model.index(row, column)
            item_data = model.data(index, Qt.DisplayRole)
            print(f"Data at [{row}, {column}]: {data}")

    # Add a new link
    new_link_data = {
        "shortName": "Fourth",
        "url": "https://example.com/v4",
        "created": "2023-04-01",
        "active": False,
    }

    if model.addLink(new_link_data):
        print("New link added successfully.")
    else:
        print("Failed to add new link.")

    # Update an existing link
    updated_link_data = {
        "shortName": "RenamedShortname",
        "url": "https://example.com/v2.1",
        "created": "2023-02-15",
        "active": True,
    }

    if model.updateLink(model.index(1, 0), updated_link_data):
        print("link updated successfully.")
    else:
        print("Failed to update link.")

    # Test the VersionModel
    # Create a test dataset
    data = [
        {
            "created": "2023-01-01",
            "uniqueName": "xczvmnxoiweurlsdkja3247",
        },
        {
            "created": "2023-02-01",
            "uniqueName": "wouencx,nvowodkjf",
        },
        {
            "created": "2023-03-01",
            "uniqueName": "adkjdlskajlskfsj",
        },
    ]
    # Create the model
    model = VersionModel(data)

    # Verify the model's data
    for row in range(model.rowCount()):
        for column in range(model.columnCount(None)):
            index = model.index(row, column)
            item_data = model.data(index, Qt.DisplayRole)
            print(f"Data at [{row}, {column}]: {data}")

    # Add a new version
    new_version_data = {"created": "2023-04-01", "uniqueName": "aldjfljdlskjdsflkjf"}

    if model.addVersion(new_version_data):
        print("New version added successfully.")
    else:
        print("Failed to add new version.")
