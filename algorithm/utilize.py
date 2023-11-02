from typing import List, Dict
import math

VEHICLE_LENGTH = 6
MIN_CYCLE = 115
MAX_CYCLE = 120
MIN_GREEN = 10


class Stage:
    def __init__(self, stage_id: int, movements: list, phases: list, green_duration: float,
                 yellow_duration: float, allred: float):

        self.id = stage_id

        # 该stage下所有的movement
        self.movements: List['Movement'] = movements  # define as: [movement1, movement2, ...]

        # 该stgae下，信号灯参数
        self.phases: List[int] = phases
        # self.green_start: float = green_start
        self.green_duration: float = green_duration
        self.yellow_duration: float = yellow_duration
        self.allred: float = allred

        self.remaining_red: float = 0
        self.saturation: float = 0
        self.pressure: float = 0

    def set_remaining_red(self, remaining_red: float):
        self.remaining_red = remaining_red / 10

    def update_saturation(self):
        saturation = 0
        for movement in self.movements:
            if movement.saturation > saturation:
                saturation = movement.saturation
        print(f'The saturation of Stage {self.id} is {saturation}')
        self.saturation = saturation

    def update_pressure(self):
        pressure = 0
        for movement in self.movements:
            pressure += movement.pressure
        self.pressure = pressure


class Lane:
    def __init__(self, ext_id: str, turnable: int, capacity: int):
        # self.lane_id: str = lane_id  #(待商议)
        self.id: str = ext_id

        # 车道连接属性
        self.turnable: int = turnable  # 车道末端可实施转向 直行=1，左转=2，直左=3，直右=5, 左直右=7
        # 车道交通属性
        self.capacity: int = capacity  # in veh/h
        self.current_queue: float = 0
        self.volume: float = 0  # in veh/h
        self.volume_list: list = []
        self.volume_duration_list: list = []
        self.max_queue_before_green: float = 0
        self.max_queue_after_green: float = 0

    def set_volume(self, volume: int):
        self.volume = volume * 0.01

    def update_volume(self, volume, duration):
        if sum(self.volume_duration_list) + duration > 300:
            self.volume_duration_list.pop(0)
            self.volume_list.pop(0)
        self.volume_duration_list.append(duration)
        self.volume_list.append(volume * 0.01)
        if sum(self.volume_duration_list) > 0:
            self.volume = sum(v * i for v, i in zip(self.volume_list, self.volume_duration_list)) / sum(
                self.volume_duration_list)
        else:
            self.set_volume(volume)

    def set_queue(self, queue):
        self.current_queue = queue * 0.1 / VEHICLE_LENGTH


class Movement:
    def __init__(self, mov_id: int, lanes: List[Lane], turning: int):
        self.id: int = mov_id

        # 该movement所对应的stage和上游车道
        self.stage = None
        self.lanes: List[Lane] = lanes
        self.turning: int = turning  # 车道实施转向 直行=1，左转=2，直左=3，直右=5, 左直右=7

        self.pressure: float = 0
        self.saturation: float = 0

    def set_stage(self, stage: Stage):
        self.stage = stage

    def get_capacity(self):
        capacity = 0
        for lane in self.lanes:
            capacity += lane.capacity
        return capacity

    def get_queue(self):
        queue = 0
        for lane in self.lanes:
            queue1, queue2 = lane.max_queue_before_green, lane.max_queue_after_green
            max_queue = max(queue1, queue2)
            queue += max_queue
        return queue

    def get_volume(self):
        volume = 0
        for lane in self.lanes:
            volume += lane.volume
        return volume

    def get_pressure(self):
        pressure = self.get_capacity() * self.get_queue() / 3600
        self.pressure = pressure
        return pressure

    def get_saturation(self):
        saturation = self.get_volume() / self.get_capacity()
        self.saturation = saturation
        return saturation


