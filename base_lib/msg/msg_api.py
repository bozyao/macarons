# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

import json
import logging.handlers
import traceback

import requests

try:
    from conf.settings import MSG_HOST
except ImportError:
    from base_conf.settings import MSG_HOST

log = logging

MERCHANT_SIGNUP_ID = 15015
CUSTOMER_SIGNUP_ID = 16188
# FLOW_SIGNUP_ID = 32270                          # 新人注册  【快服务】欢迎注册成为{1}的会员,验证码:{2},请于30分钟内输入
# FLOW_FORGET_PASSWD_ID = 102649                  # 忘记密码               【快服务】您的验证码是{1}，仅能用于修改密码！
FLOW_VERYFICODE = 136724  # 验证码通用【快服务】您的验证码是{1}，请于30分钟内输入。
FLOW_RETRIEVE_PASSWORD = 32277  # 找回密码  【快服务】您的账号密码是{1},请妥善操作,防止外泄
FLOW_STATUS_ID = 104015  # 跑腿状态模版  【快服务】您的订单{1}，服务者{2}，感谢您使用快服务
FLOW_FINISH_CODE_ID = 72276  # 接单发送完成验证码  【快服务】您的订单{1}由骑士{2}提供服务,请在服务完成后出示收货码{3},并对本次服务进行评价.
FLOW_FINISH_ORDER_ID = 103984  # 订单完成提醒 【快服务】您的订单{1}已完成，请点击{2}给个好评吧.
FLOW_INVITE_COURIER = 103988  # 邀请骑士注册
FLOW_INVITE_CONSUMER = 109940  # C端完成订单推广短信     【快服务】您的订单{1}已完成，{2}
FLOW_INCOME = 125920  # 供应商收入通知
FLOW_WALLET_TO_CHARGE = 161118  # 钱包余额不足提醒    【快服务】您的钱包余额不足{1},请尽快充值
FLOW_ORDER_TIME_OVER_BOON = 168741  # 【快服务】您尾号{1}的订单配送超时，定时炸弹已被引爆，此单享受运费减免。运费将在24小时内返还到您的快服务钱包
FLOW_FETCH_ID_AD = 169404  # 【快服务】{1}订单已取货,骑士{2}正在赶来的路上{3}.
# FLOW_COUPON_ID = 103986                         # 优惠券 【快服务】亲爱的{1}，最新{2}已到账，详情点击{3}
FLOW_COUPON_ID = 173320  # 【快服务】亲爱的{1},最新{2}已发放{3},详情点击{4} 退订回N
COURIER_CHECK_OK_WITH_GROUP_ID = 72134  # 骑士审核通过有分站 【快服务】恭喜，你已通过实名认证。邀请你参加线下培训，培训地点：{1}。
COURIER_CHECK_OK_WITHOUT_GROUP_ID = 72135  # 骑士审核通过无分站 【快服务】恭喜，你已通过实名认证，快去完善你的服务主页吧，主页越完善，招揽生意越好。
MIS_COURIER_CHECK_REJECT_ID = 54033  # 骑士审核驳回      【快服务】{1}您提交的骑士审核申请未通过，{2}，请修改资料后重新提交，快服务期待您的加入！
FLOW_NEW_FETCH_ID_AD = 190121  # 【快服务】尾号{1}订单已取货,骑士{2}


def gAlias(user_id, gCid):
    data2post = {}
    data2post['user_id'] = user_id
    data2post['gCid'] = gCid
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/push/gAlias', json=data2post)
        print('gAlias %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())

    return True

def hGetUser(username, password):
    data2post = {}
    data2post['username'] = username
    data2post['password'] = password
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/push/hGetUser', json=data2post)
        print('hGetUser %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())
        return False
    return True

def setPasswd(username, password):
    data2post = {}
    data2post['username'] = username
    data2post['password'] = password
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/push/hResetPwd', json=data2post)
        print('hGetUser %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False
    except Exception:
        print(traceback.format_exc())
        return False
    return True

def pushCmd(content, f, t, action, ext_info):
    data2post = {}
    data2post['content'] = content
    data2post['f'] = f
    data2post['t'] = t
    data2post['action'] = action
    data2post['ext_info'] = ext_info
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/push/pushCmdMsg', json=data2post)
        print('pushCmd %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())
        return False

    return True


def pushCmdN(content, f, t, action, code, data):
    data2post = {}
    data2post['content'] = content
    data2post['f'] = f
    data2post['t'] = t
    data2post['action'] = action
    data2post['code'] = code
    data2post['data'] = data
    try:
        response = requests.post(MSG_HOST + '/msg/v1_1/push/pushCmdMsg', json=data2post)
        print('pushCmd %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False
    except Exception:
        print(traceback.format_exc())
        return False

    return True


def pushTxt(content, f, t, ext_info):
    data2post = {}
    data2post['content'] = content
    data2post['f'] = f
    data2post['t'] = t
    data2post['ext_info'] = ext_info
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/push/pushTxtMsg', json=data2post)
        print('pushTxt %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())
        return False

    return True


def pushMsgCallBack():
    try:
        print('start pushMsgCallBack')
        response = requests.get(
            MSG_HOST + '/msg/v1_0/push/pushMsgCallBack?channel=0&msg_id=12345&device=android_knight'
                       '&voice=0&time=2017-2-9 12:12:12&version=1020&reason=resdddddddd')
        print('pushMsgCallBack %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            bRet = 'pushMsgCallBack respcd is %s' % nRespcd, response.text

    except Exception:
        print(traceback.format_exc())


def sendSMS(to, datas, tempId):
    data2post = {}
    data2post['to'] = to
    data2post['datas'] = datas
    data2post['tempId'] = tempId
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/sms/sendSms', json=data2post)
        print('sendSMS %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())

    return True


def sendVoiceSMS(verifyCode, to):
    data2post = {}
    data2post['to'] = to
    data2post['verifyCode'] = verifyCode
    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/sms/sendVoiceSms', json=data2post)
        print('sendSMS %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())

    return True


def landingCall(to, mediaName, mediaTxt, displayNum, playTimes, respUrl, userData):
    data2post = {}
    data2post['to'] = to
    data2post['mediaName'] = mediaName
    data2post['mediaTxt'] = mediaTxt
    data2post['displayNum'] = displayNum
    data2post['playTimes'] = playTimes
    data2post['respUrl'] = respUrl
    data2post['userData'] = userData

    try:
        response = requests.post(MSG_HOST + '/msg/v1_0/sms/landingcall', json=data2post)
        print('landingCall %s' % response.text)
        if response.status_code != 200:
            bRet = 'status_code is %s' % response.status_code, ''
        res_data = json.loads(response.text)
        nRespcd = int(res_data.get('respcd', 0))
        dictData = res_data.get('data', '')
        if nRespcd != 0000:
            return False

    except Exception:
        print(traceback.format_exc())

    return True


if __name__ == '__main__':
    pass
