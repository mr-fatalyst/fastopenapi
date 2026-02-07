# File Uploads Example

This example demonstrates how to handle file uploads in FastOpenAPI.

## Basic File Upload

### Single File Upload

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi import File, FileUpload
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="File Upload API",
    version="1.0.0"
)

@router.post(
    "/upload",
    tags=["Files"],
    summary="Upload a single file"
)
def upload_file(file: FileUpload = File(..., description="File to upload")):
    """Upload a single file and save it to disk"""
    # Read file content
    content = file.read()

    # Save to disk
    filepath = f"uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "saved_to": filepath
    }

if __name__ == "__main__":
    import os
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
```

### Testing

```bash
# Upload a file
curl -X POST http://localhost:5000/upload \
  -F "file=@document.pdf"
```

---

## Multiple File Uploads

```python
from fastopenapi import File, FileUpload

@router.post(
    "/upload-multiple",
    tags=["Files"],
    summary="Upload multiple files"
)
def upload_multiple_files(
    files: list[FileUpload] = File(..., description="Files to upload")
):
    """Upload multiple files at once"""
    uploaded = []

    for file in files:
        content = file.read()
        filepath = f"uploads/{file.filename}"

        with open(filepath, "wb") as f:
            f.write(content)

        uploaded.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content)
        })

    return {
        "uploaded_count": len(uploaded),
        "files": uploaded
    }
```

### Testing

```bash
# Upload multiple files
curl -X POST http://localhost:5000/upload-multiple \
  -F "files=@file1.pdf" \
  -F "files=@file2.jpg" \
  -F "files=@file3.txt"
```

---

## File Upload with Form Data

```python
from pydantic import BaseModel
from fastopenapi import File, FileUpload, Form

class DocumentMetadata(BaseModel):
    title: str
    description: str
    category: str

@router.post(
    "/upload-with-metadata",
    tags=["Files"],
    summary="Upload file with metadata"
)
def upload_with_metadata(
    file: FileUpload = File(..., description="File to upload"),
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...)
):
    """Upload a file along with metadata"""
    # Read and save file
    content = file.read()
    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as f:
        f.write(content)

    # Store metadata
    metadata = {
        "title": title,
        "description": description,
        "category": category,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }

    return {
        "file": filepath,
        "metadata": metadata
    }
```

### Testing

```bash
curl -X POST http://localhost:5000/upload-with-metadata \
  -F "file=@document.pdf" \
  -F "title=Important Document" \
  -F "description=A very important document" \
  -F "category=legal"
```

---

## Async File Upload (Starlette)

```python
import uvicorn
from starlette.applications import Starlette
from fastopenapi import File, FileUpload
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(
    app=app,
    title="Async File Upload API",
    version="1.0.0"
)

@router.post(
    "/upload",
    tags=["Files"],
    summary="Upload file (async)"
)
async def upload_file(file: FileUpload = File(...)):
    """Upload file asynchronously"""
    # Read file content asynchronously
    content = await file.aread()

    # Save to disk
    filepath = f"uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }

if __name__ == "__main__":
    import os
    os.makedirs("uploads", exist_ok=True)
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

## File Size Validation

```python
from fastopenapi.errors import BadRequestError

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload-limited", tags=["Files"])
def upload_limited_file(file: FileUpload = File(...)):
    """Upload file with size validation"""
    content = file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise BadRequestError(
            f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.1f} MB"
        )

    # Save file
    filepath = f"uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "size": len(content)
    }
```

---

## File Type Validation

```python
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".txt"}

@router.post("/upload-validated", tags=["Files"])
def upload_validated_file(file: FileUpload = File(...)):
    """Upload file with type validation"""
    import os

    # Get file extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    # Validate extension
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestError(
            f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate MIME type
    allowed_mimes = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/plain"
    }

    if file.content_type not in allowed_mimes:
        raise BadRequestError(
            f"Invalid content type: {file.content_type}"
        )

    # Save file
    content = file.read()
    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }
```

---

## Image Processing

```python
from PIL import Image
import io

@router.post("/upload-image", tags=["Images"])
def upload_image(file: FileUpload = File(...)):
    """Upload and process an image"""
    # Read image
    content = file.read()

    # Validate it's an image
    try:
        image = Image.open(io.BytesIO(content))
    except Exception:
        raise BadRequestError("Invalid image file")

    # Get image info
    width, height = image.size
    format_type = image.format

    # Create thumbnail
    thumbnail = image.copy()
    thumbnail.thumbnail((200, 200))

    # Save original
    original_path = f"uploads/{file.filename}"
    with open(original_path, "wb") as f:
        f.write(content)

    # Save thumbnail
    thumb_filename = f"thumb_{file.filename}"
    thumb_path = f"uploads/{thumb_filename}"
    thumbnail.save(thumb_path)

    return {
        "original": {
            "filename": file.filename,
            "path": original_path,
            "width": width,
            "height": height,
            "format": format_type,
            "size": len(content)
        },
        "thumbnail": {
            "filename": thumb_filename,
            "path": thumb_path,
            "width": thumbnail.size[0],
            "height": thumbnail.size[1]
        }
    }
```

---

## CSV File Upload

```python
import csv
import io

@router.post("/upload-csv", tags=["Files"])
def upload_csv(file: FileUpload = File(...)):
    """Upload and parse CSV file"""
    content = file.read()

    # Parse CSV
    text_content = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(text_content))

    rows = list(csv_reader)

    return {
        "filename": file.filename,
        "rows_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "sample_rows": rows[:5]  # First 5 rows
    }
```

