# -*- coding: utf-8 -*-
import ctypes
from argparse import ArgumentParser
from atexit import register
from os import remove, listdir, system, _exit
from random import uniform
from tempfile import TemporaryDirectory
from threading import Thread, enumerate, active_count
from time import sleep, time

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
ap.add_argument('--buffer', type=int, required=False, default=1048576, help='The buffering of downloading and copying')
args = vars(ap.parse_args())
del ap, meg


def trans_byte_unit(byte: int | float):
    result=byte
    for unit in ('K','M','G','T'):
        result/=1024
        if result<1024:return f'{result:.2f}{unit}'


def trans_time_unit(s):
    sec=int(s%60)
    min=int((s//60)%60)
    hou=int(s//60//60)
    return f'{hou:02}:{min:02}:{sec:02}'


def download(url: str, _from: int, to: int, id, retry=4):
    global FILE, size
    reponse = get(url, headers={'Range': f"bytes={_from}-{to}"},
                  stream=True, verify=args['no_ssl_verify'],
                  proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
    if reponse.ok:
        try:
            length = int(reponse.headers['Content-Length'])
            with open(tmpdir.name + f'\\{id}', 'wb+', buffering=buffer) as file:
                finished = 0
                for ch in reponse:
                    size += file.write(ch)
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
    for i in range(0, args.get('thread_count') - 1):
        start, end = i * each, (i + 1) * each
        t = Thread(target=download, args=(reponse.url, start, end - 1, i), daemon=True)
        t.start()
        sleep(uniform(0, 2))
    start, end = i * each, (i + 1) * each
    t = Thread(target=download, args=(reponse.url, each * (i + 1), LENGTH, i + 1, args['retry']))
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

cprint('Connecting to the server...', 'green')
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
_LENGTH = trans_byte_unit(LENGTH)

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

print('File name:' + colored(f'{FILENAME}', "blue"), 'Size:' + colored(f'{_LENGTH} B', 'blue'),
      'Type:' + colored(f'{reponse.headers.get("Content-Type")}', 'blue'), sep='\n')
if LENGTH == 0:
    cprint('File is empty.', 'red')
    _exit(1)
each = (LENGTH - 1) // args.get('thread_count')

tmpdir = TemporaryDirectory(dir=args['dir'])

size = 0

Thread(target=threads, daemon=True).start()
while True:
    start_time = time()
    start_size = size
    rate = size / LENGTH
    sleep(0.5)
    try:
        speed = (size - start_size) / (time() - start_time)
        eta=(LENGTH-size)/speed
    except ZeroDivisionError:
        speed = 0
        eta=0
    print(
        f"Progress(downloading): {active_count() - 2:03} threads {trans_byte_unit(speed):6}/s {trans_byte_unit(size):6}/{_LENGTH:6} {rate * 100:.2f}%[",
        colored(f"{round(rate * 50) * '-': <50}", 'green'),
        f"]",f'eta {trans_time_unit(eta)}', ' '*5, sep='', end='\r')
    if rate == 1: break
cprint('\nDownloading is over.', 'green')

mfile = open(args.get('dir') + '\\' + FILENAME, 'wb', buffering=buffer)

rate = 0
finished = 0
for i in range(0, listdir(tmpdir.name).__len__()):
    sfile = open(tmpdir.name + '\\' + str(i), 'rb')
    while True:
        data = sfile.read(buffer)
        if not data: break
        finished += mfile.write(data)
        rate = finished / LENGTH
        print(f"Progress(copying {i + 1}/{args['thread_count']}):{rate * 100:.2f}%[",
              colored(f"{round(rate * 50) * '-': <50}", 'green'), "]",
              sep='', end='\r')
    sfile.close()
    remove(sfile.name)
    mfile.flush()

cprint('\nDone.', 'green')
