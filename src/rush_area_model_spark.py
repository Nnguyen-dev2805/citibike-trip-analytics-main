# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.14.5 (v3.14.5:5607950ef23, May 10 2026, 07:38:09) [Clang 21.0.0 (clang-2100.0.123.102)]
# Embedded file name: /opt/project/src/rush_area_model_spark.py
# Compiled at: 2026-07-02 10:19:17
# Size of source mod 2**32: 18175 bytes
import os, pandas as pd, numpy as np
import matplotlib.pyplot as plt
import seaborn as sns, folium
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline
from pyspark.ml.functions import vector_to_array
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, roc_auc_score, average_precision_score, roc_curve, precision_recall_curve
TOP_AREAS = 150
RUSH_QUANTILE = 0.9
MIN_RUSH_THRESHOLD = 3

def build_rush_area_dataset_spark(spark, silver_path, system_name, city_name, top_areas=150, rush_quantile=0.9, min_threshold=3):
    print(f"Loading cleaned Delta Lake table directly from {silver_path}...")
    df = spark.read.format("delta").load(silver_path)
    df = df.withColumn("area_lat", F.floor(F.col("start_lat") * 100) / 100)
    df = df.withColumn("area_lng", F.floor(F.col("start_lng") * 100) / 100)
    df = df.withColumn("area_id", F.concat(F.col("area_lat").cast("string"), F.lit("_"), F.col("area_lng").cast("string")))
    df = df.withColumn("timestamp_hour", F.date_trunc("hour", F.col("started_at")))
    min_max = df.select(F.min("timestamp_hour"), F.max("timestamp_hour")).first()
    min_hour = min_max[0]
    max_hour = min_max[1]
    hours = pd.date_range(start=min_hour, end=max_hour, freq="h").tolist()
    hours_pd = pd.DataFrame({"timestamp_hour": hours})
    hours_df = spark.createDataFrame(hours_pd)
    split_idx = int(len(hours) * 0.8)
    split_threshold = hours[split_idx]
    train_trips_df = df.filter(F.col("timestamp_hour") < F.lit(split_threshold))
    top_areas_df = train_trips_df.groupBy("area_id").count().orderBy(F.desc("count")).limit(top_areas)
    top_areas_list = [row[0] for row in top_areas_df.select("area_id").collect()]
    demand_df = df.groupBy("timestamp_hour", "area_id").count().withColumnRenamed("count", "demand_count")
    demand_df = demand_df.filter(F.col("area_id").isin(top_areas_list))
    top_areas_pd = pd.DataFrame({"area_id": top_areas_list})
    top_areas_spark_df = spark.createDataFrame(top_areas_pd)
    panel_df = hours_df.crossJoin(top_areas_spark_df)
    panel_df = panel_df.join(demand_df, on=["timestamp_hour", "area_id"], how="left").na.fill(0, ["demand_count"])
    panel_df = panel_df.withColumn("hour_of_day", F.hour(F.col("timestamp_hour")))
    panel_df = panel_df.withColumn("day_of_week", F.date_format(F.col("timestamp_hour"), "EEEE"))
    panel_df = panel_df.withColumn("month_of_year", F.month(F.col("timestamp_hour")))
    panel_df = panel_df.withColumn("day_of_week_num", F.dayofweek(F.col("timestamp_hour")))
    panel_df = panel_df.withColumn("is_weekend", F.when(F.col("day_of_week_num").isin(1, 7), 1).otherwise(0))
    window_spec = Window.partitionBy("area_id").orderBy("timestamp_hour")
    for lag in (1, 2, 24, 168):
        panel_df = panel_df.withColumn(f"lag_{lag}", F.lag("demand_count", lag).over(window_spec))
    else:
        panel_df = panel_df.na.fill(0, ["lag_1", "lag_2", "lag_24", "lag_168"])
        split_idx = int(len(hours) * 0.8)
        split_threshold = hours[split_idx]
        panel_df = panel_df.withColumn("split", F.when(F.col("timestamp_hour") < F.lit(split_threshold), "train").otherwise("test"))
        train_df = panel_df.filter(F.col("split") == "train")
        thresholds_df = train_df.groupBy("area_id").agg(F.percentile_approx("demand_count", rush_quantile).alias("p_quantile"))
        panel_df = panel_df.join(thresholds_df, on="area_id", how="left")
        panel_df = panel_df.withColumn("rush_threshold", F.greatest(F.col("p_quantile"), F.lit(min_threshold)))
        panel_df = panel_df.withColumn("is_rush_area", F.when(F.col("demand_count") >= F.col("rush_threshold"), 1).otherwise(0))
        panel_df = panel_df.drop("p_quantile")
        area_coords_df = df.groupBy("area_id").agg(F.mean("start_lat").alias("lat"), F.mean("start_lng").alias("lng"))
        area_coords = area_coords_df.toPandas()
        print("PySpark Dataset generated in memory.")
        return {
            'data': panel_df, 
            'area_coords': area_coords, 
            'system_name': system_name, 
            'city_name': city_name, 
            'top_areas_list': top_areas_list, 
            'hours_list': hours, 
            'split_threshold': split_threshold
        }


