import math

# 给定的极坐标值
range_val = 0.706894636
azimuth = 2.8828218
elev = -0.0991872177

# 计算笛卡尔坐标
x = range_val * math.cos(elev) * math.sin(azimuth)
y = range_val * math.cos(elev) * math.cos(azimuth)
z = range_val * math.sin(elev)

print(f"x = {x}")
print(f"y = {y}")
print(f"z = {z}")