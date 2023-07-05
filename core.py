# c_s_b: controller switch balance
import numpy as np
import pandas as pd
import statistics
import random

MAX_LANTENCY = 44 # 最大时延

class MultiSwitch:
    """支持多控制器的交换机
    """
    def __init__(self, id, load) -> None:
        self.id = id
        self.load = load
        self.controller_id = set()
    
    def add_controller(self, controller_id):
        self.controller_id.add(controller_id)
    
    def remove_controller(self, controller_id):
        self.controller_id.remove(controller_id)
    
    def if_in_controller(self, controller_id):
        return (controller_id in self.controller_id)
    
class Switch:
    """只支持单控制器的交换机
    """
    def __init__(self, id, load) -> None:
        self.id = id
        self.load = load
        self.controller_id = None
        
    def set_controller(self, controller_id: int):
        self.controller_id = controller_id

    def if_in_controller(self, controller_id):
        return controller_id == self.controller_id

class Controller:
    def __init__(self, id, load = None) -> None:
        self.id = id
        self.load = 0
        self.switchs = {} # 附属的交换机 id -> obj
    
    def add_switch(self, switch: Switch):
        assert switch.id not in self.switchs.keys(), "已经有这个swtich对象了"
        switch.set_controller(self.id)
        self.switchs[switch.id] = switch
        self.load += switch.load
        
    def remove_switch(self, switch: Switch):
        switch.set_controller(None)
        del self.switchs[switch.id]
        self.load -= switch.load
        

class Net:
    def __init__(self, controllers: list[Controller], switchs: list[Switch], visiable_matrix: np.ndarray) -> None:
        ''' 
        字典形式存储全网所有的设备: id -> 设备对象
        '''
        self.controllers = {}
        for c in controllers:
            self.controllers[c.id] = c

        self.switchs = {}
        for s in switchs:
            self.switchs[s.id] = s
        
        self.visiable_matrix = visiable_matrix
        # print(self.visiable_matrix.shape)
    
    # controller interface
    def get_controller(self, controller_id: int) -> Controller:
        return self.controllers[controller_id]
    
    def set_controller(self, controller_id: int, controller: Controller):
        self.controllers[controller_id] = controller
    
    def add_controller(self, controller: Controller):
        assert controller.id not in self.controllers.keys(), "已经有这个controller对象了"
        self.controllers[controller.id] = controller

    def remove_controller(self, controller_id: int):
        del self.controllers[controller_id]

    # switch interface
    def get_switch(self, switch_id: int) -> Switch:
        return self.switchs[switch_id]
    
    def setswitch(self, switch_id: int, switch: Controller):
        self.switchs[switch_id] = switch
    
    def add_switch(self, switch: Switch):
        assert switch.id not in self.switchs.keys(), "已经有这个switch对象了"
        self.controllers[switch.id] = switch
        
    def remove_switch(self, switch_id: int):
        del self.switchs[switch_id]
        
    # get_distance from controller to switch
    def get_distance(self, cid: int, sid: int):
        return get_distance(self.visiable_matrix, cid, sid)

def read_visable_matrix_from_csv(file_path):
    return pd.read_csv(file_path, header=None).to_numpy()

def get_distance(matrix: np.ndarray, cid:int, sid: int):
    return matrix[cid-1][sid-1]
    
def controllers_need_blanced(controller_list: list[Controller], radio = 1.2) -> list[Controller]:
    c_load_list = [i.load for i in controller_list]
    avg_load = sum(c_load_list) / len(c_load_list)
    high_load_controllers = []
    low_load_controllers = []
    for controller in controller_list:
        if controller.load > radio*avg_load: # 高载
            high_load_controllers.append(controller)
        if controller.load*radio < avg_load: # 低载
            low_load_controllers.append(controller)
    return high_load_controllers, low_load_controllers

def migrate_by_policy_tuple(net:Net, policy: tuple):
    switch_id, aim_controller_id = policy
    switch = net.get_switch(switch_id=switch_id)
    before_controller = net.get_controller(switch.controller_id)
    aim_controller = net.get_controller(aim_controller_id)
    
    # print(f"migrate: {switch_id} to {aim_controller_id}")
    
    # 迁移交换机到新的控制器
    switch.set_controller(aim_controller_id)
    before_controller.remove_switch(switch)
    aim_controller.add_switch(switch)
    # print(f"current aim controller's switchs {[i for i in aim_controller.switchs]}")

def print_net(net: Net):
    print("controllers", [i.id for i in net.controllers.values()])
    print("con_load", [i.load for i in net.controllers.values()])
    for c in net.controllers.values():
        print("switchs", [i.id for i in c.switchs.values()])

def print_net_c_load(net: Net):
    load = [i.load for i in net.controllers.values()]
    print("con_load", load, "mean", statistics.mean(load), "std", statistics.stdev(load))

def dynamic_net_frame(visiable_matrix_path):
    # TODO: generate net frame from visiable matrix
    visiable_matrix = read_visable_matrix_from_csv(visiable_matrix_path)
    
    controller_id_list = [i for i in range(104, 114)]
    switch_id_list = [i for i in range(104)]
    
    # 初始化的控制器
    controllers = []
    controllers_dict = {}
    for i in controller_id_list:
        controller = Controller(i)
        controllers.append(controller)
        controllers_dict[i] = controller
    
    # 初始化交换机
    switchs = []
    for i in switch_id_list:
        switch = Switch(i, random.randint(200, 450))
        
        distance_list = []
        for j in controllers:
            distance = get_distance(visiable_matrix, j.id, i)
            distance_list.append((j.id, distance))
        sorted_d_l = sorted(distance_list, key=lambda x: x[1])
        aim_controller_id = sorted_d_l[0][0]
        
        aim_controller = controllers_dict[aim_controller_id]
        aim_controller.add_switch(switch)
        
        switchs.append(switch)
        
    # 构建网络
    net = Net(controllers=controllers, switchs=switchs, visiable_matrix=visiable_matrix)
    
    return net

### statistic functions
def controller_load_variance(net: Net):
    """ statistic controller_load_variance
    Returns:
        return controller_load_variance
    """
    controllers_load_list =[ i.load for i in net.controllers.values()]
    return statistics.variance(controllers_load_list)

def measure_net_lantency(net: Net):
    """ statistic lantency
    所有的控制器与交换机的距离/交换机数量
    """
    distance = []
    for controller in net.controllers.values():
        cid = controller.id
        for switch in controller.switchs.values():
            sid = switch.id
            distance.append(net.get_distance(cid=cid, sid=sid))
    return statistics.mean(distance)/(3*10**8)