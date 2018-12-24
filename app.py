import flask as f
import samehadaku as s
import time
import base64 as b64
import requests
app = f.Flask(__name__, template_folder='.')
app.cache = {}
app.init_time = time.time()


@app.before_request
def br():
    if time.time() - app.init_time >= 2*60*60:
        app.cache = {}


@app.route('/')
def root():
    return f.render_template('index.html')


@app.route('/<q>')
def query(q):
    if len(q) < 4:
        f.abort(403)
    smhdk = s.Samehadaku(q)
    if smhdk.href in app.cache:
        items = app.cache[smhdk.href]
    else:
        smhdk.get_links()
        items = smhdk.rlinks
        if not items:
            return f.jsonify(ok=False)
        items = {k: b64.urlsafe_b64encode(v.encode()).decode() for k, v in items.items()}
        app.cache[smhdk.href] = items
    return f.jsonify(ok=True, items=items, title=smhdk.title)


@app.route('/_/dl/<link>')
def get_dl(link):
    try:
        link = b64.urlsafe_b64decode(link).decode()
    except:
        return f.jsonify(ok=False)
    if not link.startswith('https://megaup.net/'):
        return f.jsonify(ok=False)
    ses = requests.Session()
    ses.get(link)
    time.sleep(6)
    r = ses.get(link, allow_redirects=False)
    if r.status_code != 302 or 'Location' not in r.headers:
        return f.redirect(link)
    else:
        return f.redirect(r.headers['Location'])


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, threaded=True, port=20001)
