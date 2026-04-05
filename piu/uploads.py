import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UploadedFile:
    filename: str
    content_type: str
    data: bytes
    size: int = field(init=False)

    def __post_init__(self):
        self.size = len(self.data)

    def save(self, directory: str, filename: str = None) -> str:
        os.makedirs(directory, exist_ok=True)
        name = filename or f"{uuid.uuid4().hex}_{self.filename}"
        path = os.path.join(directory, name)
        with open(path, "wb") as f:
            f.write(self.data)
        return path

    def __repr__(self):
        return f"<UploadedFile {self.filename} {self.size}b>"


def parse_multipart(body: bytes, content_type: str) -> tuple[dict, dict[str, UploadedFile]]:
    """
    Parse a multipart/form-data body.
    Returns (fields dict, files dict).
    """
    fields: dict[str, str] = {}
    files: dict[str, UploadedFile] = {}

    boundary_match = re.search(r"boundary=([^\s;]+)", content_type)
    if not boundary_match:
        return fields, files

    boundary = boundary_match.group(1).encode()
    delimiter = b"--" + boundary

    parts = body.split(delimiter)
    for part in parts:
        if part in (b"", b"--\r\n", b"--"):
            continue
        if part.startswith(b"\r\n"):
            part = part[2:]
        if part.endswith(b"\r\n"):
            part = part[:-2]

        if b"\r\n\r\n" not in part:
            continue

        headers_raw, _, content = part.partition(b"\r\n\r\n")
        headers = {}
        for line in headers_raw.decode(errors="replace").splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip().lower()] = v.strip()

        disposition = headers.get("content-disposition", "")
        name_match = re.search(r'name="([^"]+)"', disposition)
        filename_match = re.search(r'filename="([^"]+)"', disposition)

        if not name_match:
            continue

        name = name_match.group(1)

        if filename_match:
            fname = filename_match.group(1)
            ct = headers.get("content-type", "application/octet-stream")
            files[name] = UploadedFile(filename=fname, content_type=ct, data=content)
        else:
            fields[name] = content.decode(errors="replace")

    return fields, files