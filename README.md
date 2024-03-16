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


## Web Server for Serving IPTV Files

The `webserver.py` script is a simple yet secure Flask application designed to serve IPTV playlist files from a specified directory. It requires users to authenticate using `username` and `password` parameters in the URL query string.

### Key Features

- **Secure File Serving:** Serves files from a user-specific directory, preventing unauthorized access.
- **Authentication:** Requires URL parameters for `username` and `password` to access files, enhancing security.
- **Logging:** Implements detailed logging of access and errors, including IP address logging for requests.

### Setup and Configuration

1. **Install Flask:** Ensure Flask is installed in your environment. If not, install it using pip:

pip install Flask


2. **Configure Base Directory and Port:** Edit the `BASE_DIR` and `PORT_NUMBER` variables in the script to match your desired file serving directory and port number.

3. **Logging Configuration:** Logs are written to `/data/M3Usort/server.log`. The log file rotates after reaching 100,000 bytes, with backups for the last three logs.

4. **Running the Server:** Execute the script with Python to start the server:

python webserver.py


The server will run on the specified port and be accessible from any network interface on the host machine.

### Usage

To request a file, the client needs to provide their `username` and `password` as URL query parameters. For example:

http://server-address:8080/path/to/file.m3u?username=user&password=pass


If the authentication fails or the file does not exist, the server responds with HTTP status codes `401 Unauthorized` or `404 Not Found`, respectively.

### Security Considerations

- **Path Traversal Protection:** The server uses `secure_filename` to sanitize the requested file paths, preventing path traversal attacks.
- **Client IP Logging:** For security monitoring, the server logs the IP address of each request, considering possible `X-Forwarded-For` headers.

### Contribution

This tool is part of a static project not seeking contributions. It's provided as-is for users to fork and adapt to their needs.


## Additional Notes

- For URLs with special characters (e.g., "&", "?"), ensure they are correctly quoted in `config.py` to avoid parsing issues.
- The `Requests` library is used for downloading the playlist, and `IPyTV` for parsing and generating M3U files.

## Contributions

Thank you for your interest in our project. This repository has been established as a static resource and is intended to serve as-is, without further updates or modifications. We appreciate the understanding and support of the community in respecting this decision.

As such, we are not accepting contributions, pull requests, feature requests, or any form of public discussion. The project is provided for informational purposes, and we encourage users to fork the repository if modifications or enhancements are needed for their individual use.
