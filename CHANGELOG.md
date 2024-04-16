# Changelog

## 0.1.19
- Removed code to try to compare new M3U with previous M3U

## 0.1.18
- some code cleanup
- changed layout of Home
- When adding a channel group to the custom channel it won't screw up the current order of that custom channel
- Fixed a bug with the new watchlist where the wanted VOD was removed when no match found

## 0.1.17
- Added option to add future release movies and series to a watchlist.

## 0.1.16
- Fixed error in scheduled_renew_m3u after 0.1.15

## 0.1.15
- Schedulers are only rescheduled when the interval is changed
- system scheduler wasn't working, fixed
- Removed age check of original.mru in scheduled download
- Added new logging category: NOTICE
- Series only mentioned in the log if there are new episodes
- When rebuilding the sorted playlist only the whitelisted group channel names are mentioned in the log, not the channels in that group

## 0.1.14
- Added links to github in the menu
- Try to restart with sudo if needed (experimental)

## 0.1.13
- Only offer update in menu when there is an update
- Small fix in readme about the service

## 0.1.12
- Added detecting if running as a service to make the restart link dynamic
- Added a simple update routine (only usable when running as serice)

## 0.1.11
- When changing the 'Max Age Before Download (hours)' in the settings page it wouldn't get rescheduled. Fixed this.

## 0.1.10
- Added warning when using default password
- Added lockout of passwords after to many attempts
- Added link to the changelog on the update message
- Added possibility to display static warnings
- Added fix to get the client's real IP address
- Change the output for log viewing to get better results when hiding webserver logs

## 0.1.9
- When adding a setting not present in the current config, it is added to the config

## 0.1.8
- BREAKING: Please `run pip install packaging` before installing this version
- updated README
- small change in service file
- small change in config.sample
- added extra pagination to bottom of log page
- added option to filter out webserver calls while viewing the log
- removed 'Dev' from version numbering

## 0.1.7 Dev
- fixed problem with spcecific series (9-1-1 for example)
- fixed issue with error on scheduled M3U download

## 0.1.6 Dev
- Moved 'rebuild M3u' menu to to 'channels' in navigation menu
- downloading movies would mention series, fixed
- added logging and logviewer

## 0.1.5 Dev
- changes in html for /home
- fixed some weird loops with download and build-cache
- rebuild of sorted M3U added to the scheduler