# 出行平台订单运营分析系统

> 也可作为“行程记录管理系统”课程项目或简历项目展示使用。

## 1. 项目简介

出行平台订单运营分析系统是一个基于出租车/出行平台订单数据构建的运营分析后台。系统以订单和行程明细数据为基础，围绕订单规模、成交金额、客单价、行程效率、异常行程、支付方式分布、乘客数分布、距离分布、小时高峰分布和区域热点等指标进行统计分析与可视化展示。

项目当前采用前后端分离结构：前端负责登录、筛选、看板展示和行程记录管理；后端负责接口服务、订单数据管理、行程数据导入、异常识别和聚合统计刷新。系统适合用于出行平台订单运营分析、出租车行程数据分析、数据库课程设计、数据可视化课程项目和简历项目展示。

核心分析目标包括：

- 展示指定日期范围内的订单量、成交金额、平均客单价等核心 KPI。
- 分析每日行程趋势和 0-23 点小时高峰分布。
- 分析支付方式、乘客数、行程距离区间等订单结构。
- 识别异常行程，并在行程明细中展示异常原因。
- 统计上车区域和下车区域 Top10，辅助观察区域热点。
- 通过聚合统计表降低看板接口实时计算压力。

## 2. 项目背景

出租车和出行平台订单数据通常具有记录量大、字段多、查询维度多的特点。运营看板需要频繁按日期范围统计订单量、成交金额、支付方式、乘客数、距离区间、小时分布和区域热点。如果每次看板刷新都直接扫描订单明细表并实时分组统计，数据量较大时会影响接口响应速度和前端图表加载体验。

因此，本系统在订单明细表之外设计了多张聚合统计表。后端通过 `rebuild_taxi_stats.py` 和聚合统计服务将明细数据按日、小时、支付方式、乘客数、距离区间、上车区域、下车区域等维度预计算到统计表中。看板查询时优先读取聚合结果，从而减少重复计算，提高数据看板的查询效率和稳定性。

## 3. 技术栈

### 前端

- Vue 3
- Vite
- Element Plus
- ECharts
- Axios

### 后端

- Python
- Flask
- Flask-CORS
- Flask-SQLAlchemy
- SQLAlchemy
- PyMySQL
- PyArrow
- python-dotenv

### 数据库

- MySQL
- SQLAlchemy ORM
- 聚合统计表

### 开发工具

- VS Code
- DataGrip
- PowerShell / Terminal
- Chrome / Edge 浏览器

## 4. 功能模块

### 运营概览

运营概览页展示当前筛选日期范围内的订单规模、成交金额、平均客单价、平均行程距离、平均行程时长和异常行程数量等核心指标，适合快速了解整体运营状态。

### 日期范围筛选

前端提供日期范围选择器和快捷筛选按钮，支持按指定时间窗口查询看板数据。筛选条件会传递给后端 `/api/taxi-analysis/*` 分析接口。

### KPI 指标卡片

使用指标卡片展示总订单数、总成交金额、平均客单价、平均行程距离、平均行程时长和异常行程数，便于快速阅读核心运营数据。

### 每日行程趋势

基于 `taxi_daily_stats` 展示每日行程数量和成交金额变化，帮助观察订单规模和收入趋势。

### 分布分析

分布分析模块展示支付方式、每小时高峰、乘客数和距离区间等结构化统计结果，帮助分析订单组成。

### 支付方式占比

基于 `taxi_payment_stats` 统计不同支付类型的行程数量，并使用图表展示占比结构。

### 每小时高峰分析

基于 `taxi_hourly_stats` 展示 0-23 点订单数量分布，用于识别一天内的出行高峰时段。

### 乘客数分布

基于 `taxi_passenger_stats` 统计不同乘客数量对应的行程数量，观察单人出行和多人同行的结构差异。

### 距离区间分布

基于 `taxi_distance_stats` 将行程距离划分为 `0-1`、`1-3`、`3-5`、`5-10`、`10-20`、`20+` 等区间，并统计各区间订单量。

### 区域热点分析

区域热点页展示上车区域 Top10 和下车区域 Top10。系统通过 `taxi_pickup_location_stats` 和 `taxi_dropoff_location_stats` 聚合区域数据，并结合 `taxi_zones` 中的行政区、区域名称和服务区域展示热点区域。

### 异常行程识别

