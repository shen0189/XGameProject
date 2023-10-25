from algorithm.utilize import Intersection

class TrafficFlow:

    def __init__(self, data):
        self.data = data

    def get_stats(self):
        return self.data.get('stats', [])

    def get_stats_details(self):
        stats_list = self.get_stats()
        details = []

        for stat in stats_list:
            ext_id = stat['map_element'].get('ext_id', None)
            volume = stat.get('volume', None)
            queue_length = stat.get('queue_length', None)
            # queue_length_meters = stat.get('queue_length_meters', None)
            # queue_length_vehicles = stat.get('queue_length_vehicles', None)

            details.append({
                'ext_id': ext_id,
                'volume': volume,
                'queue_length': queue_length,
                # 'queue_length_meters': queue_length_meters,
                # 'queue_length_vehicles': queue_length_vehicles
            })

        return details


class SPAT:

    def __init__(self, data):
        self.data = data

    def get_stats_details(self):
        details = []
        phase_stats = self.data['intersections'][0]['phases']
        for phase in phase_stats:
            phase_id = phase['id']
            phase_state = phase['phaseStates'][0]
            phase_remaining_red = phase_state['timing']['startTime']
            phase_type = phase_state['light']
            if phase_type == 'protectedMovementAllowed':
                details.append({
                    'phase_id': phase_id,
                    'remaining_red': phase_remaining_red
                })

        return details


class Trigger:

    # 初始化第一个状态
    def __init__(self, first_stage: list = ['2', '10', '3', '7', '11', '15'],
                 last_stage: list = ['5', '13', '3', '7', '11', '15']):

        # 当前使用的信号配时方案及其状态
        # used用于表征当前方案是否被执行过，last用于表示当前方案是否进入最后一个stage，setting就是信号配时的msg
        self.light_setting = {'used': False, 'last': False,
                              'setting': {"phases": [{'movements': first_stage}, {'movements': last_stage}]}}
        # 将要利用的信号方案
        # send为该方案是否发送给平台
        self.light_to_set = {'send': True, 'setting': {}}

    # 本函数将对于SPAT消息进行解析
    def SPAT_msg_parse(self, SPAT_msg: dict):

        phaseNow = {}
        phaseAll = {}
        for phase in SPAT_msg["intersections"][0]["phases"]:
            # print(phase)
            # print(phaseId)
            if phase["phaseStates"][0]["light"] == 'protectedMovementAllowed':
                phaseId = str(phase["id"]) + ' ' + str(phase["phaseStates"][0]["light"])
                timing = phase["phaseStates"][0]["timing"]
                if timing["startTime"] == 0:
                    phaseNow[phaseId] = timing
                    phaseAll[phaseId] = True
                else:
                    phaseAll[phaseId] = False
        output = {"time": SPAT_msg["timeStamp"], "phaseAll": phaseAll, "phaseNow": phaseNow}
        return output

    # 本函数将对于存储在self.light_setting中的信号灯配时信息进行读取
    # 并且根据SPAT消息解析结果对于当前状态进行判断输出是否执行发送信号命令
    def detect(self, SPAT_parse: dict):

        if self.light_setting["used"]:
            last_stage = self.light_setting["setting"]["phases"][-1]
            phaseNow = ['3', '7', '11', '15']
            for phaseId in SPAT_parse["phaseNow"].keys():
                phaseNow.append(phaseId.split(' ')[0])
            if set(phaseNow) == set(last_stage["movements"]):
                self.light_setting["last"] = True
                return True
            else:
                return False
        else:
            first_stage = self.light_setting["setting"]["phases"][0]
            phaseNow = ['3', '7', '11', '15']
            for phaseId in SPAT_parse["phaseNow"].keys():
                phaseNow.append(phaseId.split(' ')[0])
            if set(phaseNow) == set(first_stage["movements"]):
                self.light_setting["used"] = True
            return False

    # 后续和算法文件进行连接 用于计算下一个周期的配时方案
    def msg_solve(self, intersection: Intersection):

        if self.light_setting['last']:
            if self.light_to_set["send"]:
                intersection.solve()
                msg = intersection.output_signal_plan()
                # msg = {'node_id': {'region': 1, 'id': 920}, 'time_span': {}, 'control_mode': 0, 'cycle': 90,
                #        'base_signal_scheme_id': 0, 'phases': [
                #         {'id': 1, 'order': 1, 'movements': ['1', '2', '3'], 'green': 20, 'yellow': 6, 'allred': 0},
                #         {'id': 2, 'order': 2, 'movements': ['5', '6', '7'], 'green': 20, 'yellow': 6, 'allred': 0},
                #         {'id': 3, 'order': 3, 'movements': ['9', '10', '11'], 'green': 20, 'yellow': 6, 'allred': 0},
                #         {'id': 4, 'order': 4, 'movements': ['13', '14', '15'], 'green': 20, 'yellow': 6, 'allred': 0}]}
                self.light_to_set = {'send': False, 'setting': msg}
                return msg

        return None

    # # 传输消息改变配方案
    # def signal_setting(self):
    #
    #     fb_converter = FBConverter(102400)
    #
    #     if not self.light_to_set["send"]:
    #         err_code, bytes_msg = fb_converter.json2fb(0x24, json.dumps(self.light_to_set["setting"]).encode())
    #         # msg = {'details': {'next_phasic_id': 2, 'effective_time': 10}, 'details_type': 'DF_SignalRequestByPhase'}
    #         # err_code, bytes_msg = fb_converter.json2fb(0x31, json.dumps(msg).encode())
    #         client = Client()
    #         client.connect('121.36.231.253', 1883)
    #         client.publish('MECUpload/1/SignalScheme', bytes_msg)
    #
    #         self.light_to_set["send"] = True
    #         self.light_setting = {'used': False, 'last': False, 'setting': self.light_to_set["setting"]}

    # 整体运行
    def execute(self, SPAT_msg, intersection):

        SPAT_parse = self.SPAT_msg_parse(SPAT_msg)
        self.detect(SPAT_parse)
        msg = self.msg_solve(intersection)
        if msg:
            self.light_to_set["send"] = True
            self.light_setting = {'used': False, 'last': False, 'setting': self.light_to_set["setting"]}
        return msg
        # self.signal_setting()
        # print(SPAT_parse["phaseNow"].keys())