class Intersection:
    def __init__(self, movements, lanes, stages, yellow, allred):
        self.stages: List[Stage] = stages
        self.movements: Dict[int, Movement] = movements
        self.lanes: Dict[str, Lane] = lanes

        self.cycle: int = 0
        self.yellow_duration = yellow
        self.allred_duration = allred
        self.factor: float = 0.01

        self.min_cycle = MIN_CYCLE
        self.max_cycle = MAX_CYCLE
        self.min_green_duration = MIN_GREEN

        self.executed_stage = []

    def read_traffic_flow(self, traffic_flow_data: list):
        # print('Extract traffic flow info')
        for stat in traffic_flow_data:
            ext_id = stat['ext_id']
            lane = self.lanes[ext_id]
            # lane.set_volume(stat['volume'])
            lane.update_volume(volume=stat['volume'], duration=stat['interval'])
            lane.set_queue(stat['queue_length'])
        self.update_max_queue()
        self.update_movement_state()

    def update_max_queue(self):
        '''
        根据当前排队和当前到达率和剩余红灯时间更新预估最大排队长度 每次接收TrafficFlow并存储信息后调用
        '''
        for movement in self.movements.values():
            stage = movement.stage
            if stage is not None:
                stage_remain_red = stage.remaining_red
                for lane in movement.lanes:
                    volume, current_queue = lane.volume, lane.current_queue
                    max_queue = current_queue + volume * stage_remain_red / 3600
                    if stage.id not in self.executed_stage:
                        lane.max_queue_before_green = max(lane.max_queue_before_green, max_queue)
                    else:
                        lane.max_queue_after_green = max(lane.max_queue_after_green, max_queue)

    def update_movement_state(self):
        for movement in self.movements.values():
            if movement.stage is not None:
                movement.get_pressure()
                movement.get_saturation()

    def read_spat(self, spat_data):
        # print('Extract spat info')
        current_stage = 0
        for phase_timing in spat_data:
            phase_id, remaining_red = phase_timing['phase_id'], phase_timing['remaining_red']
            for stage in self.stages:
                if int(phase_id) in stage.phases:
                    stage.set_remaining_red(remaining_red)
                    if remaining_red == 0:
                        current_stage = stage.id
        # 考虑到黄灯 有可能所有stage的remaining_red都不是0
        if current_stage > 0:
            if current_stage not in self.executed_stage:
                self.executed_stage.append(current_stage)

    def solve(self):

        print('Run control algorithm')

        self.update_stage()

        webster_y = 0
        for stage in self.stages:
            webster_y += stage.saturation
        loss = len(self.stages) * (self.allred_duration + self.yellow_duration)
        if webster_y >= 1:
            cycle = self.max_cycle
        else:
            cycle = int(loss / (1 - webster_y))
            if cycle < self.min_cycle:
                cycle = self.min_cycle
            elif cycle > self.max_cycle:
                cycle = self.max_cycle
        self.cycle = cycle

        weights = []
        for stage in self.stages:
            weight = math.exp(self.factor * stage.pressure)
            weights.append(weight)
        weight_total = sum(weights)

        effective_green = self.cycle - loss
        feasible = True
        for weight, stage in zip(weights, self.stages):
            green_duration = int(effective_green * weight / weight_total)
            if green_duration < self.min_green_duration:
                feasible = False
                break
            else:
                stage.green_duration = green_duration
        if not feasible:
            # 若绿灯时长不满足最小绿灯要求则重新分配绿灯
            usable_effective_green = self.cycle - loss - len(self.stages) * self.min_green_duration
            for weight, stage in zip(weights, self.stages):
                additional_green_duration = int(usable_effective_green * weight / weight_total)
                stage.green_duration = self.min_green_duration + additional_green_duration

        # 检查是否由于取整操作导致各相位之和不等于周期
        total_time = loss
        for stage in self.stages:
            total_time += stage.green_duration
        if total_time < self.cycle:
            diff = self.cycle - total_time
            self.stages[-1].green_duration += diff

        self.reset()

    def update_stage(self):

        for stage in self.stages:
            stage.update_pressure()
            stage.update_saturation()

    def reset(self):
        '''
        每次执行算法重置关键参数
        '''
        self.executed_stage = []
        for lane in self.lanes.values():
            lane.max_queue_before_green = 0
            lane.max_queue_after_green = 0

    def output_signal_plan(self):
        stage_plan = []
        for stage in self.stages:
            stage_id = stage.id
            movements = [str(phase) for phase in stage.phases] + ['3', '7', '11', '15']
            green = stage.green_duration
            yellow = stage.yellow_duration
            allred = stage.allred
            stage_timing_dict = {'id': stage_id, 'order': stage_id, 'movements': movements,
                                 'green': green, 'yellow': yellow, 'allred': allred}
            stage_plan.append(stage_timing_dict)
        signal_plan = {'node_id': {'region': 1, 'id': 920}, 'time_span': {}, 'control_mode': 0,
                       'cycle': self.cycle, 'base_signal_scheme_id': 0, 'phases': stage_plan}
        return signal_plan
