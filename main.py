from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, subprocess, sqlite3

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

AUTH_PASSWORD = 'Nactivi python'
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect('hosting.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    status TEXT,
                    output TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

@app.get('/', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('index.html', {'request': request, 'auth': False})

@app.post('/login')
async def login(request: Request, password: str = Form(...)):
    if password.strip() == AUTH_PASSWORD:
        return templates.TemplateResponse('index.html', {'request': request, 'auth': True})
    return templates.TemplateResponse('index.html', {'request': request, 'auth': False, 'error': 'كلمة السر غير صحيحة'})

@app.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, 'wb') as f:
        f.write(await file.read())
    conn = sqlite3.connect('hosting.db')
    c = conn.cursor()
    c.execute('INSERT INTO files (filename, status, output) VALUES (?, ?, ?)', (file.filename, 'مرفوع', ''))
    conn.commit()
    conn.close()
    return RedirectResponse(url='/', status_code=303)

@app.post('/run')
async def run_file(request: Request, filename: str = Form(...)):
    path = os.path.join(UPLOAD_DIR, filename)
    result = subprocess.run(['python3', path], capture_output=True, text=True)
    conn = sqlite3.connect('hosting.db')
    c = conn.cursor()
    c.execute('UPDATE files SET status=?, output=? WHERE filename=?',
              ('يعمل', result.stdout + '\n' + result.stderr, filename))
    conn.commit()
    conn.close()
    return RedirectResponse(url='/', status_code=303)

@app.post('/delete')
async def delete_file(request: Request, filename: str = Form(...)):
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect('hosting.db')
    c = conn.cursor()
    c.execute('DELETE FROM files WHERE filename=?', (filename,))
    conn.commit()
    conn.close()
    return RedirectResponse(url='/', status_code=303)

@app.get('/files', response_class=HTMLResponse)
async def list_files(request: Request):
    conn = sqlite3.connect('hosting.db')
    c = conn.cursor()
    c.execute('SELECT filename, status, output FROM files')
    rows = c.fetchall()
    conn.close()
    return templates.TemplateResponse('index.html', {'request': request, 'auth': True, 'files': rows})
