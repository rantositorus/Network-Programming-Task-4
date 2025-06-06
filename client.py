import socket
import os
import json
import time

SERVER_HOST_DEFAULT = '127.0.0.1'


def send_request(host, port, request_data_bytes):
    response_bytes = b""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(request_data_bytes)
            s.shutdown(socket.SHUT_WR)

            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_bytes += chunk

    except ConnectionRefusedError:
        print(f"KONEKSI DITOLAK: Tidak dapat terhubung ke {host}:{port}. Apakah server berjalan?")
        return None
    
    except socket.timeout:
        print(f"TIMEOUT: Waktu koneksi ke {host}:{port} habis.")
        return None
    
    except Exception as e:
        print(f"ERROR : saat mengirim/menerima dari {host}:{port}: {e}")
        return None
    
    return response_bytes.decode(errors='ignore') 

def list_directory(host, port, directory_url_path):
    print(f"\n>>> LISTDIR: Meminta daftar isi direktori '{directory_url_path}' dari {host}:{port}")

    request_header_str = f"LISTDIR {directory_url_path} HTTP/1.0\r\n"
    request_header_str += f"Host: {host}\r\n\r\n"
    
    response_str = send_request(host, port, request_header_str.encode())
    
    if response_str:
        print("--- Respons Server (LISTDIR) ---")
        print(response_str)
        print("---------------------------------")
        if response_str.startswith("HTTP/1.0 200 OK"):
            try:
                _, _, body_part = response_str.partition("\r\n\r\n")
                if body_part:
                    dir_items = json.loads(body_part)
                    print("Item direktori yang berhasil di-parse:")
                    for item in dir_items:
                        print(f"  - {item}")
                else:
                    print("Body respons kosong, tidak ada item direktori untuk di-parse.")
            
            except json.JSONDecodeError:
                print("GAGAL PARSE: Tidak dapat mem-parse body respons LISTDIR sebagai JSON.")
            
            except Exception as e:
                print(f"ERROR PARSE: Terjadi kesalahan saat memproses body respons LISTDIR: {e}")
    
    else:
        print(f"Tidak ada respons dari server untuk LISTDIR {directory_url_path}.")


def upload_file(host, port, local_filepath):
    
    filename = os.path.basename(local_filepath)
    print(f"\n>>> UPLOAD: Mencoba mengunggah '{local_filepath}' ke direktori server di {host}:{port}")
    
    if not os.path.exists(local_filepath):
        print(f"FILE LOKAL TIDAK DITEMUKAN: '{local_filepath}' tidak ada.")
        return

    try:
        with open(local_filepath, 'rb') as f:
            file_content_bytes = f.read()
    
    except Exception as e:
        print(f"ERROR BACA FILE LOKAL: Tidak dapat membaca '{local_filepath}': {e}")
        return

    upload_url_path = f"/{filename}"

    file_ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        '.txt': 'text/plain',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
        '.json': 'application/json',
        '.html': 'text/html',
    }
    content_type = mime_types.get(file_ext, 'application/octet-stream')

    request_header_str = f"POST {upload_url_path} HTTP/1.0\r\n"
    request_header_str += f"Host: {host}\r\n"
    request_header_str += f"Content-Length: {len(file_content_bytes)}\r\n"
    request_header_str += f"Content-Type: {content_type}\r\n\r\n"
    
    full_request_bytes = request_header_str.encode() + file_content_bytes
    
    response_str = send_request(host, port, full_request_bytes)
    if response_str:
        print("--- Respons Server (UPLOAD) ---")
        print(response_str)
        print("--------------------------------")
    else:
        print(f"Tidak ada respons dari server untuk UPLOAD {filename}.")


def delete_file(host, port, remote_file_url_path):
    print(f"\n>>> DELETE: Mencoba menghapus file '{remote_file_url_path}' dari {host}:{port}")
    request_header_str = f"DELETE {remote_file_url_path} HTTP/1.0\r\n"
    request_header_str += "Host: {host}\r\n\r\n"
    response_str = send_request(host, port, request_header_str.encode())
    
    if response_str:
        print("--- Respons Server (DELETE) ---")
        print(response_str)
        print("--------------------------------")
    else:
        print(f"Tidak ada respons dari server untuk DELETE {remote_file_url_path}.")


def get_file(host, port, remote_file_url_path):
    print(f"\n>>> GET: Meminta file '{remote_file_url_path}' dari {host}:{port}")
    request_header_str = f"GET {remote_file_url_path} HTTP/1.0\r\n"
    request_header_str += "Host: {host}\r\n\r\n"
    response_str = send_request(host, port, request_header_str.encode())
    
    if response_str:
        print(f"--- Respons Server (GET {remote_file_url_path}) ---")
        print(response_str)
        print("---------------------------------")
        if response_str.startswith("HTTP/1.0 200 OK"):
            _, _, body_part = response_str.partition("\r\n\r\n")
    else:
        print(f"Tidak ada respons dari server untuk GET {remote_file_url_path}.")


if __name__ == "__main__":
    # Server Thread Pool
    server_to_test = ("Thread Pool Server", SERVER_HOST_DEFAULT, 8885) 

    # Server Process Pool
    # server_to_test = ("Process Pool Server", SERVER_HOST_DEFAULT, 8889)


    server_name, server_host, server_port = server_to_test
    print(f"\n\n{'='*15} MENGUJI SERVER: {server_name} di {server_host}:{server_port} {'='*15}")
    
    list_directory(server_host, server_port, "/")
    
    upload_file(server_host, server_port, "donalbebek.jpg")

    list_directory(server_host, server_port, "/")

    print("\nPengujian operasi klien selesai.")
