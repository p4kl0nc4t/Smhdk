import base64 as b64
import re
import threading
import time

import flask as f
import requests

import samehadaku as s

app = f.Flask(__name__, template_folder='.')
app.cache = {}
app.init_time = time.time()
app.bounded_semaphore = threading.BoundedSemaphore(12)
app.client_bsemaphores = {}


@app.before_request
def before_req():
    if time.time() - app.init_time >= 2*60*60:
        app.cache = {}
        app.init_time = time.time()
    if f.request.endpoint in ['query', 'get_dl']:
        ip_addr = f.request.remote_addr
        if ip_addr not in app.client_bsemaphores:
            app.client_bsemaphores[ip_addr] = threading.BoundedSemaphore(
                3)
        app.client_bsemaphores[ip_addr].acquire()


@app.after_request
def after_req(resp):
    try:
        ip_addr = f.request.remote_addr
        app.client_bsemaphores[ip_addr].release()
    except ValueError:
        app.client_bsemaphores.pop(ip_addr)
    except Exception:
        pass
    return resp


@app.route('/')
def root():
    return f.render_template('index.html')


@app.route('/<q>')
def query(q):
    if len(q) < 4:
        f.abort(403)
    app.bounded_semaphore.acquire()
    try:
        smhdk = s.Samehadaku()
        smhdk.init(q)
        lists = smhdk.get_list()
    finally:
        app.bounded_semaphore.release()
    return f.render_template('eps_list.html',
                             lists=lists, encode=b64.urlsafe_b64encode)

@app.route('/_/<url>')
def show_modal(url):
    app.bounded_semaphore.acquire()
    url = b64.urlsafe_b64decode(url).decode()
    try:
        smhdk = s.Samehadaku()
        smhdk.get_links_external(url)
        items = smhdk.rlinks
    finally:
        app.bounded_semaphore.release()
    return f.render_template('links.html', items=items,
                             title=smhdk.title, encode=b64.urlsafe_b64encode)

@app.route('/_/dl/<link>')
def get_dl(link):
    try:
        link = b64.urlsafe_b64decode(link).decode()
    except Exception:
        f.abort(404)
    app.bounded_semaphore.acquire()
    if not link.startswith('http'):
        f.abort(404)
    if link.startswith('https://www.ahexa.com'):
        for _ in range(3):
            r = requests.get(link)
            m = re.findall(
                r'''<a.*?href=".+?\?.=(aHR0c.+?)".*?_blank".*?>''',
                r.text, re.M | re.I)
            if len(m):
                link = b64.b64decode(m[0]).decode()
            else:
                break
    else:
        r = requests.get(link)
        dLink = re.findall(
            '<form id="east_theme" method="POST" action="(.+?)" name="eastsafelink_form">',
            r.text, re.M | re.I)[0]
        dInput = re.findall(
            '<input type="hidden" name="(.+?)" value="(.+?)" />',
            r.text, re.M | re.I)[0]
        data = {
            dInput[0]:dInput[1]
        }
        r = requests.post(dLink,data=data)
        link = re.findall(
            'changeLink\(\)\{var a\=\'(.+?)\';window.open\(a,"_blank"\)\};',
            r.text, re.M | re.I)[0]
        r = requests.get(link)
        link = re.findall(
            '<a href="(.+?)" rel="nofollow" target="_blank">.+</a>',
            r.text, re.M | re.I)[0]
        link = b64.urlsafe_b64decode(link.split('?r=')[1]).decode()
    if not link.startswith('https://megaup.net/'):
        return f.redirect(link)
    try:
        ses = requests.Session()
        ses.get(link)
        time.sleep(6)
        r = ses.get(link, allow_redirects=False)
    finally:
        app.bounded_semaphore.release()
    if r.status_code != 302 or 'Location' not in r.headers:
        return f.redirect(link)
    else:
        return f.redirect(r.headers['Location'])


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, threaded=True, port=20001)
