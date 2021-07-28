#! /usr/bin/env python3

import requests
import os
import sys
import time
import random
import threading
import shutil
import math
from PIL import Image, ImageFont, ImageDraw
from http.server import BaseHTTPRequestHandler, HTTPServer

s = requests.session()
with open('.botkey', 'r') as f:
    botkey = f.read()
botkey = 'bot' + botkey
url = 'https://api.telegram.org'
res = s.get('{}/{}/getMe'.format(url, botkey))
print(res.json())

def tg_get_sticker(stickerset, offset):
    res = s.get('{}/{}/getStickerSet?name={}'.format(url, botkey, stickerset))
    j = res.json()
    print(j)
    sticker = j['result']['stickers'][offset]
    fid = sticker['file_id']
    animated = sticker['is_animated']
    res = s.get('{}/{}/getFile?file_id={}'.format(url, botkey, fid))
    j = res.json()
    fp = j['result']['file_path']
    res = s.get('{}/file/{}/{}'.format(url, botkey, fp))
    return (res.content, animated)

def get_compat_all(stickerset):
    res = s.get('{}/{}/getStickerSet?name={}'.format(url, botkey, stickerset))
    j = res.json()
    stickers = j['result']['stickers']
    w = stickers[0]['width']
    h = stickers[0]['height']
    count = len(stickers)
    for i in range(count):
        cache_path = 'cache/{}-{}.png'.format(stickerset, i)
        if os.path.isfile(cache_path):
            continue
        fid = stickers[i]['file_id']
        res = s.get('{}/{}/getFile?file_id={}'.format(url, botkey, fid))
        j = res.json()
        fp = j['result']['file_path']
        res = s.get('{}/file/{}/{}'.format(url, botkey, fp))
        tmp = '/tmp/{}-{}.webp'.format(stickerset, i)
        with open(tmp, 'wb') as f:
            f.write(res.content)
        os.system("convert {} {}".format(tmp, cache_path))
        os.remove(tmp)
    return (count, w, h)

def get_stickerset_tiled(stickerset):
    cache_path = 'cache/{}-m.png'.format(stickerset)
    if os.path.isfile(cache_path):
        with open(cache_path, 'rb') as f:
            return (f.read(), False)
    (count, w, h) = get_compat_all(stickerset)
    rows = math.ceil(count / 5)
    tw = int(w * 5 / 4)
    th = int(rows * h / 4)
    tgt = Image.new('RGBA', (tw, th), (255, 255, 255, 255))
    for i in range(count):
        img = Image.open('cache/{}-{}.png'.format(stickerset, i))
        img = img.resize((int(w/4), int(h/4)), Image.ANTIALIAS)
        draw = ImageDraw.Draw(img)
        draw.text((3,3), str(i))
        ox = int((i % 5)*w/4)
        oy = int(i/5) * int(h/4)
        tgt.paste(img, (ox, oy))
    tgt.save('cache/{}-m.png'.format(stickerset))
    with open(cache_path, 'rb') as f:
        return (f.read(), False)

def get_compat_sticker(stickerset, offset, resize):
    if resize:
        (data, anim) = get_compat_sticker(stickerset, offset, False)
        if anim:
            return (data, anim)
        cache_path = 'cache/{}-{}-s.png'.format(stickerset, offset)
        if os.path.isfile(cache_path):
            with open(cache_path, 'rb') as f:
                return (f.read(), False)
        img = Image.open('cache/{}-{}.png'.format(stickerset, offset))
        img = img.resize((int(img.size[0]/2), int(img.size[1]/2)), Image.ANTIALIAS)
        img.save(cache_path)
        with open(cache_path, 'rb') as f:
            return (f.read(), False)
    cache_path = 'cache/{}-{}.png'.format(stickerset, offset)
    if os.path.isfile(cache_path):
        with open(cache_path, 'rb') as f:
            return (f.read(), False)
    cache_path = 'cache/{}-{}.gif'.format(stickerset, offset)
    if os.path.isfile(cache_path):
        with open(cache_path, 'rb') as f:
            return (f.read(), True)
    (webp_data, animated) = tg_get_sticker(stickerset, offset)
    if animated:
        cache_path = 'cache/{}-{}.gif'.format(stickerset, offset)
        tmp = '/tmp/{}-{}.tgs'.format(stickerset, offset)
        with open(tmp, 'wb') as f:
            f.write(webp_data)
        os.system('docker run --rm -v /tmp:/source tgs-to-gif')
        os.remove(tmp)
        shutil.copy(tmp + '.gif', cache_path)
        os.remove(tmp + '.gif')
        with open(cache_path, 'rb') as f:
            return (f.read(), True)
    else:
        cache_path = 'cache/{}-{}.png'.format(stickerset, offset)
        tmp = '/tmp/{}-{}.webp'.format(stickerset, offset)
        with open(tmp, 'wb') as f:
            f.write(webp_data)
        os.system("convert {} {}".format(tmp, cache_path))
        os.remove(tmp)
        with open(cache_path, 'rb') as f:
            return (f.read(), False)

def tile_list():
    res = list()
    for f in os.listdir('cache'):
        if f.endswith('-m.png'):
            res.append(f[0:-6])
    return res

MAP = """
<html>
<body>
<a href='/@STICKERSET@/q'>
 <img src='/@STICKERSET@' ismap>
</a>
</body>
</html>
"""

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = self.path.split('?')
        url = qs[0]
        query = qs[1] if len(qs) > 1 else ''
        comps = url.split('/')[1:]
        stickerset = comps[0]
        if len(comps) == 1:
            if comps[0] == 'listall':
                res = '<html><body>'
                for s in tile_list():
                    res += '<a href="/{}/map">{}</a><br/>'.format(s, s)
                res += '</body></html>'
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(res.encode())
                return
            if comps[0] == 'showall':
                res = '<html><body>'
                for s in tile_list():
                    res += '<a href="/{}/map"><img src="/{}" width=320></a>'.format(s, s)
                res += '</body></html>'
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(res.encode())
                return
            (payload, animated) = get_stickerset_tiled(stickerset)
        else:
            if comps[1] == 'map':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(MAP.replace('@STICKERSET@', stickerset).encode())
                return
            if comps[1] == 'q':
                scoords = query.split(',')
                x = int(scoords[0])
                y = int(scoords[1])
                ox = int(x / 128)
                oy = int(y / 128)
                self.send_response(301)
                self.send_header('Location', '/' + stickerset + '/' + str(oy*5+ox))
                self.end_headers()
                return
            offset = int(comps[1])
            (payload,animated) = get_compat_sticker(stickerset, offset, len(comps) > 2 )
        self.send_response(200)
        self.send_header("Content-type", "image/gif" if animated else "image/png")
        self.send_header("Content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

webServer = HTTPServer(('0.0.0.0', 8989), MyServer)
webServer.serve_forever()