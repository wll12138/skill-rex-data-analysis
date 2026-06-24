"""
rex_analysis.py — 增程器总成台架数据分析工具集

分析油电转换效率、外特性（WOT）、系统效率、发电功率、
标准增程器对标、MAP 扫点数据可视化。

用法示例：
    from rex_analysis import *
    df = load_rex_excel("增程器数据.xlsx")
    out = rex_full_analysis("增程器数据.xlsx")
    print(out["report"])
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Dict, Tuple, List, Union
from datetime import datetime
import os
import re

# ────────────────────────────────────────────────────────────
# 常量
# ────────────────────────────────────────────────────────────

# 汽油低热值 (MJ/kg)
FUEL_LHV_DEFAULT = 42.5

# 标准数据文件路径
_STANDARD_DATA_PATH = Path(__file__).resolve().parent.parent / "assets" / "baseline_rex_database" / "baseline_rex_RE50_database.sqlite"



def make_output_dir(filepath: str) -> str:
    """创建输出文件夹 <数据目录>/YYYYMMDD_HHMMSS_<型号>/，型号从文件名正则提取。"""
    fname = Path(filepath).stem
    m = re.search(r'RE\d+|DHE\d+|H\d+[A-Z]?|[A-Z]{2,4}\d+[A-Z]?', fname, re.I)
    model = (m.group(0).upper() if m else "REX")
    dirname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{model}"
    out_dir = os.path.join(os.path.dirname(filepath) or ".", dirname)
    os.makedirs(out_dir, exist_ok=True)
    print(f"输出文件夹: {out_dir}")
    return out_dir

# 列名映射：内部键名 → 台架中文列名
COLUMN_MAP = {
    "target_torque":    "发动机设定值",
    "target_speed":     "发电机设定值",
    "actual_torque":    "发动机扭矩max",
    "actual_speed":     "发电机转速max",
    "hcu_engine_torque": "HCU_EngTrq",     # HCU 读取的实际发动机扭矩（精度高于发动机扭矩max）
    "hcu_engine_speed":  "HCU_EngSpd",     # HCU 读取的实际发动机转速
    "dc_power":         "直流功率",
    "dc_voltage":       "直流电压",
    "dc_current":       "直流电流",
    "fuel_consumption": "燃油消耗量",
    "fuel_elec_rate":    "油电转换率",
    "fuel_elec_rate_fix":"油电转换率_修正",
    "exhaust_temp":     "排气温度",
    "oil_temp":         "机油温度",
    "oil_pressure":     "机油压力",
    "backpressure":     "排气背压",
    "ambient_pressure": "大气压力",
    "ambient_temp":     "环境温度",
    "humidity":         "环境湿度",
    "density":          "密度",
    "analyzer_power":   "分析仪功率",
    "inlet_water_temp": "进水温度",
    "outlet_water_temp":"出水温度",
    "inlet_water_pressure": "进水压力",
    "outlet_water_pressure":"出水压力",
    "intake_air_temp":  "空滤前进气温度",
    "fuel_pressure":    "燃油压力",
}

# 油电转化率map sheet 列名映射
MAP_COLUMN_MAP = {
    "speed":           "speed",
    "torque":          "torque",
    "powerrequest":    "powerrequest",
    "fuel_rate":       "fuel rate（g/kwh）",
    "elec_rate":       "fuei-elec rate（kwh/l）",
    "elec_rate_fix":   "fuei-elec rate fix（kwh/l）",
}

# ────────────────────────────────────────────────────────────
# 1. 数据加载
# ────────────────────────────────────────────────────────────

def load_rex_excel(
    filepath: str,
    sheet_name: Optional[str] = None,
    encoding: str = "gbk",
    header_rows: int = 5,
    skip_time_cols: int = 3,
) -> pd.DataFrame:
    """读取增程器台架数据，自动识别 .xlsx / .csv。

    Excel: 第 0 行 = 信号名，第 1 行 = 单位，第 2+ = 数据。
    CSV:   多行表头，GBK 编码，前 N 列为时间/序号。

    Args:
        filepath: 文件路径 (.xlsx 或 .csv)
        sheet_name: Excel sheet 名称（.csv 忽略）
        encoding: CSV 编码，默认 gbk（Excel 忽略）
        header_rows: CSV 表头行数（Excel 忽略）
        skip_time_cols: CSV 跳过的前导列数（Excel 忽略）

    Returns:
        DataFrame，列名为中文信号名

    用法:
        df = load_rex_excel("数据.xlsx", sheet_name="台架原始数据")
        df = load_rex_excel("数据.csv", encoding="gbk", header_rows=5)
    """
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    if p.suffix.lower() == ".csv":
        print("检测到 CSV 文件，使用 load_rex_csv()")
        return load_rex_csv(filepath, encoding=encoding,
                            header_rows=header_rows, skip_time_cols=skip_time_cols)

    return _load_rex_xlsx(str(p), sheet_name)


def _load_rex_xlsx(filepath: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """内部：加载 .xlsx 文件。"""
    p = Path(filepath)
    xl = pd.ExcelFile(p)
    print(f"可用 sheet: {xl.sheet_names}")

    if sheet_name is None:
        sheet_name = xl.sheet_names[0]
        print(f"使用默认 sheet: {sheet_name}")
    elif sheet_name not in xl.sheet_names:
        raise ValueError(f"Sheet '{sheet_name}' 不存在。可用: {xl.sheet_names}")

    df = pd.read_excel(p, sheet_name=sheet_name, header=0)
    print(f"原始行数: {len(df)}")

    first_col = df.columns[0]
    first_val = str(df.iloc[0][first_col]) if len(df) > 0 else ""
    if first_val in ["Nm", "rpm", "kw", "V", "A", "℃", "kpa"]:
        df = df.iloc[1:].reset_index(drop=True)
        print("已跳过单位行")

    df = _ensure_numeric_rex(df)
    print(f"有效数据行数: {len(df)}")
    return df


def load_rex_csv(
    filepath: str,
    encoding: str = "gbk",
    header_rows: int = 5,
    skip_time_cols: int = 3,
) -> pd.DataFrame:
    """读取增程器台架 CSV 数据（多行表头，GBK 编码）。

    自动尝试多种编码：gbk → utf-8 → latin-1。
    多行表头合并为单层列名，跳过前 N 列时间/序号。

    Args:
        filepath: CSV 文件路径
        encoding: 首选编码
        header_rows: 表头行数
        skip_time_cols: 跳过的前导列数

    Returns:
        DataFrame

    用法:
        df = load_rex_csv("数据.csv", encoding="gbk", header_rows=5, skip_time_cols=3)
    """
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    # 编码探测
    encodings = [encoding, "utf-8", "latin-1"]
    raw_lines = None
    for enc in encodings:
        try:
            with open(p, "r", encoding=enc) as f:
                raw_lines = f.readlines()
            if enc != encoding:
                print(f"编码自动切换: {encoding} → {enc}")
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if raw_lines is None:
        raise ValueError(f"无法解码文件: {filepath}（已尝试 {encodings}）")

    # 解析表头：取前 header_rows 行，合并为列名
    header_lines = [line.rstrip("\n").split(",") for line in raw_lines[:header_rows]]
    max_cols = max(len(h) for h in header_lines)
    for h in header_lines:
        h.extend([""] * (max_cols - len(h)))

    # 合并多行表头
    col_names = []
    for j in range(max_cols):
        parts = [header_lines[i][j].strip('"').strip() for i in range(header_rows)]
        name = "_".join(p for p in parts if p)
        col_names.append(name)

    # 读数据
    data_lines = raw_lines[header_rows:]
    data = []
    for line in data_lines:
        vals = line.rstrip("\n").split(",")
        vals.extend([""] * (max_cols - len(vals)))
        data.append(vals)

    df = pd.DataFrame(data, columns=col_names)

    # 跳过前导列
    if skip_time_cols > 0 and skip_time_cols < len(df.columns):
        df = df.iloc[:, skip_time_cols:].reset_index(drop=True)

    # 清掉全空行
    df = df.dropna(how="all").reset_index(drop=True)
    print(f"原始行数: {len(df)}")

    # 跳过单位行
    if len(df) > 0:
        first_val = str(df.iloc[0, 0])
        if first_val in ["Nm", "rpm", "kw", "V", "A", "℃", "kpa"]:
            df = df.iloc[1:].reset_index(drop=True)
            print("已跳过单位行")

    df = _ensure_numeric_rex(df)
    print(f"有效数据行数: {len(df)}")
    return df


def load_rex_standard(sheet_name: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """加载内置 RE50 增程器标准数据（SQLite，6 个表）。

    Args:
        sheet_name: 指定表名，None 则加载所有

    Returns:
        dict: {table_name: DataFrame} 或单个 DataFrame

    用法:
        all_std = load_rex_standard()
        df = load_rex_standard("台架原始数据")
    """
    import sqlite3
    if not _STANDARD_DATA_PATH.exists():
        raise FileNotFoundError(f"标准数据文件不存在: {_STANDARD_DATA_PATH}")

    conn = sqlite3.connect(f"file:{_STANDARD_DATA_PATH}?mode=ro", uri=True)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()

    if sheet_name is not None:
        table = sheet_name.replace(" ", "_")
        if table not in tables:
            raise ValueError(f"表 '{table}' 不存在。可用: {tables}")
        df = pd.read_sql(f"SELECT * FROM [{table}]", conn)
        conn.close()
        return _ensure_numeric_rex(df)

    result = {}
    for t in tables:
        df = pd.read_sql(f"SELECT * FROM [{t}]", conn)
        result[t] = _ensure_numeric_rex(df)
    conn.close()
    return result


def _ensure_numeric_rex(df: pd.DataFrame) -> pd.DataFrame:
    """将 DataFrame 中的可转换列转为数值类型。"""
    skip_cols = {"ID号", "时间", "File Name"}
    for col in df.columns:
        if col in skip_cols:
            continue
        try:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except (ValueError, TypeError):
            pass
    return df


def _compute_fuel_elec_rate(
    df: pd.DataFrame,
    dc_power: pd.Series,
    fuel_cons: pd.Series,
    engine_power: pd.Series,
) -> pd.Series:
    """推算油电转换率 (kwh/L)。

    公式: 密度(kg/m³) / (BSFC(g/kWh) / 发电机效率(%))
    BSFC = 油耗(g/h) / 发动机功率(kW)
    来源: 1000×733 换算式化简。
    数据来源: 密度列（台架实测）、油耗（台架实测）、发动机功率（HCU_EngTrq推算）。

    Returns:
        Series，单位 kwh/L
    """
    density_col = COLUMN_MAP.get("density")
    if density_col and density_col in df.columns:
        density = pd.to_numeric(df[density_col], errors="coerce")  # kg/m³
    else:
        density = 733  # 汽油标准密度 kg/m³，未实测时用参考值

    bsfc = fuel_cons * 1000 / engine_power.replace(0, np.nan)  # g/kWh
    gen_eff = dc_power / engine_power.replace(0, np.nan) * 100  # %
    bsfc_elec = bsfc / (gen_eff / 100)  # 等效油耗 g/kWh

    return density / bsfc_elec  # kwh/L


# ────────────────────────────────────────────────────────────
# 2. 数据检查
# ────────────────────────────────────────────────────────────

def print_data_structure(df: pd.DataFrame) -> None:
    """打印增程器数据概览：形状、关键列、数据范围。"""
    print(f"\n{'='*60}")
    print(f" 增程器数据概览")
    print(f"{'='*60}")
    print(f"总行数: {len(df)}, 总列数: {len(df.columns)}")

    # 检测关键列
    print(f"\n关键列检测:")
    for key, col_name in COLUMN_MAP.items():
        status = "✓" if col_name in df.columns else "✗"
        print(f"  [{status}] {key:20s} → {col_name}")

    # 数据范围
    print(f"\n数据范围:")
    for key in ["target_speed", "target_torque", "dc_power", "fuel_consumption",
                "fuel_elec_rate_fix", "exhaust_temp"]:
        col = COLUMN_MAP.get(key)
        if col and col in df.columns:
            vals = df[col].dropna()
            if key == "dc_power":
                vals = vals.abs()  # 直流功率取绝对值
            if len(vals) > 0:
                print(f"  {col:20s}: {vals.min():.1f} ~ {vals.max():.1f}")

    # 转速点
    speed_col = COLUMN_MAP["target_speed"]
    if speed_col in df.columns:
        speeds = sorted(df[speed_col].dropna().unique())
        print(f"\n转速点 ({len(speeds)}): {[int(s) for s in speeds]}")


def detect_rex_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """检测增程器关键列是否存在，返回 {内部键名: 实际列名或None}。"""
    result = {}
    for key, col_name in COLUMN_MAP.items():
        result[key] = col_name if col_name in df.columns else None
    return result


# ────────────────────────────────────────────────────────────
# 3. 核心分析
# ────────────────────────────────────────────────────────────

def analyze_fuel_to_electric_efficiency(
    df: pd.DataFrame,
    fuel_lhv: float = FUEL_LHV_DEFAULT,
) -> Dict:
    """油电转换效率全面分析。

    计算各转速点的系统效率、发电机效率、油电转换率。

    Args:
        df: 增程器 DataFrame（含直流功率、燃油消耗量、油电转换率_修正 等列）
        fuel_lhv: 燃油低热值 (MJ/kg)，默认 42.5

    Returns:
        dict: efficiency_table, stats, report

    用法:
        out = analyze_fuel_to_electric_efficiency(df)
        print(out["report"])
    """
    # 列检测
    dc_col = COLUMN_MAP["dc_power"]
    fc_col = COLUMN_MAP["fuel_consumption"]
    rate_col = COLUMN_MAP["fuel_elec_rate_fix"]
    rate_raw_col = COLUMN_MAP["fuel_elec_rate"]
    speed_col = COLUMN_MAP["target_speed"]
    torque_col = COLUMN_MAP["target_torque"]
    actual_tq_col = COLUMN_MAP["actual_torque"]

    required = [dc_col, fc_col, speed_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"report": f"[错误: 缺少必需列: {missing}]"}

    # 预处理：直流功率取绝对值
    dc_power = df[dc_col].abs()
    fuel_cons = df[fc_col]
    speed = df[speed_col]

    # 计算系统效率
    # η_system = P_dc(kW) / (fuel_mass(kg/h) * LHV(MJ/kg) / 3.6)
    system_efficiency = dc_power / (fuel_cons * fuel_lhv / 3.6) * 100

    # 计算发电机效率（如有发动机扭矩和转速）
    # 优先使用 HCU_EngTrq（实际发动机扭矩）；发动机扭矩max 是容量上限，非实际扭矩
    if "hcu_engine_torque" in COLUMN_MAP and COLUMN_MAP["hcu_engine_torque"] in df.columns:
        actual_tq_for_power = df[COLUMN_MAP["hcu_engine_torque"]].abs()
    elif actual_tq_col in df.columns:
        actual_tq_for_power = df[actual_tq_col].abs()
    else:
        actual_tq_for_power = None

    if actual_tq_for_power is not None:
        engine_power = actual_tq_for_power * speed / 9549  # kW
        gen_efficiency = dc_power / engine_power.replace(0, np.nan) * 100
    else:
        gen_efficiency = None

    # 按转速汇总
    speed_points = sorted(speed.dropna().unique())
    efficiency_table = []

    for sp in speed_points:
        mask = speed == sp
        dc_vals = dc_power[mask]
        sys_eff_vals = system_efficiency[mask]
        fuel_vals = fuel_cons[mask]

        # 油电转换率：优先数据列，缺失时推算
        if rate_col and rate_col in df.columns:
            rate_vals = df.loc[mask, rate_col]
            rate_raw_vals = df.loc[mask, rate_raw_col] if rate_raw_col in df.columns else rate_vals
        elif actual_tq_for_power is not None:
            computed = _compute_fuel_elec_rate(
                df.loc[mask], dc_vals, fuel_vals,
                actual_tq_for_power[mask] * speed[mask] / 9549)
            rate_vals = computed
            rate_raw_vals = computed
        else:
            rate_vals = pd.Series([np.nan] * mask.sum())
            rate_raw_vals = pd.Series([np.nan] * mask.sum())

        row = {
            "speed": int(sp),
            "max_dc_power": round(dc_vals.max(), 1),
            "min_fuel_cons": round(fuel_vals.min(), 2),
            "max_sys_eff": round(sys_eff_vals.max(), 1),
            "avg_sys_eff": round(sys_eff_vals.mean(), 1),
            "max_fuel_elec_rate": round(rate_vals.max(), 2) if rate_vals.notna().any() else None,
            "max_fuel_elec_rate_raw": round(rate_raw_vals.max(), 2) if rate_raw_vals.notna().any() else None,
        }
        if gen_efficiency is not None:
            row["max_gen_eff"] = round(gen_efficiency[mask].max(), 1)
            row["avg_gen_eff"] = round(gen_efficiency[mask].mean(), 1)

        efficiency_table.append(row)

    # 统计
    all_sys_eff = system_efficiency.dropna()
    stats = {
        "overall_max_sys_eff": round(all_sys_eff.max(), 1),
        "overall_avg_sys_eff": round(all_sys_eff.mean(), 1),
        "overall_min_sys_eff": round(all_sys_eff.min(), 1),
        "total_points": len(all_sys_eff),
        "fuel_lhv": fuel_lhv,
    }

    if rate_col and rate_col in df.columns:
        rate_vals = df[rate_col].dropna()
        stats["max_fuel_elec_rate"] = round(rate_vals.max(), 2) if len(rate_vals) > 0 else None
        stats["avg_fuel_elec_rate"] = round(rate_vals.mean(), 2) if len(rate_vals) > 0 else None
    if rate_raw_col and rate_raw_col in df.columns:
        rate_raw_vals = df[rate_raw_col].dropna()
        stats["max_fuel_elec_rate_raw"] = round(rate_raw_vals.max(), 2) if len(rate_raw_vals) > 0 else None
        stats["avg_fuel_elec_rate_raw"] = round(rate_raw_vals.mean(), 2) if len(rate_raw_vals) > 0 else None

    # 报告
    report = _build_efficiency_report(efficiency_table, stats)

    return {
        "efficiency_table": efficiency_table,
        "stats": stats,
        "report": report,
    }


def _build_efficiency_report(table: List[Dict], stats: Dict) -> str:
    """生成油电转换效率报告。"""
    lines = [
        "=" * 70,
        " 增程器油电转换效率分析",
        "=" * 70, "",
        f"燃油低热值: {stats['fuel_lhv']} MJ/kg", "",
        "### 各转速点效率汇总", "",
    ]

    # 表头
    has_gen_eff = "max_gen_eff" in table[0]
    headers = ["RPM", "峰值DC功率(kW)", "最低油耗(kg/h)",
               "峰值系统效率(%)", "平均系统效率(%)"]
    if has_gen_eff:
        headers += ["峰值发电机效率(%)", "平均发电机效率(%)"]
    if any(r.get("max_fuel_elec_rate") is not None for r in table):
        headers.append("峰值油电转换率(原始)(kwh/L)")
        headers.append("峰值油电转换率(修正)(kwh/L)")

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    for r in table:
        vals = [
            str(r["speed"]),
            str(r["max_dc_power"]),
            str(r["min_fuel_cons"]),
            str(r["max_sys_eff"]),
            str(r["avg_sys_eff"]),
        ]
        if has_gen_eff:
            vals += [str(r.get("max_gen_eff", "-")), str(r.get("avg_gen_eff", "-"))]
        if any(r2.get("max_fuel_elec_rate") is not None for r2 in table):
            vals.append(str(r.get("max_fuel_elec_rate_raw")) if r.get("max_fuel_elec_rate_raw") is not None else "-")
            vals.append(str(r["max_fuel_elec_rate"]) if r.get("max_fuel_elec_rate") is not None else "-")
        lines.append("| " + " | ".join(vals) + " |")

    # 统计
    lines += ["", "### 统计", ""]
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 峰值系统效率 | {stats['overall_max_sys_eff']}% |")
    lines.append(f"| 平均系统效率 | {stats['overall_avg_sys_eff']}% |")
    lines.append(f"| 最低系统效率 | {stats['overall_min_sys_eff']}% |")

    if stats.get("max_fuel_elec_rate_raw"):
        lines.append(f"| 峰值油电转换率(原始) | {stats['max_fuel_elec_rate_raw']} kwh/L |")
    if stats.get("avg_fuel_elec_rate_raw"):
        lines.append(f"| 平均油电转换率(原始) | {stats['avg_fuel_elec_rate_raw']} kwh/L |")
    if stats.get("max_fuel_elec_rate"):
        lines.append(f"| 峰值油电转换率(修正) | {stats['max_fuel_elec_rate']} kwh/L |")
    if stats.get("avg_fuel_elec_rate"):
        lines.append(f"| 平均油电转换率(修正) | {stats['avg_fuel_elec_rate']} kwh/L |")

    lines.append("")
    return "\n".join(lines)


def extract_wot_curve(
    df: pd.DataFrame,
    method: str = "max_torque",
) -> pd.DataFrame:
    """从 MAP 扫点数据中提取外特性（WOT）曲线。

    对每个转速点，取发动机设定值最大的工况点。

    Args:
        df: 增程器 DataFrame
        method: 提取方式
            - "max_torque": 每转速最大设定扭矩点
            - "max_power": 每转速最大发电功率点

    Returns:
        外特性 DataFrame（每转速一行）

    用法:
        wot = extract_wot_curve(df)
    """
    speed_col = COLUMN_MAP["target_speed"]
    torque_col = COLUMN_MAP["target_torque"]
    dc_col = COLUMN_MAP["dc_power"]

    if speed_col not in df.columns:
        raise ValueError(f"缺少转速列: {speed_col}")

    wot_rows = []
    speeds = sorted(df[speed_col].dropna().unique())

    for sp in speeds:
        mask = df[speed_col] == sp
        subset = df[mask]

        if method == "max_power" and dc_col in df.columns:
            idx = subset[dc_col].abs().idxmax()
        else:
            # 默认：最大设定扭矩
            if torque_col in df.columns:
                idx = subset[torque_col].idxmax()
            else:
                idx = subset.index[0]

        wot_rows.append(subset.loc[idx])

    wot_df = pd.DataFrame(wot_rows).reset_index(drop=True)

    # 按转速排序
    wot_df = wot_df.sort_values(speed_col).reset_index(drop=True)

    return wot_df


def analyze_external_characteristic(
    df: pd.DataFrame,
) -> Dict:
    """增程器外特性分析。

    提取 WOT 曲线，分析发动机功率-发电功率-效率沿外特性的变化。

    Args:
        df: 增程器 MAP 数据

    Returns:
        dict: wot_table, report

    用法:
        out = analyze_external_characteristic(df)
    """
    wot = extract_wot_curve(df, method="max_torque")

    speed_col = COLUMN_MAP["target_speed"]
    torque_col = COLUMN_MAP["target_torque"]
    dc_col = COLUMN_MAP["dc_power"]
    rate_col = COLUMN_MAP["fuel_elec_rate_fix"]
    rate_raw_col = COLUMN_MAP["fuel_elec_rate"]
    fc_col = COLUMN_MAP["fuel_consumption"]

    table = []
    for _, row in wot.iterrows():
        sp = row[speed_col]
        tq = row[torque_col] if torque_col in wot.columns else None
        dc = abs(row[dc_col]) if dc_col in wot.columns else None
        fc = row.get(fc_col)

        # 发动机功率 — 优先 HCU_EngTrq
        hcu_tq_col = COLUMN_MAP.get("hcu_engine_torque")
        if hcu_tq_col and hcu_tq_col in wot.columns:
            actual_tq_val = abs(row[hcu_tq_col])
        elif torque_col in wot.columns:
            actual_tq_val = abs(row[torque_col])
        else:
            actual_tq_val = None

        eng_power = actual_tq_val * sp / 9549 if actual_tq_val is not None else None

        # 油电转换率：优先数据列，缺失时推算
        if rate_col and rate_col in wot.columns:
            rate_fix = row.get(rate_col)
            rate_raw = row.get(rate_raw_col) if rate_raw_col in wot.columns else rate_fix
        elif eng_power and dc and fc and not pd.isna(fc):
            # 推算：密度/等效油耗
            density_col = COLUMN_MAP.get("density")
            dens = row.get(density_col) if density_col and density_col in wot.columns else 733
            bsfc = fc * 1000 / eng_power
            gen_eff_val = dc / eng_power * 100
            bsfc_elec = bsfc / (gen_eff_val / 100)
            rate_fix = dens / bsfc_elec
            rate_raw = rate_fix
        else:
            rate_fix = None
            rate_raw = None

        rate = row.get(rate_col) if rate_col in wot.columns else rate_fix

        # 发电机效率
        gen_eff = (dc / eng_power * 100) if (dc and eng_power and eng_power > 0) else None

        # 系统效率
        sys_eff = (dc / (fc * FUEL_LHV_DEFAULT / 3.6) * 100) if (dc and fc and fc > 0) else None

        table.append({
            "speed": int(sp),
            "engine_torque": round(tq, 1) if tq is not None else None,
            "engine_power": round(eng_power, 1) if eng_power else None,
            "dc_power": round(dc, 1) if dc else None,
            "gen_efficiency": round(gen_eff, 1) if gen_eff else None,
            "sys_efficiency": round(sys_eff, 1) if sys_eff else None,
            "fuel_elec_rate": round(rate, 2) if rate and not pd.isna(rate) else None,
            "fuel_elec_rate_raw": round(row.get(rate_raw_col), 2) if rate_raw_col and row.get(rate_raw_col) and not pd.isna(row.get(rate_raw_col)) else None,
            "fuel_consumption": round(fc, 2) if fc and not pd.isna(fc) else None,
        })

    # 报告
    report = _build_wot_report(table)

    return {
        "wot_table": table,
        "report": report,
    }


def _build_wot_report(table: List[Dict]) -> str:
    """生成外特性报告，重点功率分析。"""
    lines = [
        "=" * 70,
        " 增程器外特性 (WOT) 功率分析",
        "=" * 70, "",
    ]

    # ── 功率表 ──
    lines.append("### 功率-效率表")
    lines.append("")
    lines.append("| RPM | 发动机扭矩(Nm) | 发动机功率(kW) | 发电功率(kW) | "
                 "发电机效率(%) | 系统效率(%) | 油电转换率(原始)(kwh/L) | 油电转换率(修正)(kwh/L) |")
    lines.append("|" + "|".join(["---"] * 8) + "|")

    for r in table:
        vals = [
            str(r["speed"]),
            f"{r['engine_torque']:.1f}" if r.get("engine_torque") else "-",
            f"{r['engine_power']:.1f}" if r.get("engine_power") else "-",
            f"{r['dc_power']:.1f}" if r.get("dc_power") else "-",
            f"{r['gen_efficiency']:.1f}" if r.get("gen_efficiency") else "-",
            f"{r['sys_efficiency']:.1f}" if r.get("sys_efficiency") else "-",
            f"{r['fuel_elec_rate_raw']:.2f}" if r.get("fuel_elec_rate_raw") else "-",
            f"{r['fuel_elec_rate']:.2f}" if r.get("fuel_elec_rate") else "-",
        ]
        lines.append("| " + " | ".join(vals) + " |")

    # ── 功率摘要 ──
    valid = [r for r in table if r["dc_power"] and r["engine_power"]]
    if valid:
        lines += ["", "### 功率摘要", ""]

        max_dc = max(valid, key=lambda r: r["dc_power"])
        max_eng = max(valid, key=lambda r: r["engine_power"])
        dc_powers = [r["dc_power"] for r in valid]
        eng_powers = [r["engine_power"] for r in valid]
        speeds = [r["speed"] for r in valid]

        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 峰值发电功率 | {max_dc['dc_power']:.1f} kW @ {max_dc['speed']} rpm |")
        lines.append(f"| 峰值发动机功率 | {max_eng['engine_power']:.1f} kW @ {max_eng['speed']} rpm |")
        lines.append(f"| 发电功率范围 | {min(dc_powers):.1f} – {max(dc_powers):.1f} kW |")

        # 发电机效率
        gen_effs = [r["gen_efficiency"] for r in valid if r["gen_efficiency"]]
        if gen_effs:
            lines.append(f"| 发电机效率范围 | {min(gen_effs):.1f} – {max(gen_effs):.1f}% |")

        sys_effs = [r["sys_efficiency"] for r in valid if r["sys_efficiency"]]
        if sys_effs:
            lines.append(f"| 系统效率范围 | {min(sys_effs):.1f} – {max(sys_effs):.1f}% |")

    lines.append("")
    return "\n".join(lines)


def compare_rex_with_standard(
    df: pd.DataFrame,
    standard_df: Optional[pd.DataFrame] = None,
    name: str = "测试",
) -> Dict:
    """增程器标准对标分析。

    对比测试增程器与标准增程器的外特性发电功率和效率。

    Args:
        df: 测试增程器 MAP 数据
        standard_df: 标准增程器数据。None 则加载内置 RE50 标准
        name: 测试方名称

    Returns:
        dict: comparison_table, summary, report

    用法:
        result = compare_rex_with_standard(df)
        print(result["report"])
    """
    # 加载标准数据
    if standard_df is None:
        try:
            standard_df = load_rex_standard("台架原始数据")
        except Exception as e:
            return {"report": f"[错误: 无法加载标准数据: {e}]"}

    # 提取双方外特性
    test_wot = extract_wot_curve(df)
    std_wot = extract_wot_curve(standard_df)

    speed_col = COLUMN_MAP["target_speed"]
    dc_col = COLUMN_MAP["dc_power"]
    rate_col = COLUMN_MAP["fuel_elec_rate_fix"]

    # 按转速插值对比
    test_speeds = test_wot[speed_col].values
    std_speeds = std_wot[speed_col].values

    comparison = []
    for _, row in test_wot.iterrows():
        sp = row[speed_col]
        test_dc = abs(row[dc_col]) if dc_col in test_wot.columns else None
        test_rate = row.get(rate_col)

        # 在标准数据中找最近转速点
        if len(std_speeds) > 0:
            idx = np.argmin(np.abs(std_speeds - sp))
            std_row = std_wot.iloc[idx]
            std_dc = abs(std_row[dc_col]) if dc_col in std_wot.columns else None
            std_rate = std_row.get(rate_col)

            dc_diff = (test_dc - std_dc) if (test_dc is not None and std_dc is not None) else None
            dc_diff_pct = (dc_diff / std_dc * 100) if (dc_diff is not None and std_dc > 0) else None
        else:
            std_dc = None
            std_rate = None
            dc_diff = None
            dc_diff_pct = None

        comparison.append({
            "speed": int(sp),
            "test_dc_power": round(test_dc, 1) if test_dc else None,
            "std_dc_power": round(std_dc, 1) if std_dc else None,
            "dc_diff": round(dc_diff, 1) if dc_diff is not None else None,
            "dc_diff_pct": round(dc_diff_pct, 1) if dc_diff_pct is not None else None,
            "test_rate": round(test_rate, 2) if test_rate and not pd.isna(test_rate) else None,
            "std_rate": round(std_rate, 2) if std_rate and not pd.isna(std_rate) else None,
        })

    # 评定
    diffs = [c["dc_diff_pct"] for c in comparison if c["dc_diff_pct"] is not None]
    summary = {}
    if diffs:
        summary.update({
            "avg_diff_pct": round(np.mean(diffs), 1),
            "max_advantage": round(max(diffs), 1),
            "max_deficit": round(min(diffs), 1),
            "n_better": sum(1 for d in diffs if d > 0),
            "n_worse": sum(1 for d in diffs if d < 0),
            "n_equal": sum(1 for d in diffs if abs(d) < 1),
        })

    # 报告
    report = _build_comparison_report(comparison, summary, name)

    return {
        "comparison_table": comparison,
        "summary": summary,
        "report": report,
    }


def _build_comparison_report(
    comparison: List[Dict],
    summary: Dict,
    name: str,
) -> str:
    """生成标准对标报告。"""
    lines = [
        "=" * 70,
        " 增程器标准对标 (RE50)",
        "=" * 70, "",
        f"测试: {name} vs 标准: RE50", "",
    ]

    lines.append("| RPM | 测试发电(kW) | 标准发电(kW) | 差值(kW) | 偏差(%) | "
                 "测试效率(kwh/L) | 标准效率(kwh/L) | 评级 |")
    lines.append("|" + "|".join(["---"] * 8) + "|")

    for c in comparison:
        pdiff = c["dc_diff_pct"]
        if pdiff is None:
            grade = "-"
        elif abs(pdiff) <= 5:
            grade = f"优 ({pdiff:+.1f}%)"
        elif abs(pdiff) <= 10:
            grade = f"良 ({pdiff:+.1f}%)"
        elif abs(pdiff) <= 15:
            grade = f"中 ({pdiff:+.1f}%)"
        else:
            grade = f"差 ({pdiff:+.1f}%)"

        vals = [
            str(c["speed"]),
            f"{c['test_dc_power']:.1f}" if c["test_dc_power"] else "-",
            f"{c['std_dc_power']:.1f}" if c["std_dc_power"] else "-",
            f"{c['dc_diff']:+.1f}" if c["dc_diff"] is not None else "-",
            f"{c['dc_diff_pct']:+.1f}%" if c["dc_diff_pct"] is not None else "-",
            f"{c['test_rate']:.2f}" if c["test_rate"] else "-",
            f"{c['std_rate']:.2f}" if c["std_rate"] else "-",
            grade,
        ]
        lines.append("| " + " | ".join(vals) + " |")

    # 汇总
    lines += ["", "### 综合结论", ""]
    if summary:
        lines.append(f"- 平均偏差: {summary['avg_diff_pct']:+.1f}%")
        lines.append(f"- 最大领先: +{summary['max_advantage']:.1f}%")
        lines.append(f"- 最大落后: {summary['max_deficit']:.1f}%")
        lines.append(f"- 领先点数: {summary['n_better']}, "
                     f"落后点数: {summary['n_worse']}, "
                     f"持平点数: {summary['n_equal']}")

    lines.append("")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────
# 4. 一站式全分析
# ────────────────────────────────────────────────────────────

def rex_full_analysis(
    filepath: str,
    sheet_name: str = "台架原始数据",
    fuel_lhv: float = FUEL_LHV_DEFAULT,
    standard_name: Optional[str] = None,
) -> Dict:
    """增程器一站式全分析。

    加载数据 → 油电转换效率 → 外特性 → 对标 → 综合报告。

    Args:
        filepath: 增程器 Excel 文件路径
        sheet_name: 数据 sheet 名称
        fuel_lhv: 燃油低热值
        standard_name: 标准增程器名称，None 则使用内置 RE50

    Returns:
        dict: efficiency_result, wot_result, comparison_result, report

    用法:
        out = rex_full_analysis("增程器.xlsx")
        print(out["report"])
    """
    # 加载
    df = load_rex_excel(filepath, sheet_name=sheet_name)

    # 检查数据结构
    print_data_structure(df)

    # 分析
    eff_result = analyze_fuel_to_electric_efficiency(df, fuel_lhv=fuel_lhv)
    wot_result = analyze_external_characteristic(df)

    # 标准对标
    if standard_name:
        try:
            std_df = load_rex_standard(standard_name)
        except Exception:
            std_df = load_rex_standard("台架原始数据")
    else:
        std_df = None

    cmp_result = compare_rex_with_standard(df, standard_df=std_df)

    # 合并报告
    report_parts = [
        eff_result["report"],
        wot_result["report"],
        cmp_result["report"],
    ]
    full_report = "\n\n".join(report_parts)

    return {
        "df": df,
        "efficiency": eff_result,
        "wot": wot_result,
        "comparison": cmp_result,
        "report": full_report,
    }


# ────────────────────────────────────────────────────────────
# 5. 可视化
# ────────────────────────────────────────────────────────────

def plot_rex_efficiency_map(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 10),
) -> None:
    """绘制增程器效率 MAP 图。

    四个子图：DC 功率等高线、系统效率等高线、油电转换率等高线、发电机效率等高线。
    """
    speed_col = COLUMN_MAP["target_speed"]
    torque_col = COLUMN_MAP["target_torque"]
    dc_col = COLUMN_MAP["dc_power"]
    rate_col = COLUMN_MAP["fuel_elec_rate_fix"]
    rate_raw_col = COLUMN_MAP["fuel_elec_rate"]
    fc_col = COLUMN_MAP["fuel_consumption"]
    actual_tq_col = COLUMN_MAP["actual_torque"]

    # 计算指标
    dc = df[dc_col].abs()
    fc = df[fc_col]
    speed = df[speed_col]
    torque = df[torque_col]
    sys_eff = dc / (fc * FUEL_LHV_DEFAULT / 3.6) * 100

    if actual_tq_col in df.columns:
        eng_power = df[actual_tq_col].abs() * speed / 9549
        gen_eff = dc / eng_power.replace(0, np.nan) * 100
    else:
        gen_eff = None

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    def _auto_levels(data, step, margin=0.05):
        """从数据自动计算等高线层级：下取整到步长边界，上浮一档。"""
        v = data.dropna()
        lo = np.floor((v.min() * (1 - margin)) / step) * step
        hi = np.ceil((v.max() * (1 + margin)) / step) * step + step
        return np.arange(lo, hi, step)

    # 1. DC 功率等高线 — 5kW 间隔
    _plot_contour(axes[0], speed, torque, dc, "DC 功率 (kW)", "Reds",
                  levels=_auto_levels(dc, 5))

    # 2. 系统效率等高线 — 5% 间隔
    _plot_contour(axes[1], speed, torque, sys_eff, "系统效率 (%)", "Greens",
                  levels=_auto_levels(sys_eff, 5))

    # 3. 油电转换率等高线 — 0.1 kwh/L 间隔
    if rate_col in df.columns:
        rate = df[rate_col]
        _plot_contour(axes[2], speed, torque, rate, "油电转换率 (kwh/L)", "Blues",
                      levels=_auto_levels(rate, 0.1))

    # 4. 发电机效率等高线 — 10% 间隔
    if gen_eff is not None:
        _plot_contour(axes[3], speed, torque, gen_eff, "发电机效率 (%)", "Oranges",
                      levels=_auto_levels(gen_eff, 10))

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"图表已保存: {save_path}")
    plt.show()


def _plot_contour(ax, x, y, z, title: str, cmap: str, levels=None) -> None:
    """绘制等高线图。

    Args:
        levels: 等高线层级序列，None 则自动生成 14 层
    """
    valid = x.notna() & y.notna() & z.notna()
    if valid.sum() < 3:
        ax.text(0.5, 0.5, "数据不足", transform=ax.transAxes, ha="center")
        return

    xi = np.linspace(x[valid].min(), x[valid].max(), 100)
    yi = np.linspace(y[valid].min(), y[valid].max(), 100)
    xi_grid, yi_grid = np.meshgrid(xi, yi)

    from scipy.interpolate import griddata
    zi = griddata((x[valid], y[valid]), z[valid], (xi_grid, yi_grid), method='linear')

    if levels is None:
        levels = 14

    contour = ax.contourf(xi_grid, yi_grid, zi, levels=24, cmap=cmap)
    cset = ax.contour(xi_grid, yi_grid, zi, levels=levels, colors='black', linewidths=0.4)
    ax.clabel(cset, levels=cset.levels, inline=True, fontsize=6, fmt='%.1f')
    plt.colorbar(contour, ax=ax)
    ax.set_xlabel("转速 (rpm)")
    ax.set_ylabel("扭矩 (Nm)")
    ax.set_title(title)


# ────────────────────────────────────────────────────────────
# 6. CLI 入口
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python rex_analysis.py <file.xlsx> [sheet_name]")
        print("示例: python rex_analysis.py 增程器数据.xlsx 台架原始数据")
        sys.exit(1)

    fp = sys.argv[1]
    sheet = sys.argv[2] if len(sys.argv) > 2 else "台架原始数据"
    out = rex_full_analysis(fp, sheet_name=sheet)
    print(out["report"])
