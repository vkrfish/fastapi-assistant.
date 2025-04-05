from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from starlette.responses import JSONResponse
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import fitz  # PyMuPDF
import wikipedia
import os
import google.generativeai as genai
from dotenv import load_dotenv
import webbrowser

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("AIzaSyB0cMomi8ZiHJKsP4TFxbnXaafBpg7mY7o")
EMAIL_ADDRESS = os.getenv("99230040779@gmail.com")
EMAIL_PASSWORD = os.getenv("vsjcacjwvxbsanel")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MODELS ==========
class EmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

class TimetableEntry(BaseModel):
    day: str
    period: int
    subject: str
    faculty: str

class GeminiRequest(BaseModel):
    prompt: str

class WikipediaRequest(BaseModel):
    query: str

class YouTubeRequest(BaseModel):
    query: str

# ========== API ROUTES ==========

@app.get("/")
def root():
    return {"message": "AI Assistant FastAPI Backend"}

# ---------- EMAIL ----------
@app.post("/send-email")
def send_email(data: EmailRequest):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = data.to_email
    msg['Subject'] = data.subject
    msg.attach(MIMEText(data.body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return {"message": "Email sent successfully!"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/read-emails")
def read_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()[-5:]  # Last 5 emails
        email_data = []
        for i in mail_ids:
            status, msg_data = mail.fetch(i, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["subject"]
                    from_ = msg["from"]
                    email_data.append({"from": from_, "subject": subject})
        return email_data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- TIMETABLE ----------
timetable = []

@app.post("/add-timetable")
def add_timetable(entry: TimetableEntry):
    timetable.append(entry)
    return {"message": "Timetable entry added.", "data": entry}

@app.get("/get-timetable")
def get_timetable():
    return timetable

# ---------- GEMINI ----------
@app.post("/gemini")
def gemini_response(data: GeminiRequest):
    try:
        response = model.generate_content(data.prompt)
        return {"response": response.text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- WIKIPEDIA ----------
@app.post("/wikipedia")
def get_wikipedia_summary(data: WikipediaRequest):
    try:
        summary = wikipedia.summary(data.query, sentences=2)
        return {"summary": summary}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- YOUTUBE ----------
@app.post("/youtube")
def search_youtube(data: YouTubeRequest):
    try:
        search_url = f"https://www.youtube.com/results?search_query={data.query}"
        webbrowser.open(search_url)
        return {"message": f"Opened YouTube search for: {data.query}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- OCR + PDF ----------
@app.post("/extract-text")
def extract_text_from_pdf(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        pdf_path = f"temp_{file.filename}"
        with open(pdf_path, 'wb') as f:
            f.write(contents)
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        os.remove(pdf_path)
        return {"extracted_text": text.strip()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
