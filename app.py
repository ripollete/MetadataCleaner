""""" 
Metadata Cleaner
Version: 1.1
Author: Javier Ripoll
Website: https://javierripoll.es
Contact: javier@javierripoll.es
Date: 2025-02-23

Description:
This Flask application allows users to upload files, extract metadata, 
and remove all metadata from supported file types using ExifTool.
"""

from flask import Flask, request, send_file, render_template, after_this_request, jsonify
import os
import shutil
import uuid
import subprocess
import json

# Read environment variables or use default values
MAX_FILES = int(os.getenv("MAX_FILES", 10))  # Default: 10 files
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))  # Default: 50MB
PAGE_TITLE = os.getenv("PAGE_TITLE", "Metadata Cleaner")  # Default title
SUPPORT_MESSAGE = os.getenv("SUPPORT_MESSAGE", "For support, please contact your IT Service or SATI.")


app = Flask(__name__)
BASE_UPLOAD_FOLDER = "temp_uploads"
# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "3g2", "3gp2", "3gp", "3gpp", "aax", "ai", "ait", "arq", "arw",
    "avif", "cr2", "cr3", "crm", "crw", "ciff", "cs1", "dcp", "dng",
    "dr4", "dvb", "eps", "epsf", "ps", "erf", "exif", "exv", "f4a",
    "f4b", "f4p", "f4v", "fff", "flif", "gif", "glv", "gpr", "hdp",
    "wdp", "jxr", "heic", "heif", "hif", "icc", "icm", "iiq", "ind",
    "indd", "indt", "insp", "jp2", "jpf", "jpm", "jpeg", "jpg", "jpe",
    "jxl", "lrv", "m4a", "m4b", "m4p", "m4v", "mef", "mie", "mos",
    "mov", "qt", "mp4", "mpo", "mqv", "mrw", "nef", "nksc", "nrw",
    "orf", "ori", "pdf", "pef", "png", "jng", "mng", "ppm", "pbm",
    "pgm", "psd", "psb", "psdt", "qtif", "qti", "qif", "raf", "raw",
    "rw2", "rwl", "sr2", "srw", "thm", "tiff", "tif", "vrd", "webp",
    "x3f", "xmp"
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("upload.html",
    allowed_extensions=list(ALLOWED_EXTENSIONS)
    ,page_title=PAGE_TITLE
    ,max_file_size_mb = MAX_FILE_SIZE_MB
    ,max_files = MAX_FILES
    ,support_message=SUPPORT_MESSAGE)

@app.route("/get_metadata", methods=["POST"])
def get_metadata():
    if "file" not in request.files:
        return jsonify({"error": "No file received"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Invalid file name"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File extension not allowed"}), 400

    session_id = str(uuid.uuid4())
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, session_id)
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    try:
        result = subprocess.run(["exiftool", "-j", file_path], capture_output=True, text=True)
        metadata = json.loads(result.stdout)[0] if result.stdout else {}

        # Irrelevant metadata fields to exclude
        excluded_metadata = {
            "Directory", "ExifToolVersion", "FileAccessDate", "FileInodeChangeDate", 
            "FileModifyDate", "FileName", "FilePermissions", "FileSize", "FileType", 
            "FileTypeExtension", "Linearized", "MIMEType", "PDFVersion", "PageCount", 
            "SourceFile", "BitDepth", "ColorType", "Compression", "Filter", "ImageSize",
            "ImageWidth", "Interlace", "Megapixels", "AudioBitsPerSample", "AudioChannels", 
            "AudioFormat", "AudioSampleRate", "AvgBitrate", "Balance", "CompatibleBrands", 
            "CompressorID", "CreateDate", "CurrentTime", "Duration", "GraphicsMode", 
            "HandlerType", "ImageHeight", "MajorBrand", "MatrixStructure", "MediaCreateDate", 
            "MediaDataOffset", "MediaDataSize", "MediaDuration", "MediaHeaderVersion", 
            "MediaLanguageCode", "MediaModifyDate", "MediaTimeScale", "MinorVersion", 
            "ModifyDate", "MovieHeaderVersion", "NextTrackID", "OpColor", "PosterTime", 
            "PreferredRate", "PreferredVolume", "PreviewDuration", "PreviewTime", 
            "Rotation", "SelectionDuration", "SelectionTime", "SourceImageHeight", 
            "SourceImageWidth", "TimeScale", "TrackCreateDate", "TrackDuration", 
            "TrackHeaderVersion", "TrackID", "TrackLayer", "TrackModifyDate", 
            "TrackVolume", "VideoFrameRate", "XResolution", "YResolution",
            "BlueX", "BlueY", "GreenX", "GreenY", "RedX", "RedY", "WhitePointX", "WhitePointY",
            "Language", "TaggedPDF","APP14Flags0", "APP14Flags1", "BitsPerSample", "ColorComponents", 
            "ColorTransform", "DCTEncodeVersion", "EncodingProcess", "YCbCrSubSampling"
        }

        filtered_metadata = {k: v for k, v in metadata.items() if k not in excluded_metadata}
        shutil.rmtree(upload_folder)
        return jsonify(filtered_metadata )

    except Exception as e:
        return jsonify({"error": f"Error retrieving metadata: {str(e)}"}), 500

@app.route("/process_files", methods=["POST"])
def process_files():
    if "files" not in request.files:
        return "No files received", 400

    files = request.files.getlist("files")

    if len(files) > MAX_FILES:
        return "You cannot upload more than {MAX_FILES} files at a time.", 400

    session_id = str(uuid.uuid4())
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, session_id)
    os.makedirs(upload_folder, exist_ok=True)

    cleaned_files = []

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            return f"File {file.filename} not allowed.", 400

        file.seek(0, os.SEEK_END)
        file_size = file.tell() / (1024 * 1024)
        file.seek(0)

        if file_size > MAX_FILE_SIZE_MB:
            return f"File {file.filename} exceeds the {MAX_FILE_SIZE_MB}MB limit.", 400

        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)

        subprocess.run(["exiftool", "-all=", "-ICC_Profile:all=", "-XMP:all=", "-IPTC:all=", "-overwrite_original", file_path])

        cleaned_files.append(file_path)

    if len(cleaned_files) == 1:
        file_to_send = cleaned_files[0]

        @after_this_request
        def cleanup(response):
            try:
                os.remove(file_to_send)
                shutil.rmtree(upload_folder)
            except Exception as e:
                print(f"Error removing temporary files: {e}")
            return response
        return send_file(file_to_send, as_attachment=True)
    zip_filename = f"cleaned_files_{session_id}.zip"
    zip_path = os.path.join(BASE_UPLOAD_FOLDER, zip_filename)
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", upload_folder)

    @after_this_request
    def cleanup(response):
        try:
            shutil.rmtree(upload_folder)
        except Exception as e:
            print(f"Error removing temporary files: {e}")
        return response

    if len(cleaned_files) == 1:
        return send_file(cleaned_files[0], as_attachment=True)


    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)