---

## File Download

```python
from fastopenapi import Response
from fastopenapi.errors import ResourceNotFoundError

@router.get("/download/{filename}", tags=["Files"])
def download_file(filename: str):
    """Download a file"""
    filepath = f"uploads/{filename}"

    # Check if file exists
    import os
    if not os.path.exists(filepath):
        raise ResourceNotFoundError(f"File '{filename}' not found")

    # Read file
    with open(filepath, "rb") as f:
        content = f.read()

    # Determine content type
    content_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".txt": "text/plain",
        ".csv": "text/csv"
    }

    _, ext = os.path.splitext(filename)
    content_type = content_types.get(ext.lower(), "application/octet-stream")

    return Response(
        content=content,
        status_code=200,
        headers={
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
```

---

## Complete Example with Database

```python
from flask import Flask
from pydantic import BaseModel
from datetime import datetime
from fastopenapi import File, FileUpload, Form, Response
from fastopenapi.routers import FlaskRouter
from fastopenapi.errors import ResourceNotFoundError, BadRequestError
import os
import uuid

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="File Management API",
    version="1.0.0"
)

# In-memory database
files_db = {}

class FileRecord(BaseModel):
    id: str
    filename: str
    original_filename: str
    content_type: str
    size: int
    uploaded_at: datetime
    path: str

@router.post(
    "/files",
    response_model=FileRecord,
    status_code=201,
    tags=["Files"]
)
def upload_file(file: FileUpload = File(...)):
    """Upload a file and store metadata"""
    # Generate unique ID
    file_id = str(uuid.uuid4())

    # Read content
    content = file.read()

    # Validate size (max 10 MB)
    if len(content) > 10 * 1024 * 1024:
        raise BadRequestError("File too large (max 10 MB)")

    # Save file with unique name
    ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{file_id}{ext}"
    filepath = f"uploads/{stored_filename}"

    with open(filepath, "wb") as f:
        f.write(content)

    # Create record
    record = {
        "id": file_id,
        "filename": stored_filename,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "uploaded_at": datetime.now(),
        "path": filepath
    }

    files_db[file_id] = record

    return record

@router.get(
    "/files",
    response_model=list[FileRecord],
    tags=["Files"]
)
def list_files():
    """List all uploaded files"""
    return list(files_db.values())

@router.get(
    "/files/{file_id}",
    response_model=FileRecord,
    tags=["Files"]
)
def get_file_info(file_id: str):
    """Get file metadata"""
    if file_id not in files_db:
        raise ResourceNotFoundError(f"File {file_id} not found")

    return files_db[file_id]

@router.get(
    "/files/{file_id}/download",
    tags=["Files"]
)
def download_file(file_id: str):
    """Download a file"""
    if file_id not in files_db:
        raise ResourceNotFoundError(f"File {file_id} not found")

    record = files_db[file_id]

    # Read file
    with open(record["path"], "rb") as f:
        content = f.read()

    return Response(
        content=content,
        headers={
            "Content-Type": record["content_type"],
            "Content-Disposition": f'attachment; filename="{record["original_filename"]}"'
        }
    )

@router.delete(
    "/files/{file_id}",
    status_code=204,
    tags=["Files"]
)
def delete_file(file_id: str):
    """Delete a file"""
    if file_id not in files_db:
        raise ResourceNotFoundError(f"File {file_id} not found")

    record = files_db[file_id]

    # Delete file from disk
    if os.path.exists(record["path"]):
        os.remove(record["path"])

    # Delete from database
    del files_db[file_id]

    return None

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    print("File Management API running on http://localhost:5000")
    print("Docs at http://localhost:5000/docs")
    app.run(debug=True)
```

### Testing the Complete API

```bash
# Upload a file
curl -X POST http://localhost:5000/files \
  -F "file=@document.pdf"
# Returns: {"id": "abc-123", "filename": "abc-123.pdf", ...}

# List all files
curl http://localhost:5000/files

# Get file info
curl http://localhost:5000/files/abc-123

# Download file
curl http://localhost:5000/files/abc-123/download -o downloaded.pdf

# Delete file
curl -X DELETE http://localhost:5000/files/abc-123
```

---

## Best Practices

### 1. Always Validate File Size

```python
MAX_SIZE = 10 * 1024 * 1024  # 10 MB

if len(content) > MAX_SIZE:
    raise BadRequestError("File too large")
```

### 2. Validate File Types

```python
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}

if file.content_type not in ALLOWED_TYPES:
    raise BadRequestError("File type not allowed")
```

### 3. Use Unique Filenames

```python
import uuid

unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
```

### 4. Store Metadata Separately

```python
# Save file metadata to database
metadata = {
    "original_filename": file.filename,
    "stored_filename": unique_filename,
    "content_type": file.content_type,
    "size": len(content),
    "uploaded_at": datetime.now()
}
```

### 5. Handle Errors Gracefully

```python
from fastopenapi.errors import InternalServerError

try:
    content = file.read()
    # Process file...
except Exception as e:
    raise InternalServerError(f"Failed to process file: {str(e)}")
```

---

## See Also

- [File API Reference](../api_reference/types.md#fileupload) - FileUpload class documentation
- [Request Body Guide](../guide/request_body.md) - Form data and file uploads
- [Error Handling](../guide/error_handling.md) - Handling upload errors
