#!/usr/bin/env python3
"""Перенос доски Miro в разработку «Клетки».

Читает выгрузку доски (JSON из REST API Miro: items и connectors), скачивает картинки
и пишет папку для кнопки «Импорт из Miro: папка» в «Разработках»:
  <out>/board.json   — разработка в формате доски «Клетки»
  <out>/img/<id>.*   — картинки; в board.json у них src "miro:<id>"
  <out>/img/x<id>.png — картинка, обрезанная как в Miro (src "miro:x<id>")

Рядом с board.json могут лежать exact.json (обрезка и рамка каждой картинки) и order.json
(порядок слоёв снизу вверх) — их снимают со страницы доски, см. docs/BOARDS.md.

Ключ Miro только на чтение (boards:read), в Miro ничего не меняется.
Запуск: python3 miro2kletka.py <выгрузка.json> <папка> [--no-images]
"""
import json, os, re, sys, html, statistics, urllib.request, concurrent.futures

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'miro-token.txt')

STICKY = {'gray': '#F5F6F8', 'light_yellow': '#FFF9B1', 'yellow': '#F5D128', 'orange': '#FF9D48',
          'light_green': '#D5F692', 'green': '#C9DF56', 'dark_green': '#93D275', 'cyan': '#67C6C0',
          'light_pink': '#FFCEE0', 'pink': '#EA94BB', 'violet': '#C6A2D2', 'red': '#F0939D',
          'light_blue': '#A6CCF5', 'blue': '#6CD8FA', 'dark_blue': '#9EA9FF', 'black': '#1A1A1A'}
SHAPES = {'rectangle': 'rect', 'round_rectangle': 'round', 'circle': 'ellipse', 'cloud': 'cloud',
          'star': 'star', 'triangle': 'tri', 'rhombus': 'rhomb', 'right_arrow': 'arrow'}
FONTS = {'lemon_tuesday': 'hand', 'caveat': 'hand', 'spoof': 'open',
         'open_sans': 'open', 'noto_sans': 'noto', 'arial': 'arial', 'roboto': 'roboto', 'pt_sans': 'ptsans',
         'pt_sans_narrow': 'narrow', 'plex_sans': 'plexsans', 'roobert': 'noto',
         'georgia': 'georgia', 'pt_serif': 'book', 'eb_garamond': 'garamond', 'roboto_slab': 'slab',
         'plex_serif': 'plexserif', 'tiempos_text': 'georgia', 'plex_mono': 'plexmono', 'roboto_mono': 'robomono',
         'fredoka_one': 'fredoka', 'rammetto_one': 'rammetto', 'gravitas_one': 'gravitas', 'permanent_marker': 'marker',
         'titan_one': 'titan', 'abril_fatface': 'abril', 'nixie_one': 'nixie'}
ALIGN = {'left': 'left', 'center': 'center', 'right': 'right'}


def color(c, op=None, default='#FFFFFF'):
    """Цвет Miro (#rrggbb или имя стикера) и прозрачность → #rrggbb или #rrggbbaa."""
    if not c:
        return default
    c = STICKY.get(c, c)
    if not re.fullmatch(r'#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?', c):
        return default
    c = c[:7].upper()
    try:
        a = float(op) if op is not None else 1.0
    except ValueError:
        a = 1.0
    return c if a >= .995 else c + '%02X' % max(0, min(255, round(a * 255)))


def plain(h):
    h = re.sub(r'<br\s*/?>', '\n', h or '')
    h = re.sub(r'</p>\s*<p[^>]*>', '\n', h)
    return html.unescape(re.sub(r'<[^>]+>', '', h)).strip('\n')


def res_id(url):
    m = re.search(r'/resources/images/(\d+)', url or '')
    return m and m.group(1)


EXACT, ORDER = {}, {}


def cropped(e):
    """Обрезана ли картинка в Miro: рамка обрезки меньше самой картинки."""
    x, y, w, h = e['crop']
    W, H = e['res']
    return x > 0 or y > 0 or abs(w - W) > 1 or abs(h - H) > 1


