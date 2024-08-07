import zipfile
import xml.etree.ElementTree as ET


class FreeCADFileException(Exception):
    """An exception that indicates problems reading a FreeCAD file."""


def find_paths_links_xml(xml_content):
    """Find the paths of (missing) links in XML content."""

    root = ET.fromstring(xml_content)
    paths_links = []
    for prop in root.findall(".//Property[@name='LinkedObject']/XLink"):
        file_path = prop.get("file")
        if file_path:
            paths_links.append(file_path)
    return paths_links


def find_paths_links_file(file_path):
    """Find the paths of (missing) links in a FreeCAD file."""

    if not zipfile.is_zipfile(file_path):
        raise FreeCADFileException(f"File {file_path} is not a valid FreeCAD file.")

    with zipfile.ZipFile(file_path, "r") as z:
        if "Document.xml" not in z.namelist():
            raise FreeCADFileException("Document.xml is not present")

        with z.open("Document.xml") as f:
            xml_content = f.read().decode("utf-8")
            return find_paths_links_xml(xml_content)
