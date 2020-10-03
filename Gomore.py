from webdriver_manager.chrome import ChromeDriverManager
from Gomore_IDs import get_car_IDs
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import numpy
import pandas as pd
import time
import os
import re 

all_data = []
empty_table = numpy.zeros((24,7), dtype=bool)

# Loading a pd.DataFrame with the Car's IDs
if os.path.exists('car_IDs.csv'):
	cars_db = pd.read_csv(r'car_IDs.csv')
else:
	cars_db = get_car_IDs() #you can put the location of the map, Default is all of Denmark
	cars_db.to_csv('car_IDs.csv', index=False)

base_link = 'https://gomore.dk/lejebil/'

options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {"profile.block_third_party_cookies": True})
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_experimental_option("prefs", {"profile.default_content_settings.cookies": 2})
#options.add_argument("headless") # makes the browser not show during the code run (I got errors when this is left on?!)

#If the driver is not found, then the latest chrome driver is installed
driver = webdriver.Chrome(ChromeDriverManager().install(), options = options)

for i in range(978,len(cars_db)-1):
	# Opening up each car's IDs and saving the info
	ID = cars_db['Car ID'][i]
	my_url = base_link + str(ID)
	driver.get(my_url)

	car_price = 0
	load_fail_count = 0
	
	while car_price == 0: #Little trick to search for the car price until it is different than 0 (might happen!)
		try:
			soup = bs(driver.page_source, 'lxml')
			s = soup.find_all("div", class_="flex flex-space-between flex-align-center")[0].get_text().replace("\n          ","") 
			pattern = "Periode:(.*?) dag"
			no_of_days = int(re.search(pattern, s).group(1))
			car_price = int(soup.find_all("span",class_="ml4 text-right text-nowrap")[0].get_text().split(' ')[-1].replace('.',''))/no_of_days
			service_price = int(soup.find_all("span",class_="ml4 text-right text-nowrap")[1].get_text().split(' ')[-1].replace('.',''))/no_of_days
		except:
			print("Page failed to load, trying it again.")
			load_fail_count +=1
			if load_fail_count == 10:
				print('This page probably does not exist anymore, we will skip this one!')
				break
			time.sleep(1)
	if load_fail_count ==10:
		continue
	
	# This entire section is very weird with the web scrapping, but ideally it only needs to be done/corrected once in a while
	year = soup.find(class_="mb2").text.strip().split('\n')[-1]
	owner_ID = soup.find(class_="hover:text-underline text-gray-70").get("href").replace("/profiles/","")
	owner_name = soup.find(class_="text-gray-70 mb0").text.strip().replace("Ejet af ","").replace("parkeret i","").split("  ")[0]
	address = soup.find(class_="text-gray-70 mb0").text.strip().replace("Ejet af ","").replace("parkeret i","").split("  ")[1]
	car_type = soup.find('div',class_='grid grid-template-columns-3-sm column-gap-3 row-gap-5').find_all(class_="flex")[0].get_text().replace("\n",'').strip().split(' ')[-1]
	seats = soup.find('div',class_='grid grid-template-columns-3-sm column-gap-3 row-gap-5').find_all(class_="flex")[1].get_text().replace("\n",'').strip().split(' ')[-1]
	insurance = soup.find('div',class_='grid grid-template-columns-3-sm column-gap-3 row-gap-5').find_all(class_="flex")[4].get_text().replace("\n",'').strip().split(' ')[-1]
	fuel = soup.find('div',class_='grid grid-template-columns-3-sm column-gap-3 row-gap-5').find_all(class_="flex")[5].get_text().replace("\n",'').strip().split(' ')[-1]
	road_help = soup.find('div',class_='grid grid-template-columns-3-sm column-gap-3 row-gap-5').find_all(class_="flex")[6].get_text().replace("\n",'').strip().split('  ')[-1]
	extra_km_price = soup.find('div',class_='grid grid-template-columns-3-sm column-gap-3 row-gap-5').find_all(class_="flex")[7].get_text().replace("\n",'').strip().split(' ')[-1]
	car_descr_title = soup.find_all(class_='pb10')[0].find(class_="mb3").get_text() 
	try:
		car_description = soup.find_all(class_='pb10')[0].find(class_="overflow-hidden").get_text()  
	except: 
		car_description = 'No Description'
	
	if len(soup.find_all(class_='pb10')) <= 6: #meaning that the car does not have extras:
		extras = 'No extras'
		rules = list(filter(('').__ne__,soup.find_all(class_='pb10')[3].get_text().replace('                ','').splitlines()))
	elif len(soup.find_all(class_='pb10'))== 7:
		extras = soup.find_all(class_='pb10')[2].get_text().replace('\nEkstraudstyr\n','').replace('\n',' ')
		rules = list(filter(('').__ne__,soup.find_all(class_='pb10')[3].get_text().replace('                ','').splitlines()))
	if rules[0] != 'Regler': #meaning the container has the recommendations(which are supposedly hidden)
		rules = list(filter(('').__ne__,soup.find_all(class_='pb10')[4].get_text().replace('                ','').splitlines()))

	owner_acc_rate = soup.find_all(class_='pb10')[1].find(class_='js-normal-owner-stats text-semi-bold mb0 text-nowrap').get_text().split('\n')[1][-3:]
	answer_time= soup.find_all(class_='pb10')[1].find_all(class_='js-normal-owner-stats text-semi-bold mb0 text-nowrap')[1].get_text().replace('\n                ','')
	try:
		rating = soup.find(class_='flex flex-row flex-align-center').find(itemprop='ratingValue')['content']
		no_of_ratings = soup.find(class_='flex flex-row flex-align-center').find(itemprop='ratingCount')['content']
	except TypeError:
		ratings = 'Unavailable'
		no_of_ratings = 'Unavailable'
	member_since = soup.find(class_='mb3 fbase text-gray-50').get_text().splitlines()[1].replace('        ','')
	last_online = soup.find(class_='mb3 fbase text-gray-50').get_text().splitlines()[3].replace('         ','')

	#And now the calendar!
	monday_date = soup.find(class_='table cal micro rental').find(id='js-date-0').get_text()
	my_table = numpy.copy(empty_table)
	if soup.find(class_='table cal micro rental').find_all(class_="danger") == None:
		pass
	else:
		for j in range(len(soup.find(class_='table cal micro rental').find_all(class_="danger"))):
			hour = soup.find(class_='table cal micro rental').find_all(class_="danger")[j].find_previous('tr').text.replace('\n','').replace('       ','')[0:5]
			day = soup.find(class_='table cal micro rental').find_all(class_="danger")[j]['data-weekday']
			if day == 0: 
				day = 7
			my_table[int(hour[0:2])][int(day)-1] = True
	my_table[:,1]
	all_data.append([ID, cars_db['Car Name'][i], year, car_descr_title, car_description, owner_ID, owner_name, 
	address, no_of_days, car_price, service_price , cars_db['Keyless'][i], cars_db['Quick Booking'][i], car_type,
	seats, insurance, fuel, road_help, extra_km_price, extras, rules, owner_acc_rate, answer_time, rating, no_of_ratings,
	member_since, last_online, my_table, monday_date])
	print(i)

headers = ['Car ID', 'Name', 'Year', 'Car Headlines', 'Car Description', 'Owner ID', 'Owner Name', 'Address', 'No of days','Car Price', 'Service Price', 'Keyless', 'Quick Booking',
'Type', 'Seats', 'Insurance', 'Fuel', 'Road Help', 'Extra km Price', 'Extras', 'Rules', 'Owner Accept Rate', 'Answer Time',
'Rating', 'Number of Ratings', 'Member Since', 'Last Online', 'Availability Table', 'Reference Monday']
db = pd.DataFrame(all_data, columns=headers)
db.set_index('Car ID')
db.to_excel("all_cars_info2.xlsx")