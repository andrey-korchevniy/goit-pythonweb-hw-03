from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import json
import datetime
from jinja2 import Environment, FileSystemLoader

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print('self.path', self.path)
        pr_url = urllib.parse.urlparse(self.path)
        path = pr_url.path

        if path == '/':
            self.send_html_file('index.html')
        elif path == '/message':
            self.send_html_file('message.html')
        elif path == '/read':
            self.render_template('read.html')
        else:
            if pathlib.Path().joinpath(path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
    
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
            
    def send_static(self):
        self.send_response(200)
        mt=mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as fd:
            self.wfile.write(fd.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)

        self.save_data_to_json(data_dict)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
    
    def save_data_to_json(self, data_dict):
        storage_dir = pathlib.Path('./storage')
        storage_dir.mkdir(exist_ok=True)
        json_file = storage_dir / 'data.json'
        
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as file:
                try:
                    messages = json.load(file)
                except json.JSONDecodeError:
                    messages = {}
        else:
            messages = {}

        current_time = str(datetime.datetime.now())
        messages[current_time] = {
            "username": data_dict.get("username", ""),
            "message": data_dict.get("message", "")
        }
        
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(messages, file, ensure_ascii=False, indent=2)
            
    
    def render_template(self, template_name):
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_name)
        
        data = self.load_data_from_json()

        html_content = template.render(messages=data)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
        
    
    def load_data_from_json(self):
        json_file = pathlib.Path('./storage/data.json')
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return {}
        return {}
        

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    print("Server starts...")
    try:
        http.serve_forever()
        print("Server is running...")   
    except KeyboardInterrupt:
        http.server_close()
        print("Server stopped")

if __name__ == "__main__":
    run()
