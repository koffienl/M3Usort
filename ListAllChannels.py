#!/usr/bin/env python3

import argparse
import os
from ipytv import playlist
from urllib.parse import urlparse

# Setup command line argument parsing
parser = argparse.ArgumentParser(description='List channels from a specific group in an IPTV playlist.')
group = parser.add_argument_group('source', 'Playlist source (file or url)')
source = group.add_mutually_exclusive_group(required=True)
source.add_argument('--file', type=str, help='Path to the local M3U file. Example: "/path/to/file.m3u"')
source.add_argument('--url', type=str, help='URL of the M3U playlist. Must be enclosed in quotes if it contains special characters such as &, ?. Example: "http://url.com"')
parser.add_argument('group_title', type=str, help='The title of the group for which to list channels. Example: "NL KANALEN"')

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

# Check if any channel belongs to the specified group
group_exists = any(channel.attributes.get('group-title') == args.group_title for channel in original_playlist)

if not group_exists:
    print(f'No channels found for the "{args.group_title}" group.')
    print("Consider using another tool to list all available groups.")
else:
    # Filter channels by the specific group title and print their names
    for channel in original_playlist:
        if channel.attributes.get('group-title') == args.group_title:
            print(f'Channel name: {channel.name}')

    print(f'Finished listing channels from the "{args.group_title}" group.')