系统在 CSV 或 Parquet 行程数据导入过程中根据规则识别异常行程，并记录异常原因。当前异常判断包括：金额为负、距离小于等于 0、乘客数小于等于 0、上车时间晚于或等于下车时间、行程时长异常、行程距离过大等。

### 聚合统计刷新

系统支持通过命令行脚本 `backend/rebuild_taxi_stats.py` 刷新聚合统计数据，也支持通过前端运营概览页触发聚合统计刷新接口。刷新后看板会读取最新统计结果。

### 行程记录管理

行程记录管理页支持行程明细分页查询、条件筛选、CSV 导入、CSV 导出和异常原因查看。筛选条件包括行程编号、支付方式、乘客数、上下车地点、日期范围、距离范围、金额范围和异常状态。

## 5. 系统页面展示

> 以下为项目截图预留位置。当前仓库中如尚未创建 `docs/images` 目录，可后续手动添加截图文件，不需要影响项目运行。

### 运营概览

![运营概览](docs/images/overview.png)

### 分布分析

![分布分析](docs/images/distribution.png)

### 区域热点分析

![区域热点分析](docs/images/region-analysis.png)

## 6. 数据库设计

系统后端使用 Flask-SQLAlchemy 定义数据模型，启动时会在应用上下文中执行 `db.create_all()` 创建当前模型对应的数据表。数据库连接配置位于 `backend/app/config.py`，当前默认连接 MySQL 数据库 `order_ops_db`。

### 明细表

- `orders`：核心订单明细表，用于保存通用订单编号、用户、城市、起终点、订单金额、订单状态、支付方式和下单时间等信息。当前后端仍注册了 `/api/orders` 和 `/api/analysis` 相关接口。
- `taxi_trips`：出租车行程订单事实表，是当前行程记录管理和出租车运营分析看板的主要明细数据来源。表中包含供应商编号、上车时间、下车时间、乘客数量、行程距离、上下车地点编号、支付方式、车费、小费、总金额、行程时长、异常标记和异常原因等字段。
- `taxi_zones`：地点区域维度表，用于保存 TLC LocationID 对应的行政区、区域名称和服务区域。`taxi_trips` 中的上车地点编号和下车地点编号会关联到该区域信息。

### 聚合统计表

- `taxi_daily_stats`：用于每日趋势统计，保存每日订单量、正常行程数、异常行程数、成交金额、车费、小费、总距离、总时长、平均客单价、平均距离、平均时长和小费率。
- `taxi_hourly_stats`：用于小时分布统计，保存每日每小时行程数量。
- `taxi_payment_stats`：用于支付方式分布统计，保存不同支付方式对应的行程数量。
- `taxi_passenger_stats`：用于乘客数分布统计，保存不同乘客数量对应的行程数量。
- `taxi_distance_stats`：用于距离区间分布统计，保存不同距离区间的行程数量。
- `taxi_pickup_location_stats`：用于上车热点区域 Top10 分析，保存上车地点维度的行程数量。
- `taxi_dropoff_location_stats`：用于下车热点区域 Top10 分析，保存下车地点维度的行程数量。
- `taxi_stats_meta`：用于记录聚合统计刷新状态、最后刷新时间和提示信息。

说明：`orders` 是系统中的通用订单明细表；当前出租车行程记录管理和运营分析看板主要围绕 `taxi_trips` 展开，并通过多张 `taxi_*_stats` 聚合统计表提高查询效率。

## 7. E-R 图说明

本系统以行程订单为核心实体，供应商、支付方式、地点区域、时间维度等实体围绕订单展开。

一个供应商可以对应多条订单；一种支付方式可以对应多条订单；一个地点区域可以作为多条订单的上车地点或下车地点；一个时间维度可以对应多条订单。

在当前代码实现中，`taxi_trips` 是行程订单事实表，`taxi_zones` 是已落地的地点区域维度表。供应商、支付方式和时间维度目前主要以行程表字段及聚合统计口径体现，适合在课程报告中作为逻辑维度说明。

