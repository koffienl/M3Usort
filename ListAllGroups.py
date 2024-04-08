#!/usr/bin/env python3

import argparse
import os
from ipytv import playlist
from urllib.parse import urlparse

# Setup command line argument parsing
parser = argparse.ArgumentParser(description='List all unique channel groups in an IPTV playlist.')
group = parser.add_argument_group('source', 'Playlist source (file or url)')
source = group.add_mutually_exclusive_group(required=True)
source.add_argument('--file', type=str, help='Path to the local M3U file. Example: "/path/to/file.m3u"')
source.add_argument('--url', type=str, help='URL of the M3U playlist. Must be enclosed in quotes if it contains special characters such as &, ?. Example: "http://url.com"')

args = parser.parse_args()

# Validate and load the playlist from the provided source
if args.file:
    if not os.path.exists(args.file):
        print(f"Error: The file '{args.file}' does not exist.")
        exit(1)
    print(f'Loading the playlist from file: {args.file}')
    original_playlist = playlist.loadf(args.file)
elif args.url:
    parsed_url = urlparse(args.url)
    if not parsed_url.scheme:
        print("Error: The URL seems invalid. Please include http:// or https:// and ensure it is correctly quoted.")
        exit(1)
    print(f'Loading the playlist from URL: {args.url}')
    original_playlist = playlist.loadu(args.url)

# Collect all unique group titles
group_titles = set()
for channel in original_playlist:
    group_title = channel.attributes.get('group-title')
    if group_title:
        group_titles.add(group_title)

if not group_titles:
    print("No channel groups found in the playlist.")
else:
    print("Unique channel groups found in the playlist:")
    for title in sorted(group_titles):
        print(title)
