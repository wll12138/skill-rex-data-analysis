# 增程器台架列名手册

## 数据格式说明

增程器台架数据使用**中文列名**，与 ETAS INCA 英文信号体系完全不同。

Excel 文件结构：
- 第 0 行：信号名称
- 第 1 行：单位（如 Nm, rpm, kw, kg/h, ℃）
- 第 2+ 行：数据

所有 6 个 sheet 使用相同的列名体系，只有 `油电转化率map` sheet 简化为英文列名。

## 核心分析信号

| 内部键名 | Sheet 中文列名 | 单位 | 说明 |
|---------|-------------|------|------|
| `target_torque` | 发动机设定值 | Nm | 发动机目标扭矩设定 |
| `target_speed` | 发电机设定值 | rpm | 发电机目标转速设定 |
| `actual_torque` | 发动机扭矩max | Nm | 发动机实际扭矩（均值） |
| `actual_speed` | 发电机转速max | rpm | 发电机实际转速（均值） |
| `dc_power` | 直流功率 | kw | 发电机直流输出功率（负值需取绝对值） |
| `dc_voltage` | 直流电压 | V | 直流母线电压 |
| `dc_current` | 直流电流 | A | 直流母线电流 |
| `fuel_consumption` | 燃油消耗量 | kg/h | 燃油质量流量 |
| `fuel_elec_rate` | 油电转换率 | kwh/L | 体积基准油电转换效率 |
| `fuel_elec_rate_fix` | 油电转换率_修正 | kwh/L | 修正后的油电转换效率 |
| `exhaust_temp` | 排气温度 | ℃ | 排气温度 |
| `oil_temp` | 机油温度 | ℃ | 机油温度 |
| `oil_pressure` | 机油压力 | kpa | 机油压力 |
| `backpressure` | 排气背压 | kpa | 排气背压 |
| `ambient_pressure` | 大气压力 | kpa | 环境大气压 |
| `ambient_temp` | 环境温度 | ℃ | 环境温度 |
| `humidity` | 环境湿度 | % | 环境相对湿度 |
| `density` | 密度 | kg/m3 | 燃油密度 |
| `analyzer_power` | 分析仪功率 | kw | 功率分析仪读数 |
| `inlet_water_temp` | 进水温度 | ℃ | 冷却水进水温度 |
| `outlet_water_temp` | 出水温度 | ℃ | 冷却水出水温度 |
| `inlet_water_pressure` | 进水压力 | kpa | 冷却水进水压力 |
| `outlet_water_pressure` | 出水压力 | kpa | 冷却水出水压力 |
| `intake_air_temp` | 空滤前进气温度 | ℃ | 空滤前进气温度 |
| `fuel_pressure` | 燃油压力 | kpa | 燃油供给压力 |

## 发动机/发电机辅助列

| Sheet 中文列名 | 说明 |
|-------------|------|
| 发动机扭矩min | 发动机最小扭矩 |
| 发电机转速min | 发电机最小转速 |
| 测量时间 | 采样时间 (s) |
| 低压电压_engine | 发动机低压供电电压 |
| 低压电流_engine | 发动机低压供电电流 |
| 回液温度_engine | 发动机回液温度 |
| 回液压力_engine | 发动机回液压力 |
| 进液温度_engine | 发动机进液温度 |
| 进液压力_engine | 发动机进液压力 |
| 加热罐温度_engine | 发动机加热罐温度 |
| 系统液位_engine | 发动机系统液位 |
| 储液箱液位_engine | 发动机储液箱液位 |
| 进液温度_motor | 发电机进液温度 |
| 进液流量_motor | 发电机进液流量 |
| 进液压力_motor | 发电机进液压力 |
| 回液温度_motor | 发电机回液温度 |
| 回液压力_motor | 发电机回液压力 |
| 系统液位_motor | 发电机系统液位 |
| 储液箱液位_motor | 发电机储液箱液位 |
| 曲轴箱压力 | 曲轴箱压力 |
| ID号 | 工况点编号 |
| 时间 | 采样时间戳 |
| File Name | 原始数据文件名 (.dxl) |

## 分析仪通道

