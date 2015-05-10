#coding:utf-8

import requests
import mysql.connector
import threading
import time
import re
from BeautifulSoup import BeautifulSoup

conn = mysql.connector.connect(user='root', password='', database='bugs', use_unicode=True)
cursor = conn.cursor()

lock = threading.Lock()
data_list = []


def get_html(url):
    http_header = {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}
    while True:
        try:
            r = requests.get(url, headers=http_header, timeout=10)
            break
        except Exception, e:
            print "获取页面信息失败", e

    return BeautifulSoup(r.text)


def scrapy_data(url):
    html = get_html(url).find('div', {"class": "content"})
    data = {"url": url}
    basic_data = html.findAll('h3')

    data['title'] = basic_data[1].contents[0].split(u'：')[1].encode('utf-8').strip('\t')
    data['time'] = basic_data[4].string.split(u'：')[1].encode('utf-8').strip('\t')
    data['owner'] = basic_data[3].a.string.encode('utf-8')
    data['firm'] = basic_data[2].a.string.lstrip('\r\n').strip('	').encode('utf-8')
    data['firm_url'] = basic_data[2].a['href'].encode('utf-8')
    data['type'] = html.find('p', text=re.compile(u"漏洞类型.*")).split(u'：')[1].encode('utf-8').strip('\t')
    data['focus_num'] = int(html.find('span', {"id": "attention_num"}).string)
    data['reply_num'] = len(html.findAll('li', {"class": "reply clearfix"}))

    lock.acquire()
    try:
        data_list.append(tuple(list(data.values())))
    finally:
        lock.release()


def thread_controller(start_page, end_page, thread_name):
    count = 0
    print "start %s" % thread_name

    for page in range(start_page, end_page):
        soup = get_html('http://wooyun.org/bugs/page/%d' % page)
        for x in soup.find("table", {"class": "listTable"}).tbody.findAll('td'):
            count += 1
            try:
                scrapy_data("http://wooyun.org"+x.a['href'])
            except Exception, e:
                print "读取页面数据失败"
                print e
                pass
        print "%s finish page %d" % (thread_name, page)

time1=time.time()

thread_arr = {}
PageEveryThread = int(2766/10)+1
for i in range(10):	    # 开线程
    thread_arr[i] = threading.Thread(target=thread_controller, args=(PageEveryThread*i+1, PageEveryThread*(i+1)+1, 'thread-%d' %(i+1)))
    thread_arr[i].start()


sql = 'insert ignore into wooyun (firm,firm_url,title,URL,reply_num,focus_num,time,owner,type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
while True:
    time.sleep(10)
    lock.acquire()
    try:
        if len(data_list):
            print "写入了 %d 条记录" % len(data_list)
            cursor.executemany(sql, data_list)
            conn.commit()
            data_list = []  #清空数组
        else:
            break
    finally:
        lock.release()

time2=time.time()
print time2-time1