def convert(dump):
    items = dump['items']
    by = {i['id']: i for i in items}
    frames = [i for i in items if i['type'] == 'frame']
    widths = [f['geometry']['width'] for f in frames if f['geometry'].get('width')]
    # весь масштаб доски один: средний фрейм становится шириной 2000, расположение сохраняется
    k = 2000 / statistics.median(widths) if widths else .1

    cache = {}

    def center(it):
        if it['id'] in cache:
            return cache[it['id']]
        p = it.get('position') or {}
        x, y = p.get('x', 0), p.get('y', 0)
        par = it.get('parent') and by.get(it['parent']['id'])
        if par and p.get('relativeTo') == 'parent_top_left':
            px, py = center(par)
            g = par.get('geometry', {})
            x += px - g.get('width', 0) / 2
            y += py - g.get('height', 0) / 2
        cache[it['id']] = (x, y)
        return x, y

    def box(it, hdef=None):
        g = it.get('geometry') or {}
        w = g.get('width') or 0
        h = g.get('height') or hdef or w
        cx, cy = center(it)
        return (cx - w / 2) * k, (cy - h / 2) * k, w * k, h * k

    def txt(it, out, fsdef):
        st = it.get('style') or {}
        content = (it.get('data') or {}).get('content') or ''
        out['text'] = plain(content)
        if re.search(r'<(strong|b|em|i|u|s|a|span|ol|ul|li)\b', content) or content.count('<p') > 1:
            out['html'] = content
        try:
            out['fs'] = round(float(st['fontSize']) * k, 1)
        except (KeyError, ValueError):
            out['fs'] = fsdef
        if st.get('color'):
            out['color'] = color(st['color'], default='#1A1A1A')
        out['al'] = ALIGN.get(st.get('textAlign'), 'center' if it['type'] != 'text' else 'left')
        ff = FONTS.get(st.get('fontFamily'))
        if ff:
            out['ff'] = ff
        if (st.get('textAlignVertical') or 'middle') != 'middle':
            out['va'] = st['textAlignVertical']

    out, skipped, lines = [], {}, []
    # слои как в Miro: фреймы снизу, дальше по order.json; чего там нет — сверху по времени создания
    last = len(ORDER)
    order = sorted(items, key=lambda i: (i['type'] != 'frame', ORDER.get(i['id'], last), i.get('createdAt', '')))
    for it in order:
        t, st, d = it['type'], it.get('style') or {}, it.get('data') or {}
        rot = (it.get('geometry') or {}).get('rotation') or 0
        if t == 'frame':
            x, y, w, h = box(it)
            o = {'id': 'm' + it['id'], 't': 'frame', 'x': x, 'y': y, 'w': w, 'h': h,
                 'fill': color(st.get('fillColor')), 'text': html.unescape(d.get('title') or ''), 'lock': False}
        elif t == 'image':
            x, y, w, h = box(it)
            rid = res_id(d.get('imageUrl'))
            if not rid:
                skipped[t] = skipped.get(t, 0) + 1
                continue
            e = EXACT.get(it['id'])
            o = {'id': 'm' + it['id'], 't': 'image', 'x': x, 'y': y, 'w': w, 'h': h,
                 'src': 'miro:' + ('x' + it['id'] if e and cropped(e) else rid)}
            bs = (e or {}).get('style')
            if bs and bs.get('brc', -1) >= 0 and bs.get('brw', 0) > 0:
                o['bc'] = color('#%06X' % bs['brc'], bs.get('bro'))
                o['bw'] = max(1, round(bs['brw'] * k, 1))
                if bs.get('brr'):
                    o['br'] = round(bs['brr'] * k, 1)
        elif t == 'shape':
            x, y, w, h = box(it)
            bw = float(st.get('borderWidth') or 0)
            bop = float(st.get('borderOpacity') or 1)
            o = {'id': 'm' + it['id'], 't': 'shape', 'k': SHAPES.get(d.get('shape'), 'rect'), 'x': x, 'y': y, 'w': w, 'h': h,
                 'fill': color(st.get('fillColor'), st.get('fillOpacity'), '#FFFFFF00'),
                 'stroke': color(st.get('borderColor'), bop, '#1A1A1A'),
                 'sw': 0 if bw <= 0 or bop <= 0 else max(1, round(bw * k, 1))}
            if st.get('borderStyle') in ('dashed', 'dotted'):
                o['dash'] = 'dash' if st['borderStyle'] == 'dashed' else 'dot'
            txt(it, o, 24)
        elif t == 'sticky_note':
            x, y, w, h = box(it)
            o = {'id': 'm' + it['id'], 't': 'sticky', 'x': x, 'y': y, 'w': w, 'h': h, 'fill': color(st.get('fillColor'), default='#FFF9B1')}
            txt(it, o, 0)
            if not o.get('fs'):
                # в Miro размер текста стикера подбирается сам: подбираем так же по длине самой длинной строки
                ln = o['text'].split('\n') or ['']
                longest = max(len(s) for s in ln) or 1
                o['fs'] = round(max(8, min(h * .28, w * .9 / (longest * .55), h * .8 / (len(ln) * 1.3))), 1)
            o['color'] = o.get('color', '#1A1A1A')
        elif t == 'text':
            g = it.get('geometry') or {}
            o = {'id': 'm' + it['id'], 't': 'text'}
            txt(it, o, 32)
            nl = o['text'].count('\n') + 1
            x, y, w, h = box(it, hdef=float(st.get('fontSize') or 24) * 1.3 * nl)
            o.update({'x': x, 'y': y, 'w': w, 'h': h})
            if st.get('fillColor') and float(st.get('fillOpacity') or 0) > 0:
                o['bg'] = color(st['fillColor'], st.get('fillOpacity'))
        elif t == 'card':
            x, y, w, h = box(it)
            o = {'id': 'm' + it['id'], 't': 'shape', 'k': 'round', 'x': x, 'y': y, 'w': w, 'h': h,
                 'fill': '#FFFFFF', 'stroke': color(st.get('cardTheme'), default='#2D9BF0'), 'sw': 2,
                 'text': plain(d.get('title')), 'fs': round(max(10, h * .3), 1), 'color': '#1A1A1A', 'al': 'left'}
            if re.search(r'<(strong|b|em|i|u|s|a|span)\b', d.get('title') or ''):
                o['html'] = d['title']
        elif t == 'embed':
            x, y, w, h = box(it)
            url = d.get('url') or (re.search(r'src="([^"]+)"', d.get('html') or '') or [None, ''])[1]
            title = html.unescape(d.get('title') or url)
            o = {'id': 'm' + it['id'], 't': 'shape', 'k': 'round', 'x': x, 'y': y, 'w': w, 'h': h,
                 'fill': '#F5F6F8', 'stroke': '#C9CED8', 'sw': 1, 'text': title + '\n' + url,
                 'html': f'<p><strong>{html.escape(title)}</strong></p><p><a href="{html.escape(url)}" target="_blank">Открыть ↗</a></p>',
                 'fs': round(max(12, min(w / 14, h / 5)), 1), 'color': '#1A1A1A', 'al': 'center'}
        else:
            skipped[t] = skipped.get(t, 0) + 1
            continue
        if rot:
            o['rot'] = round(rot, 2)
        out.append(o)

    # стрелки между объектами: точка на краю объекта в долях его рамки
    pos = {o['id']: o for o in out}
    for c in dump.get('connectors', []):
        ends = []
        for key in ('startItem', 'endItem'):
            e = c.get(key) or {}
            o = pos.get('m' + str(e.get('id')))
            if not o:
                break
            p = e.get('position') or {'x': '50%', 'y': '50%'}
            fx, fy = float(str(p['x']).rstrip('%')) / 100, float(str(p['y']).rstrip('%')) / 100
            ends.append((o['x'] + fx * o['w'], o['y'] + fy * o['h']))
        if len(ends) != 2:
            skipped['connector'] = skipped.get('connector', 0) + 1
            continue
        (x1, y1), (x2, y2) = ends
        st = c.get('style') or {}
        ln = {'id': 'm' + c['id'], 't': 'line', 'color': color(st.get('strokeColor'), default='#333333'),
              'sw': max(2, round(float(st.get('strokeWidth') or 2) * max(k, .5), 1)),
              'a2': (st.get('endStrokeCap') or 'none') != 'none', 'a1': (st.get('startStrokeCap') or 'none') != 'none'}
        if st.get('strokeStyle') in ('dashed', 'dotted'):
            ln['dash'] = 'dash' if st['strokeStyle'] == 'dashed' else 'dot'
        P = [x1, y1, (x1 + x2) / 2, (y1 + y2) / 2, x2, y2]
        xs, ys = P[0::2], P[1::2]
        x, y = min(xs), min(ys)
        w, h = max(1, max(xs) - x), max(1, max(ys) - y)
        ln.update({'x': x, 'y': y, 'w': w, 'h': h, 'p': [round((v - y) / h if i % 2 else (v - x) / w, 4) for i, v in enumerate(P)]})
        lines.append(ln)

    for o in out + lines:
        for key in ('x', 'y', 'w', 'h'):
            o[key] = round(o[key], 1)
    # доска начинается около нуля
    if out:
        mx, my = min(o['x'] for o in out), min(o['y'] for o in out)
        for o in out + lines:
            o['x'] = round(o['x'] - mx, 1)
            o['y'] = round(o['y'] - my, 1)
    return out + lines, skipped, k


