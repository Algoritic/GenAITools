import requests
import os
import re

from utils.lock import acquire_lock
from utils.logging import log
from constants import PDF_DIR


# Download a pdf file from a url and return the path to the file
def download(url: str) -> str:
    path = os.path.join(PDF_DIR, normalize_filename(url) + ".pdf")
    lock_path = path + ".lock"

    with acquire_lock(lock_path):
        if os.path.exists(path):
            log("Pdf already exists in " + os.path.abspath(path))
            return path

        log("Downloading pdf from " + url)
        response = requests.get(url)

        with open(path, "wb") as f:
            f.write(response.content)

        return path


def fetch_pdfs_from_blob(container_client):
    blob_list = container_client.list_blobs()
    pdf_paths = []
    for blob in blob_list:
        if blob.name.endswith(".pdf"):
            local_file_path = os.path.join(PDF_DIR, os.path.basename(blob.name))
            blob_client = container_client.get_blob_client(blob.name)
            with acquire_lock(local_file_path + ".lock"):
                if not os.path.exists(local_file_path):
                    log("Downloading " + blob.name)
                    with open(local_file_path, "wb") as download_file:
                        download_file.write(blob_client.download_blob().readall())
            pdf_paths.append(local_file_path)
    log("Downloaded " + str(len(pdf_paths)) + " pdf files")
    return pdf_paths

def normalize_filename(filename):
    # Replace any invalid characters with an underscore
    return re.sub(r"[^\w\-_. ]", "_", filename)
