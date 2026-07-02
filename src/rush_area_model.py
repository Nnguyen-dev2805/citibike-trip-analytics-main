# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.14.5 (v3.14.5:5607950ef23, May 10 2026, 07:38:09) [Clang 21.0.0 (clang-2100.0.123.102)]
# Embedded file name: /opt/project/src/rush_area_model.py
# Compiled at: 2026-07-02 07:38:28
# Size of source mod 2**32: 14082 bytes
import os, numpy as np, pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns, folium
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, roc_auc_score, average_precision_score, roc_curve, precision_recall_curve
TOP_AREAS = 150
RUSH_QUANTILE = 0.9
MIN_RUSH_THRESHOLD = 3

def build_rush_area_dataset(data_path, system_name, city_name, top_areas=150, rush_quantile=0.9, min_threshold=3):
    print(f"Loading cleaned data from {data_path}...")
    df = pd.read_parquet(data_path, columns=["started_at", "start_lat", "start_lng"])
    df["started_at"] = pd.to_datetime(df["started_at"])
    df["area_lat"] = (df["start_lat"] * 100).apply(np.floor) / 100.0
    df["area_lng"] = (df["start_lng"] * 100).apply(np.floor) / 100.0
    df["area_id"] = df["area_lat"].astype(str) + "_" + df["area_lng"].astype(str)
    df["timestamp_hour"] = df["started_at"].dt.floor("h")
    demand_df = df.groupby(["timestamp_hour", "area_id"]).size().reset_index(name="demand_count")
    top_areas_list = df["area_id"].value_counts().head(top_areas).index.tolist()
    demand_df = demand_df[demand_df["area_id"].isin(top_areas_list)]
    all_hours = pd.date_range(start=(demand_df["timestamp_hour"].min()), end=(demand_df["timestamp_hour"].max()), freq="h")
    panel_index = pd.MultiIndex.from_product([all_hours, top_areas_list], names=["timestamp_hour", "area_id"])
    panel_df = pd.DataFrame(index=panel_index).reset_index()
    panel_df = pd.merge(panel_df, demand_df, on=["timestamp_hour", "area_id"], how="left")
    panel_df["demand_count"] = panel_df["demand_count"].fillna(0).astype(int)
    panel_df["hour_of_day"] = panel_df["timestamp_hour"].dt.hour
    panel_df["day_of_week"] = panel_df["timestamp_hour"].dt.day_name()
    panel_df["month_of_year"] = panel_df["timestamp_hour"].dt.month
    panel_df["is_weekend"] = panel_df["timestamp_hour"].dt.dayofweek.isin([5, 6]).astype(int)
    panel_df = panel_df.sort_values(by=["area_id", "timestamp_hour"]).reset_index(drop=True)
    for lag in (1, 2, 24, 168):
        panel_df[f"lag_{lag}"] = panel_df.groupby("area_id")["demand_count"].shift(lag).fillna(0).astype(int)
    else:
        unique_hours = sorted(panel_df["timestamp_hour"].unique())
        split_idx = int(len(unique_hours) * 0.8)
        train_hours = unique_hours[:split_idx]
        panel_df["split"] = "test"
        panel_df.loc[(panel_df["timestamp_hour"].isin(train_hours), "split")] = "train"
        train_df = panel_df[panel_df["split"] == "train"]
        thresholds = {}
        for area in top_areas_list:
            area_train = train_df[train_df["area_id"] == area]
            if len(area_train) > 0:
                q = area_train["demand_count"].quantile(rush_quantile)
                thresholds[area] = max(q, min_threshold)
            else:
                thresholds[area] = min_threshold
        else:
            panel_df["rush_threshold"] = panel_df["area_id"].map(thresholds)
            panel_df["is_rush_area"] = (panel_df["demand_count"] >= panel_df["rush_threshold"]).astype(int)
            area_coords = df.groupby("area_id")[["start_lat", "start_lng"]].mean().reset_index()
            area_coords.columns = ["area_id", "lat", "lng"]
            print(f"Dataset generated. Rows: {len(panel_df)}, Areas: {len(top_areas_list)}")
            return {
                'data': panel_df, 
                'thresholds': thresholds, 
                'area_coords': area_coords, 
                'system_name': system_name, 
                'city_name': city_name
            }


def split_summary_table(rush_labeled):
    df = rush_labeled["data"]
    train_df = df[df["split"] == "train"]
    test_df = df[df["split"] == "test"]
    summary = pd.DataFrame([
        {'Split': "Train", 
         'Start Time': train_df["timestamp_hour"].min(), 
         'End Time': train_df["timestamp_hour"].max(), 
         'Total Rows': len(train_df)},
        {'Split': "Test", 
         'Start Time': test_df["timestamp_hour"].min(), 
         'End Time': test_df["timestamp_hour"].max(), 
         'Total Rows': len(test_df)}
    ])
    return summary


