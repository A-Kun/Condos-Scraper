#!/usr/bin/env python3


"""
Copyright Andrew Wang, 2019
Distributed under the terms of the GNU General Public License.
This is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This file is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this file.  If not, see <http://www.gnu.org/licenses/>.
"""


import datetime
import json
import pyhtgen
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.utils import formataddr


def download(url):
    data = requests.get(url)
    return data.text


def send_email(from_name, from_email, password, to_name, to_email, subject,
               body, smtp_server, port):
    try:
        msg = MIMEText(body, 'html', 'utf-8')
        msg['From'] = formataddr([from_name, from_email])
        msg['To'] = formataddr([to_name, to_email])
        msg['Subject'] = subject

        server = smtplib.SMTP_SSL(smtp_server, port)
        server.login(from_email, password)
        server.sendmail(from_email, [to_email, ], msg.as_string())
        server.quit()
    except Exception as e:
        print(e)


def do_parse(html):
    condos = []
    soup = BeautifulSoup(html, 'html.parser')
    list_row = soup.find(id='listRow')
    list_row_children = list_row.children
    for next_child in list_row_children:
        next_condo = next_child.get_text(separator=', ', strip=True)
        if 'Login' not in next_condo and next_condo.count(', ') == 8:
            condos.append(next_condo.split(', '))
    return condos


def fetch_area(area):
    _id = area['id']
    _type = area['type']
    url = 'https://condos.ca/toronto/north-york/condos-for-sale?tab=listings&{}_id={}'.format(_type, _id)
    return do_parse(download(url))


def read_lang_file(lang):
    try:
        with open('lang.json', encoding='utf8') as file:
            text = file.read()
            return json.loads(text)[lang]
    except Exception as e:
        print(e)
        print('Please make sure lang.json exists and is properly formatted.')
        exit(-1)


def read_config_file(config):
    try:
        with open('config.json', encoding='utf8') as file:
            text = file.read()
            return json.loads(text)[config]
    except Exception as e:
        print(e)
        print('Please make sure config.json exists and is properly formatted.')
        exit(-1)


def build_email(condos, lang):
    lang_dict = read_lang_file(lang)
    header_row = [
        lang_dict['price'],
        lang_dict['dom'],
        lang_dict['address'],
        lang_dict['unit'],
        lang_dict['bed'],
        lang_dict['shower'],
        lang_dict['parking'],
        lang_dict['size'],
        lang_dict['maint_fee'],
    ]
    htmlcode = pyhtgen.table(condos, header_row=header_row)
    return htmlcode


def generate_subject():
    response = download('https://api.exchangeratesapi.io/latest?' +
                        'symbols=CNY&base=CAD')
    response_json = json.loads(response)
    rate = round(response_json['rates']['CNY'], 3)
    return 'Condos {} | $1 = ¥{}'.format(str(datetime.date.today()), rate)


def send_condo_email(following_areas, lang, mailing_list, debug=False):
    lang_dict = read_lang_file(lang)
    body = ''

    for next_area in following_areas:
        condos = fetch_area(next_area)
        body += '<h2>' + next_area['name'] + '</h2>'
        body += build_email(condos, lang)

    body += ('<p>' + lang_dict['generate'] + ' ' +
             str(datetime.datetime.today()).split('.')[0] + '</p>'
             )

    if debug:
        print(body)
    else:
        subject = generate_subject()
        smtp_config = read_config_file('smtp')

        for next_email in mailing_list:
            send_email(
                smtp_config['from_name'],
                smtp_config['from_email'],
                smtp_config['password'],
                '',
                next_email,
                subject,
                body,
                smtp_config['smtp_server'],
                smtp_config['port'],
            )


if __name__ == '__main__':
    following_areas = read_config_file('following_areas')
    mailing_list = read_config_file('mailing_list')
    send_condo_email(following_areas,
                     read_config_file('language'),
                     mailing_list,
                     )