```mermaid
erDiagram
    VENDOR ||--o{ TRIP_ORDER : provides
    PAYMENT_METHOD ||--o{ TRIP_ORDER : used_by
    TIME_DIM ||--o{ TRIP_ORDER : occurs_at
    TAXI_ZONE ||--o{ TRIP_ORDER : pickup_zone
    TAXI_ZONE ||--o{ TRIP_ORDER : dropoff_zone

    VENDOR {
        int vendor_id PK
        string vendor_name
    }

    PAYMENT_METHOD {
        int payment_type PK
        string payment_name
    }

    TAXI_ZONE {
        int location_id PK
        string borough
        string zone
        string service_zone
    }

    TIME_DIM {
        int time_id PK
        date date
        int year
        int month
        int day
        int hour
        string weekday
    }

    TRIP_ORDER {
        int trip_id PK
        string trip_no
        int vendor_id FK
        int payment_type FK
        int pickup_location_id FK
        int dropoff_location_id FK
        int time_id FK
        datetime pickup_time
        datetime dropoff_time
        int passenger_count
        decimal trip_distance
        decimal fare_amount
        decimal tip_amount
        decimal total_amount
        decimal trip_duration_min
        boolean is_abnormal
    }
```

## 8. 关系模型

供应商（供应商编号，供应商名称）

支付方式（支付方式编号，支付方式名称）

地点区域（地点编号，行政区，区域名称，服务区域）

时间维度（时间编号，日期，年份，月份，日期号，小时，星期）

行程订单（订单编号，供应商编号，支付方式编号，上车地点编号，下车地点编号，时间编号，上车时间，下车时间，乘客数量，行程距离，车费金额，小费金额，总金额，行程时长，是否异常）

外键关系说明：

- 行程订单.供应商编号 → 供应商.供应商编号
- 行程订单.支付方式编号 → 支付方式.支付方式编号
- 行程订单.上车地点编号 → 地点区域.地点编号
- 行程订单.下车地点编号 → 地点区域.地点编号
- 行程订单.时间编号 → 时间维度.时间编号

当前数据库物理实现中，地点区域维度已通过 `taxi_zones.location_id` 与 `taxi_trips.pickup_location_id`、`taxi_trips.dropoff_location_id` 建立查询关联；供应商、支付方式和时间维度以 `taxi_trips` 字段和聚合统计结果体现。

## 9. 聚合统计设计

系统引入聚合统计表的原因：

- 原始订单和行程明细数据量较大，直接扫描明细表成本较高。
- 看板需要频繁按日期范围统计订单量、成交金额、支付方式、小时分布、乘客数、距离区间和区域热点。
- 如果每次查询都对明细表做实时 `GROUP BY`，接口响应速度会随着数据量增长而下降。
- 使用聚合统计表可以将高频统计结果预先计算，减少重复计算，提高看板响应速度。

`backend/rebuild_taxi_stats.py` 用于重新生成或刷新出租车订单相关聚合统计数据。该脚本会创建 Flask 应用上下文，确保数据库表存在，然后调用 `app/services/taxi_stats_service.py` 中的 `rebuild_taxi_stats` 方法，将 `taxi_trips` 明细数据聚合写入以下统计表：

- `taxi_daily_stats`
- `taxi_hourly_stats`
- `taxi_payment_stats`
- `taxi_passenger_stats`
- `taxi_distance_stats`
- `taxi_pickup_location_stats`
- `taxi_dropoff_location_stats`

脚本支持全量刷新，也支持按日期范围刷新：

```bash
python rebuild_taxi_stats.py
python rebuild_taxi_stats.py --start-date 2025-01-01 --end-date 2025-01-31
```

## 10. 项目结构

以下结构基于当前项目目录整理，已排除 `node_modules`、`.venv`、`dist`、`__pycache__` 等本地依赖、构建产物和缓存目录。

```text
order-ops-dashboard/
  .gitignore
  PRODUCT.md
  PROJECT_STRUCTURE.md
  README.md
  backend/
    requirements.txt
    run.py
    rebuild_taxi_stats.py
    app/
      __init__.py
      config.py
      extensions.py
      models/
        order.py
        taxi_stats.py
        taxi_trip.py
        taxi_zone.py
      routes/
        analysis_routes.py
        auth_routes.py
        order_routes.py
        taxi_analysis_routes.py
        taxi_trip_routes.py
      services/
        __init__.py
        taxi_stats_service.py
    data/
      taxi_zone_lookup.csv
      yellow_tripdata_2025-01.parquet
    scripts/
      add_taxi_trip_indexes.sql
      import_taxi_parquet.py
      import_taxi_zones.py
  frontend/
    package.json
    package-lock.json
    vite.config.js
    index.html
    public/
      favicon.svg
      icons.svg
    src/
      App.vue
      main.js
      style.css
      api/
        request.js
      views/
        Login.vue
        TaxiAnalysis.vue
        TaxiOverview.vue
        TaxiTripManage.vue
```

