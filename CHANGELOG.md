# Changelog

## 0.1.12
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