def panel_summary_table(rush_labeled):
    df = rush_labeled["data"]
    num_areas = df["area_id"].nunique()
    total_rows = len(df)
    rush_rows = df["is_rush_area"].sum()
    rush_pct = rush_rows / total_rows * 100
    median_threshold = pd.Series(rush_labeled["thresholds"]).median()
    summary = pd.DataFrame([
     {'Metric':"Number of Areas", 
      'Value':num_areas},
     {'Metric':"Total Rows in Panel", 
      'Value':total_rows},
     {'Metric':"Rush Labeled Rows", 
      'Value':f"{rush_rows} ({rush_pct:.2f}%)"},
     {'Metric':"Median Rush Threshold", 
      'Value':median_threshold}])
    return summary


def area_summary_table(rush_labeled, top_n=10):
    df = rush_labeled["data"]
    area_stats = df.groupby("area_id").agg(total_demand=('demand_count', 'sum'),
      rush_threshold=('rush_threshold', 'first'),
      rush_hours=('is_rush_area', 'sum')).reset_index()
    area_stats = area_stats.sort_values(by="total_demand", ascending=False).head(top_n)
    return area_stats


def plot_area_folium(rush_labeled, metric='total_demand'):
    coords_df = rush_labeled["area_coords"]
    df = rush_labeled["data"]
    if metric == "total_demand":
        stats = df.groupby("area_id")["demand_count"].sum().reset_index(name="value")
    else:
        stats = df.groupby("area_id")["demand_count"].mean().reset_index(name="value")
    stats = pd.merge(stats, coords_df, on="area_id")
    mean_lat = stats["lat"].mean()
    mean_lng = stats["lng"].mean()
    m = folium.Map(location=[mean_lat, mean_lng], zoom_start=12, tiles="cartodbpositron")
    max_val = stats["value"].max() if stats["value"].max() > 0 else 1
    for _, row in stats.iterrows():
        folium.CircleMarker(location=[
         row["lat"], row["lng"]],
          radius=(5 + 15 * (row["value"] / max_val)),
          popup=f'Area: {row["area_id"]}<br>{metric}: {row["value"]:.1f}',
          color=("crimson" if row["value"] > 0 else "blue"),
          fill=True,
          fill_color=("crimson" if row["value"] > 0 else "blue"),
          fill_opacity=0.6).add_to(m)
    else:
        return m


def train_logistic_rush_area_model(rush_labeled):
    df = rush_labeled["data"].copy()
    categorical_features = [
     "area_id", "hour_of_day", "day_of_week", "month_of_year"]
    numeric_features = ['is_weekend', 'lag_1', 'lag_2', 'lag_24', 'lag_168']
    preprocessor = ColumnTransformer(transformers=[
     (
      "cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
     (
      "num", StandardScaler(), numeric_features)])
    pipeline = Pipeline(steps=[
     (
      "preprocessor", preprocessor),
     (
      "classifier", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))])
    train_mask = df["split"] == "train"
    test_mask = df["split"] == "test"
    X_train = df.loc[(train_mask, categorical_features + numeric_features)]
    y_train = df.loc[(train_mask, "is_rush_area")]
    X_test = df.loc[(test_mask, categorical_features + numeric_features)]
    pipeline.fit(X_train, y_train)
    df["y_pred"] = 0
    df["y_prob"] = 0.0
    df.loc[(train_mask, "y_pred")] = pipeline.predict(X_train)
    df.loc[(train_mask, "y_prob")] = pipeline.predict_proba(X_train)[:, 1]
    df.loc[(test_mask, "y_pred")] = pipeline.predict(X_test)
    df.loc[(test_mask, "y_prob")] = pipeline.predict_proba(X_test)[:, 1]
    return {
        'model': pipeline, 
        'data': df, 
        'rush_labeled': rush_labeled
    }


def metrics_table(rush_result):
    df = rush_result["data"]
    metrics = []
    for split in ('train', 'test'):
        split_df = df[df["split"] == split]
        y_true = split_df["is_rush_area"]
        y_pred = split_df["y_pred"]
        y_prob = split_df["y_prob"]
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
        roc_auc = roc_auc_score(y_true, y_prob) if len(y_true.unique()) > 1 else 0.5
        pr_auc = average_precision_score(y_true, y_prob) if len(y_true.unique()) > 1 else 0.0
        metrics.append({
            'Split': split.capitalize(), 
            'Precision': round(p, 4), 
            'Recall': round(r, 4), 
            'F1-Score': round(f1, 4), 
            'ROC-AUC': round(roc_auc, 4), 
            'PR-AUC': round(pr_auc, 4)
        })
    else:
        return pd.DataFrame(metrics)


