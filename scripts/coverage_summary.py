#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

COVERAGE_FILE = "coverage.xml"


def main():
    if not os.path.exists(COVERAGE_FILE):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Coverage Summary\n")
            f.write("coverage.xml not found (tests may have failed before coverage was generated).\n")
        return

    root = ET.parse(COVERAGE_FILE).getroot()
    line_rate = root.attrib.get("line-rate")
    pct = f"{float(line_rate) * 100:.2f}%" if line_rate else "N/A"
    lines_valid = root.attrib.get("lines-valid")
    lines_covered = root.attrib.get("lines-covered")

    summary = ["# Coverage Summary\n", f"**Total**: {pct}"]
    if lines_valid and lines_covered:
        summary.append(f"**Lines**: {lines_covered}/{lines_valid}")
    summary.append("")

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write("\n".join(summary))


if __name__ == "__main__":
    main()
