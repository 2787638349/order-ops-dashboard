<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div>
        <h1>订单运营分析后台</h1>
        <p>基于订单数据的运营指标统计与可视化分析</p>
      </div>
    </div>

    <el-row :gutter="20" class="kpi-row">
      <el-col :span="5">
        <el-card class="kpi-card">
          <div class="kpi-title">总订单量</div>
          <div class="kpi-value">{{ summary.totalOrders }}</div>
          <div class="kpi-desc">全部订单数量</div>
        </el-card>
      </el-col>

      <el-col :span="5">
        <el-card class="kpi-card">
          <div class="kpi-title">已完成订单</div>
          <div class="kpi-value">{{ summary.completedOrders }}</div>
          <div class="kpi-desc">已完成订单数量</div>
        </el-card>
      </el-col>

      <el-col :span="5">
        <el-card class="kpi-card">
          <div class="kpi-title">成交金额</div>
          <div class="kpi-value">¥{{ summary.totalAmount }}</div>
          <div class="kpi-desc">仅统计已完成订单</div>
        </el-card>
      </el-col>

      <el-col :span="5">
        <el-card class="kpi-card">
          <div class="kpi-title">客单价</div>
          <div class="kpi-value">¥{{ summary.avgAmount }}</div>
          <div class="kpi-desc">成交金额 / 已完成订单</div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card class="kpi-card">
          <div class="kpi-title">完成率</div>
          <div class="kpi-value">{{ summary.completionRate }}%</div>
          <div class="kpi-desc">已完成订单 / 总订单</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="14">
        <el-card class="chart-card">
          <div class="chart-title">每日订单趋势</div>
          <div ref="dailyTrendChartRef" class="chart"></div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="chart-card">
          <div class="chart-title">城市订单分布</div>
          <div ref="cityChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="14">
        <el-card class="chart-card">
          <div class="chart-title">高峰时段分析</div>
          <div ref="hourlyChartRef" class="chart"></div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="chart-card">
          <div class="chart-title">订单状态占比</div>
          <div ref="statusChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import * as echarts from "echarts";
import request from "../api/request";

const summary = reactive({
  totalOrders: 0,
  completedOrders: 0,
  totalAmount: 0,
  avgAmount: 0,
  completionRate: 0,
});

const dailyTrendChartRef = ref(null);
const cityChartRef = ref(null);
const hourlyChartRef = ref(null);
const statusChartRef = ref(null);

let dailyTrendChart = null;
let cityChart = null;
let hourlyChart = null;
let statusChart = null;

const loadSummary = async () => {
  try {
    const res = await request.get("/api/analysis/summary");

    if (res.code === 200) {
      Object.assign(summary, res.data);
    } else {
      ElMessage.error(res.message || "获取汇总数据失败");
    }
  } catch (error) {
    ElMessage.error("后端服务连接失败");
  }
};

const loadDailyTrend = async () => {
  try {
    const res = await request.get("/api/analysis/daily-trend");

    if (res.code !== 200) {
      ElMessage.error(res.message || "获取每日趋势数据失败");
      return;
    }

    const dates = res.data.map((item) => item.date);
    const orderCounts = res.data.map((item) => item.orderCount);
    const amounts = res.data.map((item) => item.amount);

    dailyTrendChart = echarts.init(dailyTrendChartRef.value);

    dailyTrendChart.setOption({
      tooltip: {
        trigger: "axis",
      },
      legend: {
        data: ["订单量", "成交金额"],
        top: 0,
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "5%",
        top: "15%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: dates,
        axisLabel: {
          rotate: 45,
        },
      },
      yAxis: [
        {
          type: "value",
          name: "订单量",
        },
        {
          type: "value",
          name: "金额",
        },
      ],
      series: [
        {
          name: "订单量",
          type: "line",
          smooth: true,
          data: orderCounts,
        },
        {
          name: "成交金额",
          type: "line",
          smooth: true,
          yAxisIndex: 1,
          data: amounts,
        },
      ],
    });
  } catch (error) {
    ElMessage.error("每日趋势接口请求失败");
  }
};