def plot_logistic_metrics(rush_result):
    df = rush_result["data"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    for split, color in zip(["train", "test"], ["blue", "green"]):
        split_df = df[df["split"] == split]
        y_true = split_df["is_rush_area"]
        y_prob = split_df["y_prob"]
        if len(y_true.unique()) <= 1:
            pass
        else:
            fpr, tpr, _ = roc_curve(y_true, y_prob)
            roc_auc = roc_auc_score(y_true, y_prob)
            ax1.plot(fpr, tpr, color=color, label=f"{split.capitalize()} (AUC = {roc_auc:.4f})")
            precision, recall, _ = precision_recall_curve(y_true, y_prob)
            pr_auc = average_precision_score(y_true, y_prob)
            ax2.plot(recall, precision, color=color, label=f"{split.capitalize()} (AP = {pr_auc:.4f})")
    else:
        ax1.plot([0, 1], [0, 1], "k--")
        ax1.set_xlim([0.0, 1.0])
        ax1.set_ylim([0.0, 1.05])
        ax1.set_xlabel("False Positive Rate")
        ax1.set_ylabel("True Positive Rate")
        ax1.set_title("Receiver Operating Characteristic (ROC)")
        ax1.legend(loc="lower right")
        ax2.set_xlim([0.0, 1.0])
        ax2.set_ylim([0.0, 1.05])
        ax2.set_xlabel("Recall")
        ax2.set_ylabel("Precision")
        ax2.set_title("Precision-Recall Curve")
        ax2.legend(loc="lower left")
        plt.tight_layout()
        plt.show()


def plot_confusion_matrix(rush_result):
    df = rush_result["data"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for split, ax in zip(["train", "test"], [ax1, ax2]):
        split_df = df[df["split"] == split]
        y_true = split_df["is_rush_area"]
        y_pred = split_df["y_pred"]
        cm = confusion_matrix(y_true, y_pred)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("True Label")
        ax.set_title(f"{split.capitalize()} Confusion Matrix")
        ax.set_xticklabels(["Not Rush", "Rush"])
        ax.set_yticklabels(["Not Rush", "Rush"])
    else:
        plt.tight_layout()
        plt.show()


def choose_snapshot_hour(rush_result):
    df = rush_result["data"]
    test_df = df[df["split"] == "test"]
    return test_df["timestamp_hour"].median()


def show_top_rush_probabilities(rush_result, timestamp_hour, top_n=15):
    df = rush_result["data"]
    coords_df = rush_result["rush_labeled"]["area_coords"]
    ts = pd.Timestamp(timestamp_hour)
    hour_df = df[df["timestamp_hour"] == ts]
    if len(hour_df) == 0:
        print(f"No records found for timestamp: {ts}")
        return pd.DataFrame()
    hour_df = pd.merge(hour_df, coords_df, on="area_id")
    cols = ['area_id', 'demand_count', 'rush_threshold', 'is_rush_area', 'y_prob', 'y_pred', 
     'lat', 'lng']
    cols_to_select = [col for col in cols if col in hour_df.columns]
    result = hour_df[cols_to_select].sort_values(by="y_prob", ascending=False).head(top_n)
    return result


def plot_rush_probability_map(rush_result, timestamp_hour):
    df = rush_result["data"]
    coords_df = rush_result["rush_labeled"]["area_coords"]
    ts = pd.Timestamp(timestamp_hour)
    hour_df = df[df["timestamp_hour"] == ts]
    if len(hour_df) == 0:
        print(f"No records found for timestamp: {ts}")
        return
    hour_df = pd.merge(hour_df, coords_df, on="area_id")
    mean_lat = hour_df["lat"].mean()
    mean_lng = hour_df["lng"].mean()
    m = folium.Map(location=[mean_lat, mean_lng], zoom_start=12, tiles="cartodbpositron")

    def get_color(prob):
        if prob < 0.2:
            return "blue"
        if prob < 0.4:
            return "cyan"
        if prob < 0.6:
            return "yellow"
        if prob < 0.8:
            return "orange"
        return "red"

    for _, row in hour_df.iterrows():
        folium.CircleMarker(location=[
         row["lat"], row["lng"]],
          radius=10,
          popup=f'Area: {row["area_id"]}<br>Prob: {row["y_prob"]:.4f}<br>Pred: {row["y_pred"]}<br>Actual Demand: {row["demand_count"]}',
          color=(get_color(row["y_prob"])),
          fill=True,
          fill_color=(get_color(row["y_prob"])),
          fill_opacity=0.7).add_to(m)
    else:
        return m

# okay decompiling src/__pycache__/rush_area_model.cpython-38.pyc
