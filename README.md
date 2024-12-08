# getgrass-autoproxy
getgrass auto proxy support multi akun

# WebSocket Proxy with Multi-User ID Support

## Overview
This script connects to a WebSocket server using a SOCKS5 proxy, supports multiple User IDs, and periodically fetches updated proxies from an API.

## Features
- Supports multiple User IDs loaded from `user_ids.txt`.
- Automatically fetches proxy list from an API.
- Support load proxy dari proxies.txt, dengan format:
  ```bash
  http://ip:port
  ```
## Prerequisites
- Python 3.7 or higher.

## Installation
1. Clone the repository or download the file:

```bash
git clone https://github.com/adhe222/getgrass-autoproxy.git
```
2. Create a virtual environment:
```bash
   python3 -m venv venv
   source venv/bin/activate
```
open directory getgrass-autoproxy
```bash
cd getgrass-autoproxy
```
3. Install dependencies:
   
```bash
pip install -r requirements.txt
```

4. Create a file named user_ids.txt and add your User IDs, one per line:
example:
```bash
userid1
userid2
userid3
```
Usage

Run the script with:
```bash
python grassauto.py
```

You can update the URL in the script:

PROXY_API_URL = "YOUR_PROXY_API_URL"

File user_ids.txt

The script reads User IDs from user_ids.txt. Ensure the file exists in the project directory.

Known Issues

1. File Not Found:

If user_ids.txt is missing, the script will log an error and exit.



2. Proxy API Format:

Ensure the proxy API returns plain text with one proxy per line.

License

This project is licensed under the MIT License.
