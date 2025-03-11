import numpy as np

# 配置参数 前提adc为复数
tx = 1
rx = 3
Max_endFreq = 81e9  # GHz 允许的最大的endFreq
startFreq = 77e9  # GHz
idleTime = 100.00e-6  # us
adcStartTime = 6.00e-6  # us
rampEndTime = 62e-6  # us
freqSlopeConst = 60.012e12  # MHz/usec
numAdcSamples = 128
digOutSampleRate = 2500e3  # ksps
loopNum = 128

framePeriodicity = 70e-3  # ms

# 检查配置参数是否合理
allRight = 1
fs = digOutSampleRate  # 采样率
one_chirp_duration = idleTime + rampEndTime
one_loop_duration = one_chirp_duration * tx
all_loop_duration = one_loop_duration * loopNum

if all_loop_duration >= framePeriodicity:
    print('all_loop_duration>=framePeriodicity,no frame idle time')
    allRight = 0

adc_sample_time = numAdcSamples / fs
if adc_sample_time + adcStartTime >= rampEndTime:
    print('adc_sample_time+adcStartTime>=rampEndTime')
    allRight = 0

frameRate = 1 / framePeriodicity
Max_bandwidth_ramp = Max_endFreq - startFreq
bandwidth_ramp = freqSlopeConst * rampEndTime  # 指整个ramp的带宽
if bandwidth_ramp >= Max_bandwidth_ramp:
    print('bandwidth_ramp>=Max_bandwidth_ramp')
    allRight = 0

# 参数计算
rangeZeropad = numAdcSamples
dopplerZeropad = loopNum
BW = freqSlopeConst * adc_sample_time
c = 3e8
lambda_val = c / startFreq

# range
Rmax = fs * c / (2 * freqSlopeConst)
Rres = c / 2 / BW
range_arr = np.linspace(0, 1 - 1 / rangeZeropad, rangeZeropad) * Rmax

# velocity
Vmax = lambda_val / (4 * one_loop_duration)
Vres = lambda_val / (2 * all_loop_duration)
velocity = np.linspace(-Vmax, Vmax - 2 * Vmax / dopplerZeropad, dopplerZeropad)

print("Rmax:", Rmax)
print("Rres:", Rres)
# print("range_arr:", range_arr)
print("Vmax:", Vmax)
print("Vres:", Vres)
# print("velocity:", velocity)