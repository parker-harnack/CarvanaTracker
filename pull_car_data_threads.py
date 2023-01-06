#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import time
import concurrent.futures
import threading 

def get_cars_on_page(url, dict, lock):
  page = requests.get(url)

  while page.status_code != 200:
    print('Error with status code', page.status_code, 'when accessing:', url)
    
    # We made too many requests too quickly, sleep for a bit then try again
    if page.status_code == 429:
      sleep_time = page.headers['Retry-After']
      print('Sleeping for', sleep_time, 'seconds')
      time.sleep(int(sleep_time))
    else:
      print('Status code', page.status_code, 'when trying:', url)
      return
    
    page = requests.get(url)

  soup = BeautifulSoup(page.content, 'html.parser')

  results = soup.find_all(attrs={'class': 'result-tile'})

  # printing the raw html results of the get request
  # for div in results:
  #   print(div.prettify())

  # going by the data-qa attribute every field element has
  # mileage has other crap in it - split after weird character
  fields = ['make-model', 'trim-mileage', 'price', 'monthly-payment', 'get-it-by']
  data = {}
  for result in results:
    car_id = result.find('a').get('href')

    car_data = {'make-model': '', 'mileage': '', 'price': '', 'monthly-payment': '', 'get-it-by': ''}
    
    for field in fields:
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

    data[car_id] = car_data

  lock.acquire()
  dict.update(data)
  print(f'Got {len(data)} cars on page {url}')
  lock.release()

  # time.sleep(1)
  
'''
This just gets the maximum number of pages for each type of car
'''
def get_max_pages(url, page, max_pages_dict):
  try:
    req = requests.get(url)
  except:
    print('Error getting page:', url)
    return
  
  soup = BeautifulSoup(req.content, 'html.parser')
  page_text = soup.find(attrs={'data-qa': 'pagination-text'}).get_text()
  print(page_text)
  max_page = page_text.split()[-1]
  max_pages_dict[page] = int(max_page)


def main():
  url = "https://www.carvana.com/cars"
  car_types = ['trucks', 'hatchback', 'sedan', 'coupe', 'electric', 'suv']
  dict = {}

  # To get number of pages, search HTML for data-qa=pagination-text
  max_pages = {'trucks': 0, 'hatchback': 0, 'sedan': 0, 'coupe': 0, 'electric': 0, 'suv': 0}
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
    for type in car_types:
      curr_url = f'{url}/{type}'
      executor.submit(get_max_pages, curr_url, type, max_pages)

  print(max_pages)
  
  with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    lock = threading.Lock()
    for type in car_types:
      for page in range(1, max_pages[type] + 1):
        curr_url = f'{url}/{type}'
        if page > 1:
          curr_url += '?page=' + str(page)       
        
        executor.submit(get_cars_on_page, curr_url, dict, lock)

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