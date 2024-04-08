#!/usr/bin/env python3

import os
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from ipytv import playlist
from ipytv.playlist import M3UPlaylist
import config

def extract_credentials(url):
    """
    Extract the username and password from the given URL.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    username = query_params.get('username', [''])[0]
    password = query_params.get('password', [''])[0]
    return username, password

def create_directory_structure(base_dir):
    """
    Create the directory structure if it does not exist, including a 'files' subdirectory.
    """
    target_dir = os.path.join(base_dir, "files")
    os.makedirs(target_dir, exist_ok=True)
    return target_dir

def download_m3u(url, output_path):
    """
    Download the M3U file from a URL and save it to the specified path.
    """
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(response.text)

def is_download_needed(file_path, max_age_hours):
    if not os.path.exists(file_path):
        return True
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    max_age_hours = int(max_age_hours)
    if datetime.now() - file_mod_time > timedelta(hours=max_age_hours):
        return True
    return False

# Extract credentials and create directory structure
username, password = extract_credentials(config.url)
target_dir = create_directory_structure(config.base_dir)

# Determine path for original and new M3U files
original_m3u_path = os.path.join(target_dir, "original.m3u")
output_path = os.path.join(target_dir, config.output)

# Check and download M3U file based on age
if is_download_needed(original_m3u_path, config.maxage_before_download):
    print(f"The M3U file is older than {config.maxage_before_download} minutes or does not exist. Downloading now...")
    download_m3u(config.url, original_m3u_path)
    print(f"Downloaded the M3U file to: {original_m3u_path}")
else:
    print(f"Using existing M3U file: {original_m3u_path}")

# Load the M3U file locally
print("Loading the M3U playlist...")
original_playlist = playlist.loadf(original_m3u_path)

# Initialize an empty list to collect channels for the new playlist
collected_channels = []

# Process specific target channels
print("Processing specific target channels...")
for name in config.target_channel_names:
    if any(channel.name == name for channel in original_playlist):
        channel = next((channel for channel in original_playlist if channel.name == name), None)
        channel.attributes['group-title'] = config.new_group_title
        collected_channels.append(channel)
        print(f'Added "{name}" to new group "{config.new_group_title}".')

# Process channels by desired group titles
print("Filtering channels by desired group titles...")
for group_title in config.desired_group_titles:
    for channel in original_playlist:
        if channel.attributes.get('group-title') == group_title and channel not in collected_channels:
            collected_channels.append(channel)
            print(f'Included "{channel.name}" from group "{group_title}".')

print(f"Total channels to be included in the new playlist: {len(collected_channels)}")

# Create a new playlist with the collected channels
new_playlist = M3UPlaylist()
new_playlist.append_channels(collected_channels)

# Export the new playlist
with open(output_path, 'w', encoding='utf-8') as file:
    content = new_playlist.to_m3u_plus_playlist()
    file.write(content)
print(f'Exported the filtered and curated playlist to {output_path}')
