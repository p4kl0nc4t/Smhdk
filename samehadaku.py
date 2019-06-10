import requests
import re
import base64


class Samehadaku:
    def __init__(self, q):
        self.url = 'https://www.samehadaku.tv/'
        self.links = []
        self.title = None
        self.cache = {}
        self.href = None
        self.rlinks = []
        q = q + ' episode subtitle indonesia'
        r = requests.get(self.url, params={'s': q})
        results = re.findall(
            '<h3 class="post-title"><a href="(.+?)" ' +
            'title="(.+?)">.+</a></h3>',
            r.text, re.M | re.I)
        fail_indicator = 'Sorry, but nothing matched your search terms.'
        if len(results) and fail_indicator not in r.text:
            self.href = results[0][0]
            self.title = results[0][1]

    def _fetch(self, u):
        if not u.startswith(self.url):
            return False
        page = requests.get(u)
        links = re.findall(
            r'<li.*<a.*?href="(.+?)".*?>MU.*?</a>.*?</li>',
            page.text, re.M | re.I)
        self.links = links
        self.page_text = page.text
        return True

    def get_links(self):
        if not self.href or (self._fetch(self.href) and not self.links):
            return False

        def clean_type(raw_html):
            cleanr = re.compile('<.*?>')
            cleantext = re.sub(cleanr, '', raw_html).lower()
            hf_types_pr = ['3gp', 'x265', 'mp4', 'mkv']
            for t in hf_types_pr:
                if t in cleantext:
                    return t
            return cleantext.strip()

        vtypes = re.findall('^(<p.+?)\n.*?download-eps',
                            self.page_text, re.M | re.I)
        sections = {}
        for i, v in enumerate(vtypes):
            if i+1 != len(vtypes):
                sections[clean_type(v)] = self.page_text[self.page_text.find(
                    v):self.page_text.find(vtypes[i+1]):]
            else:
                sections[clean_type(
                    v)] = self.page_text[self.page_text.find(v):]
        rlinks = []
        for link in self.links:  # iterate over links
            for vtype, text in sections.items():  # check for section
                if link in text:
                    vquals = re.findall(
                        r'<li.*?>.*?<strong>(.+?)<', text, re.M | re.I)
                    for i, vqual in enumerate(vquals):
                        if i+1 != len(vquals):
                            if link in text[text.find(vqual):text.find(
                                    vquals[i+1]):]:
                                break
                        elif link in text[text.find(vqual):]:
                            break
                    break
                else:
                    continue
            if (link and vtype and vqual):
                rlinks.append(
                    {'link': link,
                     'type': vtype.lower(), 'quality': vqual.lower()})
        self.rlinks = rlinks


if __name__ == '__main__':
    s = Samehadaku('boruto')
    s.get_links()
    print(s.rlinks)
