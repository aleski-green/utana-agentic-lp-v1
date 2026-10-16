#!/usr/bin/env python3
"""Regenerate crawl files and consistent metadata from the site's visible HTML.

Run after editing a title, description, heading, or adding/removing a page.
No account verification tokens, inferred publication dates, or fabricated reviews.
"""
from pathlib import Path
import html
import json
import re
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://utana.group/'
BEGIN = '<!-- generated-seo:start -->'
END = '<!-- generated-seo:end -->'
ORG = {
    '@type': 'Organization', '@id': BASE + '#organization',
    'name': 'Utana', 'legalName': 'Utana Agentic Technologies LLC',
    'url': BASE, 'logo': BASE + 'assets/logo.svg',
    'description': 'AI automation services for marketing, sales, and business operations worldwide.',
    'email': 'sapiens@utana.group', 'telephone': '+971586601017',
    'address': {'@type': 'PostalAddress', 'streetAddress': 'Al Muhairbi Building 201, Office E-13, Al Gharhoud', 'addressLocality': 'Dubai', 'addressCountry': 'AE'},
    'areaServed': 'Worldwide',
}

def plain(text):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', text)).split())

def tag_content(s, tag):
    m = re.search(rf'<{tag}\b[^>]*>(.*?)</{tag}>', s, re.S | re.I)
    return plain(m.group(1)) if m else ''

def attr(s, name):
    m = re.search(r'<meta\b(?=[^>]*\bname="' + re.escape(name) + r'")[^>]*\bcontent="([^"]*)"[^>]*>', s, re.I)
    return html.unescape(m.group(1)) if m else ''

def hidden(path):
    return path.name.startswith('preview-') or path.name in {'navy.html', 'privacy-navy.html'} or path.parts[0] == 'blog-navy'

def canonical(path):
    return BASE if str(path) == 'index.html' else BASE + path.as_posix()

def meta(name, value, property=False):
    return f'<meta {"property" if property else "name"}="{name}" content="{html.escape(value, quote=True)}">'

