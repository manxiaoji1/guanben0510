# Author:Guan
import redis
import requests
from time import sleep
import urllib3
#强制取消没有SSL证书产生的警告信息
urllib3.disable_warnings()

'''
删除视频源脚本使用说明：
1、HOST为底层IP
2、YW_HOST为业务IP
3、AK和SK分别为底层的access_key和access_key值
4、使用脚本时，只需要更换以上四个参数为对应的值，然后直接运行就可以了
'''

#底层master节点IP
HOST = "10.9.244.97"

#业务IP
YW_HOST = "10.9.242.39"

#底层接口账户的access_ke和access_ke值
AK = "S5HJM44FwhOBGG2Sbkh1WM28"
SK = "QmRMQxYi0Wa25hMQsgeqkkm6"

#zone列表
zone_list = []

#cameras列表
cameras_list = []

#任务列表
task_list = []

#获取token，通过接口获取
def get_token():
    url = 'https://{}:30443/components/user_manager/v1/users/sign_token'.format(HOST)
    data = {"access_key": AK,"secret_key": SK}
    res = requests.post(url=url,json=data,verify=False)
    return res.json()['token']

# 获取token，通过redis获取
def redis_token():
    db = redis.Redis(host=YW_HOST, password="88stIVA", port=10200, db=0, decode_responses=False)
    if len(db.get("SenseTime:Whale:WhaleSync:Viper:Token:{}:30443".format(HOST)))>0:
        return db.get(f"SenseTime:Whale:WhaleSync:Viper:Token:{HOST}:30443").decode("utf-8")

#获取zone值,通过接口获取
def get_zone():
    url = 'https://{}:30443/engine/camera-manager/v1/zones?page.offset=0&page.limit=100'.format(HOST)
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {get_token()}"}
    res = requests.get(url=url,headers=headers,verify=False)
    for zone in res.json()['zones']:
        zone_list.append(zone['uuid'])
    return zone_list[-1]

#获取zone值，通过redis获取
def redis_zone():
    db = redis.Redis(host=YW_HOST, password="88stIVA", port=10200, db=0, decode_responses=False)
    if len(db.get("Whale:Camera:Zone:-1000000")) > 0:
        return db.get("Whale:Camera:Zone:-1000000").decode("utf-8")

#查询视频源
def get_video():
    url = 'https://{}:30443/engine/camera-manager/v1/zones/{}/cameras?page.offset=0&page.limit=100'.format(HOST,redis_zone())
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {get_token()}"}
    res = requests.get(url=url, headers=headers, verify=False)
    for uuid in res.json()['cameras']:
        cameras_list.append(uuid["uuid"])
    return cameras_list

#查询任务
def get_task():
    if len(get_video())>0:
        for cameras in get_video():
            url = 'https://{}:30443/engine/camera-manager/v1/zones/{}/cameras/{}/tasks?page.offset=0&page.limit=100'.format(HOST,redis_zone(),cameras)
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "Authorization": f"Bearer {get_token()}"}
            res = requests.get(url=url, headers=headers, verify=False)
            try:
                task_list.append((res.json()['tasks'][0]['camera_uuid'],res.json()['tasks'][0]['id']))
            except :
                print("任务已全部停止")
        return task_list

# 删除任务
def del_task():
    if get_task() != None:
       for task_and_camera in get_task():
           cameras_id = task_and_camera[0]
           task_id = task_and_camera[1]
           print(cameras_id,task_id)
           url = 'https://{}:30443/engine/camera-manager/v1/zones/{}/cameras/{}/tasks/{}'.format(HOST,redis_zone(),cameras_id,task_id)
           headers = {
               "Content-Type": "application/json;charset=UTF-8",
               "Authorization": f"Bearer {get_token()}"}
           res = requests.delete(url=url, headers=headers, verify=False)

#删除视频源
def del_video():
    if len(get_video()):
        for cameras in get_video():
            url = 'https://{}:30443/engine/camera-manager/v1/zones/{}/cameras/{}?force=true'.format(HOST,redis_zone(),cameras)
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "Authorization": f"Bearer {get_token()}"}
            res = requests.delete(url=url, headers=headers, verify=False)
        return "视频源清理完毕"
del_task()
sleep(3)
del_video()



