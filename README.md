# Condos.ca Scraper

## Introduction

Scrapes condo listings from Condos.ca, then generates and sends HTML emails.

Works great with Cron or Windows Task Scheduler for email subscriptions.

~The intention of this project is to stop my dad from asking me what condo prices in Toronto are like.~

## Usage

Settings are defined in `config.json`. See `config.json.example` for a sample setup.

Make sure `Condos-Scraper` is the current directory, then:

```
$ pip3 install requests
$ pip3 install beautifulsoup4
$ python3 condos_scraper.py
```

## Screenshot

Here's a sample generated email:

![Screenshot](http://andrewwang.ca/static/20170820/screenshot.png)
