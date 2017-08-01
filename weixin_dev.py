#!/usr/bin/env python
# coding: utf-8
import time
import qrcode
from pyqrcode import QRCode
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import http.cookiejar    #http是一个包，import必须引入包里的具体某个类， 不能只引入http
import requests
import xml.dom.minidom
import json
import time
import ssl
import re
import sys
import os
import subprocess
import random
import multiprocessing
import platform
import logging
import http.client
from collections import defaultdict
from urllib.parse import urlparse
from lxml import html
from socket import timeout as timeout_error
import csv
import os
import sys
import threading
import controller
import models


#import pdb

# for media upload
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoder

class RunError(Exception):
    def __init__(self, err):
        Exception.__init__(self, err)


def catchKeyboardInterrupt(fn):
    def wrapper(*args):
        try:
            return fn(*args)
        except KeyboardInterrupt:
            print('\n[*] 强制退出程序')
            logging.debug('[*] 强制退出程序')
    return wrapper


def catchRunError(fn):
    def wrapper(*args):
        while True:
            try:
                fn(*args)
                break
            except Exception as e:
                print ( str(e) + "goes wrong!!!!" )

    return wrapper




##递归的方式解码list（递归基是str，用encode转化成binary）
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, str):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


##递归的方式解码dict
def _decode_dict(data):
    rv = {}
    for key, value in data.items():
        if isinstance(key, str):
            key = key.encode('utf-8')
        if isinstance(value, str):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


