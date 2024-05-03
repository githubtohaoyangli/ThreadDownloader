# -*- coding: utf-8 -*-
import ctypes
from argparse import ArgumentParser
from atexit import register
from os import remove, system, _exit
from random import uniform
from tempfile import TemporaryDirectory
from threading import Thread, active_count
from time import sleep, time
from urllib.parse import unquote_plus

from requests import head, get
from termcolor import cprint, colored
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

ap = ArgumentParser('Thread Downloader', 'Download files quickly.',
                    '''This is a thread downloader.\nYou can use it Download large file quickly.''')
ap.add_argument('--URL', '-u', type=str, required=True, help='URL')
ap.add_argument('--dir', '-d', type=str, required=True, help='Download dir')
ap.add_argument('--thread-count', '-t', type=int, required=False, default=16, choices=range(1, 1000),
                help='Thread count')
ap.add_argument('--retry', type=int, required=False, default=4, help='Retry num.')
meg = ap.add_mutually_exclusive_group()
meg.add_argument('--shut', '-S', action='store_true', required=False,
                 help='Use "shutdown /p" to shutdown your computer.')
meg.add_argument('--sleep', '-s', action='store_true', required=False, help='Use "shutdown /h" to sleep your computer.')
meg.add_argument('--reboot', '-r', action='store_true', required=False,
                 help='Use "shutdown /r /t 0" to reboot your computer.')
ap.add_argument('--no-ssl-verify', action='store_false', required=False, help='Skip SSL verify')
ap.add_argument('--http-proxy', type=str, required=False, default=None)
ap.add_argument('--https-proxy', type=str, required=False, default=None)
ap.add_argument('--buffer', type=int, required=False, default=4096, help='The buffering of downloading and copying')
args = vars(ap.parse_args())
del ap, meg


def trans_byte_unit(byte: int | float):
    if byte < 0: return '? K'
    result = byte
    for unit in ('K', 'M', 'G', 'T'):
        result /= 1024
        if result < 1024: return f'{result:.2f}{unit}'


def trans_time_unit(s):
    if s < 0: return '??:??:??'
    sec = int(s % 60)
    min = int((s // 60) % 60)
    hou = int(s // 60 // 60)
    if hou > 60: return f'++:{min:02}:{sec:02}'
    return f'{hou:02}:{min:02}:{sec:02}'


def download(url: str, _from: int, to: int, id: int, retry=4):
    global rates
    reponse = get(url, headers={'Range': f"bytes={_from}-{to}",
                                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"},
                  stream=True, verify=args['no_ssl_verify'],
                  proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
    if reponse.ok:
        try:
            size = int(reponse.headers['Content-Length'])
            finished = 0
            with open(tmpdir.name + f'\\{id}', 'wb+', buffering=buffer) as file:
                for ch in reponse.iter_content(buffer):
                    finished += file.write(ch)
                    rates[id] = finished / size
                reponse.close()
        except Exception as err:
            if retry == 0:
                cprint(f"\n\nError:{err}", 'red')
                _exit(1)
            download(url, _from, to, id, retry - 1)
    else:
        if retry == 0:
            cprint(f'\n\nError:{reponse.status_code} {reponse.reason}', 'red')
            _exit(1)
        download(url, _from, to, id, retry - 1)


def threads():
    global rates, over
    ts = []
    for i in range(args['thread_count']):
        start = each * i
        if i == args['thread_count']:
            end = LENGTH
        else:
            end = start + each
        rates[i] = 0
        t = Thread(target=download, args=(reponse.url, start, end - 1, i), daemon=True, name=f'Download {i}')
        t.start()
        ts.append(t)
        uniform(1, 5)
    del start, end, i
    for i in ts:
        i.join()
    over = True
    exit(0)


@register
def on_exit():
    try:
        tmpdir.cleanup()
    except OSError:
        cprint('\nTemp dir can\'t remove.', 'yellow')

    ctypes.windll.kernel32.SetThreadExecutionState(ctypes.c_uint(0))

    if args.get('shut', False):
        system('shutdown /p')
    elif args.get('sleep', False):
        system('shutdown /h')
    elif args.get('reboot', False):
        system('shutdown /r /t 0')


disable_warnings(InsecureRequestWarning)

ctypes.windll.kernel32.SetThreadExecutionState(0x00000001)

buffer = args['buffer']

cprint('Connecting to the server...', 'green',end='\r')
reponse = head(args['URL'], headers={
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"},
               allow_redirects=True, verify=args['no_ssl_verify'],
               proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
if not reponse.ok:
    cprint(f'Error:{reponse.status_code} {reponse.reason}', 'red')
    _exit(1)
if reponse.headers.get('Accept-Ranges') == 'bytes':
    pass
else:
    cprint('This server can\'t threading download.', 'red')
    _exit(1)
LENGTH = int(reponse.headers.get('Content-Length', 0))
_LENGTH = trans_byte_unit(LENGTH)

cp:str=reponse.headers.get('Content-Disposition','')
if cp.startswith('attachment;'):
    _name = cp.split('filename=')[1].strip('"\'')
else:
    v1 = reponse.url.rfind('/') + 1
    v2 = reponse.url.rfind('?', v1)
    if v2 == -1:
        _name = reponse.url[v1:].rstrip('?')
    else:
        _name = reponse.url[v1:v2]
    del v1, v2

_name = unquote_plus(_name)
name = input(colored(f'Please enter the file name(enter to default:"{_name}"):'))
if not name:
    FILENAME = _name
else:
    FILENAME = name
del name, _name

print('File name:' + colored(f'{FILENAME}', "blue"), 'Size:' + colored(f'{_LENGTH}B', 'blue'),
      'Type:' + colored(f'{reponse.headers.get("Content-Type")}', 'blue'), sep='\n')
if LENGTH == 0:
    cprint('File is empty.', 'red')
    _exit(1)
each = LENGTH // args['thread_count']

tmpdir = TemporaryDirectory(dir=args['dir'])

rates = {}
over = False
print("Progress(downloading):")
Thread(target=threads, daemon=True).start()
while True:
    start_time = time()
    start_rate = sum(rates.values()) / args['thread_count']
    sleep(0.3)
    try:
        speed = (sum(rates.values()) / args['thread_count'] - start_rate) / (time() - start_time)
        eta = (1 - sum(rates.values()) / args['thread_count']) / speed
    except ZeroDivisionError:
        speed = 0
        eta = 0

    rate = sum(rates.values()) / args['thread_count']
    print(f"\t{active_count() - 2:3} threads|",
          colored(f"{speed * 100:3.3f}%/s", 'light_yellow'), "|",
          colored(f"{rate * 100:3.2f}%", 'grey'), "[",
          colored(f"{round(rate * 50) * '-':-<50}", 'light_green'), "]",
          colored(f'eta {trans_time_unit(eta)}', 'blue'), '|',
          sep='', end='\r')
    if over:
        del rate, start_time, start_rate, rates
        break
cprint('\nDownloading is over.', 'green')

mfile = open(args['dir'] + '\\' + FILENAME, 'wb', buffering=buffer)

print("Progress(copying):")
rate = 0
finished = 0
for i in range(args['thread_count']):
    sfile = open(tmpdir.name + '\\' + str(i), 'rb')
    while True:
        data = sfile.read(buffer)
        if not data: break
        finished += mfile.write(data)
        rate = finished / LENGTH
        print(f"\t{rate * 100:.2f}%[",
              colored(f"{round(rate * 50) * '-':-<50}", 'green'), "]",
              sep='', end='\r')
    sfile.close()
    remove(sfile.name)
    mfile.flush()

cprint('\nDone.', 'green')
