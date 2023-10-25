import json
from paho.mqtt.client import Client, MQTTMessage
from connection.python_fbconv.fbconv import FBConverter
from functools import partial
from typing import List, Dict, Tuple, Union, Iterable
from connection.dataclasses import TrafficFlow, SPAT, Trigger
from algorithm.mapInfo import intersection


# MEC_ID = '1'
#
#
# def create_topic(mec_id: str, _topic: List[str], direction: bool) -> Dict[str, Tuple[str, int]]:
#     """
#     按照通信接口协议构造topic列表，从而简化获取和调用topic的code
#     Args:
#         mec_id: MEC的id
#         _topic: 所需订阅或发布的topic项, 如BSM, TrafficFlow, so on
#         direction: 消息传输方向, True:云平台->MEC, False:MEC->云平台
#
#     Returns: topic和qos等级组成的元组列表, 如('MECUpload/<MEC_id>/TrafficFlow', 0)
#
#     """
#     if direction is True:
#         head = 'MECCloud'
#         complete_topic = {item: ('/'.join([head, item, mec_id]), 0) for item in _topic}
#     else:
#         head = 'MECUpload'
#         complete_topic = {item: ('/'.join([head, mec_id, item]), 0) for item in _topic}
#     return complete_topic


def on_connect(client, user_data, flags, rc):
    if rc == 0:
        print('Connect to MQTT Broker')
    else:
        raise ConnectionError(f'Fail to connect MQTT Broker, error code: {rc}')


def on_message(client, user_data, msg: MQTTMessage, target_topic: dict, trigger: Trigger):
    """
    接收到订阅主题消息的回调函数，算法的入口
    """
    if msg.topic == 'MECCloud/1/TrafficFlow':
        ret_val, ret_json_val = fb_converter.fb2json(0x25, msg.payload)
        if ret_val != 0:
            raise RuntimeError('Converting Flatbuffers to JSON failed')
        ret_json_val = ret_json_val.strip(str(bytes(1), encoding='utf-8'))
        ret_json = json.loads(ret_json_val)
        print(ret_json)
        # 提取TrafficFlow信息
        traffic_flow = TrafficFlow(ret_json)
        intersection.read_traffic_flow(traffic_flow_data=traffic_flow.get_stats_details())

    elif msg.topic == 'MECCloud/1/SPAT':
        ret_val, ret_json_val = fb_converter.fb2json(0x18, msg.payload)
        if ret_val != 0:
            raise RuntimeError('Converting Flatbuffers to JSON failed')
        ret_json_val = ret_json_val.strip(str(bytes(1), encoding='utf-8'))
        ret_json = json.loads(ret_json_val)
        print(ret_json)
        # 提取SPAT信息
        spat = SPAT(ret_json)
        intersection.read_spat(spat_data=spat.get_stats_details())
        # 根据触发器提取信息
        timing_plan = trigger.execute(ret_json, intersection)
        if timing_plan:
            err_code, bytes_msg = fb_converter.json2fb(0x24, json.dumps(timing_plan).encode())
            client.publish('MECUpload/1/SignalScheme', bytes_msg)
            print('Publish new signal plan')


def connect(topics: Union[str, Iterable[str]], trigger: Trigger):
    """
    通过MQTT协议与Broker连接，阻塞形式
    """

    if isinstance(topics, str):
        topic = topics
    elif isinstance(topics, Iterable):
        topic = [(t, 0) for t in topics]
    else:
        raise TypeError(f'wrong topics type {type(topics)}')

    # 接收到订阅消息后需要相应发送的消息
    target_topic_dict = {
        'signal_scheme': 'MECUpload/1/SignalScheme',
    }
    client = Client()
    client.on_connect = on_connect
    client.on_message = partial(on_message, target_topic=target_topic_dict, trigger=trigger)

    broker = '121.36.231.253'  # '10.51.50.186'
    port = 1883
    client.connect(broker, port)
    client.subscribe(topic=topic, qos=1)
    client.loop_forever()




if __name__ == '__main__':

    first_stage = [2, 10]
    last_stage = [5, 13]
    trigger = Trigger(first_stage, last_stage)


    topics = ['MECCloud/1/TrafficFlow', 'MECCloud/1/SPAT']
    # cloud_topic = ['TrafficFlow']
    # topic = create_topic(MEC_ID, cloud_topic, False)  # 构建订阅主题

    fb_converter = FBConverter(102400)  # Flatbuffers转换成json

    connect(topics=topics, trigger=trigger)
