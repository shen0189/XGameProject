from typing import List


class Stage:
    def __init__(self, movements: list, phase: str, green_start: float, green_duration: float, allred: float):
        #该stage下所有的movement
        self.movements: List['Movement'] = movements  #define as: [movement1, movement2, ...]

        #该stgae下，信号灯参数
        self.phase: str = phase
        self.green_start: float = green_start
        self.green_duration: float = green_duration
        self.allred: float = allred


class Lane:
    def __init__(self, laneId: str, turnable: int, capacity: int, queue: int):
        self.laneId: str = laneId  #(待商议)

        #车道连接属性
        self.turnable: int = turnable   #车道末端可实施转向 直行=1，左转=2，直左=3，直右=5, 左直右=7

        #车道交通属性
        self.capacity: int = capacity
        self.queue: int = queue


class Movement:
    def __init__(self, id, lane, stage, turning):
        self.id: str = id

        #该movement所对应的stage和上游车道
        self.stage: Stage = stage
        self.lane: Lane = lane
        self.turning: int = turning  #车道实施转向 直行=1，左转=2，直左=3，直右=5, 左直右=7

    def get_capacity(self, ):
        return True

    def get_queue(self, ):
        return True


class Intersection:
    def __init__(self, movements, lanes, stages):
        self.stages: List[Stage] = stages
        self.movements: List[Movement] = movements
        self.lanes: List[Lane] = lanes

    def solve(self, ):
        return True
        