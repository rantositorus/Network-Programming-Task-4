import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import json

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.png']='image/png'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
		self.types['.json']='application/json'
		self.upload_dir = './upload'
		if not os.path.exists(self.upload_dir):
			os.makedirs(self.upload_dir)
		self.root_dir = './'

	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")

		if isinstance(messagebody, str):
			messagebody = messagebody.encode()

		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))

		for kk in headers:
			resp.append("{}: {}\r\n".format(kk, headers[kk]))
		resp.append("\r\n")

		response_headers = ''
		for i in resp:
			response_headers = f"{response_headers}{i}"
		
		response_data = response_headers.encode() + messagebody
		return response_data
	
	def proses(self,data):
		parts = data.split("\r\n\r\n", 1)
		header_data = parts[0]
		body_data = parts[1] if len(parts) > 1 else ''

		request = header_data.split("\r\n")
		if not request or not request[0]:
			return self.response(400, 'Bad Request', 'Invalid HTTP request')
		
		baris = request[0]
		all_headers_list = [n for n in request[1:] if n != '']

		headers_dict = {}
		for header_line in all_headers_list:
			if ':' in header_line:
				key, value = header_line.split(':', 1)
				headers_dict[key.strip()] = value.strip()
			else:
				print(f"Invalid header line: {header_line}")
		
		j = baris.split()
		try:
			method = j[0].upper().strip()
			object_address = j[1].strip()

			if method == 'GET':
				return self.http_get(object_address, headers_dict)
			elif method == 'POST':
				return self.http_upload(object_address, headers_dict, body_data)
			elif method == 'LISTDIR':
				return self.http_listdir(object_address, headers_dict)
			elif method == 'DELETE':
				return self.http_delete(object_address, headers_dict)
			else:
				return self.response(405, 'Method Not Allowed', '', {})
		except IndexError:
			return self.response(400, 'Bad Request', 'Malformed Request Line', {})
		except Exception as e:
			return self.response(500, 'Internal Server Error', f"Server error: {str(e)}", {})
	
	def http_get(self,object_address,headers):
		if ".." in object_address:
			return self.response(400, 'Bad Request', 'Invalid path', {})
	
		if object_address == '/':
			return self.response(200, 'OK', 'Welcome to the HTTP server', {})
		
		path_segment = object_address.lstrip('/')
		target_path = os.path.join(self.root_dir, path_segment)

		abs_target_path = os.path.abspath(target_path)
		abs_root_dir = os.path.abspath(self.root_dir)

		if not abs_target_path.startswith(abs_root_dir):
			return self.response(403, 'Forbidden', 'Access denied', {})

		if not os.path.exists(abs_target_path) or not os.path.isfile(abs_target_path):
			return self.response(404, 'Not Found', f'File {object_address} not found', {})
		
		try:
			with open(abs_target_path, 'rb') as fp:
				isi = fp.read()
			
			fext = os.path.splitext(object_address)[1].lower()
			content_type = self.types.get(fext, 'application/octet-stream')

			resp_headers = {'Content-Type': content_type}
			return self.response(200, 'OK', isi, resp_headers)
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Error reading file: {str(e)}', {})

	# def http_post(self,object_address,headers):
	# 	headers ={}
	# 	isi = "kosong"
	# 	return self.response(200,'OK',isi,headers)
		
	def http_listdir(self, dir_address, headers):
		if ".." in dir_address:
			return self.response(400, 'Bad Request', 'Invalid directory path.', {})
		
		path_segment = dir_address.lstrip('/')
		target_dir_path = os.path.join(self.root_dir, path_segment) if path_segment else self.root_dir

		abs_target_dir_path = os.path.abspath(target_dir_path)
		abs_root_dir = os.path.abspath(self.root_dir)

		if not abs_target_dir_path.startswith(abs_root_dir):
			return self.response(403, 'Forbidden', 'Access denied.', {})
		
		if not os.path.exists(abs_target_dir_path) or not os.path.isdir(abs_target_dir_path):
			return self.response(404, 'Not Found', f'Directory {dir_address} not found.', {})
		
		try:
			items = os.listdir(abs_target_dir_path)
			formatted_items = []
			for item in items:
				item_path = os.path.join(abs_target_dir_path, item)
				if os.path.isdir(item_path):
					formatted_items.append(item + '/')
				else:
					formatted_items.append(item)

			response_body = json.dumps(formatted_items)
			return self.response(200, 'OK', response_body, {'Content-Type': 'application/json'})
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Error listing directory: {str(e)}', {})
		
	def http_upload(self, object_address, headers, body_data):
		if ".." in object_address:
			return self.response(400, 'Bad Request', 'Invalid upload path.', {})
		
		path_segment = object_address.lstrip('/')
		filename = os.path.basename(path_segment)

		if not filename:
			return self.response(400, 'Bad Request', 'No filename provided for upload.', {})
		
		if path_segment.startswith('upload/'):
			save_dir = self.upload_dir

		else:
			save_dir = self.root_dir
		
		file_path = os.path.join(save_dir, filename)

		abs_file_path = os.path.abspath(file_path)
		abs_save_dir = os.path.abspath(save_dir)

		if not abs_file_path.startswith(abs_save_dir):
			return self.response(403, 'Forbidden', 'Access denied. Cannot write outside of designated directory.', {})
		
		try:
			content_to_write = body_data.encode() if isinstance(body_data, str) else body_data

			with open(file_path, 'wb') as fp:
				fp.write(content_to_write)
			
			location_header = object_address
			return self.response(201, 'Created', f'File {filename} uploaded successfully.', {'Location': location_header})
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Error uploading file: {str(e)}', {})
		
	def http_delete(self, object_address, headers):
		if ".." in object_address:
			return self.response(400, 'Bad Request', 'Invalid path.', {})
		
		path_segment = object_address.lstrip('/')
		file_path_to_delete = os.path.join(self.root_dir, path_segment)

		abs_file_path_to_delete = os.path.abspath(file_path_to_delete)
		abs_root_dir = os.path.abspath(self.root_dir)
		abs_upload_dir = os.path.abspath(self.upload_dir)

		can_delete = False
		if abs_file_path_to_delete.startswith(abs_root_dir) or abs_file_path_to_delete.startswith(abs_upload_dir):
			can_delete = True

		if not can_delete:
			return self.response(403, 'Forbidden', 'Access denied.', {})

		if not os.path.exists(abs_file_path_to_delete) or not os.path.isfile(abs_file_path_to_delete):
			return self.response(404, 'Not Found', f'File {object_address} not found.', {})		
		
		try:
			os.remove(abs_file_path_to_delete)
			return self.response(200, 'OK', f'File {object_address} deleted successfully.', {})
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Error deleting file: {str(e)}', {})
		
