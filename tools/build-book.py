#!/usr/bin/env python3
"""Собирает единый book.md из страниц руководства по оглавлению README."""
import re, sys, pathlib, urllib.request, hashlib, argparse

STRINGS = {
    'ru': {
        'title': 'Контр-ОСИНТ: руководство по приватности',
        'lead': 'Как не дать собрать на себя досье. Руководство для Рунета и стран СНГ.',
        'edition': 'Издание от {date}.',
        'actual': '**Актуальная версия и другие форматы: {addr}**',
        'license': 'Материалы распространяются на условиях Creative Commons '
                   'Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). Вы можете свободно '
                   'копировать, распространять и перерабатывать их, в том числе в коммерческих '
                   'целях, при условии указания авторства и распространения производных работ '
                   'под той же лицензией.',
        'colophon_head': 'Об этом издании',
        'colophon': 'Книга собрана автоматически из исходного текста руководства, который '
                    'ведётся в открытом репозитории. Содержание и опечатки правятся там же.',
        'stale': 'Если вы читаете устаревшую копию — по этому адресу всегда лежит свежая.',
        'stub': r'Раздел будет дополняться|Здесь будет глава',
        'site_path': '',
    },
    'en': {
        'title': 'Counter-OSINT: a guide to protecting your personal data',
        'lead': 'How to keep others from building a dossier on you. Written for Russia '
                'and the CIS, useful anywhere.',
        'edition': 'Edition of {date}.',
        'actual': '**The current version and other formats: {addr}**',
        'license': 'This work is distributed under the Creative Commons '
                   'Attribution-ShareAlike 4.0 International licence (CC BY-SA 4.0). You are '
                   'free to copy, distribute and adapt it, including commercially, as long as '
                   'you give credit and release derivative works under the same licence.',
        'colophon_head': 'About this edition',
        'colophon': 'The book is built automatically from the source text of the guide, which '
                    'lives in an open repository. Content and typos are fixed there.',
        'stale': 'If you are reading an outdated copy, the latest one is always at that address.',
        'stub': r'The section will be updated|This chapter is coming',
        'site_path': '/en',
    },
}
SITE = 'counter-osint.soxoj.com'

ap = argparse.ArgumentParser()
ap.add_argument('repo')
ap.add_argument('out')
ap.add_argument('--lang', default='ru', choices=sorted(STRINGS))
ap.add_argument('--format', default='pdf')
ap.add_argument('--date', default='без даты')
args = ap.parse_args()

REPO, OUT, S = pathlib.Path(args.repo), pathlib.Path(args.out), STRINGS[args.lang]
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'img').mkdir(exist_ok=True)

readme = (REPO / 'README.md').read_text(encoding='utf-8')
order = []
for m in re.finditer(r'\]\(\./pages/([a-z0-9-]+\.md)\)', readme):
    if m.group(1) not in order:
        order.append(m.group(1))
print(f'страниц в оглавлении: {len(order)}')

def grab_image(url):
    name = hashlib.sha1(url.encode()).hexdigest()[:12] + '.png'
    dst = OUT / 'img' / name
    if not dst.exists():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            dst.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print(f'  не скачал {url[:60]}: {e}')
            return None
    return f'img/{name}'

def slug(h):
    h = h.strip().lower()
    return '#' + ''.join(c for c in h if c.isalnum() or c in ' -_').replace(' ', '-')

anchors = {}
for page in order:
    for line in (REPO / 'pages' / page).read_text(encoding='utf-8').split('\n'):
        if line.startswith('# '):
            anchors[page] = slug(line[2:]); break

parts, missed = [], 0
for page in order:
    text = (REPO / 'pages' / page).read_text(encoding='utf-8')
    text = re.sub(r'\n---\n\n\[⬅️.*$', '', text, flags=re.S)
    text = re.sub(r'\]\(\./([a-z0-9-]+)\.md(?:#[^)]*)?\)',
                  lambda m: f']({anchors.get(m.group(1) + ".md", "#")})', text)
    text = re.sub(r'counter-osint\+[a-z]+@soxoj\.com', 'counter-osint+book@soxoj.com', text)
    text = text.replace('../img/', 'img/')
    for url in set(re.findall(r'https://user-images\.githubusercontent\.com[^\s")]+', text)):
        local = grab_image(url)
        if local:
            text = text.replace(url, local)
        else:
            missed += 1
    parts.append(text.strip())

for src in (REPO / 'img').glob('*.png'):
    (OUT / 'img' / src.name).write_bytes(src.read_bytes())

label = f"{SITE}{S['site_path']}/{ {'html': 'pdf'}.get(args.format, args.format) }"
addr = f'[{label}](https://{label})' if args.format in ('pdf', 'html') else label
edition = S['edition'].format(date=args.date)
actual = S['actual'].format(addr=addr)

title = f"# {S['title']}\n\n{S['lead']}\n\n{edition}\n\n{actual}\n\n{S['license']}\n"
colophon = (f"# {S['colophon_head']}\n\n{S['colophon']}\n\n{edition}\n\n{actual}\n\n{S['stale']}\n")

(OUT / 'book.md').write_text(
    title + '\n\n\\newpage\n\n'
    + '\n\n\\newpage\n\n'.join(parts)
    + '\n\n\\newpage\n\n' + colophon, encoding='utf-8')

stubs = sum(len(re.findall(S['stub'], t)) for t in parts)
print(f'собрано: {len(parts)} страниц, картинок не скачалось: {missed}')
print(f'незаполненных разделов в книге: {stubs}')
