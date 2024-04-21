# -*- coding: utf-8 -*-
import ctypes
from argparse import ArgumentParser
from atexit import register
from os import remove, listdir, system, _exit
from random import uniform
from tempfile import TemporaryDirectory
from threading import Thread, enumerate
from time import sleep

from requests import head, get
from termcolor import cprint, colored
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

ap = ArgumentParser('Thread Downloader', 'Download files quickly.',
                    '''This is a thread downloader.\nYou can use it Download large file quickly.''')
ap.add_argument('--URL', '-u', type=str, required=True, help='URL')
ap.add_argument('--dir', '-d', type=str, required=True, help='Download dir')
ap.add_argument('--thread-num', '-t', type=int, required=False, default=16, help='Thread num')
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
ap.add_argument('--buffer', type=int, required=False, default=1048576, help='The buffering of downloading and copying')
args = vars(ap.parse_args())
del ap, meg


def download(url: str, _from: int, to: int, id, retry=4):
    global rates, FILE
    reponse = get(url, headers={'Range': f"bytes={_from}-{to}",
                                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"},
                  stream=True, verify=args['no_ssl_verify'],
                  proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
    if reponse.ok:
        try:
            length = int(reponse.headers['Content-Length'])
            with open(tmpdir.name + f'\\{id}', 'wb+', buffering=buffer) as file:
                finished = 0
                for ch in reponse:
                    finished += file.write(ch)
                    rates[id] = finished / length
                reponse.close()
        except Exception as err:
            if retry == 0:
                cprint(f"\n\nError:{err}", 'red')
                _exit()
            download(url, _from, to, id, retry - 1)
    else:
        if retry == 0:
            cprint(f'\n\nError:{reponse.status_code} {reponse.reason}', 'red')
            _exit()
        download(url, _from, to, id, retry - 1)


def threads():
    i = -1
    for i in range(0, args.get('thread_num') - 1):
        start, end = i * ONELENGTH, (i + 1) * ONELENGTH
        t = Thread(target=download, args=(reponse.url, start, end - 1, i), daemon=True)
        t.start()
        sleep(uniform(0, 2))
    start, end = i * ONELENGTH, (i + 1) * ONELENGTH
    t = Thread(target=download, args=(reponse.url, ONELENGTH * (i + 1), LENGTH, i + 1, args['retry']))
    t.start()

    del i, t
    while True:
        for thread in enumerate():
            if not thread.is_alive(): thread.join()


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

cprint('Finding file...', 'green')
reponse = head(args['URL'], allow_redirects=True, verify=args['no_ssl_verify'],
               proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
if not reponse.ok:
    cprint(f'Error:{reponse.status_code} {reponse.reason}', 'red')
    _exit(1)
if reponse.headers.get('Accept-Ranges') == 'bytes':
    cprint('Server support "Range" header.', 'green')
else:
    cprint('This server can\'t threading download.', 'red')
    _exit(1)
LENGTH = int(reponse.headers.get('Content-Length', 0))

v1 = reponse.url.rfind('/') + 1
v2 = reponse.url.rfind('?', v1)
if v2 == -1:
    _name = reponse.url[v1:].rstrip('?')
else:
    _name = reponse.url[v1:v2]
del v1, v2

name = input(colored(f'Please enter the file name[{_name}]:'))
if not name:
    FILENAME = _name
else:
    FILENAME = name
del name, _name

print('File found:' + colored(f'{FILENAME}', "blue"), 'Size:' + colored(f'{LENGTH} B', 'blue'),
      'Type:' + colored(f'{reponse.headers.get("Content-Type")}', 'blue'), sep='\n')
if LENGTH == 0:
    cprint('URL is not right.', 'red')
    _exit(1)
ONELENGTH = (LENGTH - 1) // args.get('thread_num')

tmpdir = TemporaryDirectory(dir=args['dir'])

rates = {}

Thread(target=threads, daemon=True).start()
while True:
    try:
        rate = sum(rates.values()) / args['thread_num']
    except ZeroDivisionError:
        rate = 0.0
    print(f"Progress(downloading):{rate * 100:.2f}%[", colored(f"{round(rate * 50) * '-': <50}", 'green'),
          f"] {len(enumerate()) - 2} threads", sep='', end='\r')
    if rate == 1: break
cprint('\nDownloading is over.', 'green')

mfile = open(args.get('dir') + '\\' + FILENAME, 'wb', buffering=buffer)
for i in range(0, listdir(tmpdir.name).__len__()):
    sfile = open(tmpdir.name + '\\' + str(i), 'rb')
    finished = 0
    while True:
        data = sfile.read(buffer)
        if not data: break
        finished += mfile.write(data)
        rate = finished / LENGTH
        print(f"Progress(copying {i + 1}/{args['thread_num']}):{rate * 100:.2f}%[",
              colored(f"{round(rate * 50) * '-': <50}", 'green'), "]",
              sep='', end='\r')
    sfile.close()
    remove(sfile.name)
    mfile.flush()

cprint('\nDone.', 'green')
