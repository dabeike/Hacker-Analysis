#coding:utf-8

import requests         # http请求包，可以模拟发起HTTP请求，可参考：http://www.itwhy.org/%E8%BD%AF%E4%BB%B6%E5%B7%A5%E7%A8%8B/python/python-%E7%AC%AC%E4%B8%89%E6%96%B9-http-%E5%BA%93-requests-%E5%AD%A6%E4%B9%A0.html
import mysql.connector  # 连接mysql数据库
import threading        # 多线程
import time
import re               # 正则表达式
from BeautifulSoup import BeautifulSoup     # 解析HTML页面的包，提供一些函数，从爬取的页面中提取信息

conn = mysql.connector.connect(user='root', password='', database='bugs', use_unicode=True)     # 连接本地数据库
cursor = conn.cursor()      # 实例化mysql操作指针

lock = threading.Lock()     # 线程锁，可参考: http://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/00143192823818768cd506abbc94eb5916192364506fa5d000
data_list = []


def get_html(url):
    '''
        获取HTML页面信息
        wooyun有简单的反爬虫机制，需要在请求包里添加User-Agent参数
    '''
    http_header = {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"} 
    while True:
        try:
            r = requests.get(url, headers=http_header, timeout=10)          # 发起get请求，十秒无回应自动断开
            break
        except Exception, e:
            print "获取页面信息失败", e

    return BeautifulSoup(r.text)


def scrapy_data(url):
    '''
        用beautifulsoup的一些函数，解析HTML内容，并且添加到data_list中
    '''
    html = get_html(url).find('div', {"class": "content"})
    data = {"url": url}
    basic_data = html.findAll('h3')

    data['title'] = basic_data[1].contents[0].split(u'：')[1].encode('utf-8').strip('\t')
    data['time'] = basic_data[4].string.split(u'：')[1].encode('utf-8').strip('\t')
    data['owner'] = basic_data[3].a.string.encode('utf-8')
    data['firm'] = basic_data[2].a.string.lstrip('\r\n').strip('    ').encode('utf-8')
    data['firm_url'] = basic_data[2].a['href'].encode('utf-8')
    data['type'] = html.find('p', text=re.compile(u"漏洞类型.*")).split(u'：')[1].encode('utf-8').strip('\t')
    data['focus_num'] = int(html.find('span', {"id": "attention_num"}).string)
    data['reply_num'] = len(html.findAll('li', {"class": "reply clearfix"}))

    lock.acquire()      # 获得锁
    try:
        data_list.append(tuple(list(data.values())))
    finally:
        lock.release()  # 释放锁


def thread_controller(start_page, end_page, thread_name):
    '''
        @start_page     开始页
        @end_page       结束页
        @thread_name    线程名，只是为了区分，无实际意义

        主体函数，有几个线程就会开启几个这个函数，并进行爬取操作
    '''
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


# 获取开始时间
time1=time.time()

# 开始线程
thread_arr = {}
PageEveryThread = int(2766/10)+1
for i in range(10):     # 开线程
    thread_arr[i] = threading.Thread(target=thread_controller, args=(PageEveryThread*i+1, PageEveryThread*(i+1)+1, 'thread-%d' %(i+1)))
    thread_arr[i].start()

# 每十秒往数据库写入一次数据
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
print time2-time1   # 打印爬虫所花费的时间
