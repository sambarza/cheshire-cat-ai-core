import os

for root, dirs, files in os.walk("./plugins"):
    for file in files:
        if file == "requirements.txt":
            req_file = os.path.join(root, file)
            os.system(f'uv pip install --no-cache-dir -r "{req_file}"')
