import sys
import os
import json
import zipfile
import hashlib
import shutil

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 3:
        print("Usage: python release_plugin.py <plugin_id> <version>")
        sys.exit(1)

    plugin_id = sys.argv[1]
    version   = sys.argv[2]

    src_dir  = os.path.join("plugins", plugin_id)
    dist_dir = os.path.join("dist", f"{plugin_id}-{version}")
    zip_path = os.path.join(dist_dir, f"{plugin_id}.zip")

    if not os.path.isdir(src_dir):
        print(f"Error: plugins/{plugin_id}/ not found")
        sys.exit(1)

    os.makedirs(dist_dir, exist_ok=True)

    from datetime import datetime, timezone
    meta = {
        "id": plugin_id,
        "version": version,
        "released_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = os.path.join(src_dir, "__meta__.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fname in files:
                if fname.endswith(".pyc"):
                    continue
                full_path = os.path.join(root, fname)
                arcname   = os.path.relpath(full_path, start=os.path.dirname(src_dir))
                z.write(full_path, arcname)

    checksum  = sha256(zip_path)
    size      = os.path.getsize(zip_path)

    if os.path.exists(meta_path):
        os.remove(meta_path)

    print(f"\n✓  Built: {zip_path}")
    print(f"\nPaste into registry.json for '{plugin_id}':")
    print(f'  "version":          "{version}",')
    print(f'  "download_url":     "https://github.com/NeosCodes/ToolBox-plugins/releases/download/{plugin_id}-{version}/{plugin_id}.zip",')
    print(f'  "checksum_sha256":  "{checksum}",')
    print(f'  "size_bytes":       {size},')
    print(f"\nUpload {zip_path} as a GitHub Release asset tagged: {plugin_id}-{version}")


if __name__ == "__main__":
    main()