pages = []
for file in sorted(ROOT.rglob('*.html')):
    path = file.relative_to(ROOT)
    s = file.read_text()
    s = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), '', s, flags=re.S)
    s = re.sub(r'<!-- generated-breadcrumb:start -->.*?<!-- generated-breadcrumb:end -->', '', s, flags=re.S)
    # Normalize legacy metadata too, so generation cannot produce duplicate tags.
    s = re.sub(r'<link\b(?=[^>]*\brel="canonical")[^>]*>', '', s, flags=re.I)
    s = re.sub(r'<meta\b(?=[^>]*\b(?:name|property)="(?:robots|og:[^"]+|twitter:[^"]+)")[^>]*>', '', s, flags=re.I)
    title = tag_content(s, 'title')
    heading = tag_content(s, 'h1')
    description = attr(s, 'description')
    redirect = re.search(r'<meta\b[^>]*http-equiv="refresh"[^>]*content="0;url=([^"]+)"', s, re.I)
    url = canonical(path)
    bits = [BEGIN]
    if redirect:
        destination = urljoin(url, html.unescape(redirect.group(1)))
        bits.append(f'<link rel="canonical" href="{html.escape(destination, quote=True)}">')
    elif hidden(path):
        bits.append(meta('robots', 'noindex,follow'))
    else:
        if not description:
            if path.name == 'privacy.html':
                description = 'How Utana handles enquiries, email drafts, website hosting, and Google Fonts. Contact details for privacy questions.'
            else:
                raise ValueError(f'{path}: add a specific meta description before publishing')
            s = s.replace('</head>', meta('description', description) + '</head>')
        bits += [f'<link rel="canonical" href="{url}">', meta('robots', 'index,follow,max-image-preview:large')]
        is_article = path.parts[0] in {'blog', 'use-cases'}
        for key, value in {'og:type': 'article' if is_article else 'website', 'og:site_name': 'Utana', 'og:title': title, 'og:description': description, 'og:url': url, 'og:image': BASE+'assets/social/utana.png', 'og:image:width': '1200', 'og:image:height': '630', 'og:image:alt': 'Utana — AI automation for marketing, sales and operations', 'og:locale': 'en_GB'}.items():
            bits.append(meta(key, value, True))
        for key, value in {'twitter:card': 'summary_large_image', 'twitter:title': title, 'twitter:description': description, 'twitter:image': BASE+'assets/social/utana.png', 'twitter:image:alt': 'Utana — AI automation for marketing, sales and operations'}.items():
            bits.append(meta(key, value))
        graph = [ORG, {'@type': 'WebSite', '@id': BASE+'#website', 'url': BASE, 'name': 'Utana', 'publisher': {'@id': BASE+'#organization'}}]
        webpage = {'@type': 'WebPage', '@id': url+'#webpage', 'url': url, 'name': title, 'description': description, 'inLanguage': 'en', 'isPartOf': {'@id': BASE+'#website'}}
        if str(path) != 'index.html':
            crumbs = [('Home', BASE)]
            if path.parts[0] == 'services': crumbs.append(('Services', BASE+'services.html'))
            elif path.parts[0] == 'use-cases': crumbs.append(('Use cases', BASE+'use-cases.html'))
            elif path.parts[0] == 'blog': crumbs.append(('Insights', BASE+'#insights'))
            crumbs.append((heading or title, url))
            crumb_id = url+'#breadcrumb'
            graph.append({'@type': 'BreadcrumbList', '@id': crumb_id, 'itemListElement': [{'@type': 'ListItem', 'position': i+1, 'name': name, 'item': href} for i,(name,href) in enumerate(crumbs)]})
            webpage['breadcrumb'] = {'@id': crumb_id}
            trail = ' <span aria-hidden="true">/</span> '.join(f'<a href="{href.replace(BASE, "/", 1)}">{html.escape(name)}</a>' if i < len(crumbs)-1 else f'<span aria-current="page">{html.escape(name)}</span>' for i,(name,href) in enumerate(crumbs))
            breadcrumb = '<!-- generated-breadcrumb:start --><nav class="breadcrumbs" aria-label="Breadcrumb">'+trail+'</nav><!-- generated-breadcrumb:end -->'
            s = re.sub(r'(<main\b[^>]*>)', lambda m: m.group(1)+breadcrumb, s, count=1)
        if is_article:
            graph.append({'@type': 'Article', '@id': url+'#article', 'headline': heading, 'description': description, 'mainEntityOfPage': {'@id': url+'#webpage'}, 'author': {'@id': BASE+'#organization'}, 'publisher': {'@id': BASE+'#organization'}, 'image': BASE+'assets/social/utana.png', 'inLanguage': 'en'})
            webpage['mainEntity'] = {'@id': url+'#article'}
            # Make the organizational authorship visible; do not invent a named author.
            if 'class="article-byline"' not in s:
                s = re.sub(r'(</h1>)', r'\1<p class="article-byline">By Utana Agentic Technologies · Workflow design</p>', s, count=1)
        elif path.parts[0] == 'services':
            graph.append({'@type': 'Service', '@id': url+'#service', 'name': heading, 'serviceType': heading, 'description': description, 'url': url, 'provider': {'@id': BASE+'#organization'}, 'areaServed': 'Worldwide'})
            webpage['mainEntity'] = {'@id': url+'#service'}
        elif path.name == 'sapiens4.html':
            graph.append({'@type': 'SoftwareApplication', '@id': url+'#software', 'name': 'sapiens4', 'url': 'https://sapiens4.ai/', 'downloadUrl': 'https://github.com/aleski-green/sapiens4', 'operatingSystem': ['macOS 13+', 'Windows 10', 'Windows 11'], 'applicationCategory': 'BusinessApplication', 'license': 'https://github.com/aleski-green/sapiens4/blob/main/license/LICENSE.md', 'description': 'Source-available software with local agents and computer access for business process automation. Free for permitted personal and internal business use under its license.'})
            webpage['mainEntity'] = {'@id': url+'#software'}
        graph.append(webpage)
        bits.append('<script type="application/ld+json">'+json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')+'</script>')
        pages.append((url, heading or title, description))
    bits.append(END)
    s = s.replace('</head>', ''.join(bits)+'</head>', 1)
    file.write_text(s)

ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
tree = ET.Element(ns+'urlset')
for url, _, _ in pages:
    ET.SubElement(ET.SubElement(tree, ns+'url'), ns+'loc').text = url
ET.indent(tree)
(ROOT/'sitemap.xml').write_bytes(ET.tostring(tree, encoding='utf-8', xml_declaration=True)+b'\n')
(ROOT/'robots.txt').write_text('''# Public production pages may be crawled. Preview pages carry noindex in HTML.
User-agent: *
Allow: /

# Search discovery; model-training crawler preferences are independent.
User-agent: OAI-SearchBot
Allow: /

Sitemap: https://utana.group/sitemap.xml
''')
directory = '''# Utana

> Utana Agentic Technologies LLC helps businesses worldwide with AI automation for marketing, sales, and operations. Based in Dubai.

This directory links to public pages. The linked HTML pages are the authoritative service descriptions. Workflow guides describe proposed implementations, not measured customer outcomes.

## Services and company
'''
for url, title, description in pages:
    if '/blog/' not in url and '/use-cases/' not in url and not url.endswith('privacy.html'):
        directory += f'- [{title}]({url}): {description}\n'
directory += '\n## Workflow guides and insights\n'
for url, title, description in pages:
    if '/blog/' in url or '/use-cases/' in url:
        directory += f'- [{title}]({url}): {description}\n'
directory += '''
## Contact and policies
- Email: sapiens@utana.group
- Phone: +971 58 660 1017
- [Technology and model policy](https://utana.group/technology.html#model-policy): Utana does not use Claude models in business workflows.
- [Privacy](https://utana.group/privacy.html)
- [Sitemap](https://utana.group/sitemap.xml)
- [sapiens4 official website](https://sapiens4.ai/): source-available software for macOS and Windows; permitted free use is subject to the project license.
'''
(ROOT/'llms.txt').write_text(directory)
print(f'Generated metadata and sitemap for {len(pages)} production pages; excluded previews and redirects.')
