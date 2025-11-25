# file_storage.py
import os
from uuid import uuid4
from supabase import create_client, Client
from config import settings

UPLOAD_DIR = "uploads"

supabase: Client = create_client(str(settings.SUPABASE_URL), settings.SUPABASE_KEY)

def upload_file(bucket_name: str, filename: str, contents: bytes, content_type: str) -> str:
    unique_name = f"{uuid4().hex}_{filename}"
    path = unique_name

    if settings.PRODUCTION:
        # Upload to Supabase Storage
        response = supabase.storage.from_(bucket_name).upload(
            path,
            contents,
            {
                "content-type": content_type,
                "upsert": "true",
            },
        )

        # Build public URL
        base_url = str(settings.SUPABASE_URL).rstrip("/")
        return f"{base_url}/storage/v1/object/public/{bucket_name}/{path}"

    else:
        # Local dev: save file under uploads/<bucket_name>/<path>
        bucket_dir = os.path.join(UPLOAD_DIR, bucket_name)
        os.makedirs(bucket_dir, exist_ok=True)

        file_path = os.path.join(bucket_dir, path)
        with open(file_path, "wb") as f:
            f.write(contents)

        return f"/{UPLOAD_DIR}/{bucket_name}/{path}"
