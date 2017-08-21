#!/usr/bin/env python3


"""
Copyright Andrew Wang, 2017
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
import ftfy
import json
import pyhtgen
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.utils import formataddr


AREA_CODE = {
    590: 'Downtown Toronto',
    591: 'Scarborough',
    593: 'North York',
}


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
    soup = BeautifulSoup(html, 'html.parser')
    listing_tab = soup.find(id='listing-tab')
    rows = listing_tab.findAll('div', {'class': 'listing-info-sec'})
    condos = []
    for i in range(len(rows)):
        try:
            next_condo = []

            # id
            next_condo.append(rows[i].parent.parent['href'].split('-')[-1])

            # name
            next_condo.append(rows[i].findAll(
                'span', {'class': 'listing-name'})[0].text.strip())

            # price
            next_condo.append(rows[i].findAll(
                'span', {'class': 'tag-price'})[0].text.strip())

            # size
            size_div = rows[i].findAll('div', {'class': 'listing-size-div'})
            next_condo.append(size_div[0].findAll(
                'span', recursive=False)[0].text.strip())

            # per_ft2
            teal_span = rows[i].findAll('span', {'class': 'teal'})
            if len(teal_span) > 0:
                next_condo.append(teal_span[0].text.strip())
            else:
                next_condo.append('')

            # bed, shower, parking
            bed_bath_div = rows[i].findAll('div', {'class':
                                                   'listing-bed-bath-div'})
            next_condo.append(bed_bath_div[0].findAll(
                'span', recursive=False)[0].text.strip())
            next_condo.append(bed_bath_div[0].findAll(
                'span', recursive=False)[1].text.strip())
            next_condo.append(bed_bath_div[0].findAll(
                'span', recursive=False)[2].text.strip())

            # dom, maint_fee
            list_fee_ul = rows[i].findAll('ul', {'class': 'list-fee'})
            dom_text = list_fee_ul[0].findAll('li',
                                              recursive=False)[1].text.strip()
            dom_number = ''
            for j in range(len(dom_text) - 1, -1, -1):
                if dom_text[j].isdigit():
                    dom_number += dom_text[j]
                else:
                    break
            next_condo.append(dom_number)
            next_condo.append('$' + list_fee_ul[0].findAll(
                'li', recursive=False)[2].text.strip().split('$')[-1])

            condos.append(next_condo)
        except Exception as e:
            print(e)
            print(rows[i])
    return condos


def fetch_area(area_id):
    url = ('https://condos.ca/search?for=sale&search_by=Neighbourhood&polygo' +
           'n=&is_nearby=&area_ids=' + str(area_id) +
           '&buy_min=0&buy_max=99999999&rent_min=800&rent_max=6000&unit_area' +
           '_min=0&unit_area_max=99999999&type=0&beds_min=0'
           )
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
        lang_dict['id'],
        lang_dict['name'],
        lang_dict['price'],
        lang_dict['size'],
        lang_dict['per_ft2'],
        lang_dict['bed'],
        lang_dict['shower'],
        lang_dict['parking'],
        lang_dict['dom'],
        lang_dict['maint_fee'],
    ]
    htmlcode = pyhtgen.table(condos, header_row=header_row)
    return htmlcode


def send_condo_email(following_areas, lang, mailing_list):
    lang_dict = read_lang_file(lang)
    body = ''

    for next_area in following_areas:
        condos = fetch_area(next_area)
        body += '<h2>' + AREA_CODE[next_area] + '</h2>'
        body += ftfy.fix_encoding(build_email(condos, lang))

    body += ('<p>' + lang_dict['generate'] + ' ' +
             str(datetime.datetime.today()).split('.')[0] + '</p>'
             )

    smtp_config = read_config_file('smtp')

    for next_email in mailing_list:
        send_email(
            smtp_config['from_name'],
            smtp_config['from_email'],
            smtp_config['password'],
            '',
            next_email,
            'Condo Listings ' + str(datetime.date.today()),
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
