# -*- coding: utf-8 -*-
import ctypes
import curses
from argparse import ArgumentParser
from atexit import register
from os import remove, system, _exit
from os.path import join
from random import uniform
from tempfile import TemporaryDirectory
from threading import Thread, active_count
from time import sleep, time
from urllib.parse import unquote_plus

from requests import head, get
from termcolor import cprint
from urllib3 import disable_warnings

ap = ArgumentParser('Thread Downloader', 'Download files quickly.',
                    '''This is a thread downloader.\nYou can use it Download large file quickly.''')
ap.add_argument('--URL', '-u', type=str, required=True, help='URL')
ap.add_argument('--dir', '-d', type=str, required=True, help='Download dir')
ap.add_argument('--thread-count', '-t', type=int, required=False, default=16,
                help='Thread count')
ap.add_argument('--retry', type=int, required=False, default=4, help='Retry num.')
meg = ap.add_mutually_exclusive_group()
meg.add_argument('--shutdown', '-S', action='store_true', required=False,
                 help='Use "shutdown /p" to shutdown your computer.')
meg.add_argument('--sleep', '-s', action='store_true', required=False,
                 help='Use WindowsAPI to sleep your computer.')
meg.add_argument('--hibernation', '-H', action='store_true', required=False,
                 help='Use "shutdown /h" to hibernation your computer.')
meg.add_argument('--reboot', '-r', action='store_true', required=False,
                 help='Use "shutdown /r /t 0" to reboot your computer.')
ap.add_argument('--no-ssl-verify', action='store_false', required=False, help='Skip SSL verify')
ap.add_argument('--http-proxy', type=str, required=False, default=None)
ap.add_argument('--https-proxy', type=str, required=False, default=None)
ap.add_argument('--buffer', type=int, required=False, default=16384,
                help='The buffering of downloading and copying')
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
    global rates, size
    reponse = get(url, headers={'Range': f"bytes={_from}-{to}",
                                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                              "like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"},
                  stream=True, verify=args['no_ssl_verify'],
                  proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
    if reponse.ok:
        try:
            size_total = int(reponse.headers['Content-Length'])
            finished = 0
            with open(join(tmpdir.name, f'{id}.tmp'), 'wb+', buffering=buffer) as file:
                for ch in reponse:
                    added = file.write(ch)
                    size += added
                    finished += added
                    rates[id] = finished / size_total
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
            end = total
        else:
            end = start + each
        rates[i] = 0
        t = Thread(target=download, args=(response.url, start, end - 1, i), daemon=True, name=f'Download {i}')
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
    except:
        cprint('\nTemp dir can\'t remove.', 'yellow')

    SetThreadExecutionState(0x80000000)

    if args.get('shut', False):
        system('shutdown /p')
    elif args.get('sleep', False):
        SetSystemPowerState = ctypes.windll.kernel32.SetSystemPowerState
        SetSystemPowerState.argtypes = [ctypes.c_wchar_p, ctypes.c_bool]
        SetSystemPowerState.restype = ctypes.c_bool
        SetSystemPowerState(u'Monitor-timeout', True)

    elif args.get('hibernation', False):
        system('shutdown /h')
    elif args.get('reboot', False):
        system('shutdown /r /t 0')
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    cprint('Done.', 'green')


disable_warnings()

SetThreadExecutionState = ctypes.windll.kernel32.SetThreadExecutionState
SetThreadExecutionState.argtypes = [ctypes.c_uint32]
SetThreadExecutionState.restype = ctypes.c_uint32
SetThreadExecutionState(0x00000001 | 0x80000000)

buffer = args['buffer']

stdscr = curses.initscr()
curses.start_color()
curses.curs_set(False)

stdscr.addstr(curses.LINES // 5, curses.COLS // 5, 'Connecting to the server...', curses.color_pair(2))
stdscr.refresh()
response = head(args['URL'], headers={
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 "
                  "Safari/537.36 Edg/124.0.0.0"},
                allow_redirects=True, verify=args['no_ssl_verify'],
                proxies={'http': args['http_proxy'], 'https': args['https_proxy']})
if not response.ok:
    stdscr.clear()
    stdscr.addstr(curses.LINES // 5, curses.COLS // 5, f'Error:{response.status_code} {response.reason}',
                  curses.color_pair(2))
    stdscr.refresh()
    exit(1)
if response.headers.get('Accept-Ranges') == 'bytes':
    pass
else:
    stdscr.clear()
    stdscr.addstr(curses.LINES // 2, curses.COLS // 5, 'This server can\'t threading download.', curses.color_pair(2))
    stdscr.refresh()
    exit(1)
total = int(response.headers.get('Content-Length', 0))
_total = trans_byte_unit(total)

cd: str = response.headers.get('Content-Disposition', '')
if cd.startswith('attachment;'):
    _name = cd.split('filename=')[1].strip('"\'')
else:
    v1 = response.url.rfind('/') + 1
    v2 = response.url.rfind('?', v1)
    if v2 == -1:
        _name = response.url[v1:].rstrip('?')
    else:
        _name = response.url[v1:v2]
    del v1, v2

_name = unquote_plus(_name)
stdscr.clear()
stdscr.addstr(curses.LINES // 5, curses.LINES // 5, f'Please enter the file name(default by"{_name}"):')
stdscr.refresh()
curses.curs_set(True)
name = stdscr.getstr().decode()
curses.curs_set(False)
if not name:
    FILENAME = _name
else:
    FILENAME = name
del name, _name

stdscr.clear()
stdscr.addstr(0, curses.COLS // 5, 'File name:' + f'{FILENAME}')
stdscr.addstr(1, curses.COLS // 5, 'Size:' + f'{_total}B')
stdscr.addstr(2, curses.COLS // 5, 'Type:' + response.headers.get("Content-Type"))
stdscr.refresh()
if total == 0:
    stdscr.addstr(4, curses.COLS // 5, 'File is empty.', curses.color_pair(1))
    stdscr.refresh()
    exit(1)
each = total // args['thread_count']

tmpdir = TemporaryDirectory(dir=args['dir'])

rates = {}
over = False
stdscr.addstr(5, curses.COLS // 5, "Downloading:")
Thread(target=threads, daemon=True).start()
while True:
    start_time = time()
    size = 0
    sleep(0.3)
    try:
        speed = size / (time() - start_time)
    except ZeroDivisionError:
        speed = 0

    rate = sum(rates.values()) / args['thread_count']
    stdscr.addstr(6, curses.COLS // 4, f"{active_count() - 2:3} threads")
    stdscr.addstr(7, curses.COLS // 4, f"{trans_byte_unit(speed):^8}/s")
    stdscr.addstr(8, curses.COLS // 4, f"{rate * 100:6.2f}%")
    stdscr.addstr(9, curses.COLS // 4, f"{round(rate * 50) * '▌':=<50}", curses.color_pair(2))
    stdscr.refresh()
    if over:
        del rate, start_time, rates
        break

mfile = open(args['dir'] + '\\' + FILENAME, 'wb', buffering=buffer)

stdscr.addstr(10, curses.COLS // 5, "Copying:")
rate = 0
finished = 0
for i in range(args['thread_count']):
    sfile = open(join(tmpdir.name, f'{i}.tmp'), 'rb')
    while True:
        data = sfile.read(buffer)
        if not data: break
        finished += mfile.write(data)
        rate = finished / total
        stdscr.addstr(11, curses.COLS // 4, f"{rate * 100:.2f}%{round(rate * 50) * '=':-<50}")
        stdscr.refresh()
    sfile.close()
    remove(sfile.name)
    mfile.flush()
