import os
import re
import json
import requests
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from threading import Thread
from urllib.parse import urlparse
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, session, send_from_directory, jsonify, abort, current_app as app
)
from werkzeug.security import generate_password_hash, check_password_hash
from ipytv import playlist
from ipytv.playlist import M3UPlaylist
from .forms import ConfigForm
from flask_apscheduler import APScheduler
import secrets
import socket
from time import sleep
import logging
logging.getLogger('ipytv').setLevel(logging.WARNING)



# Initialize and configure APScheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


# Global variables
VERSION = '0.1.6 Dev'
GROUPS_CACHE = {'groups': [], 'last_updated': None}
CACHE_DURATION = 3600  # Duration in seconds (e.g., 300 seconds = 5 minutes)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, '..', 'config.py')
CONFIG_PATH = os.path.normpath(CONFIG_PATH)
BASE_DIR = os.path.dirname(CONFIG_PATH)

#@app.route('/restart', methods=['POST'])
@app.route('/restart', methods=['GET', 'POST'])
def restart_service():
    try:
        subprocess.run(['systemctl', 'restart', 'M3Usort.service'], check=True)
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        # Handle error here
        PrintLog(f"Error restarting service: {e}", "ERROR")
        return "Error restarting the service", 500

@app.route('/healthcheck')
def healthcheck():
    return jsonify({"status": "OK"})

def get_internal_ip():
    try:
        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Attempt to connect to a known external address
            s.connect(("8.8.8.8", 80))
            # Get the socket's own address
            ip = s.getsockname()[0]
            return ip
    except Exception as e:
        PrintLog(f"Error obtaining internal IP address: {e}", "ERROR")
        return None

def scheduled_vod_download():
    series_dir = get_config_variable(CONFIG_PATH, 'series_dir')
    update_series_directory(series_dir)

    movies_dir = get_config_variable(CONFIG_PATH, 'movies_dir')
    update_movies_directory(movies_dir)

def scheduled_renew_m3u():
    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    maxage_before_download = int(get_config_variable(CONFIG_PATH, 'maxage_before_download'))
    original_m3u_path = f'{BASE_DIR}/files/original.m3u'

    if is_download_needed(original_m3u_path, maxage_before_download):
        PrintLog(f"The M3U file is older than {maxage_before_download} hours or does not exist. Downloading now...", "INFO")
        download_m3u(m3u_url, original_m3u_path)
        PrintLog(f"Downloaded the M3U file to: {original_m3u_path}", "INFO")
    else:
        PrintLog(f"Using existing M3U file: {original_m3u_path}", "INFO")
        rebuild()

