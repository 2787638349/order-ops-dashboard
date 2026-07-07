<template>
  <div class="dashboard-page">
    <section class="page-hero">
      <div>
        <div class="eyebrow">NYC Yellow Taxi Analytics</div>
        <h1>出租车数据看板</h1>
        <p>当前统计范围：{{ activeDateRange[0] }} 至 {{ activeDateRange[1] }}</p>
      </div>

      <div class="date-tools">
        <el-date-picker
          v-model="selectedDateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          class="date-picker"
        />
        <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">查询</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
      </div>
    </section>

    <el-row :gutter="14" class="kpi-row">
      <el-col v-for="item in kpiCards" :key="item.key" :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="kpi-card" shadow="never">
          <div class="kpi-icon" :class="item.tone">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <div class="kpi-content">
            <div class="kpi-title">{{ item.title }}</div>
            <div class="kpi-value">{{ item.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="chart-row">
      <el-col :xs="24" :lg="14">
        <ChartCard title="每日行程趋势">
          <div ref="dailyTrendChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
      <el-col :xs="24" :lg="10">
        <ChartCard title="每小时高峰分析">
          <div ref="hourlyChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="chart-row">
      <el-col :xs="24" :lg="8">
        <ChartCard title="支付方式占比">
          <div ref="paymentChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
      <el-col :xs="24" :lg="8">
        <ChartCard title="乘客数分布">
          <div ref="passengerChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
      <el-col :xs="24" :lg="8">
        <ChartCard title="距离区间分布">
          <div ref="distanceChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="chart-row">
      <el-col :xs="24" :lg="12">
        <ChartCard title="上车区域 Top 10">
          <div ref="pickupChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
      <el-col :xs="24" :lg="12">
        <ChartCard title="下车区域 Top 10">
          <div ref="dropoffChartRef" class="chart"></div>
        </ChartCard>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  Coin,
  DataAnalysis,
  Money,
  Odometer,
  Refresh,
  Search,
  Timer,
  TrendCharts,
  WarningFilled,
} from "@element-plus/icons-vue";
import * as echarts from "echarts";
import request from "../api/request";

const DEFAULT_DATE_RANGE = ["2025-01-01", "2025-01-31"];
const chartColors = ["#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#0f766e", "#ef4444"];

const ChartCard = defineComponent({
  props: {
    title: {
      type: String,
      required: true,
    },
  },
  setup(props, { slots }) {
    return () =>
      h("section", { class: "chart-card" }, [
        h("div", { class: "chart-card-header" }, [
          h("span", { class: "chart-title-dot" }),
          h("h3", props.title),
        ]),
        slots.default?.(),
      ]);
  },
});

const loading = ref(false);
const selectedDateRange = ref([...DEFAULT_DATE_RANGE]);
const activeDateRange = ref([...DEFAULT_DATE_RANGE]);

const summary = reactive({
  totalTrips: 0,
  normalTrips: 0,
  abnormalTrips: 0,
  totalAmount: 0,
  avgAmount: 0,
  avgDistance: 0,
  avgDuration: 0,
  tipRate: 0,
});

const dailyTrendChartRef = ref(null);
const hourlyChartRef = ref(null);
const paymentChartRef = ref(null);
const passengerChartRef = ref(null);
const pickupChartRef = ref(null);
const dropoffChartRef = ref(null);
const distanceChartRef = ref(null);
const charts = {};

const formatNumber = (value) => Number(value || 0).toLocaleString();
const formatMoney = (value) => Number(value || 0).toFixed(2);

const kpiCards = computed(() => [
  {
    key: "totalTrips",
    title: "总行程数",
    value: formatNumber(summary.totalTrips),
    icon: DataAnalysis,
    tone: "blue",
  },
  {
    key: "totalAmount",
    title: "总成交金额",
    value: `$${formatMoney(summary.totalAmount)}`,
    icon: Money,
    tone: "green",
  },
  {
    key: "avgAmount",
    title: "平均客单价",
    value: `$${formatMoney(summary.avgAmount)}`,
    icon: Coin,
    tone: "orange",
  },
  {
    key: "avgDistance",
    title: "平均行程距离",
    value: `${formatMoney(summary.avgDistance)} mi`,
    icon: Odometer,
    tone: "purple",
  },
  {
    key: "avgDuration",
    title: "平均行程时长",
    value: `${formatMoney(summary.avgDuration)} min`,
    icon: Timer,
    tone: "teal",
  },
  {
    key: "tipRate",
    title: "小费率",
    value: `${formatMoney(summary.tipRate)}%`,
    icon: TrendCharts,
    tone: "blue",
  },
  {
    key: "abnormalTrips",
    title: "异常行程数",
    value: formatNumber(summary.abnormalTrips),
    icon: WarningFilled,
    tone: "red",
  },
]);

const analysisParams = () => ({
  startDate: activeDateRange.value[0],
  endDate: activeDateRange.value[1],
});

const getChart = (key, targetRef) => {
  if (!charts[key]) {
    charts[key] = echarts.init(targetRef.value);
  }
  return charts[key];
};

const hasValues = (values) => values.some((value) => Number(value || 0) > 0);

const emptyTitle = (show, text = "暂无数据") => ({
  show,
  text,
  left: "center",
  top: "45%",
  textStyle: {
    color: "#94a3b8",
    fontSize: 14,
    fontWeight: 500,
  },
});

const baseGrid = {
  left: 42,
  right: 18,
  bottom: 40,
  top: 34,
  containLabel: true,
};

const loadSummary = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/summary", {
      params: analysisParams(),
    });
    if (res.code === 200) {
      Object.assign(summary, res.data);
    }
  } catch (error) {
    ElMessage.error("KPI 数据加载失败");
  }
};

