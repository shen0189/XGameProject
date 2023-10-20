class Stage:
    def __init__(self, movements, phase, green_start, green_duration, allred):
        #该stage下所有的movement
        self.movements = movements  #define as: [movement1, movement2, ...]

        #该stgae下，信号灯参数
        self.phase = phase
        self.green_start = green_start
        self.green_duration = green_duration
        self.allred = allred


class Movement:
    def __init__(self, id, lane, stage, green_start, green_duration):
        self.id = id

        #该movement所对应的stage和lane
        self.stage = stage
        self.lane = lane

        #该movement对应的信号灯参数，考虑双环八相位可以在stage中提取？
        # self.green_start = green_start
        # self.green_duration = green_duration

class Lane:
    def __init_(self, laneId, turning, capacity, queue):
        self.laneId = laneId  #(待商议)

        #车道连接属性
        self.turning = turning #车道末端可实施转向 直行=0，左转=1，右转2，（待商议）

        #车道交通属性
        self.capacity = capacity
        self.queue = queue

        # self.green_start = green_start
        # self.green_duration = green_duration
        # # self.speedlimits = speedlimits
    
class Intersection:
    def __init__(self, movements, lanes, stages):
        self.stages = stages
        self.movements = movements
        self.lanes = lanes
        