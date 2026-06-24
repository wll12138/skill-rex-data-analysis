# rex-data-analysis

增程器总成台架 MAP 数据分析 — 油电转换效率、外特性（WOT）、系统效率、发电功率、标准对标。

## 功能

| 功能 | 说明 |
|------|------|
| 油电转换效率分析 | 各转速点系统效率、发电机效率、油电转换率（原始+修正双列），统计峰值/均值/最低 |
| 外特性（WOT）功率分析 | 提取 WOT 曲线，发动机功率-发电功率-效率沿转速变化，功率摘要 |
| 标准增程器对标 | 测试 vs RE50 标准发电功率逐点对比，偏差百分比 + 评级 |
| 效率 MAP 可视化 | DC 功率/系统效率/油电转换率/发电机效率四子图等高线，自动适配层级 |
| 多格式加载 | .xlsx（多 sheet 自动探测）/ .csv（GBK 多行表头，编码自动切换） |
| 标准数据库 | RE50 增程器 SQLite 基准（6 表），`load_rex_standard()` 一键加载 |

## 文件结构

```
├── SKILL.md                         # 触发条件、快速入口、公式、注意事项
├── README.md
├── scripts/
│   └── rex_analysis.py              # 核心分析模块
├── references/
│   ├── rex_signals.md               # 台架列名手册（6 个 sheet 全列名）
│   └── rex_workflows.md             # 场景化工作流 + 常见问题
└── assets/
    └── baseline_rex_database/
        └── baseline_rex_RE50_database.sqlite  # RE50 标准数据库（6 表）
```

## 快速使用

```python
from rex_analysis import *

# 加载数据
df = load_rex_excel("数据.xlsx", sheet_name="台架原始数据")
# df = load_rex_excel("数据.csv", encoding="gbk", header_rows=5)  # CSV 也支持

# 一站式分析
out_dir = make_output_dir("数据.xlsx")
out = rex_full_analysis("数据.xlsx", sheet_name="台架原始数据")
with open(os.path.join(out_dir, "综合报告.md"), "w", encoding="utf-8") as f:
    f.write(out["report"])
```

## 核心函数

| 函数 | 用途 |
|------|------|
| `load_rex_excel` | 加载 .xlsx/.csv，自动识别格式 |
| `load_rex_csv` | CSV 专用：GBK 编码、多行表头、编码自动探测 |
| `load_rex_standard` | 加载内置 RE50 标准数据库 |
| `analyze_fuel_to_electric_efficiency` | 油电转换效率分析 |
| `analyze_external_characteristic` | 外特性（WOT）功率分析 |
| `compare_rex_with_standard` | 标准增程器对标 |
| `rex_full_analysis` | 一站式全分析 |
| `plot_rex_efficiency_map` | 效率 MAP 等高线图 |
| `make_output_dir` | 创建输出文件夹 `YYYYMMDD_HHMMSS_<型号>/` |

## 效率公式

- **油电转换率** — 优先数据列（`油电转换率`/`油电转换率_修正`），缺失时推算：`密度(kg/m³) / (BSFC / 发电机效率)`
- **系统效率** — `DC功率 / (油耗 × LHV / 3.6)`，LHV 默认 42.5 MJ/kg
- **发电机效率** — `DC功率 / (HCU_EngTrq × 转速 / 9549)`

## 维护与发布

本地源文件路径：`~/AppData/Local/hermes/skills/engineering/rex-data-analysis/`

发布至 GitHub：

```bash
cd ~/AppData/Local/hermes/skills/engineering/rex-data-analysis
git add -A && git commit -m "<message>"
git push origin master
```

仓库地址：`git@github.com:wll12138/skill-rex-data-analysis.git`

## 更新日志

### 2026-06-24

- 初始版本：油电转换效率分析、外特性功率分析、标准对标
- 支持 .xlsx / .csv 数据加载
- RE50 标准数据库（SQLite，6 表）
- 效率 MAP 等高线可视化
- 报告自动生成原始/修正油电转换率双列