const loadDailyTrend = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/daily-trend", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const dates = res.data.map((item) => item.date);
    const tripCounts = res.data.map((item) => item.tripCount);
    const amounts = res.data.map((item) => item.totalAmount);
    const chart = getChart("dailyTrend", dailyTrendChartRef);

    chart.setOption({
      color: [chartColors[0], chartColors[1]],
      title: emptyTitle(!hasValues(tripCounts) && !hasValues(amounts)),
      tooltip: { trigger: "axis", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      legend: { data: ["行程数", "成交金额"], top: 0, itemWidth: 12, itemHeight: 8 },
      grid: { ...baseGrid, top: 48 },
      xAxis: { type: "category", data: dates, axisLabel: { rotate: 36, color: "#64748b" } },
      yAxis: [
        { type: "value", name: "行程数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "#edf2f7" } } },
        { type: "value", name: "金额", axisLabel: { color: "#64748b" }, splitLine: { show: false } },
      ],
      series: [
        { name: "行程数", type: "line", smooth: true, symbolSize: 6, data: tripCounts },
        { name: "成交金额", type: "line", smooth: true, symbolSize: 6, yAxisIndex: 1, data: amounts },
      ],
    }, true);
  } catch (error) {
    ElMessage.error("每日趋势加载失败");
  }
};

const loadHourlyDistribution = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/hourly-distribution", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const values = res.data.map((item) => item.tripCount);
    const chart = getChart("hourly", hourlyChartRef);

    chart.setOption({
      color: [chartColors[0]],
      title: emptyTitle(!hasValues(values)),
      tooltip: { trigger: "axis", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      grid: baseGrid,
      xAxis: { type: "category", data: res.data.map((item) => `${item.hour}:00`), axisLabel: { color: "#64748b" } },
      yAxis: { type: "value", name: "行程数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "#edf2f7" } } },
      series: [{ name: "行程数", type: "bar", barWidth: "52%", data: values, itemStyle: { borderRadius: [5, 5, 0, 0] } }],
    }, true);
  } catch (error) {
    ElMessage.error("小时分布加载失败");
  }
};

