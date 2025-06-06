from socket import *
import socket
import logging
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
)

httpserver = HttpServer()

def ProcessTheClient(connection, address):

    logging.info(f"New connection from {address}")
    rcv = b""
    header_ended = False
    content_length = 0

    while True:
        try:
            logging.debug("Menunggu data dari client...")
            data = connection.recv(4096)
            if not data:
                logging.warning(f"Koneksi ditutup oleh {address}")
                break
            rcv += data

            logging.info(f"Menerima {len(data)} bytes. Total Buffer sekarang {len(rcv)} bytes.")

            if not header_ended:
                header_end_idx = rcv.find(b"\r\n\r\n")
                if header_end_idx != -1:
                    logging.info("End of Header (\\r\\n\\r\\n) ditemukan.")
                    header_ended = True

                    header = rcv[:header_end_idx+4].decode()
                    
                    logging.debug(f"Header diterima:\n---\n{header}\n---")

                    for line in header.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            try:
                                content_length = int(line.split(":")[1].strip())
                                logging.info(f"Content-Length ditemukan: {content_length}")
                            except (ValueError, IndexError):
                                  logging.warning(f"Format Content-Length tidak valid dari {address}")
                            break
                    
                    body_start = header_end_idx + 4
                    body = rcv[body_start:]
                    
                    logging.info(f"Mulai menerima body. Panjang body awal: {len(body)} bytes. Target: {content_length} bytes.")
                    
                    while len(body) < content_length:
                        more = connection.recv(4096)
                        if not more:
                            logging.warning("Koneksi tertutup saat menerima body.")
                            break
                        body += more
                        logging.info(f"Body diterima: {len(body)} bytes. Masih menunggu {content_length - len(body)} bytes.")
                    
                    full_request = rcv[:body_start] + body
                    logging.info(f"Request lengkap diterima. Total panjang: {len(full_request)} bytes.")
                    
                    decoded_request = full_request.decode(errors="ignore")
                    logging.info(f"\n--- REQUEST DARI {address} ---\n{decoded_request}\n---------------------------------")
                    
                    hasil = httpserver.proses(full_request.decode(errors="ignore"))
                    
                    connection.sendall(hasil)
                    connection.close()
                    return
            else:
                break
        except OSError:
            break
    connection.close()
    return



def Server():
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    my_socket.bind(('0.0.0.0', 8889))
    my_socket.listen(5)

    logging.info("Server HTTP Process Pool berjalan di port 8889...")  
    
    with ProcessPoolExecutor(max_workers=20, thread_name_prefix = "ClientHandler") as executor:
        while True:
                connection, client_address = my_socket.accept()
                p = executor.submit(ProcessTheClient, connection, client_address)
                the_clients.append(p)
                
                the_clients = [f for f in the_clients if not f.done()]
                logging.info(f"Jumlah klien yang sedang diproses: {len(the_clients)}")




def main():
    Server()

if __name__=="__main__":
    main()

