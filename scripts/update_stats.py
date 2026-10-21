"""Refresh public GitHub stats, preserving the last valid SVG on failure."""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import time

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assets' / 'github-stats.svg'
PARAMS = dict(username='YossofAlmadhagi', show_icons='true', hide_rank='true',
              hide_border='false', border_radius='14', border_color='294558',
              bg_color='0A192B', title_color='8BECD8', text_color='C5D4E5',
              icon_color='79C9ED', custom_title='Public GitHub activity',
              disable_animations='true')
URL = 'https://github-readme-stats.vercel.app/api?' + urlencode(PARAMS)


def validate_svg(data):
    if len(data) > 200_000:
        raise ValueError('Stats response exceeds expected size')
    root = ET.fromstring(data)
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('Response is not an SVG')
    words = ' '.join(root.itertext()).lower()
    if not all(label in words for label in ('total stars', 'total commits', 'total prs')):
        raise ValueError('Response does not contain expected statistics')
    if 'something went wrong' in words or 'could not fetch' in words:
        raise ValueError('Stats provider returned an error card')
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1] in ('script', 'foreignObject', 'image'):
            raise ValueError('Unexpected embedded content in statistics')
        if any(key.lower().startswith('on') or key.rsplit('}', 1)[-1] == 'href'
               for key in node.attrib):
            raise ValueError('Unexpected external reference in statistics')
    return data


def main():
    last_error = None
    for attempt in range(3):
        try:
            req = Request(URL, headers={'User-Agent': 'YossofAlmadhagi-profile'})
            with urlopen(req, timeout=40) as response:
                data = validate_svg(response.read(200_001))
            DEST.parent.mkdir(parents=True, exist_ok=True)
            pending = DEST.with_suffix('.tmp')
            pending.write_bytes(data)
            pending.replace(DEST)
            print('Public activity card updated.')
            return
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(3)
    raise RuntimeError('Refresh failed; previous statistics preserved.') from last_error


if __name__ == '__main__':
    main()
