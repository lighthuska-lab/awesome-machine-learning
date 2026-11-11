#!/usr/bin/env python3
"""Generate Packages.txt from the CRAN Machine Learning task view."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

VIEW_URL = 'https://cran.r-project.org/web/views/MachineLearning.html'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.label = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.label = []

    def handle_data(self, data):
        if self.href is not None:
            self.label.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, ''.join(self.label).strip()))
            self.href = None


class Heading(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.active = True

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


def fetch(url):
    with urlopen(url, timeout=30) as response:
        return response.read().decode('utf-8')


def generate(fetch_page=fetch):
    links = Links()
    links.feed(fetch_page(VIEW_URL))
    rows = []
    seen = set()
    for href, name in links.links:
        url = urljoin(VIEW_URL, href)
        parsed = urlparse(url)
        if (parsed.scheme != 'https' or parsed.netloc != 'cran.r-project.org'
                or not parsed.path.startswith('/web/packages/')
                or not parsed.path.endswith('/index.html') or not name or url in seen):
            continue
        seen.add(url)
        heading = Heading()
        heading.feed(fetch_page(url))
        description = ' '.join(''.join(heading.parts).split())
        if not description:
            raise ValueError(f'Missing package heading: {url}')
        rows.append(f' [{name}]({url}) - {description} \n')
    if not rows:
        raise ValueError('No package links found in CRAN task view')
    return ''.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('Packages.txt'))
    args = parser.parse_args()
    # Complete all network operations before touching an existing output file.
    result = generate()
    args.output.write_text(result, encoding='utf-8')


if __name__ == '__main__':
    main()
