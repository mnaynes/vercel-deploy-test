#api/index.py

from fastapi import FastAPI
from pydantic import BaseModel
from src.send_personalized_emails import send_personalized_emails

app = FastAPI()

# Create a request model
class EmailRequest(BaseModel):
    websites: str
    offer_document: str

@app.get('/')
def hello_world():
    return "Hello,World"

@app.post('/send-personalized-emails')
def send_personalized_emails_endpoint(request: EmailRequest):
    return send_personalized_emails(request.websites, request.offer_document)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)


# from http.server import BaseHTTPRequestHandler

# #!/usr/bin/python
# from src.send_personalized_emails import send_personalized_emails

# class handler(BaseHTTPRequestHandler):
 
#     def do_GET(self):
#         self.send_response(200)
#         self.send_header('Content-type','text/plain')
#         self.end_headers()
#         send_personalized_emails("../data/websites.txt", "../data/AIA Sales Hacker.docx")
#         return