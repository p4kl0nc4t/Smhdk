import requests
import re
import base64
import concurrent.futures


class Samehadaku:
    def __init__(self, q):
        self.url = 'https://www.samehadaku.tv/'
        self.links = []
        self.title = None
        self.cache = {}
        self.href = None
        self.rlinks = {}
        q = q + ' episode subtitle indonesia'
        r = requests.get(self.url, params={'s': q})
        results = re.findall(
            r'<h3 class="post-title"><a href="(.+?)" title="(.+?)">.+</a></h3>', r.text, re.M | re.I)
        if len(results):
            self.href = results[0][0]
            self.title = results[0][1]

    def _fetch(self, u):
        if not u.startswith(self.url):
            return False
        page = requests.get(u)
        links = re.findall(
            r'<li.*<a.*?href="(.+?)".*?>MU.*?</a>.*?</li>', page.text, re.M | re.I)
        self.links = links

    def _extract(self, u):
        if not u.startswith('http'):
            return False
        for _ in range(2):
            r = requests.get(u)
            m = re.findall(
                r'''<a.*?href=".+?\?.=(aHR0c.+?)".*?_blank".*?>''', r.text, re.M | re.I)
            if len(m):
                u = base64.b64decode(m[0]).decode()
            else:
                break
        return u

    def get_links(self):
        if not self.href:
            return False
        else:
            self._fetch(self.href)
        if not self.links:
            return False

        def work(link):
            link = self._extract(link)
            if not link:
                return
            r = requests.get(link)
            m = re.findall(
                r'''btn btn-default' href='(.+?)'>download now</a>"\);''', r.text, re.M | re.I)
            if not len(m):
                return
            title = re.findall(
                r'<div class="heading-1">(.+?)</div>', r.text, re.M | re.I)
            if len(title):
                return title[0], m[0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as e:
            futures = e.map(work, self.links)
            for future in futures:
                title, href = future
                self.rlinks[title] = href


if __name__ == '__main__':
    s = Samehadaku('boruto')
    s.get_links()
    print(s.rlinks)
