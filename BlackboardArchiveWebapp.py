from flask import *
import threading, queue, time, zipfile, io, json
from BlackboardCollectSpecifics import Blackboard
from pathlib import Path
import os, glob

app = Flask(__name__)

SESSIONS = {}

INDEX_HTML = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Blackboard Archiver</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background:#0b1020; color:#e5e7eb }
    .card { background:#111827; border:1px solid #1f2937 }
    .course { cursor:pointer }
    .course:hover { background:#6FC7D6 }
  </style>
</head>
<body>
<div class="container py-5" style="max-width:600px">
  <div class="card p-4 shadow-lg">
    <h4 class="mb-3" style="color: #a5d2f9;">📦 Blackboard Archiver</h4>

    <div id="loginBox">
      <input id="user" class="form-control mb-2" placeholder="Username">
      <input id="pass" type="password" class="form-control mb-3" placeholder="Password">
      <button class="btn btn-primary w-100" onclick="login()">Connexion</button>
    </div>

    <div id="courseBox" class="d-none">
      <h6 class="mt-3" style="color: #69cdec;">Cours disponibles</h6>
      <div id="courses" class="list-group mb-3"></div>
      <button class="btn btn-success w-100" onclick="archive()">Télécharger en ZIP</button>
    </div>

    <div id="progressBox" class="d-none mt-4">
      <div class="progress">
        <div id="bar" class="progress-bar progress-bar-striped progress-bar-animated" style="width:0%"></div>
      </div>
      <div id="status" class="small mt-2"></div>
    </div>
  </div>
</div>

<script>
let evt

async function login(){
  const r = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user.value,password:pass.value})})
  const j = await r.json()

  loginBox.classList.add('d-none')
  courseBox.classList.remove('d-none')

  courses.innerHTML=''
  j.courses.forEach(c=>{
    courses.innerHTML += `
      <label class="list-group-item course">
        <input class="form-check-input me-2" type="checkbox" value="${c.name}">
        ${c.name}
      </label>`
  })
}

function archive(){
  const selected=[...document.querySelectorAll('input:checked')].map(x=>x.value)
  progressBox.classList.remove('d-none')

  fetch('/api/archive',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({courses:selected})})

  evt = new EventSource('/api/progress')
  evt.onmessage = e => {
    const d = JSON.parse(e.data)
    bar.style.width = d.progress + '%'
    status.innerText = d.status
    if(d.done){ evt.close(); window.location='/api/download' }
  }
}
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    bbs = Blackboard(base=open("base_url.txt").read().strip())
    bbs.login(data['username'], data['password'])

    sid = str(bbs.ajax_id)
    SESSIONS[sid] = {
        'bbs': bbs,
        'queue': queue.Queue(),
        'zip': None
    }

    courses = bbs.getCourses()
    resp = jsonify({'courses':[{'name':k} for k in courses.keys()]})
    resp.set_cookie('sid', sid)
    return resp

@app.route('/api/archive', methods=['POST'])
def api_archive():
    sid = request.cookies.get('sid')
    q = SESSIONS[sid]['queue']
    bbs = SESSIONS[sid]['bbs']
    courses = request.json['courses']

    def worker():
        zbuf = io.BytesIO()
        z = zipfile.ZipFile(zbuf,'w', zipfile.ZIP_DEFLATED)
        total = len(courses)
        for i, course in enumerate(courses):
            q.put(json.dumps({'status':f'📥 {course}','progress':int((i/total)*100)}))
            sections = bbs.getCourseSections(course)
            time.sleep(0.5)
        q.put(json.dumps({'status':'✅ Terminé','progress':100,'done':True}))
        
        SESSIONS[sid]['z'] = z
        SESSIONS[sid]["zip"] = zbuf

    threading.Thread(target=worker, daemon=True).start()
    return '',204

@app.route('/api/progress')
def api_progress():
    sid = request.cookies.get('sid')
    q = SESSIONS[sid]['queue']

    def gen():
        while True:
            msg = q.get()
            yield f"data: {msg}\n\n"
            if 'done' in msg:
                break

    return Response(gen(), mimetype='text/event-stream')

@app.route('/api/download')
def api_download():
    sid = request.cookies.get('sid')
    z = SESSIONS[sid]['z']
    zbuf = SESSIONS[sid]['zip']

    os.chdir(os.path.join("~tmp", sid))
    files = glob.glob(os.path.join("./**", "*.*"), recursive=True)
    for fi in files:
        if os.path.isfile(fi):
            z.write(fi)
    
    z.close()
    zbuf.seek(0)
    return send_file(zbuf, as_attachment=True, download_name='blackboard.zip')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)