def download(dump, folder):
    tok = open(TOKEN_FILE).read().strip()
    os.makedirs(folder, exist_ok=True)
    urls = {}
    for i in dump['items']:
        if i['type'] == 'image':
            rid = res_id(i['data'].get('imageUrl'))
            if rid:
                urls[rid] = i['data']['imageUrl'].replace('format=preview', 'format=original')

    def one(rid):
        if any(f.startswith(rid + '.') for f in os.listdir(folder)):
            return 'есть'
        for attempt in range(3):
            try:
                r = urllib.request.Request(urls[rid], headers={'Authorization': 'Bearer ' + tok})
                link = json.load(urllib.request.urlopen(r, timeout=60))['url']
                data = urllib.request.urlopen(link, timeout=120).read()
                ext = re.search(r'/original\.(\w+)', link)
                ext = ext.group(1).lower() if ext else 'png'
                with open(os.path.join(folder, f'{rid}.{ext}'), 'wb') as f:
                    f.write(data)
                return 'ok'
            except Exception as e:
                err = e
        return f'ошибка {err}'

    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(one, urls))
    return len(urls), sum(r != 'ok' and r != 'есть' for r in res)


def crop_images(dump, folder):
    """Режет оригиналы так же, как они обрезаны на доске: img/x<id>.png."""
    from PIL import Image
    files = {f.split('.')[0]: f for f in os.listdir(folder)}
    n = bad = 0
    for i in dump['items']:
        e = EXACT.get(i['id'])
        if i['type'] != 'image' or not e or not cropped(e):
            continue
        rid = res_id(i['data'].get('imageUrl'))
        dst = os.path.join(folder, 'x' + i['id'] + '.png')
        if os.path.exists(dst):
            n += 1
            continue
        try:
            im = Image.open(os.path.join(folder, files[rid]))
            sx, sy = im.width / e['res'][0], im.height / e['res'][1]
            x, y, w, h = e['crop']
            im.crop((round(x * sx), round(y * sy), round((x + w) * sx), round((y + h) * sy))).save(dst)
            n += 1
        except Exception:
            bad += 1
    return n, bad


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    dump = json.load(open(src))
    for name, into in (('exact.json', EXACT), ('order.json', ORDER)):
        fp = os.path.join(dst, name)
        if os.path.exists(fp):
            data = json.load(open(fp))
            into.update(data if isinstance(data, dict) else {v: n for n, v in enumerate(data)})
    items, skipped, k = convert(dump)
    os.makedirs(dst, exist_ok=True)
    title = dump['board'].get('name') or os.path.splitext(os.path.basename(src))[0]
    json.dump({'title': title, 'from': 'miro', 'miroId': dump['board'].get('id'), 'items': items},
              open(os.path.join(dst, 'board.json'), 'w'), ensure_ascii=False)
    print(f'{title}: {len(items)} объектов, масштаб {k:.4f}, не переносится: {skipped}')
    if '--no-images' not in sys.argv:
        n, bad = download(dump, os.path.join(dst, 'img'))
        print(f'картинок {n}, не скачалось {bad}')
    if EXACT:
        n, bad = crop_images(dump, os.path.join(dst, 'img'))
        print(f'обрезанных картинок {n}, не вышло {bad}')
