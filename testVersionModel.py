import unittest
from PySide2.QtCore import Qt
from VersionModel import LocalVersionModel, OndselVersionModel
import pprint
import shutil
import os
import time
import FreeCAD as App


class TestLocalVersionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.mkdir("test_dir")
        pg = App.ParamGet("User parameter:BaseApp/Preferences/Document")

        cls.backupcount = pg.GetInt("CountBackupFiles")
        pg.SetInt("CountBackupFiles", 3)

        cls.create_file("test_dir/file1.FCStd")
        cls.filename = "test_dir/file1.FCStd"
        cls.model = LocalVersionModel(cls.filename)

    @classmethod
    def tearDownClass(cls):
        # Remove the test directory and all its contents
        shutil.rmtree("test_dir")

        pg = App.ParamGet("User parameter:BaseApp/Preferences/Document")
        pg.SetInt("CountBackupFiles", cls.backupcount)

    @classmethod
    def create_file(self, file_path):
        doc = App.newDocument()
        doc.saveAs(file_path)
        doc.saveAs(file_path)
        doc.saveAs(file_path)
        App.closeDocument(doc.Name)
        time.sleep(1)

    def test_00_initial_state(self):
        pprint.pprint(self.model.dump())
        self.assertEqual(self.model.rowCount(), 2)
        self.assertEqual(self.model.columnCount(None), 2)

    def test_10_add_version(self):
        doc = App.openDocument(self.filename)
        doc.save()
        doc.save()
        time.sleep(1)
        self.assertEqual(self.model.rowCount(), 3)

class TestOndselVersionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        modelID = 9999
        cls.model = OndselVersionModel(modelID)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_00_initial_state(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
