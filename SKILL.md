---
name: rex-data-analysis
description: Analyze range extender (增程器) test data — fuel-to-electric conversion efficiency, system efficiency, external characteristic (WOT), fuel consumption, DC power output, standard REX benchmarking, and MAP sweep analysis. Use when the user asks about 增程器, range extender, 油电转换效率, 发电功率, 直流功率, or REX test data.
---

# 增程器数据分析

分析增程器总成台架 MAP 测试数据：油电转换效率、外特性（WOT）、系统效率、发电功率、油耗、标准对标和可视化。

## 触发条件

当用户提及以下任何内容时，应加载本 skill：

- 增程器 / range extender / REX / 增程
- 油电转换效率 / 油电转化率 / 系统效率
- 发电功率 / 直流功率 / DC 功率
- 增程器 MAP / 扫点数据 / 外特性
- `.xlsx` / `.csv` 增程器台架数据（中文列名：发动机设定值、发电机设定值、直流功率、燃油消耗量）

## 数据特征（与发动机分析的关键区别）

增程器台架数据使用**中文列名**，与 ETAS INCA 信号体系完全不同：

- 无燃烧数据（COV / AI50 / 点火角 / 爆震 / VVT）
- 无增压器数据（涡轮转速 / 增压压力 / WG）
- 核心指标是**油电转换效率**（kwh/L）和**发电功率**（kW），非 BSFC (g/kWh)
- 数据为 MAP 扫点（转速 × 扭矩矩阵），非外特性曲线

## 资源导航

- 核心分析模块：`scripts/rex_analysis.py`
- 台架列名手册：`references/rex_signals.md`
- 场景化工作流与示例：`references/rex_workflows.md`
- RE50 标准增程器数据：`assets/baseline_rex_database/baseline_rex_RE50_database.sqlite`

## 快速入口

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / "AppData/Local/hermes/skills/engineering/rex-data-analysis/scripts"))
from rex_analysis import *
```

### 加载数据

```python
# Excel
df = load_rex_excel("增程器数据.xlsx", sheet_name="台架原始数据")
# CSV（GBK 编码，多行表头）
df = load_rex_excel("增程器数据.csv", encoding="gbk", header_rows=5)
print_data_structure(df)
```

### 油电转换效率分析

```python
out = analyze_fuel_to_electric_efficiency(df)
print(out["report"])
```

### 外特性分析

```python
out = analyze_external_characteristic(df, wot_sheet="功率转速选点")
print(out["report"])
```

### 增程器标准对标

```python
std = load_rex_standard()  # 加载内置 RE50 标准
result = compare_rex_with_standard(df, standard_df=std)
print(result["report"])
```

### 一站式全分析

```python
out = rex_full_analysis(
    filepath="增程器数据.xlsx",
    sheet_name="台架原始数据",
    save_plot=os.path.join(out_dir, "rex_analysis.png"),
)
print(out["report"])
```

## 分析工作流

0. 创建输出文件夹：`make_output_dir(filepath)` → `YYYYMMDD_HHMMSS_<型号>/`。
1. 调用 `load_rex_excel()` 加载数据（自动识别 .xlsx / .csv），处理表头行和单位行。
2. 使用 `print_data_structure()` 确认关键列存在。
3. 核心分析：`analyze_fuel_to_electric_efficiency()` → 油电转换效率 + 系统效率。
4. 外特性分析：按各转速最大扭矩点提取 WOT 曲线，或读 `功率转速选点` sheet。
5. 标准对标：加载内置 RE50 标准数据 → `compare_rex_with_standard()`。
6. 图表：保存到输出文件夹，答复时给出路径。

## 关键列名

详见 `references/rex_signals.md`。常用列：`发动机设定值`(Nm)、`发电机设定值`(rpm)、`直流功率`(kw)、`燃油消耗量`(kg/h)、`油电转换率`/`油电转换率_修正`(kwh/L)、`HCU_EngTrq`(发动机实际扭矩)、`密度`(kg/m³)、`排气温度`(℃)。

## 效率公式

> 标注"数据"=直接引用台架导出列；"计算"=代码推算。

```
油电转换率 (kwh/L) — 优先数据，缺失时计算
  数据: 列 "油电转换率"（原始）/ "油电转换率_修正"（台架修正，算法未知）
  计算: = 密度(kg/m³) / 等效油耗(g/kWh)
         等效油耗 = BSFC(g/kWh) / 发电机效率(%)
         BSFC = 燃油消耗量(kg/h) × 1000 / 发动机功率(kW)
         来源: 1000/733 换算式（733=汽油标准密度 kg/m³），化简为密度/等效油耗

系统效率 (%) — 计算（标准热力学公式，LHV 可配置）
  = 直流功率(kW) / (燃油消耗量(kg/h) × LHV(MJ/kg) / 3.6) × 100
  LHV 默认 42.5 MJ/kg（汽油参考值），通过 fuel_lhv 参数覆盖

发电机效率 (%) — 计算（标准定义）
  = 直流功率(kW) / 发动机机械功率(kW) × 100
  发动机功率 = HCU_EngTrq(Nm) × 转速(rpm) / 9549
  注: 发动机扭矩max 是容量上限，不可用于功率计算
```

## 关键注意事项

- **发动机扭矩max 是容量上限**，非实际运行扭矩。发动机功率计算优先使用 HCU_EngTrq 列。
- 直流功率为负值（台架方向定义），`load_rex_excel()` 和分析函数已自动取绝对值。
- 低负荷工况（<5kW）发电机效率可能 >100%，属测量精度导致的正常偏差。WOT 工况不应出现。
- 标准对标对比的是发电功率（kW）和效率，非发动机扭矩。

## 标准数据

RE50 增程器标准数据位于 `assets/baseline_rex_database/baseline_rex_RE50_database.sqlite`，6 个表：

| 表名 | 用途 |
|------|------|
| 台架原始数据 | 全 MAP 扫点基准（254 工况点 × 314 通道） |
| 燃油压力4bar扫点 | 4bar 油压条件扫点基准 |
| 油电转化率map | 效率 map 快速查询 |
| 功率转速选点 | WOT 外特性定义线（31 点） |
| 功率转速选点复测_台架数据 | WOT 复测全通道基准 |
| 功率转速选点_台架_ECU | WOT ECU 数据基准 |

## 输出文件夹管理

每次分析在数据文件所在目录下创建 `YYYYMMDD_HHMMSS_<型号>` 文件夹（型号从文件名自动提取），所有输出写入该文件夹。

```python
out_dir = make_output_dir("增程器数据.xlsx")  # → 20260623_135034_RE50/
```

## matplotlib 中文设置

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

## 输出要求

报告由内置函数生成，直接从返回 dict 的 `"report"` 键取字符串保存为 `.md`，禁止自行重写。

评级（对标报告）：≤5%优 / ≤10%良 / ≤15%中 / >15%差，括号内附实际偏差值。

答复时给出文件夹路径和文件清单。

## 编写规范

- 公式必须标注来源：标准热力学 / 数据列 / 推算（注明推算依据）
- 报告中所有数值列先原始后修正（油电转换率、功率等）
- 不编造阈值、切割线、评级标准；新增指标前确认工程意义
- 示例数据必须标注"举例"，不得与真实输出混排
- 文档简洁，分条优于表格，不过度解释名词术语
