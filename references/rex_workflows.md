# 增程器数据分析工作流

按用户目标选择入口，先确认数据结构和关键列，再进入具体分析。

## 前置步骤：创建输出文件夹 + 环境配置

### 输出文件夹

每次分析第一步——创建时间戳文件夹。型号从文件名自动提取。

```python
out_dir = make_output_dir("增程器数据.xlsx")
# → 如 20260623_135034_RE50/
```

后续所有报告和图表均写入 `out_dir`。

### matplotlib 无头环境

在 sandbox、无 GUI 环境或服务器中：

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

## 场景 1：油电转换效率分析

适用于需要全面了解增程器效率特性的场景。

```python
df = load_rex_excel("增程器数据.xlsx", sheet_name="台架原始数据")
print_data_structure(df)

out = analyze_fuel_to_electric_efficiency(df)
print(out["report"])

# 保存报告
with open(os.path.join(out_dir, "效率分析报告.md"), "w", encoding="utf-8") as f:
    f.write(out["report"])
```

输出内容：
- 各转速点峰值 DC 功率、最低油耗、峰值/平均系统效率
- 发电机效率（如有 HCU_EngTrq 列）
- 油电转换率（kwh/L）

## 场景 2：外特性分析

提取 WOT 曲线，分析沿外特性的功率和效率变化。

```python
df = load_rex_excel("增程器数据.xlsx", sheet_name="台架原始数据")

out = analyze_external_characteristic(df)
print(out["report"])

# 或手动提取 WOT 曲线
wot = extract_wot_curve(df, method="max_torque")
```

输出内容：
- 各转速点发动机扭矩/功率、DC 发电功率
- 发电机效率、系统效率
- 油电转换率

## 场景 3：增程器标准对标

对比测试增程器与 RE50 标准的外特性发电功率。

```python
df = load_rex_excel("测试增程器.xlsx", sheet_name="台架原始数据")

out = compare_rex_with_standard(df)
print(out["report"])
```

输出内容：
- 各转速点测试 vs 标准发电功率及偏差
- 效率对比
- 综合评级（优/良/中/差）

### 使用自定义标准数据

```python
std = load_rex_excel("自定义标准.xlsx", sheet_name="台架原始数据")
out = compare_rex_with_standard(df, standard_df=std, name="方案A")
```

## 场景 4：一站式全分析

```python
out = rex_full_analysis(
    filepath="增程器数据.xlsx",
    sheet_name="台架原始数据",
    fuel_lhv=42.5,  # 汽油低热值，可覆盖
)
print(out["report"])

# 保存综合报告
with open(os.path.join(out_dir, "综合报告.md"), "w", encoding="utf-8") as f:
    f.write(out["report"])
```

## 场景 5：A/B 增程器对比

两个增程器的效率和外特性横向对比。

```python
df_a = load_rex_excel("方案A.xlsx", sheet_name="台架原始数据")
df_b = load_rex_excel("方案B.xlsx", sheet_name="台架原始数据")

eff_a = analyze_fuel_to_electric_efficiency(df_a)
eff_b = analyze_fuel_to_electric_efficiency(df_b)

wot_a = analyze_external_characteristic(df_a)
wot_b = analyze_external_characteristic(df_b)

# 保存两份报告
with open(os.path.join(out_dir, "方案A_效率报告.md"), "w", encoding="utf-8") as f:
    f.write(eff_a["report"])
with open(os.path.join(out_dir, "方案B_效率报告.md"), "w", encoding="utf-8") as f:
    f.write(eff_b["report"])
```

## 场景 6：指定燃油压力条件分析

读取 `燃油压力4bar扫点` sheet 进行特定油压下的效率分析。

```python
df_4bar = load_rex_excel("增程器数据.xlsx", sheet_name="燃油压力4bar扫点")

# 列名不同，需手动构建
# 参见 references/rex_signals.md → 燃油压力4bar扫点
```

## 常见问题

### 直流功率为负值

台架的功率分析仪方向定义：消耗为正，发电为负。`load_rex_excel()` 和所有分析函数已自动取绝对值。

### 发电机效率 > 100%

在极低负荷工况（< 5kW DC 功率），测量精度导致的正常偏差。通常出现在 1000-1200rpm 最低扭矩点。WOT 工况不应出现此情况。

### 发动机扭矩max 不是实际扭矩

`发动机扭矩max` 是"该工况下发动机可输出的最大扭矩"，非实际运行扭矩。实际发动机扭矩应使用 `HCU_EngTrq` 列。分析函数已自动优先使用 `HCU_EngTrq`。

### 标准数据加载失败

标准数据路径：`assets/baseline_rex_database/baseline_rex_RE50_database.sqlite`。如文件不存在，`compare_rex_with_standard()` 会返回错误信息。

### 自定义燃油低热值

```python
out = analyze_fuel_to_electric_efficiency(df, fuel_lhv=44.0)  # 天然气
# 或
out = rex_full_analysis("数据.xlsx", fuel_lhv=44.0)
```

## 输出要求

报告由内置函数生成，直接从返回 dict 的 `"report"` 键取字符串保存，禁止自行重写。评级使用四档：优 / 良 / 中 / 差。

每次分析将所有输出写入同一个时间戳文件夹，答复时给出路径和文件清单。