## 11. 本地运行

### 11.1 数据库准备

后端当前使用 MySQL，数据库连接配置在 `backend/app/config.py`：

```text
mysql+pymysql://root:123456@127.0.0.1:3306/order_ops_db?charset=utf8mb4
```

运行前请确保本地 MySQL 已启动，并已创建数据库：

```sql
CREATE DATABASE order_ops_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

后端启动时会执行 `db.create_all()` 创建模型中定义的数据表。

### 11.2 后端启动

进入后端目录：

```bash
cd backend
```

创建并激活虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

启动后端服务：

```bash
python run.py
```

后端默认运行地址：

```text
http://127.0.0.1:5000
```

### 11.3 数据导入与统计刷新

导入地点区域维度数据：

```bash
python scripts/import_taxi_zones.py
```

导入 Parquet 行程数据：

```bash
python scripts/import_taxi_parquet.py data/yellow_tripdata_2025-01.parquet --batch-size 5000
```

刷新聚合统计数据：

```bash
python rebuild_taxi_stats.py
```

如只刷新指定日期范围：

```bash
python rebuild_taxi_stats.py --start-date 2025-01-01 --end-date 2025-01-31
```

数据库索引脚本位于：

```text
backend/scripts/add_taxi_trip_indexes.sql
```

该脚本用于为 `taxi_trips` 增加距离、时间、支付方式、乘客数和上下车区域相关索引。由于模型中已定义部分索引，执行前建议先在数据库中确认当前索引情况。

### 11.4 前端启动

前端脚本来自 `frontend/package.json`：

```json
{
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview"
}
```

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run dev
```

构建生产环境资源：

```bash
npm run build
```

本地预览构建结果：

```bash
npm run preview
```

前端请求地址配置在 `frontend/src/api/request.js`，当前默认请求：

```text
http://127.0.0.1:5000
```

### 11.5 登录说明

演示账号配置在 `backend/app/config.py`：

```text
用户名：admin
密码：123456
```

登录成功后，前端会将后端返回的 token 保存到浏览器本地存储，并在后续接口请求中通过 `Authorization: Bearer <token>` 发送给后端。

## 12. 常见问题

### ModuleNotFoundError: No module named 'flask'

原因：后端依赖未安装，或当前终端没有进入 Python 虚拟环境。

解决方式：

```bash
cd backend
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

### 'vite' 不是内部或外部命令

原因：前端依赖尚未安装，`node_modules` 中不存在 Vite 命令。

解决方式：

```bash
cd frontend
npm install
npm run dev
```

### 前端请求 127.0.0.1:5000 报 ERR_CONNECTION_REFUSED

原因：后端服务未启动、后端端口不是 5000，或前端请求地址与后端配置不一致。

解决方式：

- 确认已在 `backend` 目录执行 `python run.py`。
- 确认后端输出地址为 `http://127.0.0.1:5000`。
- 确认 `frontend/src/api/request.js` 中的 `baseURL` 与后端地址一致。

### DataGrip 中看不到表

原因：数据库连接的 schema 未刷新，或后端尚未成功创建表。

解决方式：

```sql
SHOW TABLES;
```

如果 SQL 能看到表但 DataGrip 左侧没有显示，请刷新 DataGrip 的 schema；如果 SQL 也看不到表，请确认 MySQL 数据库名、连接配置和后端启动日志。

## 13. 项目亮点

- 面向百万级出行订单数据分析场景，支持 Parquet 批量导入和 CSV 明细导入。
- 使用聚合统计表承载看板高频查询，减少对明细表的重复统计计算。
- 使用 Vue 3 + Element Plus + ECharts 构建可视化数据看板。
- 支持订单规模、成交金额、客单价、行程效率、支付方式、乘客数、距离区间、小时分布和区域热点等多维度运营分析。
- 支持异常行程识别，并在行程记录管理中展示异常原因。
- 支持上车区域和下车区域 Top10 热点分析。
- 前后端分离结构清晰，后端按 models、routes、services 分层组织，前端按 api、views 组织页面和请求逻辑。