const loadPaymentDistribution = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/payment-distribution", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const values = res.data.map((item) => item.tripCount);
    const chart = getChart("payment", paymentChartRef);

    chart.setOption({
      color: chartColors,
      title: emptyTitle(!hasValues(values)),
      tooltip: { trigger: "item", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      legend: { bottom: 0, itemWidth: 12, itemHeight: 8 },
      series: [
        {
          name: "支付方式",
          type: "pie",
          radius: ["42%", "68%"],
          center: ["50%", "43%"],
          label: { formatter: "{b}: {d}%" },
          data: res.data.map((item) => ({ name: item.paymentName, value: item.tripCount })),
        },
      ],
    }, true);
  } catch (error) {
    ElMessage.error("支付方式加载失败");
  }
};

const loadPassengerDistribution = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/passenger-distribution", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const values = res.data.map((item) => item.tripCount);
    const chart = getChart("passenger", passengerChartRef);

    chart.setOption({
      color: [chartColors[1]],
      title: emptyTitle(!hasValues(values)),
      tooltip: { trigger: "axis", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      grid: baseGrid,
      xAxis: { type: "category", data: res.data.map((item) => `${item.passengerCount}人`), axisLabel: { color: "#64748b" } },
      yAxis: { type: "value", name: "行程数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "#edf2f7" } } },
      series: [{ name: "行程数", type: "bar", barWidth: "46%", data: values, itemStyle: { borderRadius: [5, 5, 0, 0] } }],
    }, true);
  } catch (error) {
    ElMessage.error("乘客分布加载失败");
  }
};

const loadPickupLocationTop = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/pickup-location-top", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const values = res.data.map((item) => item.tripCount);
    const chart = getChart("pickup", pickupChartRef);

    chart.setOption({
      color: [chartColors[4]],
      title: emptyTitle(!hasValues(values)),
      tooltip: { trigger: "axis", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      grid: { ...baseGrid, bottom: 72 },
      xAxis: {
        type: "category",
        data: res.data.map((item) => item.pickupLocationName || item.pickupLocationId),
        axisLabel: { rotate: 32, width: 92, overflow: "truncate", color: "#64748b" },
      },
      yAxis: { type: "value", name: "行程数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "#edf2f7" } } },
      series: [{ name: "行程数", type: "bar", barWidth: "48%", data: values, itemStyle: { borderRadius: [5, 5, 0, 0] } }],
    }, true);
  } catch (error) {
    ElMessage.error("上车区域加载失败");
  }
};

const loadDropoffLocationTop = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/dropoff-location-top", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const values = res.data.map((item) => item.tripCount);
    const chart = getChart("dropoff", dropoffChartRef);

    chart.setOption({
      color: [chartColors[2]],
      title: emptyTitle(!hasValues(values)),
      tooltip: { trigger: "axis", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      grid: { ...baseGrid, bottom: 72 },
      xAxis: {
        type: "category",
        data: res.data.map((item) => item.dropoffLocationName || item.dropoffLocationId),
        axisLabel: { rotate: 32, width: 92, overflow: "truncate", color: "#64748b" },
      },
      yAxis: { type: "value", name: "行程数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "#edf2f7" } } },
      series: [{ name: "行程数", type: "bar", barWidth: "48%", data: values, itemStyle: { borderRadius: [5, 5, 0, 0] } }],
    }, true);
  } catch (error) {
    ElMessage.error("下车区域加载失败");
  }
};

