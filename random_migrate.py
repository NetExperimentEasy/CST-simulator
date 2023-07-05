from core import *
import sys
import time

# 随机迁移策略
def random_migrate(net: Net):
    """random_migrate algorithm
    
    Inputs:
        net: Net
    Returns:
        net: Net
        state: {"balance"}
    """
    high_controller_nb_list, low_controller_nb_list = controllers_need_blanced(list(net.controllers.values()))

    if len(high_controller_nb_list) < 1:
        print("没有需要迁移的交换机了")
        sys.exit(-1)
    
    # print([i.id for i in controller_nb_list])
    random_choosed_high_controller = random.sample(high_controller_nb_list, 1)[0]
    random_choosed_high_switch = random.sample(list(random_choosed_high_controller.switchs.values()), 1)[0]
    
    random_aim_low_controller = random.sample(low_controller_nb_list, 1)[0]
    
    policy = (random_choosed_high_switch.id, random_aim_low_controller.id)
    
    migrate_by_policy_tuple(net, policy)

# 02.csv为从STK导出的可见性矩阵
net  = dynamic_net_frame("02.csv") 
print_net(net)

for i in range(1000):    
    start = time.time()
    random_migrate(net=net)
    end = time.time()
    print(f"delta time:{end - start}")
    print_net_c_load(net)
    