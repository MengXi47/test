import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

# 臺北思源黑體.ttf
font_path = 'TaipeiSansTCBeta-Regular.ttf'
if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    plt.rc('font', family='Taipei Sans TC Beta')

np.random.seed(0)
n_patients = 30

body_temp  = np.random.normal(37, 0.5, n_patients)   # 體溫
heart_rate = np.random.normal(75, 12, n_patients)    # 心率

plt.figure()
plt.scatter(body_temp, heart_rate)
plt.title('模擬病患生命徵象散佈圖')
plt.xlabel('體溫 (°C)')
plt.ylabel('心率 (次/分鐘)')
plt.tight_layout()
plt.show()
