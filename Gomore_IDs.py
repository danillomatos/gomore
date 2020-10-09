from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pandas as pd
import time
import os

# returns a pandas database without index of all the car_IDs in Denmark for a given location in the format below
def get_car_IDs(location = 
	'&latitude=56.141478587100686&longitude=12.336501796875012&position_lat=&position_lon=&within=408.54'):
	car_IDs = []
	''' Here the browser gets opened '''
	options = webdriver.ChromeOptions()
	options.add_experimental_option("prefs", {"profile.block_third_party_cookies": True})
	options.add_argument('--ignore-certificate-errors')
	options.add_argument('--incognito')
	options.add_experimental_option("prefs", {"profile.default_content_settings.cookies": 2})
	#options.add_argument("headless") # makes the browser not show during the code run (I got errors when this is left on?!)
	
	#opening up connection and grabbing the page

	driver = webdriver.Chrome(ChromeDriverManager().install(), options = options)

	my_url = 'https://gomore.dk/biludlejning?offset=0' + location
	driver.get(my_url)

	#Pressing OK in the 'cookie' button
	cookie_button = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH,
	 '/html/body/div[6]/div/div/div/button')))
	cookie_button.click()

	#starting at page 0 and creating an empty set
	page = 0 
	car_IDs = []
	car_Names = []
	car_Keyless = []
	car_Thunderbolt = []

	while True:
		page +=1
		print(page)
		soup = bs(driver.page_source, 'lxml')
		#getting the contents of the soup
		content = soup.findAll('li', class_='card pa0 mb0 mt4 relative w-100%')
		for boxes in content:
				#getting only the links (href) in the html parsing, thereafter grabbing the car IDs
			full_link = boxes.find('a', href = True)['href']
			text = boxes.find(class_="mb0 trunc-line").get_text()
			
			while only_ID in car_IDs:
				only_ID = full_link.split('/lejebil/')[1].split('?')[0]
				time.sleep(3) # Wait until new page loads

			if boxes.find(class_="inline-block ml2") ==  None:
				thunderbolt = False
			else:
				if boxes.find(class_="inline-block ml2")['data-original-title']=='Kvikbooking - book denne bil uden at vente på ejers accept.':
					thunderbolt = True
				else:
					thunderbolt = False


			if boxes.find(class_="inline-block") == None:
				keyless = False
			else:
				if boxes.find(class_="inline-block")['data-original-title'] == 'GoMore Nøglefri – afhent denne bil helt selv ved hjælp af appen':
					keyless = True
				else:
					keyless = False

			car_IDs.append(only_ID)
			car_Names.append(text)
			car_Keyless.append(keyless)
			car_Thunderbolt.append(thunderbolt)
		try:
			#clicking the next page button until there is no next page
			next_page_button = driver.find_element_by_id("next")
			next_page_button.click()
		except:
			print('last page found! (or something might have gone wrong!)')
			break
	#driver.quit()
	#saving the car IDs in a pandas dataframe in order to convert it easily to a csv file
	IDs = pd.DataFrame()
	IDs['Car ID'] = car_IDs
	IDs['Car Name'] =car_Names
	IDs['Keyless'] = car_Keyless
	IDs['Quick Booking'] = car_Thunderbolt
	return IDs

filename = 'car_IDs.csv'
if __name__ == '__main__':
	if os.path.exists(filename):
		answer = input('\nThis file already exists, would you like to overwrite it? (y/n)\t')	
		if answer in ['yes','y']:
			Car_IDs = get_car_IDs()
			Car_IDs.to_csv(filename,index = False)
		elif answer in ['no','n']:
			print('\nAlright, nothing happens!')
		else:
			print('Invalid answer. Run it again, bye bye!')
	else:
		Car_IDs = get_car_IDs()
		Car_IDs.to_csv(filename,index = False)