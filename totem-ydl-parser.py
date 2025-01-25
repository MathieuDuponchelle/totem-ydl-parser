#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
script used by totem-pl-parser.
It uses the module yt_dlp which, by the given url, will extract all his information.
"""

# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

import argparse
import json
import sys
import yt_dlp

class TotemYdlLogger:
    """
    The Logger given to yt_dlp.YoutubeDl
    """
    def __init__(self, enable_debug: bool):
        self._debug = enable_debug

    def debug(self, msg: str) -> None:
        """
        Print a debug message
        :param msg: the message to print
        :return: None
        """
        self.show_msg(msg=msg)

    def info(self, msg: str) -> None:
        """
        print an info message
        :param msg: the message to print
        :return: None
        """
        self.show_msg(msg=msg)

    def warning(self, msg: str):
        """
        print a warning message
        :param msg: the message to print
        :return: None
        """
        self.show_msg(msg=msg)

    def error(self, msg: str):
        """
        print an error message
        :param msg: the message to print
        :return: None
        """
        self.show_msg(msg=msg)

    def show_msg(self, msg):
        """
        Show the message (only if the debug option is set)
        :param msg: the message to print
        :return: None
        """
        if self._debug:
            print(msg)

def parse_results(result: dict, debug: bool) -> str | None:
    """
    Parse the information extracted by yt_dlp.YoutubeDL.
    We only search for the url which have an audio stream AND a video stream and the largest with
    :param result: the dict given by yt_dlp.YoutubeDL
    :param debug: if debug is enabled we dump the result
    :return: the url if found else None
    """
    width = 0
    url = None

    if debug:
        print(json.dumps(obj=result, indent=4))

    for element in result['formats']:
        if element.get('acodec') != 'none' and element.get('vcodec') != 'none':
            if element.get('width') is not None and int(element.get('width')) > width:
                width = element.get('width')
                url = element.get('url')

    return url

def url_is_valid(ydl: yt_dlp.YoutubeDL, url: str) -> bool:
    """
    Check if the yt_dlp has a suitable extractor for this url
    :param ydl: the instance of YoutubeDL
    :param url: the url to check
    :return: TRUE if found the extractor, False otherwise
    """
    for name, ie in ydl._ies.items(): # pylint: disable=W0212
        if name != 'Generic' and ie.suitable(url) and ie.working():
            return True
    return False

def extract_url(url: str, check: bool, debug: bool) -> None:
    """
    Give the url to YoutubeDL for extracting info
    :param url: the url
    :param check: if True we only check if this url can be handled by YoutubeDL
    :param debug: if True we display the log from  YoutubeDL
    :return: None
    """
    ydl_opts = {
        'logger': TotemYdlLogger(enable_debug=debug),
        'verbose': debug,
        'format': 'bestaudio/best',
        'noplaylist': True, # if the user give a playlist, it will get only the first video
        'extractor_args': {
            'youtube': {
                # By using the default clients, the quality of YouTube video will be of 360p
                # Unfortunately using all clients, the script will be slow
                'player_client':  ['default' ],
            },
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        is_valid = url_is_valid(ydl=ydl, url=url)
        if check:
            result = 'TRUE' if is_valid else 'FALSE'
            print(result, end='')
            sys.exit(1)
        elif not is_valid:
            print('TOTEM_PL_PARSER_RESULT_ERROR', end='')
            sys.exit(1)

        try:
            result = ydl.extract_info(
                url=url,
                download=False,  # We just want to extract the info
            )

            info_dict = ydl.sanitize_info(info_dict=result)
            url = parse_results(result=info_dict, debug=debug)
        except Exception as e: # pylint: disable=W0718
            if debug:
                print (e)
            sys.exit(1)

    if url is not None:
        print(f"title={result.get('title')}")
        print(f"id={result.get('id')}")
        print(f"moreinfos={result.get('webpage_url')}")
        print(f"duration={result.get('duration_string')}")
        print(f"url={url}")

        if result.get('thumbnail') is not None:
            print(f"image-url={result.get('thumbnail')}")
    else:
        print('TOTEM_PL_PARSER_RESULT_ERROR', end='')

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='totem-ydl-parser',
                                         description='Prout')
    arg_parser.add_argument("-u", "--url",
                            action="store", dest="url",
                            help="Url to scan or check",
                            required=True)
    arg_parser.add_argument("-c", "--check",
                            action="store_true",
                            help="only check if the url can be scanned",
                            default=False)
    arg_parser.add_argument("-d", "--debug",
                            action="store_true",
                            help="enable debug",
                            default=False)

    args = arg_parser.parse_args()

    extract_url (url=args.url, check=args.check, debug=args.debug)
