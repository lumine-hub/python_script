import math

# 给定的笛卡尔坐标值
x = -0.68
y = 0.18
z = -0.07
# -68,18,-7,12,2000
# 计算范围
range_val = math.sqrt(x**2 + y**2 + z**2)

# 计算方位角
azimuth = math.atan2(x, y)

# 计算仰角
elev = math.atan(z / math.sqrt(x**2 + y**2))

print(f"range = {range_val}")
print(f"azimuth = {azimuth}")
print(f"elev = {elev}")