def download_m3u(url, output_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(response.text)
    sleep(1)
    update_groups_cache()

def is_download_needed(file_path, max_age_hours):
    #file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))

    if not os.path.exists(file_path):
        return True
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    max_age_hours = int(max_age_hours)

    debug = get_config_variable(CONFIG_PATH, 'debug')
    if debug == "yes":
        if datetime.now() - file_mod_time > timedelta(minutes=max_age_hours):
            return True
        return False
    else:
        if datetime.now() - file_mod_time > timedelta(hours=max_age_hours):
            return True
        return False

def update_series_directory(series_dir):
    # Retrieve the list of series from the API
    series_list = GetSeriesList()
    
    # Loop through all directories within series_dir
    for root, dirs, files in os.walk(series_dir):
        for dir_name in dirs:
            # Find a matching series by name
            matching_series = next((series for series in series_list if series['name'] == dir_name), None)
            
            # If a match is found, download the series
            if matching_series:
                PrintLog(f"Updating series: {matching_series['name']}", "INFO")
                DownloadSeries(matching_series['series_id'])
            else:
                PrintLog(f"No matching series found for directory: {dir_name}", "INFO")

def update_movies_directory(movies_dir):
    # Retrieve the list of series from the API
    movies_list = GetMoviesList()
    overwrite_movies = int(get_config_variable(CONFIG_PATH, 'overwrite_movies'))

    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    username, password = extract_credentials_from_url(m3u_url)
    parsed_url = urlparse(m3u_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Loop through all directories within movies_dir
    for root, dirs, files in os.walk(movies_dir):
        for dir_name in dirs:
            # Find a matching series by name
            matching_movie = next((movies for movies in movies_list if movies['name'] == dir_name), None)
            
            # If a match is found, download the series
            if matching_movie:
                strm_file_path = os.path.join(movies_dir, f"{matching_movie['name']}", f"{matching_movie['name']}.strm")
                # Check if .strm file exists and the overwrite setting
                if not os.path.exists(strm_file_path) or overwrite_movies == 1:
                    PrintLog(f"Updating movie: {matching_movie['name']}", "INFO")
                    strm_content = f"{base_url}/movie/{username}/{password}/{matching_movie['stream_id']}.mkv"
                    PrintLog(strm_file_path, "INFO")
                    PrintLog(strm_content, "INFO")
                    
                    # Write to .strm file
                    with open(strm_file_path, 'w') as strm_file:
                        strm_file.write(strm_content)

            else:
                PrintLog(f"No matching movie found for directory: '{dir_name}'", "WARNING")


def get_config_variable(config_path, variable_name):
    try:
        with open(CONFIG_PATH, 'r') as file:
            config_content = file.read()
        config_namespace = {}
        exec(config_content, {}, config_namespace)
        config_variable = config_namespace.get(variable_name)

    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return config_variable

def update_config_variable(config_path, variable_name, new_value):
    with open(config_path, 'r') as file:
        lines = file.readlines()

    with open(config_path, 'w') as file:
        for line in lines:
            if line.strip().startswith(f'{variable_name} ='):
                file.write(f'{variable_name} = "{new_value}"\n')
            else:
                file.write(line)

def update_config_array(config_path, array_name, new_value):
    # Rewrite the configuration file with the updated group order

    # Read the existing configuration file
    with open(CONFIG_PATH, 'r') as file:
        lines = file.readlines()

    with open(CONFIG_PATH, 'w') as file:
        in_desired_group_titles_section = False
        for line in lines:
            if line.strip().startswith(f'{array_name} = ['):
                file.write(f'{array_name} = [\n')
                for value in new_value:
                    file.write(f'    "{value}",\n')
                file.write(']\n')
                in_desired_group_titles_section = True
            elif in_desired_group_titles_section and line.strip() == ']':
                in_desired_group_titles_section = False
            elif not in_desired_group_titles_section:
                file.write(line)


def extract_credentials_from_url(m3u_url):
    match = re.search(r'username=([^&]+)&password=([^&]+)', m3u_url)
    if match:
        return match.groups()
    return None, None

main_bp = Blueprint('main_bp', __name__)

@app.before_request
def require_auth():
    # Exclude authentication for specific file download route
    if request.path.startswith('/m3u'):
        return

    if request.path.startswith('/get.php'):
        return

    if request.path.startswith('/player_api.php'):
        return

    if request.path.startswith('/healthcheck'):
        return

    # Check if user is logged in
    if not session.get('logged_in') and request.endpoint not in ['login', 'static']:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    hashed_pw_from_config = get_config_variable(CONFIG_PATH, 'admin_password')

    if request.method == 'POST':
        password = request.form['password']
        
        if check_password_hash(hashed_pw_from_config, password):
            session['logged_in'] = True
            session.permanent = True  # Make the session permanent so it uses the app's permanent session lifetime
            return redirect(url_for('main_bp.home'))
        else:
            flash('Incorrect password.', 'error')

    return render_template('login.html')


from flask import jsonify, render_template
import requests
import os

def get_time_diff(file_path):
    current_time = datetime.now()

    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    time_difference = current_time - file_mod_time
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_difference = f"{hours:02d}:{minutes:02d}"

    return formatted_difference

@main_bp.route('/update_home_data')
def update_home_data():
    try:
        current_time = datetime.now()

        original_m3u_path = f'{BASE_DIR}/files/original.m3u'
        original_m3u_age = get_time_diff(original_m3u_path)

        output = get_config_variable(CONFIG_PATH, 'output')
        sorted_m3u_path = f'{BASE_DIR}/files/{output}'
        sorted_m3u_age = get_time_diff(sorted_m3u_path)

        next_m3u = "-"
        job = scheduler.get_job('M3U Download scheduler')
        if job:
            now = datetime.now(timezone.utc)
            next_run_time = job.next_run_time
            remaining_time = next_run_time - now
            total_seconds = int(remaining_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            next_m3u = f"{hours:02d}:{minutes:02d}"

        next_vod = "-"
        job = scheduler.get_job('VOD scheduler')
        if job:
            now = datetime.now(timezone.utc)
            next_run_time = job.next_run_time
            remaining_time = next_run_time - now
            total_seconds = int(remaining_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            next_vod = f"{hours:02d}:{minutes:02d}"

        m3u_url = get_config_variable(CONFIG_PATH, 'url')
        scheme, rest = m3u_url.split('://')
        domain_with_port, _ = rest.split('/get.php')
        username, password = extract_credentials_from_url(m3u_url)

        api_url = f"{scheme}://{domain_with_port}/player_api.php?username={username}&password={password}&action=get_user_info"
        response = requests.get(api_url)
        user_info = response.json()['user_info']

        # Convert Unix timestamp to readable date for expiration date
        exp_date_readable = datetime.utcfromtimestamp(int(user_info['exp_date'])).strftime('%Y-%m-%d')

        uptime_duration = current_time - app.app_start_time
        # Convert to total seconds and then to hours, minutes, seconds
        total_seconds = int(uptime_duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        internal_ip = get_internal_ip()
        port_number = get_config_variable(CONFIG_PATH, 'port_number')
        output = get_config_variable(CONFIG_PATH, 'output')

        data = {
            "next_m3u": next_m3u,
            "next_vod": next_vod,
            "original_m3u_age": original_m3u_age,
            "sorted_m3u_age": sorted_m3u_age,
            "uptime": uptime_str,
            "output": output,
            "internal_ip": internal_ip, 
            "port_number": port_number, 
            "status": user_info['status'],
            "exp_date": exp_date_readable,
            "active_cons": user_info['active_cons'],
            "is_trial": user_info['is_trial'],
            "status": user_info['status'],
            "max_connections": user_info['max_connections']
        }
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e))  # For debugging


@main_bp.route('/home')
def home():
    try:
        current_time = datetime.now()

        original_m3u_path = f'{BASE_DIR}/files/original.m3u'
        original_m3u_age = get_time_diff(original_m3u_path)

        output = get_config_variable(CONFIG_PATH, 'output')
        sorted_m3u_path = f'{BASE_DIR}/files/{output}'
        sorted_m3u_age = get_time_diff(sorted_m3u_path)

        next_m3u = "-"
        job = scheduler.get_job('M3U Download scheduler')
        if job:
            now = datetime.now(timezone.utc)
            next_run_time = job.next_run_time
            remaining_time = next_run_time - now
            total_seconds = int(remaining_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            next_m3u = f"{hours:02d}:{minutes:02d}"

        next_vod = "-"
        job = scheduler.get_job('VOD scheduler')
        if job:
            now = datetime.now(timezone.utc)
            next_run_time = job.next_run_time
            remaining_time = next_run_time - now
            total_seconds = int(remaining_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            next_vod = f"{hours:02d}:{minutes:02d}"

        m3u_url = get_config_variable(CONFIG_PATH, 'url')
        scheme, rest = m3u_url.split('://')
        domain_with_port, _ = rest.split('/get.php')
        username, password = extract_credentials_from_url(m3u_url)

        api_url = f"{scheme}://{domain_with_port}/player_api.php?username={username}&password={password}&action=get_user_info"
        response = requests.get(api_url)
        user_info = response.json()['user_info']

        # Convert Unix timestamp to readable date for expiration date
        exp_date_readable = datetime.utcfromtimestamp(int(user_info['exp_date'])).strftime('%Y-%m-%d')

        uptime_duration = current_time - app.app_start_time
        # Convert to total seconds and then to hours, minutes, seconds
        total_seconds = int(uptime_duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        internal_ip = get_internal_ip()
        port_number = get_config_variable(CONFIG_PATH, 'port_number')
        output = get_config_variable(CONFIG_PATH, 'output')


        return render_template('home.html',version=VERSION, 
                               next_m3u=next_m3u,
                               next_vod=next_vod,
                               original_m3u_age=original_m3u_age,
                               sorted_m3u_age=sorted_m3u_age,
                               uptime=uptime_str,
                               internal_ip=internal_ip, 
                               port_number=port_number, 
                               output=output, 
                               status=user_info['status'], 
                               exp_date=exp_date_readable, 
                               is_trial=user_info['is_trial'], 
                               active_cons=user_info['active_cons'], 
                               max_connections=user_info['max_connections'])
    except Exception as e:
        return str(e)  # For debugging


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/GetMoviesList')
def GetMoviesList():
    movies = []
    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    
    # Parse the M3U URL to construct the API URL
    scheme, rest = m3u_url.split('://')
    domain_with_port, _ = rest.split('/get.php')
    username, password = extract_credentials_from_url(m3u_url)
    api_url = f"{scheme}://{domain_with_port}/player_api.php?username={username}&password={password}&action=get_vod_streams&category_id=ALL"

    # Make the API call
    response = requests.get(api_url)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    movies_data = response.json()

    # Filter the needed data
    movies = [{'name': movie['name'], 'stream_id': movie['stream_id']} for movie in movies_data]
    return movies

@app.route('/GetSeriesList')
def GetSeriesList():
    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    scheme, rest = m3u_url.split('://')
    domain_with_port, _ = rest.split('/get.php')
    username, password = extract_credentials_from_url(m3u_url)
    api_url = f"{scheme}://{domain_with_port}/player_api.php?username={username}&password={password}&action=get_series&category_id=ALL"

    # Make the API call
    response = requests.get(api_url)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    series_data = response.json()

    # Filter the needed data
    series = [{'name': serie['name'], 'series_id': serie['series_id']} for serie in series_data]

    return series

@main_bp.route('/series')
def series():
    series = GetSeriesList()
    return render_template('series.html', series=series)


def DownloadSeries(series_id):
    series_dir = get_config_variable(CONFIG_PATH, 'series_dir')
    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    username, password = extract_credentials_from_url(m3u_url)
    overwrite_series = int(get_config_variable(CONFIG_PATH, 'overwrite_series'))  # Assuming this is how you'd get it

    # Ensure series_dir, m3u_url, username, password, and overwrite_series are available
    if not all([series_dir, m3u_url, username, password, isinstance(overwrite_series, int)]):
        raise ValueError("Configuration error. Ensure series_dir, m3u_url, username, password, and overwrite_series are set.")

    # API call to get series info
    parsed_url = urlparse(m3u_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    series_info_url = f"{base_url}/player_api.php?username={username}&password={password}&action=get_series_info&series_id={series_id}"
    response = requests.get(series_info_url)
    series_info = response.json()

    # Extract series name
    series_name = series_info['info']['name']

    # Process each episode
    for season in series_info['episodes']:
        try:
            for episode in series_info['episodes'][season]:
                episode_id = episode['id']
                episode_num = str(episode['episode_num']).zfill(2)
                season_num = str(episode['season']).zfill(2)
                strm_file_name = f"{series_name} S{season_num}E{episode_num}.strm"
                strm_content = f"{base_url}/series/{username}/{password}/{episode_id}.mkv"

                # Ensure series directory exists
                series_dir_path = os.path.join(series_dir, series_name)
                os.makedirs(series_dir_path, exist_ok=True)

                # Determine path for .strm file
                strm_file_path = os.path.join(series_dir_path, strm_file_name)

                # Check if .strm file exists and the overwrite setting
                if not os.path.exists(strm_file_path) or overwrite_series == 1:
                    PrintLog(f"Adding new file: {strm_file_path}", "INFO")
                    with open(strm_file_path, 'w') as strm_file:
                        strm_file.write(strm_content)
                #else:
                    #print(f"Skipping existing file without overwrite: {strm_file_path}")
        except Exception as inner_error:
            PrintLog(f"Error processing episodes for series '{series_name}' with ID {series_id}: {inner_error}", "WARNING")

@main_bp.route('/add_series_to_server', methods=['POST'])
def add_series_to_server():
    data = request.get_json()
    series_id = data['serieId']
    DownloadSeries(series_id)

    return jsonify(message="Series added successfully"), 200

@main_bp.route('/rebuild')
def rebuild():
    original_m3u_path = f'{BASE_DIR}/files/original.m3u'
    output = get_config_variable(CONFIG_PATH, 'output')

    output_name = get_config_variable(CONFIG_PATH, 'output')
    #original_m3u_path = os.path.join(BASE_DIR, "original.m3u")
    output_path = os.path.join(BASE_DIR, 'files', output_name)
    original_playlist = playlist.loadf(original_m3u_path)
    target_channel_names = get_config_variable(CONFIG_PATH, 'target_channel_names')
    desired_group_titles = get_config_variable(CONFIG_PATH, 'desired_group_titles')
    new_group_title = get_config_variable(CONFIG_PATH, 'new_group_title')
    collected_channels = []

    # Process specific target channels
    PrintLog("Processing specific target channels...", "INFO")
    for name in target_channel_names:
        if any(channel.name == name for channel in original_playlist):
            channel = next((channel for channel in original_playlist if channel.name == name), None)
            channel.attributes['group-title'] = new_group_title
            collected_channels.append(channel)
            PrintLog(f'Added "{name}" to new group "{new_group_title}".', "INFO")

    # Process channels by desired group titles
    PrintLog("Filtering channels by desired group titles...", "INFO")
    for group_title in desired_group_titles:
        for channel in original_playlist:
            if channel.attributes.get('group-title') == group_title and channel not in collected_channels:
                collected_channels.append(channel)
                PrintLog(f'Included "{channel.name}" from group "{group_title}".', "INFO")

    PrintLog(f"Total channels to be included in the new playlist: {len(collected_channels)}", "INFO")

    # Create a new playlist with the collected channels
    new_playlist = M3UPlaylist()
    new_playlist.append_channels(collected_channels)

    # Export the new playlist
    with open(output_path, 'w', encoding='utf-8') as file:
        content = new_playlist.to_m3u_plus_playlist()
        file.write(content)
    PrintLog(f'Exported the filtered and curated playlist to {output_path}', "INFO")

    # Redirect back to the referrer page, or to a default page if no referrer is set
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    else:
        # Redirect to a default route if the referrer is not found
        return redirect(url_for('main_bp.home'))

@main_bp.route('/download')
def download():
    series_dir = get_config_variable(CONFIG_PATH, 'series_dir')
    update_series_directory(series_dir)

    movies_dir = get_config_variable(CONFIG_PATH, 'movies_dir')
    update_movies_directory(movies_dir)

    # Redirect back to the referrer page, or to a default page if no referrer is set
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    else:
        # Redirect to a default route if the referrer is not found
        return redirect(url_for('main_bp.home'))


@app.route('/m3u/<path:filename>')
def download_file(filename):
    url_password = request.args.get('password')
   
    # Check if the provided password matches the hashed password
    hashed_pw_from_config = get_config_variable(CONFIG_PATH, 'playlist_password')
    if not check_password_hash(hashed_pw_from_config, url_password):
        abort(401, 'Invalid password')

    # Serve the file if authentication succeeds
    directory_to_serve = f'{BASE_DIR}/files'  # Update with your actual directory path
    return send_from_directory(directory_to_serve, filename, as_attachment=True)



@main_bp.route('/security', methods=['GET'])
def security():
    playlist_username = get_config_variable(CONFIG_PATH, 'playlist_username')
    return render_template('security.html', playlist_username=playlist_username)


@main_bp.route('/change_admin_password', methods=['POST'])
def change_admin_password():
    new_password = request.form.get('admin_password')
    hashed_password = generate_password_hash(new_password)
    update_config_variable(CONFIG_PATH, 'admin_password', hashed_password)
    
    flash('Admin password updated successfully!', 'success')

    return redirect(url_for('main_bp.security'))


@main_bp.route('/change_playlist_credentials', methods=['POST'])
def change_playlist_credentials():
    new_password = request.form.get('playlist_password')
    hashed_password = generate_password_hash(new_password)
    update_config_variable(CONFIG_PATH, 'playlist_password', hashed_password)
    
    flash('Playlist credentials updated successfully!', 'success')

    return redirect(url_for('main_bp.security'))



@main_bp.route('/movies')
def movies():
    movies = []

    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    
    # Parse the M3U URL to construct the API URL
    scheme, rest = m3u_url.split('://')
    domain_with_port, _ = rest.split('/get.php')
    username, password = extract_credentials_from_url(m3u_url)
    api_url = f"{scheme}://{domain_with_port}/player_api.php?username={username}&password={password}&action=get_vod_streams&category_id=ALL"

    # Make the API call
    response = requests.get(api_url)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    movies_data = response.json()

    # Filter the needed data
    movies = [{'name': movie['name'], 'stream_id': movie['stream_id']} for movie in movies_data]

    return render_template('movies.html', movies=movies)




@main_bp.route('/add_movie_to_server', methods=['POST'])
def add_movie_to_server():
    data = request.get_json()
    movie_name = data['movieName']
    movie_id = data['movieId']

    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    movies_dir = get_config_variable(CONFIG_PATH, 'movies_dir')

    username, password = extract_credentials_from_url(m3u_url)

    # Check if URL, username, and password are present
    if not m3u_url or not username or not password:
        raise ValueError("M3U URL, username, or password not found in the configuration.")
    
    # Parse the M3U URL to get the base parts for constructing the .strm URL
    parsed_url = urlparse(m3u_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Prepare the directory and .strm file
    movie_dir_path = os.path.join(movies_dir, movie_name)
    os.makedirs(movie_dir_path, exist_ok=True)
    strm_file_path = os.path.join(movie_dir_path, f"{movie_name}.strm")
    strm_content = f"{base_url}/movie/{username}/{password}/{movie_id}.mkv"
    
    # Write to .strm file
    with open(strm_file_path, 'w') as strm_file:
        strm_file.write(strm_content)

    return jsonify(message="Movie added successfully"), 200
    # flash('Movie addedd successfully!', 'success')

@main_bp.route('/')
def index():
    return redirect(url_for('main_bp.home'))

# Display the group selection form
@main_bp.route('/channel_selection', methods=['GET'])
def channel_selection():
    # Ensure your GROUPS_CACHE is up to date before rendering the page
    if not is_cache_valid():
        update_groups_cache()
    return render_template('channel_selection.html', groups=GROUPS_CACHE['groups'])

# Process the selected groups and update config.py
@main_bp.route('/save_channel_selection', methods=['POST'])
def save_channel_selection():
    selected_groups = request.form.getlist('selected_groups[]')
    all_channels = get_channels_for_selected_groups(selected_groups)

    if update_target_channel_names(all_channels):
        flash('Channel selection updated successfully!', 'success')
    else:
        flash('Failed to update channel selection.', 'danger')
    
    return redirect(url_for('main_bp.channel_selection'))


def get_channels_for_selected_groups(selected_groups):
    all_channels = []

    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    username, password = extract_credentials_from_url(m3u_url)
    if not username or not password:
        raise ValueError("Username or password could not be extracted from the M3U URL.")

    m3u_path = f'{BASE_DIR}/files/original.m3u'
    
    if not os.path.exists(m3u_path):
        raise FileNotFoundError(f"The original M3U file at '{m3u_path}' was not found.")
    
    # Use the playlist module correctly to load the M3U file
    m3u_playlist = playlist.loadf(m3u_path)
    for channel in m3u_playlist:
        if channel.attributes.get('group-title') in selected_groups:
            all_channels.append(channel.name)
    
    PrintLog(f"Channels to be added: {all_channels}", "INFO")
    return all_channels









def update_target_channel_names(new_channels):
    existing_channel_names = get_config_variable(CONFIG_PATH, 'target_channel_names')

    # Combine existing channels with new channels, ensuring uniqueness
    updated_channel_names = list(set(existing_channel_names + new_channels))
    PrintLog(f"updated channels: ", updated_channel_names)

    update_config_array(CONFIG_PATH, 'target_channel_names', updated_channel_names)

    return True


@main_bp.route('/reorder_channels', methods=['GET'])
def reorder_channels():
    # Load channels from config.py
    channel_names = get_config_variable(CONFIG_PATH, 'target_channel_names')

    return render_template('reorder_channels.html', channel_names=channel_names)

@main_bp.route('/save_reordered_channels', methods=['POST'])
def save_reordered_channels():
    new_order = request.form.get('channel_order')
    new_channel_names = json.loads(new_order)

    update_config_array(CONFIG_PATH, 'target_channel_names', new_channel_names)

    return redirect(url_for('main_bp.reorder_channels'))

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    form = ConfigForm(request.form)
    
    if request.method == 'POST' and form.validate():

        current_url = get_config_variable(CONFIG_PATH, 'url')
        if form.url.data != current_url:
            original_m3u_path = f'{BASE_DIR}/files/original.m3u'
            download_m3u(form.url.data, original_m3u_path)

        update_config_variable(CONFIG_PATH, 'url',form.url.data)
        update_config_variable(CONFIG_PATH, 'output', form.output.data)
        update_config_variable(CONFIG_PATH, 'maxage_before_download', form.maxage.data)
        update_config_variable(CONFIG_PATH, 'new_group_title', form.new_group_title.data)
        update_config_variable(CONFIG_PATH, 'movies_dir', form.movies_dir.data)
        update_config_variable(CONFIG_PATH, 'series_dir', form.series_dir.data)
        update_config_variable(CONFIG_PATH, 'enable_scheduler', form.enable_scheduler.data)
        update_config_variable(CONFIG_PATH, 'scan_interval', form.scan_interval.data)
        update_config_variable(CONFIG_PATH, 'overwrite_series', form.overwrite_series.data)
        update_config_variable(CONFIG_PATH, 'overwrite_movies', form.overwrite_movies.data)

        job = scheduler.get_job('VOD scheduler')
        if form.enable_scheduler.data == "0":
            if job:
                PrintLog("Disable scheduled task", "INFO")
                scheduler.remove_job(id='VOD scheduler')

        if form.enable_scheduler.data == "1":
            form.scan_interval.data = int(form.scan_interval.data)
            if job:
                scheduler.remove_job(id='VOD scheduler')
            PrintLog("Enable scheduled task", "INFO")
            
            debug = get_config_variable(CONFIG_PATH, 'debug')
            if debug == "yes":
                scheduler.add_job(id='VOD scheduler', func=scheduled_vod_download, trigger='interval', minutes=form.scan_interval.data)
            else:
                scheduler.add_job(id='VOD scheduler', func=scheduled_vod_download, trigger='interval', hours=form.scan_interval.data)

        return redirect(url_for('main_bp.settings'))

    # For a GET request, populate the form with existing values
    else:
        form.url.data = get_config_variable(CONFIG_PATH, 'url')
        form.output.data = get_config_variable(CONFIG_PATH, 'output')
        form.maxage.data = get_config_variable(CONFIG_PATH, 'maxage_before_download')
        form.new_group_title.data = get_config_variable(CONFIG_PATH, 'new_group_title')
        form.movies_dir.data = get_config_variable(CONFIG_PATH, 'movies_dir')
        form.series_dir.data = get_config_variable(CONFIG_PATH, 'series_dir')
        form.enable_scheduler.data = get_config_variable(CONFIG_PATH, 'enable_scheduler')
        form.scan_interval.data = get_config_variable(CONFIG_PATH, 'scan_interval')
        form.overwrite_series.data = get_config_variable(CONFIG_PATH, 'overwrite_series')
        form.overwrite_movies.data = get_config_variable(CONFIG_PATH, 'overwrite_movies')

    return render_template('settings.html', form=form)


@main_bp.route('/groups')
def groups():
    global GROUPS_CACHE  # Reference the global cache
    desired_group_titles = []

    try:
        # Check if the cache is valid and use it if so
        if is_cache_valid():
            # Read desired_group_titles from config.py for checking checkboxes
            with open(CONFIG_PATH, 'r') as file:
                config_content = file.read()
            config_namespace = {}
            exec(config_content, {}, config_namespace)
            desired_group_titles = config_namespace.get('desired_group_titles', [])
            # Render with cached groups and desired_group_titles for checkbox states
            return render_template('groups.html', groups=GROUPS_CACHE['groups'], desired_group_titles=desired_group_titles)

        # Cache is not valid; proceed to fetch and update
        with open(CONFIG_PATH, 'r') as file:
            config_content = file.read()
        config_namespace = {}
        exec(config_content, {}, config_namespace)
        m3u_url = config_namespace.get('url')

        if not m3u_url:
            raise ValueError("M3U URL not found in the configuration.")
        
        username, password = extract_credentials_from_url(m3u_url)
        if not username or not password:
            raise ValueError("Username or password could not be extracted from the M3U URL.")

        m3u_path = f'{BASE_DIR}/files/original.m3u'
        if not os.path.exists(m3u_path):
            raise FileNotFoundError(f"The original M3U file at '{m3u_path}' was not found.")

        # Fetch new groups since the cache is invalid or empty
        GROUPS_CACHE['groups'] = fetch_channel_groups(m3u_path)
        GROUPS_CACHE['last_updated'] = datetime.now()
        desired_group_titles = config_namespace.get('desired_group_titles', [])

    except FileNotFoundError as e:
        flash(str(e), 'danger')
        GROUPS_CACHE['groups'] = []
    except Exception as e:
        flash(str(e), 'danger')
        GROUPS_CACHE['groups'] = []

    # Render the template with groups and desired_group_titles to control checkbox states
    return render_template('groups.html', groups=GROUPS_CACHE['groups'], desired_group_titles=desired_group_titles)

@main_bp.route('/save-groups', methods=['POST'])
def save_groups():
    selected_groups = request.form.getlist('selected_groups[]')
    
    # Call the function to update config.py
    if save_selected_groups(selected_groups):
        flash('Group settings updated successfully!', 'success')
    else:
        flash('Failed to update group settings.', 'danger')
    
    return redirect(url_for('main_bp.groups'))

@main_bp.route('/reorder-groups', methods=['GET'])
def reorder_groups():
    desired_group_titles = []

    try:
        with open(CONFIG_PATH, 'r') as file:
            config_content = file.read()
        config_namespace = {}
        exec(config_content, {}, config_namespace)
        desired_group_titles = config_namespace.get('desired_group_titles', [])
    except Exception as e:
        flash(f"An error occurred while loading group titles: {e}", "danger")

    return render_template('reorder_groups.html', desired_group_titles=desired_group_titles)

@main_bp.route('/save_reordered_groups', methods=['POST'])
def save_reordered_groups():

    # Retrieve and parse the JSON string from the form
    group_order_str = request.form.get('group_order', '[]')
    new_order = json.loads(group_order_str)

    app.logger.debug(f"New order from the form: {new_order}")  # Log for debugging
    update_config_array(CONFIG_PATH, 'desired_group_titles', new_order)

    '''
    try:
        # Read the existing configuration file
        with open(CONFIG_PATH, 'r') as file:
            lines = file.readlines()

        # Rewrite the configuration file with the updated group order
        with open(CONFIG_PATH, 'w') as file:
            in_desired_group_titles_section = False
            for line in lines:
                if line.strip().startswith('desired_group_titles = ['):
                    file.write('desired_group_titles = [\n')
                    for group in new_order:
                        file.write(f'    "{group}",\n')
                    file.write(']\n')
                    in_desired_group_titles_section = True
                elif in_desired_group_titles_section and line.strip() == ']':
                    in_desired_group_titles_section = False
                elif not in_desired_group_titles_section:
                    file.write(line)

        flash('Group order has been updated successfully!', 'success')
    except Exception as e:
        flash(f"An error occurred while saving group order: {e}", "danger")
    '''

    return redirect(url_for('main_bp.reorder_groups'))



































def save_selected_groups(selected_groups):
    start_marker = 'desired_group_titles = ['
    end_marker = ']'

    try:
        # Read the entire config file
        with open(CONFIG_PATH, 'r') as file:
            lines = file.readlines()
        
        # Find start and end of the desired_group_titles list
        start_index = end_index = None
        for i, line in enumerate(lines):
            if start_marker in line:
                start_index = i
            elif end_marker in line and start_index is not None:
                end_index = i
                break
        
        # Safety check in case the markers are not found or improperly formatted
        if start_index is None or end_index is None:
            raise ValueError("Could not locate 'desired_group_titles' list in config.py")
        
        # Remove existing groups within the markers
        del lines[start_index + 1:end_index]
        
        # Insert new groups
        new_groups_lines = [f'    "{group}",\n' for group in sorted(selected_groups)]
        lines[start_index + 1:start_index + 1] = new_groups_lines
        
        # Write back to config.py
        with open(CONFIG_PATH, 'w') as file:
            file.writelines(lines)

        return True
    except Exception as e:
        PrintLog(f"Error updating config.py: {e}", "ERROR")
        return False


def ansi_to_html_converter(text):
    # ANSI color code regex
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

    # Dictionary of ANSI color codes and their HTML class equivalents
    ansi_to_html = {
        '\x1B[0m': '</span>',  # Reset code
        '\x1B[33m': '<span class="ansi-yellow">',  # Yellow text
        '\x1B[31m\x1B[1m': '<span class="ansi-bold-red">',  # Bold Red text
        '\x1B[36m': '<span class="ansi-cyan">',  # Cyan text
        # Add other color codes and their classes as needed
    }


    # Replace ANSI codes with HTML span tags and classes
    for ansi, html in ansi_to_html.items():
        text = text.replace(ansi, html)
    # Remove any remaining ANSI codes that haven't been translated
    text = ansi_escape.sub('', text)
    return text



@main_bp.route('/log')
def log():
    page = request.args.get('page', 1, type=int)
    lines_per_page = 75
    start_line = (page - 1) * lines_per_page
    log_file = f'{BASE_DIR}/logs/M3Usort.log'

    log_entries = []  # Will store tuples of (metadata, message, css_class)

    try:
        with open(log_file, 'r') as file:
            log_lines = file.readlines()
        total_pages = len(log_lines) // lines_per_page + (1 if len(log_lines) % lines_per_page > 0 else 0)
        log_content = log_lines[-(start_line + lines_per_page):len(log_lines) - start_line][::-1]
    except Exception as e:
        log_content = [f"Error reading log file: {e}"]
        total_pages = 1

    for line in log_content:
        parts = line.split(' ', 3)  # Split at the third space character
        if len(parts) >= 4:
            metadata, message = parts[0] + ' ' + parts[1] + ' ' + parts[2], parts[3]
        else:
            metadata, message = line, ''

        if 'DEBUG' in metadata:
            css_class = 'log-debug'
        elif 'INFO' in metadata:
            css_class = 'log-info'
        elif 'WARNING' in metadata:
            css_class = 'log-warning'
        elif 'ERROR' in metadata:
            css_class = 'log-error'
        elif 'CRITICAL' in metadata:
            css_class = 'log-critical'
        else:
            css_class = ''

        message = ansi_to_html_converter(message)

        
        log_entries.append((metadata, message, css_class))

    return render_template('log.html', log_entries=log_entries, current_page=page, total_pages=total_pages)

def extract_credentials_from_url(m3u_url):
    match = re.search(r'username=([^&]+)&password=([^&]+)', m3u_url)
    if match:
        return match.groups()
    return None, None

def is_cache_valid():
    if not GROUPS_CACHE['last_updated']:
        return False
    return datetime.now() - GROUPS_CACHE['last_updated'] < timedelta(seconds=CACHE_DURATION)

def fetch_channel_groups(m3u_path):
    """Fetch channel groups using the ipytv library."""
    original_playlist = playlist.loadf(m3u_path)
    group_titles = set(channel.attributes.get('group-title', 'No Group Title') for channel in original_playlist)
    return sorted(group_titles)

def init():
    PrintLog(f"Starting M3Usort {VERSION}", "INFO")

    # Startup
    startup_instant()

    # Startup stuff that needs the server to be ready before execution
    Thread(target=startup_delayed).start()



def startup_delayed():
    sleep(1)
    internal_ip = get_internal_ip()
    port_number = get_config_variable(CONFIG_PATH, 'port_number')
    max_age_before_download = get_config_variable(CONFIG_PATH, 'maxage_before_download')
    max_age_before_download = int(max_age_before_download)
    base_url = "http://" + internal_ip + ":" + port_number

    while True:
        try:
            response = requests.get(f"{base_url}/healthcheck")
            if response.status_code == 200:
                PrintLog("Server is up and running.", "INFO")

                # Schedule a task to check for
                debug = get_config_variable(CONFIG_PATH, 'debug')
                if debug == "yes":
                    scheduler.add_job(id='M3U Download scheduler', func=scheduled_renew_m3u, trigger='interval', minutes=max_age_before_download)
                else:
                    scheduler.add_job(id='M3U Download scheduler', func=scheduled_renew_m3u, trigger='interval', hours=max_age_before_download)

                m3u_url = get_config_variable(CONFIG_PATH, 'url')

                enable_scheduler = get_config_variable(CONFIG_PATH, 'enable_scheduler')

                if enable_scheduler == "1":
                    scan_interval = int(get_config_variable(CONFIG_PATH, 'scan_interval'))
                    debug = get_config_variable(CONFIG_PATH, 'debug')
                    if debug == "yes":
                        scheduler.add_job(id='VOD scheduler', func=scheduled_vod_download, trigger='interval', minutes=scan_interval)
                    else:
                        scheduler.add_job(id='VOD scheduler', func=scheduled_vod_download, trigger='interval', hours=scan_interval)
                break                

        except requests.exceptions.RequestException as e:
            PrintLog("Server not yet available, retrying...", "WARNING")
        sleep(1)

def startup_instant():
    current_secret_key = get_config_variable(CONFIG_PATH, 'SECRET_KEY')
    if current_secret_key == "ChangeMe!":
        PrintLog("Updating SECRET_KEY . . .", "INFO")
        new_secret_key = secrets.token_urlsafe(16)  # Generates a secure, random key
        update_config_variable(CONFIG_PATH, 'SECRET_KEY', new_secret_key)
        app.config['SECRET_KEY'] = new_secret_key

    current_url = get_config_variable(CONFIG_PATH, 'url')
    if current_url == "":
        internal_ip = get_internal_ip()
        port_number = get_config_variable(CONFIG_PATH, 'port_number')
        new_url = "http://" + internal_ip + ":" + port_number + "/get.php?username=123&password=456&output=mpegts&type=m3u_plus"
        update_config_variable(CONFIG_PATH, 'url', new_url)

    files_dir = f'{BASE_DIR}/files'
    if not os.path.exists(files_dir):
        # Create the directory
        os.makedirs(files_dir)
        PrintLog(f"Directory {files_dir} created.", "INFO")

    m3u_url = get_config_variable(CONFIG_PATH, 'url')
    maxage_before_download = int(get_config_variable(CONFIG_PATH, 'maxage_before_download'))
    original_m3u_path = f'{BASE_DIR}/files/original.m3u'
    if is_download_needed(original_m3u_path, maxage_before_download):
        PrintLog(f"The M3U file is older than {maxage_before_download} hours or does not exist. Downloading now...", "INFO")
        download_m3u(m3u_url, original_m3u_path)
        PrintLog(f"Downloaded the M3U file to: {original_m3u_path}", "INFO")
    else:
        PrintLog(f"Using existing M3U file: {original_m3u_path}", "INFO")
        update_groups_cache()

def PrintLog(string, type):
    if type == "DEBUG":
        logging.debug(string)
    elif type == "INFO":
        logging.info(string)
    elif type == "WARNING":
        logging.warning(string)
    elif type == "ERROR":
        logging.error(string)
    elif type == "CRITICAL":
        logging.critical(string)

    print(string)


def update_groups_cache():
    PrintLog("Building the cache...", "INFO")
    #m3u_url = get_config_variable(CONFIG_PATH, 'url')
    #maxage_before_download = int(get_config_variable(CONFIG_PATH, 'maxage_before_download'))
    #original_m3u_path = f'{BASE_DIR}/files/original.m3u'

    '''
    # Check and download M3U file based on age
    if is_download_needed(original_m3u_path, maxage_before_download):
        print(f"The M3U file is older than {maxage_before_download} hours or does not exist. Downloading now...")
        download_m3u(m3u_url, original_m3u_path)
        print(f"Downloaded the M3U file to: {original_m3u_path}")
    else:
        print(f"Using existing M3U file: {original_m3u_path}")
    '''

    '''
    with open(CONFIG_PATH, 'r') as file:
        config_content = file.read()
    config_namespace = {}
    exec(config_content, {}, config_namespace)
    m3u_url = config_namespace.get('url', None)

    if not m3u_url:
        raise ValueError("M3U URL not found in config.")
    '''

    '''
    # Extract username and password from the M3U URL
    username, password = extract_credentials_from_url(m3u_url)
    if not username or not password:
        raise ValueError("Username or password could not be extracted from the M3U URL.")
    
    m3u_path = f'{BASE_DIR}/files/original.m3u'
    if not os.path.exists(m3u_path):
        raise FileNotFoundError(f"The original M3U file at '{m3u_path}' was not found.")
    '''
        
    m3u_path = f'{BASE_DIR}/files/original.m3u'
    fetched_groups = fetch_channel_groups(m3u_path)
    
    GROUPS_CACHE['groups'] = fetched_groups
    GROUPS_CACHE['last_updated'] = datetime.now()

    PrintLog("End building the cache", "INFO") 

###################################################
# Emulate functions
###################################################

@app.route('/get.php', methods=['GET', 'POST'])
def getphp():
    channels = """
#EXTM3U
#EXTINF:-1 tvg-id="NPO1.nl" tvg-name="NL: NPO 1" tvg-logo="" group-title="NL NPO KANALEN",NL: NPO 1
http://fakeiptv.fake:123/456/789/16268
#EXTINF:-1 tvg-id="NPO1.nl" tvg-name="NL: NPO 2" tvg-logo="" group-title="NL NPO KANALEN",NL: NPO 2
http://fakeiptv.fake:123/456/789/16269
#EXTINF:-1 tvg-id="NPO1.nl" tvg-name="NL: NPO 3" tvg-logo="" group-title="NL NPO KANALEN",NL: NPO 3
http://fakeiptv.fake:123/456/789/16270
#EXTINF:-1 tvg-id="RTL4.nl" tvg-name="NL: RTL 4" tvg-logo="" group-title="NL RTL KANALEN",NL: RTL 4
http://fakeiptv.fake:123/456/789/16271
#EXTINF:-1 tvg-id="RTL4.nl" tvg-name="NL: RTL 5" tvg-logo="" group-title="NL RTL KANALEN",NL: RTL 5
http://fakeiptv.fake:123/456/789/16313
#EXTINF:-1 tvg-id="NL.000080.019484" tvg-name="NL: NPO 1 Extra" tvg-logo="" group-title="NPO Extra",NL: NPO 1 Extra
http://fakeiptv.fake:123/456/789/16645
#EXTINF:-1 tvg-id="NL.000080.019484" tvg-name="NL: NPO 2 Extra" tvg-logo="" group-title="NPO Extra",NL: NPO 2 Extra
http://fakeiptv.fake:123/456/789/16644
"""
    return channels, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/player_api.php', methods=['GET', 'POST'])
def player_apiphp():

    # Sample data to mimic the response from the API
    user_info = {"user_info":{"auth":1,"status":"Active","exp_date":"2524876541","is_trial":"1","active_cons":"0","created_at":"1619992800","max_connections":"99"}}
    series_data = [{"name":"Breaking Bad (FAKE)","series_id":"1001"},{"name":"Game of Thrones (FAKE)","series_id":"1002"},{"name":"Stranger Things (FAKE)","series_id":"1003"}]
    episode_data_1001 = {"seasons":[{"episode_count":4,"id":71170,"name":"Season 1","season_number":1}],"info":{"name":"Breaking Bad (FAKE)"},"episodes":{"1":[{"id":"11933","episode_num":1,"season":1},{"id":"11933","episode_num":2,"season":1},{"id":"11933","episode_num":3,"season":1}]}}
    episode_data_1002 = {"seasons":[{"episode_count":4,"id":71170,"name":"Season 1","season_number":1}],"info":{"name":"Game of Thrones (FAKE)"},"episodes":{"1":[{"id":"11933","episode_num":1,"season":1},{"id":"11933","episode_num":2,"season":1},{"id":"11933","episode_num":3,"season":1}]}}
    episode_data_1003 = {"seasons":[{"episode_count":4,"id":71170,"name":"Season 1","season_number":1}],"info":{"name":"Stranger Things (FAKE)"},"episodes":{"1":[{"id":"11933","episode_num":1,"season":1},{"id":"11933","episode_num":2,"season":1},{"id":"11933","episode_num":3,"season":1}]}}
    movies_data = [{"name":"Interstellar (FAKE)","stream_id":"103"},{"name":"Blade Runner 2049 (FAKE)","stream_id":"105"},{"name":"The Grand Budapest Hotel (FAKE)","stream_id":"106"}]


    action = request.args.get('action')
    #category_id = request.args.get('catgeory_id')
    series_id = request.args.get('series_id')
    
    # Return user info
    if action == 'get_user_info':
        return jsonify(user_info)

    # Return series data
    if action == 'get_series':
        return jsonify(series_data)

    if action == 'get_series_info':
        if series_id == "1001":
            return jsonify(episode_data_1001)
        elif series_id == "1002":
            return jsonify(episode_data_1002)
        elif series_id == "1003":
            return jsonify(episode_data_1003)


    # Return movies data
    elif action == 'get_vod_streams':
        return jsonify(movies_data)
    
    # Default response for unsupported actions
    return jsonify({"error": "Unsupported action"}), 400

