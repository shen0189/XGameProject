from algorithm.utilize import Intersection, Stage, Movement, Lane
from typing import List, Dict
# turnable = k, 直行=1，左转=2，直左=3，直右=5, 左直右=7
# turning = maneuver, 直行=0, 左转=1, 右转=2, 掉头=3 
# movement(phaseID, lane, stage, turning)
# lane(laneId, turnable, **)

# Lane reference id related to reference line of this link
# Ref. line belongs to lane ref. id 0
# Lane ref. ids on the left side of ref. line should be 1, 2, 3, ... in sequence
# Ref. ids on the right side should be -1, -2, -3, ... in sequence

#说明: 车道的capacity,queue需要获取, Movement的Stage()仍需确定

# 全局参数
ALLRED = 0
YELLOW = 3
THROUGH_SFR = 1400
LEFT_SFR = 1300
THROUGH_RIGHT_SFR = 1250


#车道定义
# TODO: 修改为MAP.json中定义的id
Lanes_N = [Lane('0KUyAFxYUW.0.0000000000_2', 2, capacity=LEFT_SFR),
           Lane('0KUyAFxYUW.0.0000000000_1', 1, capacity=THROUGH_SFR),
           Lane('0KUyAFxYUW.0.0000000000_0', 5, capacity=THROUGH_RIGHT_SFR)]
Lanes_W = [Lane('AyE3bDm3uL.0.0000000000_2', 2, capacity=LEFT_SFR),
           Lane('AyE3bDm3uL.0.0000000000_1', 1, capacity=THROUGH_SFR),
           Lane('AyE3bDm3uL.0.0000000000_0', 5, capacity=THROUGH_RIGHT_SFR)]
Lanes_E = [Lane('-HK3TRJVTf7.294.0683777000_2', 2, capacity=LEFT_SFR),
           Lane('-HK3TRJVTf7.294.0683777000_1', 1, capacity=THROUGH_SFR),
           Lane('-HK3TRJVTf7.294.0683777000_0', 5, capacity=THROUGH_RIGHT_SFR)]
Lanes_S = [Lane('-4xnhzLD_vP.143.8795332000_2', 2, capacity=LEFT_SFR),
           Lane('-4xnhzLD_vP.143.8795332000_1', 1, capacity=THROUGH_SFR),
           Lane('-4xnhzLD_vP.143.8795332000_0', 5, capacity=THROUGH_RIGHT_SFR)]
Lanes = [*Lanes_E, *Lanes_S, *Lanes_W, *Lanes_N]
Lanes_dict: Dict[str, Lane] = {lane.id: lane for lane in Lanes}

#movement与phaseID关系
Movement_N = [Movement(10, [Lanes_N[1], Lanes_N[2]], 0),
              Movement(11, [Lanes_N[2]], 2),
              Movement(9, [Lanes_N[0]], 1)]
Movement_S = [Movement(2, [Lanes_S[1], Lanes_S[2]], 0),
              Movement(3, [Lanes_S[2]], 2),
              Movement(1, [Lanes_S[0]], 1)]
Movement_W = [Movement(14, [Lanes_W[1], Lanes_W[2]], 0),
              Movement(15, [Lanes_W[2]], 2),
              Movement(13, [Lanes_W[0]], 1)]
Movement_E = [Movement(6, [Lanes_E[1], Lanes_E[2]], 0),
              Movement(7, [Lanes_E[2]], 2),
              Movement(5, [Lanes_E[0]], 1)]
Movements = [*Movement_E, *Movement_S, *Movement_W, *Movement_N]
Movements_dict: Dict[int, Movement] = {movement.id: movement for movement in Movements}

#Stage定义，基本双环八相位
Stage1 = Stage(1, [Movement_S[0], Movement_N[0]], [2, 10], green_duration=0, yellow_duration=YELLOW, allred=ALLRED)
Stage2 = Stage(2, [Movement_S[2], Movement_N[2]], [1, 9], green_duration=0, yellow_duration=YELLOW, allred=ALLRED)
Stage3 = Stage(3, [Movement_E[0], Movement_W[0]], [6, 14], green_duration=0, yellow_duration=YELLOW, allred=ALLRED)
Stage4 = Stage(4, [Movement_E[2], Movement_W[2]], [5, 13], green_duration=0, yellow_duration=YELLOW, allred=ALLRED)
Stages = [Stage1, Stage2, Stage3, Stage4]

# Movement与Stage绑定
# 相序：南北直行(2-10)-南北左转(1-9)-东西直行(6-14)-东西左转(5-13)
Movements_dict[1].set_stage(Stage2)
Movements_dict[2].set_stage(Stage1)
# Movements_dict[3].set_stage(Stage2)
Movements_dict[5].set_stage(Stage4)
Movements_dict[6].set_stage(Stage3)
# Movements_dict[7].set_stage(Stage4)
Movements_dict[9].set_stage(Stage2)
Movements_dict[10].set_stage(Stage1)
# Movements_dict[11].set_stage(Stage2)
Movements_dict[13].set_stage(Stage4)
Movements_dict[14].set_stage(Stage3)
# Movements_dict[15].set_stage(Stage4)

#intersection定义
intersection = Intersection(Movements_dict, Lanes_dict, Stages, YELLOW, ALLRED)
