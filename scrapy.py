#coding:utf-8

import requests
import mysql.connector
import threading
from BeautifulSoup import BeautifulSoup

conn = mysql.connector.connect(user='root', password='', database='bugs', use_unicode=True)
cursor = conn.cursor()

def GetHtml(url):
	httpHeader = {"User-Agent":"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}
	while True:
		try:
			r = requests.get(url,headers=httpHeader)
			break
		except Exception, e:
			print Exception

	return BeautifulSoup(r.text)

def ScrapyData(url):
	html = GetHtml(url).find('div',{"class":"content"})
	data = {"url":url}
	basic_data = html.findAll('h3')


	data['title']=basic_data[1].contents[0].split(u'：')[1].encode('utf-8').strip('\t')
	data['time']=basic_data[4].string.split(u'：')[1].encode('utf-8').strip('\t')
	data['owner']=basic_data[3].a.string.encode('utf-8')
	data['firm']=basic_data[2].a.string.lstrip('\r\n').strip('	').encode('utf-8')
	data['firm_url']=basic_data[2].a['href'].encode('utf-8')
	data['type']=basic_data[6].string.split(u'：')[1].encode('utf-8').strip('\t')
	data['focus_num']=int(html.find('span',{"id":"attention_num"}).string)
	data['reply_num']=len(html.findAll('li',{"class":"reply clearfix"}))

	cursor.execute('insert into wooyun (title,URL,time,owner,firm,firm_url,type,reply_num,focus_num) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
	[data['title'],data['url'], data['time'],data['owner'],data['firm'],data['firm_url'],data['type'],data['reply_num'],data['focus_num']])





#
# print type(soup.contents[1])

# if type(soup.contents[1])==type(BeautifulSoup.NavigableString):
# 	print 2333
count=0

for page_count in range(1,2755):
	soup = GetHtml('http://wooyun.org/bugs/page/%d' %(page_count))
	for x in soup.find("table",{"class":"listTable"}).tbody.findAll('td'):
		count+=1
		try:
			ScrapyData("http://wooyun.org"+x.a['href'])
			print "adding %d" %(count)
		except Exception, e:
			print "repete, pass %d" %(count)
			pass

	conn.commit()	
cursor.close()