class WebWeixin(object):


    ##当print 类的实例的时候，就会输出description，方便调试程序
    def __str__(self):
        description = \
            "=========================\n" + \
            "[#] Web Weixin\n" + \
            "[#] Debug Mode: " + str(self.DEBUG) + "\n" + \
            "[#] Uuid: " + self.uuid + "\n" + \
            "[#] Uin: " + str(self.uin) + "\n" + \
            "[#] Sid: " + self.sid + "\n" + \
            "[#] Skey: " + self.skey + "\n" + \
            "[#] DeviceId: " + self.deviceId + "\n" + \
            "[#] PassTicket: " + self.pass_ticket + "\n" + \
            "========================="
        return description

    def __init__(self, user_id, process_id):
        self.user_id = user_id   ##用户的唯一标识id
        self.process_id = process_id
        self.DEBUG = True
        self.commandLineQRCode = False
        self.uuid = ''
        self.base_uri = ''    #https://wx.qq.com/cgi-bin/mmwebwx-bin/
        self.redirect_uri = ''
        self.uin = ''
        self.sid = ''
        self.skey = ''
        self.pass_ticket = ''
        self.deviceId = 'e' + repr(random.random())[2:17]
        self.BaseRequest = {}   #之后每次请求带上的参数
        self.synckey = ''
        self.SyncKey = []
        self.User = []
        self.MemberList = []
        self.ContactList = []  # 好友
        self.GroupList = []  # 群
        self.GroupMemeberList = []  # 群友
        self.PublicUsersList = []  # 公众号／服务号
        self.SpecialUsersList = []  # 特殊账号
        self.autoReplyMode = False
        self.syncHost = ''
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'
        self.interactive = False
        self.autoOpen = True     ##收到图片视频等文件是否自动打开
        self.saveFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'user', self.user_id)
        self.saveSubFolders = {'webwxgeticon': 'icons', 'webwxgetheadimg': 'headimgs', 'webwxgetmsgimg': 'msgimgs',
                               'webwxgetvideo': 'videos', 'webwxgetvoice': 'voices', '_showQRCodeImg': 'qrcodes'}
        self.appid = 'wx782c26e4c19acffb'
        self.lang = 'zh_CN'
        self.lastCheckTs = time.time()
        self.memberCount = 0
        self.SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 'qmessage', 'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp', 'blogapp', 'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp',
                             'voip', 'blogappweixin', 'weixin', 'brandsessionholder', 'weixinreminder', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'officialaccounts', 'notification_messages', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil', 'userexperience_alarm', 'notification_messages']
        self.TimeOut = 20  # 同步最短时间间隔（单位：秒）
        self.media_count = -1

        self.cookie = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie))
        opener.addheaders = [('User-agent', self.user_agent)]
        urllib.request.install_opener(opener)

    def loadConfig(self, config):
        '''便于加载配置

        '''
        if config['DEBUG']:
            self.DEBUG = config['DEBUG']
        if config['autoReplyMode']:
            self.autoReplyMode = config['autoReplyMode']
        if config['user_agent']:
            self.user_agent = config['user_agent']
        if config['interactive']:
            self.interactive = config['interactive']
        if config['autoOpen']:
            self.autoOpen = config['autoOpen']

    def getUUID(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': self.appid,
            'fun': 'new',
            'lang': self.lang,
            '_': int(time.time()),
        }
        #r = requests.get(url=url, params=params)
        #r.encoding = 'utf-8'
        #data = r.text
        data = self._post(url, params, False).decode("utf-8")
        if data == '':
            return False
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            return code == '200'
        return False


    ##生成二维码
    def genQRCode(self):
        self._showQRCodeImg()

    def _showQRCodeImg(self):
        if self.commandLineQRCode:
            qrCode = QRCode('https://login.weixin.qq.com/l/' + self.uuid)
            self._showCommandLineQRCode(qrCode.text(1))
        else:
            url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
            params = {
                't': 'webwx',
                '_': int(time.time())
            }

            data = self._post(url, params, False)
            if data == '':
                return

            if not os.path.exists(self.saveFolder+'/qrcode/'):
                os.makedirs(self.saveFolder+'/qrcode/', mode=0o777)

            with open(self.saveFolder+'/qrcode/qrcode.jpg', 'wb') as fp:
                fp.write(data)

            print("Successfully write the qrcode in {0}/qrcode/qrcode.jpg".format(self.saveFolder))


    def _showCommandLineQRCode(self, qr_data, enableCmdQR=2):
        try:
            b = u'\u2588' ##这是一个黑色方块
            sys.stdout.write(b + '\r')
            sys.stdout.flush()
        except UnicodeEncodeError:
            white = 'MM'
        else:
            white = b
        black = '  '
        blockCount = int(enableCmdQR)
        if abs(blockCount) == 0:
            blockCount = 1
        white *= abs(blockCount)
        if blockCount < 0:
            white, black = black, white
        sys.stdout.write(' ' * 50 + '\r')
        sys.stdout.flush()
        qr = qr_data.replace('0', white).replace('1', black)
        sys.stdout.write(qr)
        sys.stdout.flush()

    def waitForLogin(self, tip=1):
        ''' 扫码登录，按照不同的code进行不同操作

        '''
        time.sleep(tip)
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
            tip, self.uuid, int(time.time()))
        data = self._get(url)
        if data == '':
            return False
        pm = re.search(r"window.code=(\d+);", data)
        code = pm.group(1)

        ##扫描成功
        if code == '201':
            return True

        #还需要确认登录
        elif code == '200':
            pm = re.search(r'window.redirect_uri="(\S+?)";', data)
            r_uri = pm.group(1) + '&fun=new'
            self.redirect_uri = r_uri
            self.base_uri = r_uri[:r_uri.rfind('/')]
            return True

        #登录超时
        elif code == '408':
            self._echo('[登陆超时] \n')

        ##其他号码为登录异常
        else:
            self._echo('[登陆异常] \n')
        return False




    def login(self):
        data = self._get(self.redirect_uri)
        if data == '':
            return False

        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data


        ##一个也不能为空
        if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
            return False

        ##构造BaseRequest
        self.BaseRequest = {
            'Uin': int(self.uin),
            'Sid': self.sid,
            'Skey': self.skey,
            'DeviceID': self.deviceId,
        }

        return True

    def webwxinit(self):
        url = self.base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, int(time.time()))
        params = {
            'BaseRequest': self.BaseRequest
        }
        dic = self._post(url, params)
        if dic == '':
            return False
        self.SyncKey = dic['SyncKey']
        self.User = dic['User']
        # synckey for synccheck
        self.synckey = '|'.join(
            [str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.SyncKey['List']])

        return dic['BaseResponse']['Ret'] == 0

    def webwxstatusnotify(self):
        url = self.base_uri + \
            '/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            "Code": 3,
            "FromUserName": self.User['UserName'],
            "ToUserName": self.User['UserName'],
            "ClientMsgId": int(time.time())
        }
        dic = self._post(url, params)
        if dic == '':
            return False

        return dic['BaseResponse']['Ret'] == 0

    def webwxgetcontact(self):
        SpecialUsers = self.SpecialUsers
        url = self.base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, int(time.time()))
        dic = self._post(url, {})
        if dic == '':
            return False

        self.MemberCount = dic['MemberCount']
        self.MemberList = dic['MemberList']
        ContactList = self.MemberList[:]
        GroupList = self.GroupList[:]
        PublicUsersList = self.PublicUsersList[:]
        SpecialUsersList = self.SpecialUsersList[:]

        for i in range(len(ContactList) - 1, -1, -1):
            Contact = ContactList[i]
            if Contact['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                # ContactList.remove(Contact)
                self.PublicUsersList.append(Contact)
            elif Contact['UserName'] in SpecialUsers:  # 特殊账号
                # ContactList.remove(Contact)
                self.SpecialUsersList.append(Contact)
            elif '@@' in Contact['UserName']:  # 群聊
                # ContactList.remove(Contact)
                self.GroupList.append(Contact)
            elif Contact['UserName'] == self.User['UserName']:  # 自己
                # ContactList.remove(Contact)
                pass


        self.ContactList = ContactList

        return True

    def webwxbatchgetcontact(self):
        url = self.base_uri + \
            '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (
                int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            "Count": len(self.GroupList),
            "List": [{"UserName": g['UserName'], "EncryChatRoomId":""} for g in self.GroupList]
        }
        dic = self._post(url, params)
        if dic == '':
            return False

        # blabla ...
        ContactList = dic['ContactList']
        ContactCount = dic['Count']
        self.GroupList = ContactList

        for i in range(len(ContactList) - 1, -1, -1):
            Contact = ContactList[i]
            MemberList = Contact['MemberList']
            for member in MemberList:
                self.GroupMemeberList.append(member)
        return True

    def getNameById(self, id):
        '''通过群id获取群的名称

        @param id group id
        @return groupname list
        '''
        url = self.base_uri + \
            '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (
                int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            "Count": 1,
            "List": [{"UserName": id, "EncryChatRoomId": ""}]
        }
        dic = self._post(url, params)
        if dic == '':
            return None

        # blabla ...
        return dic['ContactList']

    def testsynccheck(self):
        '''检查下面列表中的host中是否至少有一个是正常的

        '''
        SyncHost = ['wx2.qq.com',
                    'webpush.wx2.qq.com',
                    'wx8.qq.com',
                    'webpush.wx8.qq.com',
                    'qq.com',
                    'webpush.wx.qq.com',
                    'web2.wechat.com',
                    'webpush.web2.wechat.com',
                    'wechat.com',
                    'webpush.web.wechat.com',
                    'webpush.weixin.qq.com',
                    'webpush.wechat.com',
                    'webpush1.wechat.com',
                    'webpush2.wechat.com',
                    'webpush.wx.qq.com',
                    'webpush2.wx.qq.com']
        try:
            for host in SyncHost:
                self.syncHost = host
                print ('try' + host + '.....')
                [retcode, selector] = self.synccheck()
                if retcode == '0':
                    return True
            return False
        except:
            import traceback
            logging.error('wield exception: ' + traceback.format_exc())

    def synccheck(self):
        '''发送一次get请求，timeout设置为5秒

        '''
        params = {
            'r': int(time.time()),
            'sid': self.sid,
            'uin': self.uin,
            'skey': self.skey,
            'deviceid': self.deviceId,
            'synckey': self.synckey,
            '_': int(time.time()),
        }
        url = 'https://' + self.syncHost + '/cgi-bin/mmwebwx-bin/synccheck?' + urllib.parse.urlencode(params)
        data = self._get(url, timeout=5)


        ##没有数据返回[-1, -1]
        if data == '':
            return [-1,-1]

        pm = re.search(
            r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', data)
        retcode = pm.group(1)
        selector = pm.group(2)

        print (data)
        return [retcode, selector]

    def webwxsync(self):
        '''向server端请求，获取数据

           @return 字典类型的数据
        '''
        url = self.base_uri + \
            '/webwxsync?sid=%s&skey=%s&pass_ticket=%s' % (
                self.sid, self.skey, self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            'SyncKey': self.SyncKey,
            'rr': ~int(time.time())  #对数据取反
        }
        dic = self._post(url, params)
        if dic == '':
            return None

        if dic['BaseResponse']['Ret'] == 0:
            self.SyncKey = dic['SyncKey']
            self.synckey = '|'.join(
                [str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.SyncKey['List']])
        return dic

    def webwxsendmsg(self, word, to='filehelper'):
        url = self.base_uri + \
            '/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)
        clientMsgId = str(int(time.time() * 1000)) + \
            str(random.random())[:5].replace('.', '')
        params = {
            'BaseRequest': self.BaseRequest,
            'Msg': {
                "Type": 1,
                "Content": self._transcoding(word),
                "FromUserName": self.User['UserName'],
                "ToUserName": to,
                "LocalID": clientMsgId,
                "ClientMsgId": clientMsgId
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        r = requests.post(url, data=data, headers=headers)
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def _saveFile(self, filename, data, api=None):
        """ 保存文件

        利用不同的api创建不同的文件夹和子文件名，然后将内容写入
        @param filename 文件名
        @param data 字符串数据
        @param api 函数名称
        @return fn 路径名加文件名
        """
        fn = filename
        if self.saveSubFolders[api]:
            dirName = os.path.join(self.saveFolder, self.saveSubFolders[api])
            if not os.path.exists(dirName):
                os.makedirs(dirName)
            fn = os.path.join(dirName, filename)
            logging.debug('Saved file: %s' % fn)
            with open(fn, 'wb') as f:
                f.write(data)
                f.close()
        return fn

    def webwxgeticon(self, id):
        """

        """
        url = self.base_uri + \
            '/webwxgeticon?username=%s&skey=%s' % (id, self.skey)
        data = self._get(url)
        if data == '':
            return ''
        fn = 'img_' + id + '.jpg'
        return self._saveFile(fn, data, 'webwxgeticon')

    def webwxgetheadimg(self, id):
        url = self.base_uri + \
            '/webwxgetheadimg?username=%s&skey=%s' % (id, self.skey)
        data = self._get(url)
        if data == '':
            return ''
        fn = 'img_' + id + '.jpg'
        return self._saveFile(fn, data, 'webwxgetheadimg')

    def webwxgetmsgimg(self, msgid):
        '''向服务器端发起get请求，获取微信图片

            @param msgid 消息的id
        '''

        url = self.base_uri + \
            '/webwxgetmsgimg?MsgID=%s&skey=%s' % (msgid, self.skey)
        data = self._get(url, api='webwxgetmsgimg')
        if data == '':
            return ''
        fn = 'img_' + msgid + '.jpg'
        return self._saveFile(fn, data, 'webwxgetmsgimg')

    # Not work now for weixin haven't support this API
    def webwxgetvideo(self, msgid):
        url = self.base_uri + \
            '/webwxgetvideo?msgid=%s&skey=%s' % (msgid, self.skey)
        data = self._get(url, api='webwxgetvideo')
        if data == '':
            return ''
        fn = 'video_' + msgid + '.mp4'
        return self._saveFile(fn, data, 'webwxgetvideo')

    def webwxgetvoice(self, msgid):
        url = self.base_uri + \
            '/webwxgetvoice?msgid=%s&skey=%s' % (msgid, self.skey)
        data = self._get(url, api='webwxgetvoice')
        if data == '':
            return ''
        fn = 'voice_' + msgid + '.mp3'
        return self._saveFile(fn, data, 'webwxgetvoice')

    def getGroupName(self, id):
        '''根据群的id获取群的名称

        @param id 群的id
        @return 群的名称
        '''
        name = '未知群'

        for member in self.GroupList:
            ###先在已经获取到的群里面搜集
            if member['UserName'] == id:
                name = member['NickName']

        if name == '未知群':
            # 现有群里面查不到，再用id请求一次groupList
            GroupList = self.getNameById(id)
            for group in GroupList:
                ##更新现有的groupList，同时查找这些group中有没有想要的群名称
                self.GroupList.append(group)
                if group['UserName'] == id:
                    name = group['NickName']
                    MemberList = group['MemberList']
                    for member in MemberList:
                        self.GroupMemeberList.append(member)
        return name

    def getUserRemarkName(self, id):
        '''利用用户(群)的id来得到用户的昵称

          @param id 返回过来的名称(用户读不懂）
          @return 用户的昵称
        '''

        ##首先假定陌生
        name = '未知群' if id[:2] == '@@' else '陌生人'


        if id == self.User['UserName']:
            return self.User['NickName']  # 自己



        if id[:2] == '@@':
            # 群
            name = self.getGroupName(id)


        else:
            # 特殊账号
            for member in self.SpecialUsersList:
                if member['UserName'] == id:
                    name = member['RemarkName'] if member[
                        'RemarkName'] else member['NickName']

            # 公众号或服务号
            for member in self.PublicUsersList:
                if member['UserName'] == id:
                    name = member['RemarkName'] if member[
                        'RemarkName'] else member['NickName']

            # 直接联系人
            for member in self.ContactList:
                if member['UserName'] == id:
                    name = member['RemarkName'] if member[
                        'RemarkName'] else member['NickName']
            # 群友
            for member in self.GroupMemeberList:
                if member['UserName'] == id:
                    name = member['DisplayName'] if member[
                        'DisplayName'] else member['NickName']

        if name == '未知群' or name == '陌生人':
            logging.debug(id)
        return name

    def getUSerID(self, name):
        for member in self.MemberList:
            if name == member['RemarkName'] or name == member['NickName']:
                return member['UserName']
        return None

    def _showMsg(self, message, link=None):
        '''显示参数，写入log里面去

        @param message 字典类型的信息
        '''
        srcName = None
        dstName = None
        groupName = None
        content = None

        msg = message
        # logging.debug(msg)

        if msg['raw_msg']:
            srcName = self.getUserRemarkName(msg['raw_msg']['FromUserName'])
            dstName = self.getUserRemarkName(msg['raw_msg']['ToUserName'])

            #将转义字符替换成可显示的字符
            content = msg['raw_msg']['Content'].replace(
                '&lt;', '<').replace('&gt;', '>')
            message_id = msg['raw_msg']['MsgId']
            create_time = msg['raw_msg']['CreateTime']


            ##关于群的消息，会设置groupName


            ##自己接收到群里发的消息，有两种情况（群成员发送的，和系统发送的）
            if msg['raw_msg']['FromUserName'][:2] == '@@':

                ##群成员发送的，需要把发送人和内容分开，终点是group
                if ":<br/>" in content:
                    [people, content] = content.split(':<br/>', 1)
                    groupName = srcName
                    srcName = self.getUserRemarkName(people)
                    dstName = 'GROUP'
                ##系统发送的，直接设置起点为system
                else:
                    groupName = srcName
                    srcName = 'SYSTEM'


             # 自己发给群的消息
            elif msg['raw_msg']['ToUserName'][:2] == '@@':
                groupName = dstName
                dstName = 'GROUP'



            # 收到了红包
            if content == '收到红包，请在手机上查看':
                msg['message'] = content

            # 指定了消息内容
            if 'message' in list(msg.keys()):
                content = msg['message']


        ##打印信息

        ##群的消息(在前缀上加一个群的名称)
        if groupName != None:
            if not os.path.exists('{0}/group_talk/'.format(self.saveFolder)):
                os.makedirs("{0}/group_talk/".format(self.saveFolder),0o777)


            if not os.path.exists('{0}/group_talk/{1}_group.csv'.format(self.saveFolder, groupName.strip())):

                csvFile = open('{0}/group_talk/{1}_group.csv'.format(self.saveFolder, groupName.strip()), 'w')
                writer = csv.writer(csvFile)
                writer.writerow(['发送者', '内容', '接收者', '时间', '相关链接'])
                csvFile.close()

            ##如果存在@
            start = content.find('@')
            if start >= 0:
                end = content.find('\u2005', start)
                print(start)
                print(end)
                print('content: ' + content)
                dstName = content[start+1: end]
                content = content[end+1:]

            ##追加模式
            csvFile = open('{0}/group_talk/{1}_group.csv'.format(self.saveFolder, groupName.strip()), 'a')
            writer = csv.writer(csvFile)
            writer.writerow([srcName, content.replace('<br/>', '\n'), dstName, create_time, link])
            csvFile.close()


            print('%s |%s| %s -> %s: %s' % (message_id, groupName.strip(), srcName.strip(), dstName.strip(), content.replace('<br/>', '\n')))
            logging.info('%s |%s| %s -> %s: %s' % (message_id, groupName.strip(), srcName.strip(), dstName.strip(), content.replace('<br/>', '\n')))

        ##私聊的消息
        else:
            print('%s %s -> %s: %s' % (message_id, srcName.strip(), dstName.strip(), content.replace('<br/>', '\n')))
            logging.info('%s %s -> %s: %s' % (message_id, srcName.strip(),
                                              dstName.strip(), content.replace('<br/>', '\n')))




    def handleMsg(self, r):
        '''已经获得消息,开始处理消息

           @param r 字典类型的消息
        '''
        for msg in r['AddMsgList']:
            print('[*] 你有新的消息，请注意查收')
            logging.debug('[*] 你有新的消息，请注意查收')

            if self.DEBUG:
                fn = 'msg' + str(int(time.time())) + '.json'

                timeArray = time.localtime(msg['CreateTime'])
                msg['CreateTime'] = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

                # with open(fn, 'w') as f:
                #     f.write(json.dumps(msg))
                # print ('[*] 该消息已储存到文件: ' + fn)
                # logging.debug('[*] 该消息已储存到文件: %s' % (fn))

            msgType = msg['MsgType']
            name = self.getUserRemarkName(msg['FromUserName'])
            content = msg['Content'].replace('&lt;', '<').replace('&gt;', '>')
            msgid = msg['MsgId']



            ##文本消息
            if msgType == 1:
                raw_msg = {'raw_msg': msg}
                self._showMsg(raw_msg)

            #图片消息
            elif msgType == 3:
                ##返回图片文件名称
                image = self.webwxgetmsgimg(msgid)  #保存图片
                raw_msg = {'raw_msg': msg,
                           'message': '%s 发送了一张图片: %s' % (name, image)}
                self._showMsg(raw_msg, link=image)
                # self._safe_open(image)


            #语音消息
            elif msgType == 34:
                ##返回语音的路径
                voice = self.webwxgetvoice(msgid)
                raw_msg = {'raw_msg': msg,
                           'message': '%s 发了一段语音: %s' % (name, voice)}
                self._showMsg(raw_msg, link=voice)
                # self._safe_open(voice)

            ##动画表情
            elif msgType == 47:
                url = self._searchContent('cdnurl', content)
                raw_msg = {'raw_msg': msg,
                           'message': '%s 发了一个动画表情，点击下面链接查看: %s' % (name, url)}
                self._showMsg(raw_msg, link=url)
                # self._safe_open(url)



            ##分享链接
            elif msgType == 49:
                appMsgType = defaultdict(lambda: "")
                appMsgType.update({5: '链接', 3: '音乐', 7: '微博'})
                print('%s 分享了一个%s:' % (name, appMsgType[msg['AppMsgType']]))
                print('=========================')
                print('= 标题: %s' % msg['FileName'])
                print('= 描述: %s' % self._searchContent('des', content, 'xml'))
                print('= 链接: %s' % msg['Url'])
                print('= 来自: %s' % self._searchContent('appname', content, 'xml'))
                print('=========================')
                card = {
                    'title': msg['FileName'],
                    'description': self._searchContent('des', content, 'xml'),
                    'url': msg['Url'],
                    'appname': self._searchContent('appname', content, 'xml')
                }
                raw_msg = {'raw_msg': msg, 'message': '%s 分享了一个%s: %s' % (
                    name, appMsgType[msg['AppMsgType']], json.dumps(card))}
                self._showMsg(raw_msg, link=msg['Url'])


            ##视频
            elif msgType == 62:
                video = self.webwxgetvideo(msgid)
                raw_msg = {'raw_msg': msg,
                           'message': '%s 发了一段小视频: %s' % (name, video)}
                self._showMsg(raw_msg, link=video)
                # self._safe_open(video)


            ##撤回消息
            elif msgType == 10002:
                raw_msg = {'raw_msg': msg, 'message': '%s 撤回了一条消息' % name}
                self._showMsg(raw_msg)


    @catchRunError
    def listenMsgMode(self):
        print('[*] 进入消息监听模式 ... 成功')
        logging.debug('[*] 进入消息监听模式 ... 成功')
        self._run('[*] 进行同步线路测试 ... ', self.testsynccheck)


        #在while循环里每隔一段时间去做synccheck，以确定保持在线状态还是终止
        while True:
            self.lastCheckTs = time.time()
            [retcode, selector] = self.synccheck()
            if self.DEBUG:
                print('retcode: %s, selector: %s' % (retcode, selector))
            logging.debug('retcode: %s, selector: %s' % (retcode, selector))


            #登录失败,退出当前进程，重新开始一个子进程
            if retcode == '1100' or retcode == '1101':
                print('[*] 你在手机上登出了微信，债见')
                logging.debug('[*] 你在手机上登出了微信，债见')

                raise RunError("手机登出微信，重新开始")

                #有新的信息
            if retcode == '0' and selector == '2':
                print ('开始发起webwxsync（）。。。。') #To be deleted
                r = self.webwxsync()

                if r is not None:
                    self.handleMsg(r)

            elif retcode == '0':
                time.sleep(30)
                raise RunError("奇怪的selector "+selector)

            # elif selector == '6':

                # ##红包
                # # elif selector == '6':
                # #     # TODO
                # #     redEnvelope += 1
                # #     print('[*] 收到疑似红包消息 %d 次' % redEnvelope)
                # #     logging.debug('[*] 收到疑似红包消息 %d 次' % redEnvelope)

                # ##进入聊天界面
                # elif selector == '7':
                #     playWeChat += 1
                #     print('[*] 你在手机上玩微信被我发现了 %d 次' % playWeChat)
                #     logging.debug('[*] 你在手机上玩微信被我发现了 %d 次' % playWeChat)
                #     r = self.webwxsync()

                # ##正常

            ##小于20秒，则先睡一会儿，再进行syncheck()检查
            if (time.time() - self.lastCheckTs) <= 20:
                print ( 'Last Checked in ' + str(self.lastCheckTs) )
                print ( 'Now in ' + str(time.time()) )
                time.sleep(5)


    def _configLog(self):
        if not os.path.exists('{0}/log'.format(self.saveFolder)):
            os.makedirs('{0}/log'.format(self.saveFolder), mode=0o777);


        logging.basicConfig(filename='{0}/log'.format(self.saveFolder), level=logging.DEBUG)
        if not sys.platform.startswith('win'):
            import coloredlogs
            coloredlogs.install(level='DEBUG')

    @catchKeyboardInterrupt
    def start(self):
        ###将日志输出到指定文件
        self._configLog()
        self._echo('[*] 微信网页版 ... 开动')
        print()
        logging.debug('[*] 微信网页版 ... 开动')

        print('当前的目录为{0}'.format(self.saveFolder) )
        ##一直循环知道用户扫描成功
        while True:
            self._run('[*] 正在获取 uuid ... ', self.getUUID)
            self._echo('[*] 正在获取二维码 ... 成功')
            print()
            logging.debug('[*] 微信网页版 ... 开动')
            self.genQRCode()
            print('[*] 请使用微信扫描二维码以登录 ... ')
            if not self.waitForLogin():
                continue
                print('[*] 请在手机上点击确认以登录 ... ')
            if not self.waitForLogin(0):
                continue
            break

        ##登录完成，修改当前进程的状态
        controller.scanProcess(self.process_id)



        self._run('[*] 正在登录 ... ', self.login)
        self._run('[*] 微信初始化 ... ', self.webwxinit)
        self._run('[*] 开启状态通知 ... ', self.webwxstatusnotify)  #和通信相关
        self._run('[*] 获取联系人 ... ', self.webwxgetcontact)
        self._echo('[*] 应有 %s 个联系人，读取到联系人 %d 个' %
                   (self.MemberCount, len(self.MemberList)))
        print()
        self._echo('[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(self.GroupList),
                                                                         len(self.ContactList), len(self.SpecialUsersList), len(self.PublicUsersList)))
        print()

        self._run('[*] 获取群 ... ', self.webwxbatchgetcontact)
        logging.debug('[*] 微信网页版 ... 开动')


        ##得到使用者的整体信息
        with open('{0}/ContactList.json'.format(self.saveFolder), 'w') as fp:
            fp.write(json.dumps(self.ContactList))

        with open('{0}/GroupList.json'.format(self.saveFolder), 'w') as fp:
            fp.write(json.dumps(self.GroupList))

        with open('{0}/GroupMemberList.json'.format(self.saveFolder), 'w') as fp:
            fp.write(json.dumps(self.GroupMemeberList))


        ##开启一个子进程监听
        print("开始监听")
        self.listenMsgMode()

    def _run(self, str, func, *args):
        ''' 执行函数，记录成功与失败，失败会退出进程


        '''
        self._echo(str)
        if func(*args):
            print('成功')
            logging.debug('%s... 成功' % (str))
        else:
            print('失败\n[*] 退出程序')
            logging.debug('%s... 失败' % (str))
            logging.debug('[*] 退出程序')
            raise RunError(func.__name__)

    def _echo(self, str):
        '''简单的写到标准输出当中

        @param str 输入的字符串
        '''
        sys.stdout.write(str)
        sys.stdout.flush()


    def _transcoding(self, data):
        if not data:
            return data
        result = None
        if type(data) == str:
            result = data
        elif type(data) == str:
            result = data.decode('utf-8')
        return result

    def _get(self, url: object, api: object = None, timeout: object = None) -> object:
        ''' 用get方法请求

        @param url 请求的url
        @param api 相应类型的文件夹（可选）
        @param timeout 默认timeout时间为0
        @return data 声音和视频返回二进制流，文本图片转化成str
        '''
        request = urllib.request.Request(url=url)
        request.add_header('Referer', 'https://wx.qq.com/')
        if api == 'webwxgetvoice' or api == 'webwxgetvideo' or api == 'webwxgetmsgimg':
            request.add_header('Range', 'bytes=0-')
        try:
            response = urllib.request.urlopen(request, timeout=timeout) if timeout else urllib.request.urlopen(request)

            ##如果是二进制文件就直接读入，否则转化成utf-8成str再读入
            if api == 'webwxgetvoice' or api == 'webwxgetvideo' or api == 'webwxgetmsgimg':
                data = response.read()
            else:
                data = response.read().decode('utf-8')
            # logging.debug(url)
            return data

        except urllib.error.HTTPError as e:
            logging.error('HTTPError = ' + str(e.code))
        except urllib.error.URLError as e:
            logging.error('URLError = ' + str(e.reason))
        except http.client.HTTPException as e:
            logging.error('HTTPException')
        except timeout_error as e:
            pass
        except ssl.CertificateError as e:
            pass
        except Exception:
            import traceback
            logging.error('generic exception: ' + traceback.format_exc())
        return ''

    def _post(self, url: object, params: object, jsonfmt: object = True) -> object:
        ''' 向url发送post请求

        @param url 发送地址
        @param params 发送参数
        '''

        #如果是json格式
        if jsonfmt:
            data = (json.dumps(params)).encode()

            request = urllib.request.Request(url=url, data=data)
            request.add_header(
                'ContentType', 'application/json; charset=UTF-8')
        else:
            request = urllib.request.Request(url=url, data=urllib.parse.urlencode(params).encode(encoding='utf-8'))


        try:
            response = urllib.request.urlopen(request)
            data = response.read()
            if jsonfmt:
                return json.loads(data.decode('utf-8') )#object_hook=_decode_dict)
            return data
        except urllib.error.HTTPError as e:
            logging.error('HTTPError = ' + str(e.code))
        except urllib.error.URLError as e:
            logging.error('URLError = ' + str(e.reason))
        except http.client.HTTPException as e:
            logging.error('HTTPException')
        except Exception:
            import traceback
            logging.error('generic exception: ' + traceback.format_exc())

        return ''






    def _searchContent(self, key, content, fmat='attr'):
        ''' 按照key值寻找内容

        @param key 关键词
        @param content 要查找的内容
        @return 匹配到的括号里的关键字
        '''
        if fmat == 'attr':
            pm = re.search(key + '\s?=\s?"([^"<]+)"', content)
            if pm:
                return pm.group(1)
        elif fmat == 'xml':
            pm = re.search('<{0}>([^<]+)</{0}>'.format(key), content)
            if not pm:
                pm = re.search(
                    '<{0}><\!\[CDATA\[(.*?)\]\]></{0}>'.format(key), content)
            if pm:
                return pm.group(1)
        return '未知'


#重写write和flush方法
class UnicodeStreamFilter:

    def __init__(self, target):
        self.target = target
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.target.encoding

    def write(self, s):
        if type(s) == str:
            s = s.encode().decode('utf-8')
        s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
        self.target.write(s)

    def flush(self):
        self.target.flush()

if sys.stdout.encoding == 'cp936':
    sys.stdout = UnicodeStreamFilter(sys.stdout)

if __name__ == '__main__':

    wx = WebWeixin(sys.argv[1], os.getpid())
    wx.start()
