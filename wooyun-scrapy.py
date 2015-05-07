#coding:utf-8

import requests
import mysql.connector
import threading
import time
from BeautifulSoup import BeautifulSoup

lock = threading.Lock()
def GetHtml(url):
	httpHeader = {"User-Agent":"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}
	while True:
		try:
			r = requests.get(url,headers=httpHeader,timeout=10)
			break
		except Exception, e:
			print Exception
			print "卡死了哎。。休息30秒"
			time.sleep(30)	#应对防火墙
			
		print "Go Go !!"

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
	if lock.acquire():
		try:
			cursor.execute('insert into wooyun (title,URL,time,owner,firm,firm_url,type,reply_num,focus_num) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)',[data['title'],data['url'], data['time'],data['owner'],data['firm'],data['firm_url'],data['type'],data['reply_num'],data['focus_num']])
		finally:
			lock.release()	
	

def ThreadController(start_page,end_page,thread_name):
	count=0
	for page in range(start_page,end_page+1):
		soup = GetHtml('http://wooyun.org/bugs/page/%d' %(page))
		for x in soup.find("table",{"class":"listTable"}).tbody.findAll('td'):
			count+=1
			try:
				ScrapyData("http://wooyun.org"+x.a['href'])
				print "【adding】 in %s page=%d" %(thread_name,page)
			except Exception, e:
				print "【pass】 in %s page=%d" %(thread_name,page)
				pass

		print "%s finish page %d,totally %d" %(thread_name,page,count)
		if lock.acquire():
			try:
				conn.commit()	
			finally:
				lock.release()	
		

conn = mysql.connector.connect(user='root', password='', database='bugs', use_unicode=True)
cursor = conn.cursor()

thread={}
PageEveryThread = 2754/9
for i in range(9):	#开9个线程
	thread[i] = threading.Thread(target=ThreadController,args=(PageEveryThread*i+1,PageEveryThread*(i+1),'thread-%d' %(i+1)))
	thread[i].start()