def split_summary_table_spark(rush_labeled):
    df = rush_labeled["data"]
    stats = df.groupBy("split").agg(F.min("timestamp_hour").alias("Start Time"), F.max("timestamp_hour").alias("End Time"), F.count("*").alias("Total Rows")).toPandas()
    stats.columns = [
     "Split", "Start Time", "End Time", "Total Rows"]
    stats["Split"] = stats["Split"].str.capitalize()
    return stats


def panel_summary_table_spark(rush_labeled):
    df = rush_labeled["data"]
    num_areas = len(rush_labeled["top_areas_list"])
    total_rows = df.count()
    rush_rows = df.filter(F.col("is_rush_area") == 1).count()
    rush_pct = rush_rows / total_rows * 100
    thresholds = df.groupBy("area_id").agg(F.first("rush_threshold").alias("thresh")).toPandas()["thresh"]
    median_threshold = thresholds.median()
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


def area_summary_table_spark(rush_labeled, top_n=10):
    df = rush_labeled["data"]
    stats = df.groupBy("area_id").agg(F.sum("demand_count").alias("total_demand"), F.first("rush_threshold").alias("rush_threshold"), F.sum("is_rush_area").alias("rush_hours")).orderBy(F.desc("total_demand")).limit(top_n).toPandas()
    return stats


def plot_area_folium_spark(rush_labeled, metric='total_demand'):
    coords_df = rush_labeled["area_coords"]
    df = rush_labeled["data"]
    if metric == "total_demand":
        stats = df.groupBy("area_id").agg(F.sum("demand_count").alias("value")).toPandas()
    else:
        stats = df.groupBy("area_id").agg(F.mean("demand_count").alias("value")).toPandas()
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


def train_logistic_rush_area_model_spark(rush_labeled):
    df = rush_labeled["data"]
    categorical_features = [
     "area_id", "day_of_week"]
    numeric_features = [
     "lag_1", "lag_2", "lag_24", "lag_168"]
    indexers = [
     StringIndexer(inputCol="area_id", outputCol="area_id_idx", handleInvalid="keep"),
     StringIndexer(inputCol="day_of_week", outputCol="day_of_week_idx", handleInvalid="keep")]
    encoder = OneHotEncoder(inputCols=[
     "area_id_idx", "day_of_week_idx", "hour_of_day"],
      outputCols=[
     "area_id_vec", "day_of_week_vec", "hour_of_day_vec"],
      handleInvalid="keep")
    assembler_num = VectorAssembler(inputCols=numeric_features,
      outputCol="num_features")
    scaler = StandardScaler(inputCol="num_features",
      outputCol="scaled_num_features",
      withStd=True,
      withMean=True)
    assembler_final = VectorAssembler(inputCols=[
     'area_id_vec', 'day_of_week_vec', 'hour_of_day_vec', 'is_weekend', 
     'scaled_num_features'],
      outputCol="features")
    train_df = df.filter(F.col("split") == "train")
    total_train = train_df.count()
    rush_train = train_df.filter(F.col("is_rush_area") == 1).count()
    non_rush_train = total_train - rush_train
    w_1 = float(total_train) / (2.0 * rush_train) if rush_train > 0 else 1.0
    w_0 = float(total_train) / (2.0 * non_rush_train) if non_rush_train > 0 else 1.0
    df_weighted = df.withColumn("weight", F.when(F.col("is_rush_area") == 1, F.lit(w_1)).otherwise(F.lit(w_0)))
    lr = LogisticRegression(featuresCol="features",
      labelCol="is_rush_area",
      weightCol="weight",
      probabilityCol="probability",
      predictionCol="prediction",
      maxIter=100,
      regParam=0.01)
    stages = indexers + [encoder, assembler_num, scaler, assembler_final, lr]
    pipeline = Pipeline(stages=stages)
    train_data = df_weighted.filter(F.col("split") == "train")
    print("Training PySpark Logistic Regression model directly on Delta Lake data...")
    model = pipeline.fit(train_data)
    predictions = model.transform(df_weighted)
    predictions = predictions.withColumn("y_prob_arr", vector_to_array(F.col("probability")))
    predictions = predictions.withColumn("y_prob", F.col("y_prob_arr")[1])
    predictions = predictions.withColumnRenamed("prediction", "y_pred")
    predictions = predictions.withColumn("y_pred", F.col("y_pred").cast("int"))
    return {'model':model, 
     'data':predictions, 
     'rush_labeled':rush_labeled}


