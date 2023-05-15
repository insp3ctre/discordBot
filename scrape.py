import requests
from bs4 import BeautifulSoup

def meal(x):
	if x == 3:
		lunchRes = "The options for lunch are "
	elif x == 4:
		lunchRes = "The options for dinner are "
	else:
		lunchRes = "The options are "

	URL = "https://lewisandclark.cafebonappetit.com/cafe/fields-dining-room/"
	page = requests.get(URL)
	soup = BeautifulSoup(page.content, "html.parser")

	"""
	div[data-daypart-id = "#"] div div div div div div div div header button
		breakfast = 1
		brunch = 2
		lunch = 3
		dinner = 4 
	"""
	lunch = soup.select(f'div[data-daypart-id="{x}"] > div > div > div > div > div > div > div > div > header > button')

	lunch = lunch[0:4]

	for i in range(len(lunch)):
		lunch[i] = str(lunch[i])
		lunch[i] = lunch[i].replace('\t', "").replace('\n', "")

		# remove beginning html
		rmStart = lunch[i].find('<')
		rmEnd = lunch[i].find('>')
		lunch[i] = lunch[i].replace(lunch[i][rmStart:rmEnd+1], "")

		# remove end html
		rmStart = lunch[i].find('<')
		rmEnd = lunch[i].rfind('>')
		lunch[i] = lunch[i].replace(lunch[i][rmStart:rmEnd+1], "")

		lunchRes += lunch[i]
		if i < len(lunch)-2:
			lunchRes += ", "
		elif i == len(lunch)-2:
			lunchRes += ", and "
		else:
			lunchRes += "."

	return lunchRes