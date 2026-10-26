# Обновляет в прототипе таблицу пропорций картинок ART_AR по файлам в папке art.
# Темы находят свои наборы по префиксу файла (pooh-1-top.webp → тема с art:'pooh'),
# поэтому после нарезки новых картинок достаточно запустить этот скрипт.
#   python3 tools/build-art.py ../prototype/kletka.html ../prototype/art
import json, os, re, sys
from PIL import Image

page, art = sys.argv[1], sys.argv[2]
ar = {}
for f in sorted(os.listdir(art)):
    if f.endswith('-top.webp') or f.endswith('-mid.webp'):
        w, h = Image.open(os.path.join(art, f)).size
        ar[f[:-5]] = round(w / h, 3)
s = open(page, encoding='utf-8').read()
s, n = re.subn(r'const ART_AR=\{[^\n]*\};', 'const ART_AR=' + json.dumps(ar, separators=(',', ':')) + ';', s)
assert n == 1, 'ART_AR not found'
open(page, 'w', encoding='utf-8').write(s)
print(len(ar) // 2, 'sets')