const loadCityDistribution = async () => {
  try {
    const res = await request.get("/api/analysis/city-distribution");

    if (res.code !== 200) {
      ElMessage.error(res.message || "获取城市分布数据失败");
      return;
    }

    const cities = res.data.map((item) => item.city);
    const orderCounts = res.data.map((item) => item.orderCount);

    cityChart = echarts.init(cityChartRef.value);

    cityChart.setOption({
      tooltip: {
        trigger: "axis",
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "5%",
        top: "12%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: cities,
      },
      yAxis: {
        type: "value",
        name: "订单量",
      },
      series: [
        {
          name: "订单量",
          type: "bar",
          data: orderCounts,
          barWidth: "45%",
        },
      ],
    });
  } catch (error) {
    ElMessage.error("城市分布接口请求失败");
  }
};

const loadHourlyDistribution = async () => {
  try {
    const res = await request.get("/api/analysis/hourly-distribution");

    if (res.code !== 200) {
      ElMessage.error(res.message || "获取高峰时段数据失败");
      return;
    }

    const hours = res.data.map((item) => `${item.hour}:00`);
    const orderCounts = res.data.map((item) => item.orderCount);

    hourlyChart = echarts.init(hourlyChartRef.value);

    hourlyChart.setOption({
      tooltip: {
        trigger: "axis",
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "5%",
        top: "12%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: hours,
      },
      yAxis: {
        type: "value",
        name: "订单量",
      },
      series: [
        {
          name: "订单量",
          type: "bar",
          data: orderCounts,
          barWidth: "45%",
        },
      ],
    });
  } catch (error) {
    ElMessage.error("高峰时段接口请求失败");
  }
};


const loadStatusDistribution = async () => {
  try {
    const res = await request.get("/api/analysis/status-distribution");

    if (res.code !== 200) {
      ElMessage.error(res.message || "获取订单状态数据失败");
      return;
    }

    const pieData = res.data.map((item) => {
      return {
        name: item.statusName,
        value: item.orderCount,
      };
    });

    statusChart = echarts.init(statusChartRef.value);

    statusChart.setOption({
      tooltip: {
        trigger: "item",
      },
      legend: {
        bottom: 0,
      },
      series: [
        {
          name: "订单状态",
          type: "pie",
          radius: ["45%", "70%"],
          center: ["50%", "45%"],
          avoidLabelOverlap: true,
          label: {
            formatter: "{b}: {d}%",
          },
          data: pieData,
        },
      ],
    });
  } catch (error) {
    ElMessage.error("订单状态接口请求失败");
  }
};

const resizeCharts = () => {
  dailyTrendChart?.resize();
  cityChart?.resize();
  hourlyChart?.resize();
  statusChart?.resize();
};

onMounted(async () => {
  await loadSummary();

  await nextTick();

  await loadDailyTrend();
  await loadCityDistribution();
  await loadHourlyDistribution();
  await loadStatusDistribution();

  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);

  dailyTrendChart?.dispose();
  cityChart?.dispose();
  hourlyChart?.dispose();
  statusChart?.dispose();
});
</script>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding: 16px 20px;
  box-sizing: border-box;
}

.page-header {
  background: linear-gradient(135deg, #2f6bff, #1e40af);
  color: white;
  padding: 22px 28px;
  border-radius: 12px;
  margin-bottom: 18px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.page-header p {
  margin: 8px 0 0;
  font-size: 14px;
  opacity: 0.9;
}

.kpi-row {
  margin-top: 14px;
}

.kpi-card {
  border-radius: 12px;
  min-height: 112px;
}

.kpi-card :deep(.el-card__body) {
  padding: 18px 20px;
}

.kpi-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 10px;
}

.kpi-desc {
  font-size: 12px;
  color: #909399;
}

.chart-row {
  margin-top: 18px;
}

.chart-card {
  border-radius: 12px;
}

.chart-card :deep(.el-card__body) {
  padding: 18px 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12px;
}

.chart {
  width: 100%;
  height: 300px;
}
</style>