| Sheet 中文列名 | 说明 |
|-------------|------|
| 分析仪直流电压 | 分析仪测量的直流电压 |
| 分析仪直流电流 | 分析仪测量的直流电流 |
| 分析仪功率 | 分析仪计算的功率 |
| 功率分析DCA | 功率分析仪 DCA 通道 |

## GCU（发电机控制器）信号

| Sheet 英文列名 | 说明 |
|-------------|------|
| GCU_Fail_Grade | GCU 故障等级 |
| GCU_IGBT_Enable_Fb | IGBT 使能反馈 |
| GCU_MotorSpeed_Vd | 电机速度有效位 |
| GCU_MotorTorque_Vd | 电机扭矩有效位 |
| GCU_Motor_Speed | GCU 读取电机转速 |
| GCU_Motor_Torque | GCU 读取电机扭矩 |
| GCU_OperModFdbk | GCU 工作模式反馈 |
| GCU_DC_Current | GCU 直流电流 |
| GCU_DC_Voltage | GCU 直流电压 |
| GCU_DTC_Code | GCU 故障码 |
| GCU_INVActTemp | 逆变器实际温度 |
| GCU_MotorActTemp | 电机实际温度 |
| GCU_TrqLimitMax | 扭矩上限 |
| GCU_TrqLimitMin | 扭矩下限 |

## HCU（混合动力控制器）信号

| Sheet 英文列名 | 说明 |
|-------------|------|
| HCU_EngCoolantTpt | 发动机冷却液温度 |
| HCU_EngSpd | HCU 读取发动机转速 |
| HCU_EngTrq | HCU 读取发动机扭矩 |
| HCU_FualtLevel | HCU 故障等级 |
| HCU_ModeFeedback | HCU 模式反馈 |
| HCU_GCU_Enable | HCU 使能 GCU |
| HCU_GcuModeReq | HCU 请求 GCU 模式 |
| HCU_GcuSpdReq | HCU 请求 GCU 转速 |
| HCU_GcuTorqueReq | HCU 请求 GCU 扭矩 |
| HCU_EngFaultLevel | HCU 发动机故障等级 |
| HCU_FuelConSump | HCU 燃油消耗 |
| HCU_OilPressureWarn | HCU 机油压力报警 |
| HCU_ThrottlePos | HCU 节气门位置 |

## 油电转化率map sheet 列名

此 sheet 使用英文列名，结构简化：

| 列名 | 说明 |
|------|------|
| speed | 转速 (rpm) |
| torque | 扭矩 (Nm) |
| powerrequest | 请求功率 (kW) |
| fuel rate（g/kwh） | 燃油消耗率 (g/kWh 电) |
| fuei-elec rate（kwh/l） | 油电转化率 (kwh/L) |
| fuei-elec rate fix（kwh/l） | 修正油电转化率 (kwh/L) |

## 燃油压力4bar扫点 sheet 列名

| 列名 | 说明 |
|------|------|
| 序号 | 数据序号 |
| 请求转速 | 目标转速 (rpm) |
| 请求扭矩 | 目标扭矩 (Nm) |
| 请求功率powerrequest | 目标功率 (kW) |
| GCU反馈转速 | GCU 反馈转速 (rpm) |
| GCU反馈扭矩 | GCU 反馈扭矩 (Nm) |
| 扭矩误差 | 扭矩误差 (Nm) |
| 发动机反馈扭矩 | 发动机反馈扭矩 (Nm) |
| 请求发动机扭矩与发动机反馈扭矩误差 | 扭矩误差 (Nm) |
| 油耗量(KG/H) | 燃油消耗量 (kg/h) |
| GCU机械功率 | GCU 机械功率 (kW) |
| 发电功率（KW） | 发电功率 (kW) |

## 功率转速选点 sheet 列名

| 列名 | 说明 |
|------|------|
| power | 目标发电功率 (kW) |
| speed | 目标转速 (rpm) |
| torque | 对应扭矩 (Nm) |

这是 RE50 的 WOT 外特性定义线（31 个工况点，覆盖 3-60kW 发电功率）。

## 直流功率符号说明

台架原始数据中 `直流功率` 为**负值**（功率分析仪方向定义：消耗为正，发电为负）。分析时统一取绝对值。
