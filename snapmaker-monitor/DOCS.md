# Home Assistant Community Add-on: Snapmaker Monitor

[![GitHub Release][releases-shield]][releases] ![Project Stage][project-stage-shield] [![License][license-shield]](LICENSE.md)
![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armv7 Architecture][armv7-shield]
[![Github Actions][github-actions-shield]][github-actions] ![Project Maintenance][maintenance-shield] [![GitHub Activity][commits-shield]][commits]
[![Discord][discord-shield]][discord] [![Community Forum][forum-shield]][forum]
[![Sponsor NemesisRE via GitHub Sponsors][github-sponsors-shield]][github-sponsors]

This add-on runs a python script, which collects the the current status from
the Snapmaker 2.0 3D-Printer API and sends it to a Home Assistant webhook.

I refactored and modified the original [version][original-script] of the script from [NiteCrwlr](https://github.com/NiteCrwlr)

## Installation

The installation of this add-on is pretty straightforward and not different in
comparison to installing any other Home Assistant add-on.

1. Click the Home Assistant My button below to open the add-on on your Home
   Assistant instance.

   [![Open this add-on in your Home Assistant instance.][addon-badge]][addon]

1. Click the "Add" button to add the add-on repository.
1. Install the add-on "Snapmaker Monitor" from the Add-on Store
1. Set your snapmaker ip in the configuration
1. Check the logs of the "Snapmaker Monitor" add-on to see if everything went
   well.

## Configuration

**Note**: _Remember to restart the add-on when the configuration is changed._

Example add-on configuration:

```yaml
ha_token: >-
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2Y2U0ZWI3NDQ0MDI0MWE2YWIzMzE5YjUzNTkxMGZmMSIsImlhdCI6MTc1NDA5NTc4MSwiZXhwIjoyMDY5NDU1NzgxfQ.6dXkjxX2Iu8kCaIf6ngG-NKLfqnAFsCnj6oKWGgcum8
ha_webhook_url: https://homeassistant.local:8123/api/webhook/wh-snapmaker
sm_ip: 192.168.0.10
sm_port: "8080"
log_level: info
```

**Note**: _This is just an example, don't copy and paste it! Create your own!_

### Option: `log_level`

The `log_level` option controls the level of log output by the addon and can
be changed to be more or less verbose, which might be useful when you are
dealing with an unknown issue. Possible values are:

- `trace`: Show every detail, like all called internal functions.
- `debug`: Shows detailed debug information.
- `info`: Normal (usually) interesting events.
- `warning`: Exceptional occurrences that are not errors.
- `error`: Runtime errors that do not require immediate action.
- `fatal`: Something went terribly wrong. Add-on becomes unusable.

Please note that each level automatically includes log messages from a
more severe level, e.g., `debug` also shows `info` messages. By default,
the `log_level` is set to `info`, which is the recommended setting unless
you are troubleshooting.

### Option: `ha_token`

The Home Assistant Long-Lived Access Token. Used to authenticate with Home Assistant.

### Option: `ha_webhook_url`

The webhook URL that the script will use to send updates to Home Assistant.

### Option: `sm_ip`

The IP address of your Snapmaker 2.0 printer.

### Option: `sm_port`

The port number of your Snapmaker 2.0 printer api. The default is `8080`.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality.

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Support

Got questions?

You have several options to get them answered:

- The [Home Assistant Community Add-ons Discord chat server][discord] for add-on
  support and feature requests.
- The [Home Assistant Discord chat server][discord-ha] for general Home
  Assistant discussions and questions.
- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

You could also [open an issue here][issue] GitHub.

## Authors & contributors

The original setup of this repository is by [Steven Kurz][NemesisRE].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2019-2025 Steven "NemesisRE" Kurz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]:https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?addon=snapmaker-monitor&repository_url=https%3A%2F%2Fgithub.com%2FNemesisRE%2Fhassio-addon-snapmaker-monitor
[contributors]: https://github.com/NemesisRE/hassio-addon-snapmaker-monitor/graphs/contributors
[discord-ha]: https://discord.gg/c5DvZ4e
[discord]: https://discord.me/hassioaddons
[forum]: https://community.home-assistant.io/t/home-assistant-add-on-snapmaker-monitor/916652?u=nemesisre
[NemesisRE]: https://github.com/NemesisRE
[issue]: https://github.com/NemesisRE/hassio-addon-snapmaker-monitor/issues
[reddit]: https://reddit.com/r/homeassistant
[releases]: https://github.com/NemesisRE/hassio-addon-snapmaker-monitor/releases
[semver]: https://semver.org/spec/v2.0.0
[original-script]: https://github.com/NiteCrwlr/playground/blob/main/SNStatus/SNStatusV2.py
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-no-red.svg
[commits-shield]: https://img.shields.io/github/commit-activity/y/NemesisRE/hassio-addon-snapmaker-monitor
[commits]: https://github.com/NemesisRE/hassio-addon-snapmaker-monitor/commits/main
[discord-shield]: https://img.shields.io/discord/478094546522079232.svg
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg
[github-actions-shield]: https://github.com/NemesisRE/hassio-addon-snapmaker-monitor/workflows/CI/badge.svg
[github-actions]: https://github.com/NemesisRE/hassio-addon-snapmaker-monitor/actions
[github-sponsors-shield]: https://img.shields.io/github/sponsors/NemesisRE
[github-sponsors]: https://github.com/sponsors/NemesisRE
[license-shield]: https://img.shields.io/github/license/NemesisRE/hassio-addon-snapmaker-monitor
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[releases-shield]: https://img.shields.io/github/release/NemesisRE/hassio-addon-snapmaker-monitor.svg
