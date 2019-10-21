import requests
import re
import base64


class Samehadaku:
    def __init__(self):
        self.url = 'https://www.samehadaku.tv/'
        self.links = []
        self.title = None
        self.cache = {}
        self.href = None
        self.rlinks = []
        self.eps = []
        
    def init(self,q):
        r = requests.get(self.url, params={'s': q})
        results = re.findall(
            '<a class=\'tip\' rel=".+"   href="(.+?)" title="(.+?)" alt=".+">',
            r.text, re.M | re.I)
        fail_indicator = 'Sorry, but nothing matched your search terms.'
        if len(results) and fail_indicator not in r.text:
            self.href = results[0][0]
            self.title = results[0][1]
            r = requests.get(self.href)
            self.eps = re.findall(
                r'<span class="leftoff"><a href="(.+?)" target="_blank">(.+?)</a></span>',
                r.text, re.M | re.I)
            self.href = self.eps[0][0]
            self.title = self.eps[0][1]
            print(self.href+"==>"+self.title)

    def get_list(self):
        return self.eps

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
                        '<li><strong>(.+?)</strong>.+</li>', text, re.M | re.I)
                    for i, vqual in enumerate(vquals):
                        if (link and vtype and vqual):
                            rlinks.append(
                                {'link': link,
                                'type': vtype.lower(), 'quality': vqual.lower()})
                            break
                else:
                    continue
        self.rlinks = rlinks



    def get_links_external(self,u):
        if not u.startswith(self.url):
            return False
        page = requests.get(u)
        self.links = re.findall(
            r'<li.*<a.*?href="(.+?)".*?>MU.*?</a>.*?</li>',
            page.text, re.M | re.I)
        self.href = u
        self.title = re.findall(
            r'<h1 class="entry-title" itemprop="name">(.+?)</h1>',
            page.text, re.M | re.I)
        self.page_text = page.text

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
                        '<li><strong>(.+?)</strong>.+</li>', text, re.M | re.I)
                    for i, vqual in enumerate(vquals):
                        if (link and vtype and vqual):
                            rlinks.append(
                                {'link': link,
                                'type': vtype.lower(), 'quality': vqual.lower()})
                            break
                else:
                    continue
        self.rlinks = rlinks


if __name__ == '__main__':
    # s = Samehadaku()
    # s.init("boruto")
    # s.get_links()
    
    s = Samehadaku()
    s.get_links_external('https://www.samehadaku.tv/boruto-episode-128/')
    print(s.rlinks)