if __name__=="__main__":
	httpserver = HttpServer()
	
	if not os.path.exists(httpserver.upload_dir):
		os.makedirs(httpserver.upload_dir)
	
	with open("testfile.txt", "w") as f:
		f.write("This is a test file.")
	
	with open(os.path.join(httpserver.upload_dir, "already_exists.txt"), "w") as f:
		f.write("This file already exists in the upload directory.")

	print("--- Testing GET /testfile.txt ---")
	d = httpserver.proses('GET /testfile.txt HTTP/1.0\r\n\r\n')
	print(d.decode(errors='ignore'))

	print("\n--- Testing LISTDIR / ---")
	d = httpserver.proses('LISTDIR / HTTP/1.0\r\n\r\n')
	print(d.decode(errors='ignore'))

	print(f"\n--- Testing LISTDIR /{httpserver.upload_dir.strip('./')} ---")
	d = httpserver.proses(f'LISTDIR /{httpserver.upload_dir.strip("./")} HTTP/1.0\r\n\r\n')
	print(d.decode(errors='ignore'))

	print("\n--- Testing UPLOAD new_uploaded_file.txt ---")
	upload_content = "This is the content of the new uploaded file."
	d = httpserver.proses(f'POST /upload/new_uploaded_file.txt HTTP/1.0\r\nContent-Length: {len(upload_content)}\r\n\r\n{upload_content}')
	print(d.decode(errors='ignore'))

	if os.path.exists(os.path.join(httpserver.upload_dir, "new_uploaded_file.txt")):
		print("UPLOAD VERIFIED: new_uploaded_file.txt exists in the upload directory.")
		with open(os.path.join(httpserver.upload_dir, "new_uploaded_file.txt"), "r") as f:
			print("Content of new_uploaded_file.txt:", f.read())
	else:
		print("UPLOAD FAILED: new_uploaded_file.txt does not exist in the upload directory.")
		
	print("\n--- Testing DELETE /testfile.txt ---")
	d = httpserver.proses('DELETE /testfile.txt HTTP/1.0\r\n\r\n')
	print(d.decode(errors='ignore'))
	if not os.path.exists("testfile.txt"):
		print("DELETE VERIFIED: testfile.txt has been deleted.")
	else:
		print("DELETE FAILED: testfile.txt still exists.")
	
	print(f"\n--- Testing DELETE uploaded file /{httpserver.upload_dir.strip('./')}/new_uploaded_file.txt ---")

	delete_path = os.path.join(httpserver.upload_dir, "new_uploaded_file.txt")
	d = httpserver.proses(f'DELETE /{delete_path} HTTP/1.0\r\n\r\n')
	print(d.decode(errors='ignore'))

	if not os.path.exists(os.path.join(httpserver.upload_dir, "new_uploaded_file.txt")):
		print("DELETE VERIFIED: new_uploaded_file.txt has been deleted from the upload directory.")
	else:
		print("DELETE FAILED: new_uploaded_file.txt still exists in the upload directory.")


	if os.path.exists("testfile.txt"): os.remove("testfile.txt")
	if os.path.exists(os.path.join(httpserver.upload_dir, "new_uploaded_file.txt")):
		os.remove(os.path.join(httpserver.upload_dir, "new_uploaded_file.txt"))
	if os.path.exists(os.path.join(httpserver.upload_dir, "already_exists.txt")):
		os.remove(os.path.join(httpserver.upload_dir, "already_exists.txt"))













