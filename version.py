# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

import re
from datetime import datetime
import sys


def increment_version(version):
    version_parts = version.split(".")
    if len(version_parts) == 4:
        try:
            year, month, day, sequence_number = map(int, version_parts)
            today = datetime.today()
            if year == today.year and month == today.month and day == today.day:
                sequence_number += 1
            else:
                sequence_number = 1
            new_version = (
                f"{today.year:04d}.{today.month:02d}.{today.day:02d}"
                f".{sequence_number:02d}"
            )
            return new_version, f"{today.year}-{today.month:02d}-{today.day:02d}"
        except ValueError:
            pass

    # Invalid or unexpected version format, return the original version and date
    return version, None


def update_version_in_file(filename, new_version, new_date):
    with open(filename, "r") as file:
        content = file.read()

    updated_content = re.sub(
        r"<version>.*<\/version>", f"<version>{new_version}</version>", content
    )
    updated_content = re.sub(
        r"<date>.*<\/date>", f"<date>{new_date}</date>", updated_content
    )

    with open(filename, "w") as file:
        file.write(updated_content)


def update_version_changelog(filename, new_version):
    with open(filename, "r") as file:
        content = file.read()

    updated_content = re.sub(r"<version>", f"# {new_version}", content)

    with open(filename, "w") as file:
        file.write(updated_content)

    if content == updated_content:
        print(
            """
Please add a Changelog line such as:
<version>
This version introduces...
        """
        )
        sys.exit(1)
    else:
        print(f"Changelog updated to version {new_version}")


if __name__ == "__main__":
    package_xml_file = "./package.xml"
    changelog_file = "./changeLog.md"

    with open(package_xml_file, "r") as file:
        package_xml_content = file.read()

    current_version = re.search(
        r"<version>(.*?)<\/version>", package_xml_content
    ).group(1)
    new_version, new_date = increment_version(current_version)

    if new_version != current_version:
        update_version_in_file(package_xml_file, new_version, new_date)
        print(f"Version updated from {current_version} to {new_version}")
        print(f"Date updated to {new_date}")
        update_version_changelog(changelog_file, new_version)
    else:
        print("Version remains unchanged. No update needed.")
