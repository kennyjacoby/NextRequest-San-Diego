import time
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import smtplib

class ScrapingBrowser(webdriver.Chrome):
	def __init__(self, addr, *args, **kwargs):
		super(ScrapingBrowser, self).__init__(*args, **kwargs)
		self.implicitly_wait(6)
		self.get(addr)

	def click_xpath(self, location):
		self.find_element_by_xpath(location).click()

def getClosedCases(path):
	closed = []
	fd = open(path + 'closed_requests.txt', 'r')
	for line in fd:
		closed.append(line.rstrip('\n'))
	fd.close()
	return closed

def go(path):
	new_requests = []
	email_body = ""
	closed = getClosedCases(path)
	soup = getSoup('https://sandiego.nextrequest.com/requests')
	lastPageURL = soup.find("ul", {"class":"pagination"}).findAll("li")[-1].a['href']
	numPages = int(lastPageURL.split('=')[-1])
	#for pageNum in range(1, numPages+1):
	for pageNum in range(1, 10):
		new_requests, email_body = compare(pageNum, closed, new_requests, email_body)
	numRequests = len(new_requests)
	if numRequests > 0: 
		send_email(email_body, numRequests)
	for idNum in new_requests:
		fd = open(path + 'closed_requests.txt', 'a')
		fd.write(idNum + '\n')

def compare(pageNum, closed, new_requests, email_body):
	records = []
	url = 'https://sandiego.nextrequest.com/requests?requests_smart_listing[page]={}'.format(pageNum)
	soup = getSoup(url)
	for row in soup.find("table", {"class":"request_table responsive"}).tbody.findAll("tr"):
		data = row.findAll("td")
		link = 'https://sandiego.nextrequest.com' + data[0].a['href'].encode('utf8')
		idNum = link.split('/')[-1]
		if idNum not in closed:
			email_body = getRequest(idNum, link, email_body)
			new_requests.append(idNum)
	return new_requests, email_body

def getRequest(idNum, link, email_body):
	soup = getSoup(link)
	status = soup.find("div", {"class":"request-status-label"}).find("h5").contents[0].encode('utf8')
	req_text = soup.find("div", {"id":"request-text"})
	[s.extract() for s in req_text(['style', 'script', '[document]', 'head', 'title'])]
	visible_text = req_text.getText().encode("utf8")
	final_text = ''
	punctuation = ['.', ':', ';', '?', '!']
	for ch in range(len(visible_text)-1):
		current = visible_text[ch]
		next = visible_text[ch+1]
		final_text += current
		if (current.islower() and next.isupper()) or (current in punctuation and next.isupper()):
			final_text += '\n\n'
	req_date = soup.find("p", {"class":"request_date"}).strong.contents[0].encode('utf8').strip()
	dept = soup.find("div", {"class":"department row"}).strong.contents[0].encode('utf8').strip()
	docs = soup.find("div", {"class":"row published-documents"}).p
	docs_links = docs.findAll("a")
	final_links = ''
	if len(docs_links) == 0:
		final_links = "N/A"
	else:
		for docs_link in docs_links:
			final_links += 'https://sandiego.nextrequest.com' + docs_link['href'] + '\n'
	contact = soup.find("p", {"class":"request-detail"}).contents[0].encode('utf8').strip()
	body = '\nRequest ID: {}\nRequest Date: {}\nStatus: {}\nDepartment: {}\nStaff Contact: {}\nLink: {}\nDocument(s): {}\n{}\n'.format(idNum, req_date, status, dept, contact, link, final_links, final_text)
	print(body)
	email_body += body
	return email_body

def getSoup(url):
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data)
	return soup

def send_email(body, ctr):
	for toaddr in ['kenny.jacoby@nbcuni.com', 'TomJ@nbcuni.com', 'JW.August@nbcuni.com', 'Paul.Krueger@nbcuni.com', 'Lynn.walsh@nbcuni.com', 'Mari.Payton@nbcuni.com', 'Jay.Yoo@nbcuni.com']:
		fromaddr = 'scrapingkj@gmail.com'
		pwd = 'kjscraping'
		msg = "\r\n".join([
			"From: {}".format(fromaddr),
			"To: {}".format(toaddr),
			"Subject: {} new public records on NextRequest".format(ctr),
			"",
			"{}".format(body)
			])
		server = smtplib.SMTP('smtp.gmail.com:587')
		server.ehlo()
		server.starttls()
		server.login(fromaddr, pwd)
		server.sendmail(fromaddr, toaddr, msg)
		server.quit()
	print('\nEmail sent!')

def main():
	path = "/Users/kennyjacoby/Documents/scrapers/"
	start_time = time.time()
	go(path)
	print('\n{} minutes, {} seconds'.format(int(round((time.time() - start_time)//60)), int(round((time.time() - start_time)%60))))

if __name__ == "__main__":
    main()