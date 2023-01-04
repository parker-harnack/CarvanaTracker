#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os

def get_cars_on_page(url, dict):
  page = requests.get(url)
  soup = BeautifulSoup(page.content, 'html.parser')

  results = soup.find_all(attrs={'class': 'result-tile'})

  # printing the raw html results of the get request
  # for div in results:
  #   print(div.prettify())

  # going by the data-qa attribute every field element has
  # mileage has other crap in it - split after weird character
  fields = ['make-model', 'trim-mileage', 'price', 'monthly-payment', 'get-it-by']

  for result in results:
    car_id = result.find('a').get('href')

    car_data = {'make-model': '', 'mileage': '', 'price': '', 'monthly-payment': '', 'get-it-by': ''}
    
    for index, field in enumerate(fields):
      curr_field_value = result.find(attrs={'data-qa': field})
      field_text = curr_field_value.get_text()
      if field == 'trim-mileage':

        # the mileage part of a result tile also has info on the type of car,
        # so we have to split the string by the middle dot character and append
        # the car data to the make-model
        arr = field_text.split(' • ')
        car_data['make-model'] += ' - ' + arr[0]
        car_data['mileage'] = arr[1]

      elif field == 'get-it-by':
        car_data[field] = field_text.replace('Get it by ', '')

      else:
        car_data[field] = field_text

    dict[car_id] = car_data

def main():
  url = "https://www.carvana.com/cars/suv"
  dict = {}

  NUM_PAGES = 10
  for page in range(1, NUM_PAGES + 1):
    curr_url = url
    if page > 1:
      curr_url += '?page=' + str(page)

    get_cars_on_page(curr_url, dict)

  json_data = json.dumps(dict, indent = 4)

  # if the car_data folder does not exist, create it
  folder_name = 'car_data/'
  if not os.path.exists(folder_name):
    os.mkdir(folder_name)

  now = str(datetime.now())
  filename = now.replace(' ', '_') + '_carvana.json'
  filename = 'car_data/' + filename.replace(':', ';')
  with open(filename, 'w') as output_file:
    output_file.write(json_data)

  print('Gathered data on', len(dict), 'cars')
  print('Data written to:', filename)

if __name__ == '__main__':
  main()