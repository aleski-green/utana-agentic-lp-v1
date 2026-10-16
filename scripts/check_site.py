#!/usr/bin/env python3
"""Validate public crawl paths, metadata, structured data, and local links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://utana.group/'

class Page(HTMLParser):
    def __init__(self, file):
        super().__init__(convert_charrefs=True)
        self.file = file
        self.meta = {}
        self.canonicals = []
        self.links = []
        self.ids = set()
        self.h1s = 0
        self.titles = 0
        self.redirect = False
        self.json_text = None
        self.schemas = []
        self.feed(file.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag == 'h1': self.h1s += 1
        if tag == 'title': self.titles += 1
        if tag == 'meta':
            name = a.get('name') or a.get('property')
            if name: self.meta.setdefault(name, []).append(a.get('content', ''))
            if a.get('http-equiv', '').lower() == 'refresh': self.redirect = True
        if tag == 'link' and a.get('rel') == 'canonical': self.canonicals.append(a.get('href'))
        if tag in {'a', 'link', 'img', 'script'}:
            href = a.get('href') or a.get('src')
            if href: self.links.append(href)
        if tag == 'script' and a.get('type') == 'application/ld+json': self.json_text = ''

    def handle_data(self, text):
        if self.json_text is not None: self.json_text += text

    def handle_endtag(self, tag):
        if tag == 'script' and self.json_text is not None:
            self.schemas.append(json.loads(self.json_text))
            self.json_text = None

pages = {p.resolve(): Page(p) for p in ROOT.rglob('*.html')}
sitemap = ET.parse(ROOT/'sitemap.xml')
urls = [e.text for e in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(urls) == len(set(urls)), 'Duplicate sitemap URLs'
indexed = []
for path, page in pages.items():
    relative = path.relative_to(ROOT)
    preview = relative.name.startswith('preview-') or relative.name in {'navy.html','privacy-navy.html'} or relative.parts[0] == 'blog-navy'
    noindex = any('noindex' in x for x in page.meta.get('robots', []))
    assert page.titles == 1, f'{relative}: expected one title'
    if preview: assert noindex, f'{relative}: preview must be noindex'
    if not noindex and not page.redirect:
        expected = BASE if relative.as_posix() == 'index.html' else BASE+relative.as_posix()
        assert page.canonicals == [expected], f'{relative}: wrong canonical'
        assert page.h1s == 1, f'{relative}: expected one h1'
        for key in ('description','og:title','og:description','og:url','og:image','twitter:card'):
            assert len(page.meta.get(key, [])) == 1 and page.meta[key][0], f'{relative}: missing/duplicate {key}'
        assert page.meta['og:url'] == [expected], f'{relative}: sharing URL mismatch'
        assert len(page.schemas) == 1, f'{relative}: expected one schema graph'
        graph = page.schemas[0]['@graph']
        webpage = next(n for n in graph if n['@type'] == 'WebPage')
        assert webpage['url'] == expected, f'{relative}: schema URL mismatch'
        if relative.parts[0] == 'services': assert any(n['@type']=='Service' for n in graph)
        if relative.parts[0] in {'use-cases','blog'}: assert any(n['@type']=='Article' for n in graph)
        assert expected in urls, f'{relative}: not in sitemap'
        indexed.append(expected)
    else:
        assert BASE+relative.as_posix() not in urls, f'{relative}: excluded page in sitemap'
    for link in page.links:
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc: continue
        urlpath = unquote(parsed.path)
        if urlpath.startswith('/'):
            target = ROOT/urlpath.lstrip('/')
        elif not urlpath:
            target = path
        else:
            target = path.parent/urlpath
        if target.is_dir(): target = target/'index.html'
        target = target.resolve()
        assert target.is_relative_to(ROOT), f'{relative}: link leaves site root: {link}'
        assert target.exists(), f'{relative}: broken resource {link}'
        if parsed.fragment and target in pages:
            assert unquote(parsed.fragment) in pages[target].ids, f'{relative}: missing anchor {link}'
assert set(indexed) == set(urls), 'Sitemap contains missing or non-indexable pages'
robots = (ROOT/'robots.txt').read_text()
assert 'User-agent: OAI-SearchBot\nAllow: /' in robots
assert 'Sitemap: '+BASE+'sitemap.xml' in robots
assert 'Disallow:' not in robots, 'Crawl blocks require explicit review'
directory = (ROOT/'llms.txt').read_text()
for link in re.findall(r'\]\((https://utana\.group/[^)]*)\)', directory):
    target = link.split('#')[0]
    assert target in urls or target == BASE+'sitemap.xml', f'Unexpected llms.txt URL: {link}'
for path in ('index.html','technology.html'):
    assert 'We do not use Claude models in business workflows.' in (ROOT/path).read_text()
assert 'https://sapiens4.ai/' in (ROOT/'sapiens4.html').read_text()
assert 'source-available' in (ROOT/'sapiens4.html').read_text()
print(f'PASS: {len(pages)} HTML pages, {len(urls)} production URLs, schema graphs, metadata, local resources, anchors, crawler policy, and discovery directory.')