def metrics_table_spark(rush_result):
    predictions = rush_result["data"]
    metrics = []
    for split in ('train', 'test'):
        split_df = predictions.filter(F.col("split") == split).select("is_rush_area", "y_pred", "y_prob").toPandas()
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


def plot_logistic_metrics_spark(rush_result):
    predictions = rush_result["data"]
    plot_df = predictions.select("split", "is_rush_area", "y_prob").toPandas()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    for split, color in zip(["train", "test"], ["blue", "green"]):
        split_df = plot_df[plot_df["split"] == split]
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


def plot_confusion_matrix_spark(rush_result):
    predictions = rush_result["data"]
    plot_df = predictions.select("split", "is_rush_area", "y_pred").toPandas()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for split, ax in zip(["train", "test"], [ax1, ax2]):
        split_df = plot_df[plot_df["split"] == split]
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


def choose_snapshot_hour_spark(rush_result):
    predictions = rush_result["data"]
    test_hours = predictions.filter(F.col("split") == "test").select("timestamp_hour").distinct().toPandas()
    sorted_hours = test_hours["timestamp_hour"].sort_values().reset_index(drop=True)
    middle_idx = len(sorted_hours) // 2
    return sorted_hours.iloc[middle_idx]


def show_top_rush_probabilities_spark(rush_result, timestamp_hour, top_n=15):
    predictions = rush_result["data"]
    coords_df = rush_result["rush_labeled"]["area_coords"]
    ts = pd.Timestamp(timestamp_hour)
    hour_df = predictions.filter(F.col("timestamp_hour") == ts)
    spark = predictions.sparkSession
    coords_spark = spark.createDataFrame(coords_df)
    hour_df = hour_df.join(coords_spark, on="area_id", how="inner")
    cols = ['area_id', 'demand_count', 'rush_threshold', 'is_rush_area', 'y_prob', 'y_pred', 
     'lat', 'lng']
    hour_pd = hour_df.select(*[col for col in cols if col in hour_df.columns]).toPandas()
    if len(hour_pd) == 0:
        print(f"No records found for timestamp: {ts}")
        return pd.DataFrame()
    result = hour_pd.sort_values(by="y_prob", ascending=False).head(top_n)
    return result


def plot_rush_probability_map_spark(rush_result, timestamp_hour):
    predictions = rush_result["data"]
    coords_df = rush_result["rush_labeled"]["area_coords"]
    ts = pd.Timestamp(timestamp_hour)
    hour_df = predictions.filter(F.col("timestamp_hour") == ts)
    spark = predictions.sparkSession
    coords_spark = spark.createDataFrame(coords_df)
    hour_df = hour_df.join(coords_spark, on="area_id", how="inner")
    hour_pd = hour_df.toPandas()
    if len(hour_pd) == 0:
        print(f"No records found for timestamp: {ts}")
        return
    mean_lat = hour_pd["lat"].mean()
    mean_lng = hour_pd["lng"].mean()
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

    for _, row in hour_pd.iterrows():
        actual_label = "🔴 Cao điểm" if row["is_rush_area"] == 1 else "🟢 Bình thường"
        pred_label = "🔴 Cao điểm" if row["y_pred"] == 1 else "🟢 Bình thường"
        folium.CircleMarker(location=[
         row["lat"], row["lng"]],
          radius=10,
          popup=folium.Popup(f'<b>Khu vực:</b> {row["area_id"]}<br><b>Nhu cầu thực:</b> {row["demand_count"]} chuyến/giờ<br><b>Ngưỡng cao điểm:</b> {row["rush_threshold"]} chuyến/giờ<br><b>Nhãn thực tế:</b> {actual_label}<br><b>Dự đoán:</b> {pred_label}<br><b>Xác suất cao điểm:</b> {row["y_prob"]:.4f}',
          max_width=250),
          color=(get_color(row["y_prob"])),
          fill=True,
          fill_color=(get_color(row["y_prob"])),
          fill_opacity=0.7).add_to(m)
    else:
        return m

# okay decompiling src/__pycache__/rush_area_model_spark.cpython-38.pyc
