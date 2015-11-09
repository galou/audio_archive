#!/usr/bin/env python3
# -* coding: utf-8 -*-
# Access to the radio archive of the Czech national radios (Český rozhlas).

# Python2 compatibility
from __future__ import print_function, unicode_literals

import bs4
import copy
import string
import re
import requests
from collections import OrderedDict
from gettext import gettext as _

from broadcast import Broadcast
from getch import getch
from gstreamer_player import Player

# Radio list, the ordered in which radios are added will be the order they
# will be presented to the user.
_radios = OrderedDict()
_radios['ČRo Radiožurnál'] = '%C4%8CRo+Radio%C5%BEurn%C3%A1l'
_radios['ČRo Dvojka'] = '%C4%8CRo+Dvojka'
_radios['ČRo Vltava'] = '%C4%8CRo+Vltava'
_radios['ČRo Plus'] = '%C4%8CRo+Plus'
_radios['ČRo Radio Wave'] = '%C4%8CRo+Radio+Wave'
_radios['ČRo Jazz'] = '%C4%8CRo+Jazz'
_radios['Rádio Junior'] = 'R%C3%A1dio+Junior'
_radios['Rádio vašeho kraje'] = 'R%C3%A1dio+va%C5%A1eho+kraje'
_radios['Brno'] = 'Brno'
_radios['České Budějovice'] = '%C4%8Cesk%C3%A9+Bud%C4%9Bjovice'
_radios['Hradec Králové'] = 'Hradec+Kr%C3%A1lov%C3%A9'
_radios['Olomouc'] = 'Olomouc'
_radios['Ostrava'] = 'Ostrava'
_radios['Pardubice'] = 'Pardubice'
_radios['Plzeň'] = 'Plze%C5%88'
_radios['Regina'] = 'Regina'
_radios['Region - štredný Čechy'] = 'Region+-+st%C5%99edn%C3%AD+%C4%8Cechy'
_radios['Region - Vysočina'] = 'Region+-+Vyso%C4%8Dina'
_radios['Sever'] = 'Sever'
_radios['ČRo 6'] = '%C4%8CRo+6'
_radios['Rádio Česko'] = 'R%C3%A1dio+%C4%8Cesko'
_radios['ČRo Leonardo'] = '%C4%8CRo+Leonardo'
_radios['Rádio Retro'] = 'R%C3%A1dio+Retro'

_default_radios = ['ČRo Dvojka']


def get_index():
    """Get an index, i.e. either 1-9 or 010-099

    Return the index as int.
    Return -1 to signify no index selection, on carriage return, line feed, or
    'q'.
    """
    text_index = []
    expected_length = 1
    while len(text_index) < expected_length:
        ch = getch()
        print(ch, end='', flush=True)
        if ch == '\r' or ch == '\n' or ch == 'q':
            return -1
        elif ch in string.digits:
            if expected_length == 1 and ch == '0':
                expected_length = 3
            text_index.append(ch)
    print()
    return int(''.join(text_index))


def get_two_digits():
    """Get an index from two digits

    Return the index as int.
    Return -1 to signify no index selection, on carriage return, line feed, or
    'q'.
    """
    text_index = []
    expected_length = 2
    while len(text_index) < expected_length:
        ch = getch()
        print(ch, end='', flush=True)
        if ch == '\r' or ch == '\n' or ch == 'q':
            return -1
        elif ch in string.digits:
            text_index.append(ch)
    print()
    return int(''.join(text_index))


def get_str_index(index):
    """Return '1' to '9' or '010' to '099'"""
    if index < 10:
        return str(index)
    else:
        return '{:03}'.format(index)


def get_query(search_text, search_radios, offset):
    print('search_text: {}'.format(search_text))
    search_radios_query = ''.join(
        ['&stanice[]=' + _radios[key] for key in search_radios])
    query = ('http://hledani.rozhlas.cz/iradio/?query={}' +
             '&reader=true&porad[]=&offset={}{}').format(
                 search_text, offset, search_radios_query)
    with open('/tmp/query.txt', 'w') as f:
        # f.write('query: {}'.format(query))
        f.writelines([(str(ord(ch)) + ',\n') for ch in query])
    return query


def get_result_list(search_text, radios):
    query = get_query(search_text, radios, 0)
    res = requests.get(query)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'lxml')
    audio_archives = soup.select('.box-audio-archive')
    results = []
    for audio_archive in audio_archives:
        title = audio_archive.select('.icon')[0].attrs['title']
        playlist_url = audio_archive.select('.action > a')[1].attrs['href']
        res = requests.get(playlist_url)
        res.raise_for_status()
        match = re.match(r'.*\n\n.*\nFile1=(.*)', res.text)
        if not match:
            continue
        uri = match.groups()[0]
        desc_tag = '.column.column-content > .title'
        desc_children = audio_archive.select(desc_tag)[0].children
        desc = ''
        for i, child in enumerate(desc_children):
            if i == 0:
                date = child.string
            else:
                desc += child.string
        results.append(Broadcast(title, uri, desc, date))
    return results


def filter_radios(radios):
    for index, k in enumerate(_radios.keys()):
        if k in radios:
            print('{}, {}, {}'.format(
                get_str_index(index + 1), k, _('activated')))
        else:
            print('{}, {}, {}'.format(
                get_str_index(index + 1), k, _('deactivated')))
    while True:
        index = get_index()
        if index == -1:
            print(_('Quitting radio selection'))
            return
        selected_radio = list(_radios.keys())[index - 1]
        if selected_radio in radios:
            radios.remove(selected_radio)
            print('{} {}'.format(selected_radio, _('deactivated')))
        else:
            radios.append(selected_radio)
            print('{} {}'.format(selected_radio, _('activated')))


def print_search_results(search_results):
    """Print the search results with format 'index title'"""
    if not search_results:
        print(_('No result'))
    else:
        for i, result in enumerate(search_results):
            print('{}\t{}'.format(get_str_index(i + 1), result.title))


def print_help():
    print('h ' + _('Help'))
    print('r ' + _('Choose radios'))
    print('s ' + _('Enter search text'))
    print('a ' + _('Repeat search results'))
    print('0-9 ' + _('Select an entry, 1-9 for entries 1 to 9, 010-099 for entries 10 to 99'))
    print('p ' + _('Play'))
    print(_('<Espace> Pause'))
    print('o ' + _('Stop'))


def main():
    radios = copy.copy(_default_radios)
    player = Player()
    ch = ''
    search_results = []
    while ch != 'q':
        ch = getch()
        if ch == ' ':
            player.pause()
        elif ch == 'a':
            print_search_results(search_results)
        elif ch == 'h':
            print_help()
        elif ch == 'o':
            player.stop()
        elif ch == 'p':
            player.play()
        elif ch == 'r':
            filter_radios(radios)
            print(radios)
        elif ch == 's':
            search_text = input()
            search_results = get_result_list(search_text, radios)
            print_search_results(search_results)
        elif ch in string.digits:
            index = int(ch) - 1
            if index == -1:
                index = get_two_digits() - 1
            else:
                print(ch)
            try:
                search_result = search_results[index]
            except IndexError:
                print(_('Index must be at most {}'.format(len(search_results))))
                continue
            print('index: {}'.format(index + 1))
            print('uri: {}'.format(search_result.uri))
            print('desc: {}'.format(search_result.description))
            print('date: {}'.format(search_result.date))
            player.uri = search_result.uri

if __name__ == '__main__':
    main()