const loadDistanceDistribution = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/distance-distribution", {
      params: analysisParams(),
    });
    if (res.code !== 200) return;

    const values = res.data.map((item) => item.tripCount);
    const chart = getChart("distance", distanceChartRef);

    chart.setOption({
      color: [chartColors[3]],
      title: emptyTitle(!hasValues(values)),
      tooltip: { trigger: "axis", backgroundColor: "#ffffff", borderColor: "#dbe4f0", textStyle: { color: "#172033" } },
      grid: baseGrid,
      xAxis: { type: "category", data: res.data.map((item) => item.range), axisLabel: { color: "#64748b" } },
      yAxis: { type: "value", name: "行程数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "#edf2f7" } } },
      series: [{ name: "行程数", type: "bar", barWidth: "46%", data: values, itemStyle: { borderRadius: [5, 5, 0, 0] } }],
    }, true);
  } catch (error) {
    ElMessage.error("距离分布加载失败");
  }
};

const loadDashboard = async () => {
  loading.value = true;
  try {
    await loadSummary();
    await nextTick();
    await Promise.allSettled([
      loadDailyTrend(),
      loadHourlyDistribution(),
      loadPaymentDistribution(),
      loadPassengerDistribution(),
      loadPickupLocationTop(),
      loadDropoffLocationTop(),
      loadDistanceDistribution(),
    ]);
  } finally {
    loading.value = false;
  }
};

const handleSearch = async () => {
  if (!selectedDateRange.value || selectedDateRange.value.length !== 2) {
    ElMessage.warning("请选择日期范围");
    return;
  }

  activeDateRange.value = [...selectedDateRange.value];
  await loadDashboard();
};

const handleReset = async () => {
  selectedDateRange.value = [...DEFAULT_DATE_RANGE];
  activeDateRange.value = [...DEFAULT_DATE_RANGE];
  await loadDashboard();
};

const resizeCharts = () => {
  Object.values(charts).forEach((chart) => chart.resize());
};

onMounted(async () => {
  await loadDashboard();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  Object.values(charts).forEach((chart) => chart.dispose());
});
</script>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 56px);
  background: #f4f7fb;
  padding: 16px 20px 22px;
  box-sizing: border-box;
}

.page-hero {
  background: #ffffff;
  border: 1px solid #e5eaf3;
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 14px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  margin-bottom: 6px;
}

.page-hero h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.25;
  color: #172033;
}

.page-hero p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 13px;
}

.date-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.date-picker {
  width: 280px;
}

.kpi-row,
.chart-row {
  row-gap: 14px;
}

.chart-row {
  margin-top: 14px;
}

.kpi-card {
  border: 1px solid #e5eaf3;
  border-radius: 14px;
  height: 104px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
}

.kpi-card :deep(.el-card__body) {
  height: 100%;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.kpi-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
}

.kpi-icon.blue {
  color: #2563eb;
  background: #eaf2ff;
}

.kpi-icon.green {
  color: #16a34a;
  background: #eaf8ef;
}

.kpi-icon.orange {
  color: #d97706;
  background: #fff4df;
}

.kpi-icon.purple {
  color: #7c3aed;
  background: #f1eaff;
}

.kpi-icon.teal {
  color: #0f766e;
  background: #e7f6f3;
}

.kpi-icon.red {
  color: #dc2626;
  background: #feecec;
}

.kpi-content {
  min-width: 0;
}

.kpi-title {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 21px;
  line-height: 1.2;
  font-weight: 760;
  color: #172033;
  word-break: break-word;
}

.dashboard-page :deep(.chart-card) {
  background: #ffffff;
  border: 1px solid #e5eaf3;
  border-radius: 14px;
  padding: 14px 14px 10px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
}

.dashboard-page :deep(.chart-card-header) {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.dashboard-page :deep(.chart-title-dot) {
  width: 4px;
  height: 16px;
  border-radius: 999px;
  background: #2563eb;
}

.dashboard-page :deep(.chart-card h3) {
  margin: 0;
  color: #172033;
  font-size: 16px;
  line-height: 1.3;
  font-weight: 720;
}

.chart {
  width: 100%;
  height: 316px;
}

@media (max-width: 980px) {
  .page-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .date-tools {
    justify-content: flex-start;
    width: 100%;
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 12px;
  }

  .date-picker {
    width: 100%;
  }

  .chart {
    height: 288px;
  }
}
</style>
