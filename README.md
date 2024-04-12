# M3USort
A webserver for sorting and customizing IPTV playlists, and building a local streaming catalog for VOD.

What started as a small python tool has grown into its current form. With M3USort, you can create a custom IPTV playlist based on the original playlist from your IPTV provider. You can easily remove unwanted channel groups, sort channel groups, and even create a custom channel group with channels from existing groups.

After a fresh install, the program will create a URL to emulate the IPTV API. It will connect to itself, providing some fake channel groups, fake channels, fake movies, and fake series. The playlist works for the program but obviously will not work with an IPTV player. It is made to get to know the app. You will need your own IPTV subscription. Do not ask me about where to get that.

## Installation on plain Linux
When using a freshly installed Linux server (Debian 12, for instance), these are the steps to install:
```bash
apt install python3 pip git -y
git clone https://github.com/koffienl/M3USort.git
pip install Flask Flask-WTF requests m3u-ipytv flask_apscheduler packaging --break-system-packages
cd M3USort
python3 run.py
```

optional for running as a service:
```bash
nano M3USort.service
    # Edit the file according to the correct path (in this example, it would be /root/M3Usort) and save
cp M3Usort.service /etc/systemd/system/M3Usort.service
systemctl enable M3Usort && systemctl start M3Usort
```
## All the menu items

### Home
Simple, this will bring you to the landing page. It will show some server information as well as information about your IPTV subscription. The data is refreshed in the background every 60 seconds.

### Admin -> Settings
Here you can change all the settings:

- M3U URL: If you have a valid IPTV subscription, this is the place to enter the URL.
- Output File Name: The name of the new M3U playlist.
- Max Age Before Download (hours): Time interval for downloading the original playlist from the IPTV provider and rebuilding the custom playlist.
- Custom Group Title: Name of the custom channel group. This will always be the first group in the list on your IPTV player.
- Enable VOD Scheduler: If set to yes, it will 'download' the movies and series you watch.
- VOD Schedule Interval (hours): Time interval for downloading the movies and series. If 'Enable VOD Scheduler' is set to No, this timer is ignored.
- Hide webserver logs: If set to Yest the log viewer will filter out webserver requests.
- Series Directory: Where to put the files for series.
- Overwrite Existing Episodes: If set to Yes, it will recreate all the episode files every time the interval runs.
- Movies Directory: Where to put the files for movies.
- Overwrite Existing Movies: If set to Yes, it will recreate the movie file every time the interval runs.

### Admin -> Security
Here you can change the password for the admin and for downloading the playlists. It is strongly advised to change this after installation.

### Admin -> Log
Here you can view and search the logfile. Searching only works for the current page you are viewing. The logfile is located in M3USort/logs/M3USort.log.

### Admin -> Restart server
If installed as a systemctl service as root (no sudo), you can easily restart the webserver with this option.

### Groups -> Add Groups
Select the channel groups you would like to save to the new playlist.

### Groups -> Sort Groups
Here you can sort the groups in the order you like. The custom group is not listed here as it is always the first.

### Channels -> Add Channel Groups
Select one or more channel groups. All the channels that are in the selected groups will be added to the custom channel group upon saving.

### Channels -> Sort Channels
Here you can sort (and remove) the channels that are in the custom channel group.

### Channels -> Rebuild M3U
After sorting channels and groups when you do not want to wait for the scheduled timer, you can instantly rebuild the new playlist with this option.

### VOD -> Movies
Select the movies you want to 'download'. Note: this will NOT download the movie; it will only create a .strm file that has a link to the movie on the server of your IPTV provider. You still need an active subscription to watch this movie. The .strm file can be used for projects like Jellyfin.

### VOD -> Series
Select the series you want to 'download'. Note: this will NOT download the series; it will only create a .strm file for each episode that has a link to the episode on the server of your IPTV provider. You still need an active subscription to watch this series. The .strm file can be used for projects like Jellyfin.

### VOD -> Start Download
With this option, you can start the VOD download process immediately instead of waiting for the next scheduled runtime.

### Logout
Take a wild guess...


--------------------------------------



# OLD README BELOW

# IPTV Playlist Tools

This project includes two scripts designed to work with IPTV playlists in M3U format. These tools help users to filter channels by a specific group and list all unique channel groups within a playlist.

## Requirements

- Python 3
- Requests library (for downloading playlists from URLs)
- IPyTV library (for parsing and manipulating M3U playlists)

Install the necessary libraries using pip:

pip install requests m3u-ipytv



## Scripts

### ListAllChannels.py

This script filters and lists channels from a specified channel group in an IPTV playlist.

#### Usage

The script accepts the playlist source (either a local file or a URL) and the group title as command-line arguments.

python ListAllChannels.py --file "/path/to/playlist.m3u" "Group Title"

Or:

python ListAllChannels.py --url "http://example.com/playlist.m3u" "Group Title"

Make sure to replace "/path/to/playlist.m3u", "http://example.com/playlist.m3u", and "Group Title" with your file path, URL, and desired group title, respectively.



### ListAllGroups.py

This script lists all unique channel groups found in an IPTV playlist.

#### Usage

Similar to the first script, it accepts the playlist source as a command-line argument.

python ListAllGroups.py --file "/path/to/playlist.m3u"

Or:

python ListAllGroups.py --url "http://example.com/playlist.m3u"

Replace "/path/to/playlist.m3u" and "http://example.com/playlist.m3u" with the actual file path or URL of your playlist.




### config.py

Before running `M3Usort.py`, configure `config.py` with your IPTV playlist details and sorting preferences:

- `url`: The URL of your IPTV M3U playlist. This should include any necessary parameters such as username and password if required by the provider.
- `output`: The filename for the sorted and filtered playlist (e.g., 'sorted.m3u').
- `base_dir`: The base directory where the script operates. It will contain downloaded and generated playlists.
- `maxage_before_download`: The maximum age (in minutes) of a previously downloaded playlist before a new download is triggered.
- `desired_group_titles`: A list of channel group titles that you want to include in your sorted playlist. Channels outside these groups will be ignored.
- `new_group_title`: The title for a new group created from specific channels you want to highlight or place at the top of your playlist.
- `target_channel_names`: A list of specific channel names to include in the `new_group_title` group. This allows for custom ordering or prioritization of channels.

### M3Usort.py

This script sorts and filters an IPTV M3U playlist based on the configurations set in `config.py`. It can download the playlist, reorganize it, and save the result as a new M3U file.

#### How It Works

1. Downloads the M3U playlist from the specified `url` if the existing file is older than `maxage_before_download` minutes or if it doesn't exist.
2. Filters and sorts channels based on `desired_group_titles` and `target_channel_names`, creating a new playlist that matches your preferences.
3. Saves the newly generated playlist to `output`, within the `base_dir`.

#### Usage

After configuring `config.py`, run the script from the command line:

python M3Usort.py

This will generate a new M3U playlist file according to your specifications, which can be found at the path specified by the `output` parameter in `config.py`.



## Additional Notes

- For URLs with special characters (e.g., "&", "?"), ensure they are correctly quoted in `config.py` to avoid parsing issues.
- The `Requests` library is used for downloading the playlist, and `IPyTV` for parsing and generating M3U files.

