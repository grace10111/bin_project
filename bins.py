from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from bs4 import BeautifulSoup
import urllib.request
import datetime
from datetime import timedelta
from selenium import webdriver
from itertools import groupby


#using chrome webdriver and beautiful soup, make a soup of the website
council_website = 'https://www.southampton.gov.uk/whereilive/wastecalendar.aspx?UPRN=---------------'

driver = webdriver.Chrome()
driver.get(council_website)
html = driver.page_source

soup = BeautifulSoup(html, features='html.parser')

#scrapes all title/date/bin data out of the tables
month_list = []
for x in soup.find_all('span', {'class': 'bincal-l-title'}):
	month_list.append(x.text)
day_list = []
for y in soup.find_all('span', {'class': 'bincal-l-date'}):
	day_list.append(y.text)
type_list = []
for z in soup.find_all('span', {'class': 'bincal-l-type'}):
	type_list.append(z.text)

#gives us lists separated by title words
dates_list = [list(group) for k, group in groupby(day_list, lambda i: i == "Date") if not k]
bins_list = [list(group) for k, group in groupby(type_list, lambda i: i == "Type") if not k]

zipped_entire_list = (list(zip(month_list,dates_list,bins_list)))

list_of_bin_items = []

for item in zipped_entire_list:
  z_month = item[0].split()[0] #July
  z_year = item[0].split()[1] #2020
  z_day_bin = list(zip(item[1],item[2])) #[('03','General'), ('10', 'Glass'),....]
  for x in z_day_bin:
    dt_bin_obj = [z_year,z_month,x[0],x[1]] #['2020', 'July', '03', 'General']
    list_of_bin_items.append(dt_bin_obj)

###Google calendar API###
SCOPES = ['https://www.googleapis.com/auth/calendar']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('calendar', 'v3', credentials=creds)

#creating the reminder
for dt_bin_item in list_of_bin_items:
  date_time_obj = datetime.datetime.strptime('-'.join(dt_bin_item[0:3]), '%Y-%B-%d')
  bin_string = f'{dt_bin_item[3]} bin due out!'

  #taking 5 hours off bin time to make the reminder 7pm night before
  reminder_time = date_time_obj - timedelta(hours=5, minutes=0)

  end_time = reminder_time + timedelta(hours=2)

  #dictionary of the insert event - details
  GMT_OFF = '+01:00'      # PDT/MST/GMT-7
  event = {
    'summary': f'{bin_string}',
    'location': '-----------',
    'description': 'An automated, up-to-date bin checker.',
    'start': {
      'dateTime': reminder_time.strftime("%Y-%m-%dT%H:%M:%S+01:00"),
    },
    'end': {
      'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S+01:00"),
    },

    'attendees': [
    {'email': '------------@gmail.com'},
      ],
    'reminders': {
      'useDefault': False,
      'overrides': [
        {'method': 'popup', 'minutes': 10},
      ],
    },
  }

  #puts the event on bin_calendar instead of primary calendar
  event = service.events().insert(calendarId='--------------@group.calendar.google.com', body=event).execute()
