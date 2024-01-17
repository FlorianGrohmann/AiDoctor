import os
import requests

links_file_path = 'leitlinien_links.txt'
download_folder = 'data/'

os.makedirs(download_folder, exist_ok=True)

with open(links_file_path, 'r') as file:
    links = file.readlines()

for link in links:
    link = link.strip()
    if link:
        try:
            file_name = link.split('/')[-1]
            file_path = os.path.join(download_folder, file_name)
            response = requests.get(link, stream=True)

            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"Downloaded: {file_name}")
            else:
                print(f"Failed to download {link}: Status code {response.status_code}")

        except Exception as e:
            print(f"An error occurred while downloading {link}: {e}")

print("All downloads completed.")
