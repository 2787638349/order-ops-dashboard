<template>
  <div class="overview-page">
    <section class="overview-header">
      <div class="header-copy">
        <div class="title-row">
          <div class="title-mark">
            <el-icon><Van /></el-icon>
          </div>
          <div>
            <h1>行程记录管理</h1>
            <p>聚合查看订单规模、客单价、行程效率、异常识别与分布分析。</p>
          </div>
        </div>
        <div class="header-meta">
          <span>当前范围：{{ activeDateRange[0] }} 至 {{ activeDateRange[1] }}</span>
          <span>异常占比：{{ abnormalRate }}</span>
          <span>{{ statsRefreshing ? "聚合统计刷新中" : "聚合统计已就绪" }}</span>
        </div>
      </div>

      <div class="filter-panel">
        <el-date-picker
          v-model="selectedDateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          class="date-picker"
        />
        <el-button-group class="quick-range-group">
          <el-button
            v-for="item in quickRanges"
            :key="item.label"
            :type="isActiveQuickRange(item.range) ? 'primary' : 'default'"
            @click="handleQuickRange(item)"
          >
            {{ item.label }}
          </el-button>
        </el-button-group>
        <div class="action-group">
          <el-button type="primary" :icon="Search" :loading="summaryLoading" @click="handleSearch">
            查询
          </el-button>
          <el-button class="refresh-stats-button" :icon="Refresh" :loading="statsRefreshing" @click="handleRefreshStats">
            刷新聚合统计
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </div>
      </div>
    </section>

    <el-alert
      v-if="pageNotice"
      class="page-alert"
      :title="pageNotice"
      type="warning"
      show-icon
      :closable="true"
      @close="pageNotice = ''"
    />

    <div class="overview-tabs" role="tablist" aria-label="看板视图切换">
      <button
        type="button"
        :class="{ active: activeTab === 'overview' }"
        @click="activeTab = 'overview'"
      >
        运营概览
      </button>
      <button
        type="button"
        :class="{ active: activeTab === 'distribution' }"
        @click="activeTab = 'distribution'"
      >
        分布分析
      </button>
    </div>

    <section v-show="activeTab === 'overview'" class="tab-panel">
      <div v-if="summaryLoading" class="kpi-grid">
        <div v-for="item in 6" :key="item" class="stat-skeleton"></div>
      </div>
      <div v-else class="kpi-grid">
        <StatCard
          v-for="item in kpiCards"
          :key="item.key"
          :title="item.title"
          :meta="item.meta"
          :value="item.value"
          :tone="item.tone"
          :icon="item.icon"
          :spark="item.spark"
        />
      </div>

      <div class="overview-grid">
        <ChartCard
          class="trend-card"
          title="每日行程趋势"
          description="按日期观察行程数与成交金额变化"
          unit="行程 / 金额"
          :state="chartStates.dailyTrend"
          @retry="loadDailyTrend"
        >
          <div ref="dailyTrendChartRef" class="chart trend-chart"></div>
        </ChartCard>

        <section class="insight-card">
          <div class="insight-card-header">
            <h2>异常概览</h2>
            <span :class="{ warning: summary.abnormalTrips > 0 }">
              {{ summary.abnormalTrips > 0 ? "需关注" : "状态正常" }}
            </span>
          </div>
          <div class="insight-number">{{ formatNumber(summary.abnormalTrips) }}</div>
          <p>当前日期范围内识别出的异常行程数量。异常原因可在「行程记录管理」中查看。</p>
          <div class="insight-metrics">
            <div>
              <span>异常占比</span>
              <strong>{{ abnormalRate }}</strong>
            </div>
            <div>
              <span>订单总量</span>
              <strong>{{ formatNumber(summary.totalTrips) }}</strong>
            </div>
          </div>
        </section>
      </div>
    </section>

    <section v-show="activeTab === 'distribution'" class="tab-panel">
      <div class="distribution-grid">
        <ChartCard
          title="每小时高峰分析"
          description="识别一天内订单高峰时段"
          
          :state="chartStates.hourly"
          @retry="loadHourlyDistribution"
        >
          <div ref="hourlyChartRef" class="chart"></div>
        </ChartCard>

        <ChartCard
          title="支付方式占比"
          description="不同支付类型的行程分布"
          
          :state="chartStates.payment"
          @retry="loadPaymentDistribution"
        >
          <div ref="paymentChartRef" class="chart"></div>
        </ChartCard>

        <ChartCard
          title="乘客数分布"
          description="按乘客人数统计行程数量"
          
          :state="chartStates.passenger"
          @retry="loadPassengerDistribution"
        >
          <div ref="passengerChartRef" class="chart"></div>
        </ChartCard>

        <ChartCard
          title="距离区间分布"
          description="按行程距离区间统计订单量"
          
          :state="chartStates.distance"
          @retry="loadDistanceDistribution"
        >
          <div ref="distanceChartRef" class="chart"></div>
        </ChartCard>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { ElButton, ElIcon, ElMessage } from "element-plus";
import { Coin, DataAnalysis, Money, Odometer, Refresh, Search, Timer, Van, WarningFilled } from "@element-plus/icons-vue";
import * as echarts from "echarts";
import request from "../api/request";

const DEFAULT_DATE_RANGE = ["2025-01-26", "2025-02-01"];
const quickRanges = [
  { label: "最近 3 天", range: ["2025-01-30", "2025-02-01"] },
  { label: "最近 7 天", range: ["2025-01-26", "2025-02-01"] },
  { label: "最近 14 天", range: ["2025-01-19", "2025-02-01"] },
  { label: "整月", range: ["2025-01-01", "2025-01-31"], heavy: true },
];

const chartColors = {
  blue: "#1d63d8",
  navy: "#0b2f63",
  cyan: "#0891b2",
  orange: "#f59e0b",
  green: "#16a34a",
  slate: "#64748b",
  red: "#dc2626",
};

const makeGradient = (from, to, vertical = true) => new echarts.graphic.LinearGradient(
  0,
  0,
  vertical ? 0 : 1,
  vertical ? 1 : 0,
  [
    { offset: 0, color: from },
    { offset: 1, color: to },
  ],
);

const StatCard = defineComponent({
  props: {
    title: { type: String, required: true },
    meta: { type: String, required: true },
    value: { type: String, required: true },
    tone: { type: String, required: true },
    icon: { type: [Object, Function], required: true },
    spark: { type: Array, required: true },
  },
  setup(props) {
    return () =>
      h("section", { class: ["stat-card", props.tone] }, [
        h("div", { class: "stat-card-main" }, [
          h("div", { class: "stat-icon" }, [h(ElIcon, null, () => h(props.icon))]),
          h("div", { class: "stat-copy" }, [
            h("span", props.meta),
            h("strong", props.value),
            h("p", props.title),
          ]),
        ]),
        h("div", { class: "stat-spark", "aria-hidden": "true" }, props.spark.map((height, index) =>
          h("i", { key: index, style: { height: `${height}%` } }),
        )),
      ]);
  },
});

const EmptyState = defineComponent({
  setup() {
    return () =>
      h("div", { class: "chart-state empty-state" }, [
        h("strong", "暂无数据"),
        h("p", "当前筛选范围下没有可展示的数据，请调整日期范围后重试。"),
      ]);
  },
});

const ErrorState = defineComponent({
  emits: ["retry"],
  setup(_, { emit }) {
    return () =>
      h("div", { class: "chart-state error-state" }, [
        h("strong", "数据加载失败"),
        h("p", "请稍后重试，或检查后端服务是否正常运行。"),
        h(ElButton, { size: "small", type: "primary", onClick: () => emit("retry") }, () => "重试"),
      ]);
  },
});

const ChartCard = defineComponent({
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
    unit: { type: String, required: true },
    state: { type: Object, required: true },
  },
  emits: ["retry"],
  setup(props, { slots, emit }) {
    return () =>
      h("section", { class: "chart-card" }, [
        h("div", { class: "chart-card-header" }, [
          h("div", null, [
            h("h2", props.title),
            h("p", props.description),
          ]),
          h("span", props.unit),
        ]),
        h("div", { class: "chart-body" }, [
          h("div", { class: ["chart-layer", (props.state.loading || props.state.error || props.state.empty) && "is-muted"] }, slots.default?.()),
          props.state.loading && h("div", { class: "chart-skeleton" }, [h("i"), h("i"), h("i"), h("i")]),
          props.state.error && h(ErrorState, { onRetry: () => emit("retry") }),
          props.state.empty && h(EmptyState),
        ]),
      ]);
  },
});

const activeTab = ref("overview");
const summaryLoading = ref(false);
const statsRefreshing = ref(false);
const statsPollingTimer = ref(null);
const selectedDateRange = ref([...DEFAULT_DATE_RANGE]);
const activeDateRange = ref([...DEFAULT_DATE_RANGE]);
const dailyTripTrend = ref([]);
const dailyAmountTrend = ref([]);
const pageNotice = ref("");
const charts = {};

const summary = reactive({
  totalTrips: 0,
  abnormalTrips: 0,
  totalAmount: 0,
  avgAmount: 0,
  avgDistance: 0,
  avgDuration: 0,
});

const chartStates = reactive({
  dailyTrend: { loading: false, error: "", empty: false },
  hourly: { loading: false, error: "", empty: false },
  payment: { loading: false, error: "", empty: false },
  passenger: { loading: false, error: "", empty: false },
  distance: { loading: false, error: "", empty: false },
});

const dailyTrendChartRef = ref(null);
const hourlyChartRef = ref(null);
const paymentChartRef = ref(null);
const passengerChartRef = ref(null);
const distanceChartRef = ref(null);

const formatNumber = (value) => Number(value || 0).toLocaleString();
const formatMoney = (value) => Number(value || 0).toFixed(2);
const hasValues = (values) => values.some((value) => Number(value || 0) > 0);
const toSpark = (values) => {
  const cleanValues = values.map((value) => Number(value || 0));
  const max = Math.max(...cleanValues, 0);
  if (!max) return [36, 44, 40, 58, 52, 68, 60];
  return cleanValues.slice(-7).map((value) => Math.max(24, Math.round((value / max) * 100)));
};

const tripSpark = computed(() => toSpark(dailyTripTrend.value));
const amountSpark = computed(() => toSpark(dailyAmountTrend.value));
const neutralSpark = computed(() => tripSpark.value.map((value, index) => Math.max(24, Math.min(96, value - index * 2 + 8))));
const abnormalRate = computed(() => {
  const total = Number(summary.totalTrips || 0);
  if (!total) return "0.00%";
  return `${((Number(summary.abnormalTrips || 0) / total) * 100).toFixed(2)}%`;
});

const kpiCards = computed(() => [
  { key: "totalTrips", title: "总订单数", meta: "订单规模", value: formatNumber(summary.totalTrips), icon: DataAnalysis, tone: "blue", spark: tripSpark.value },
  { key: "totalAmount", title: "总成交金额", meta: "成交统计", value: `$${formatMoney(summary.totalAmount)}`, icon: Money, tone: "green", spark: amountSpark.value },
  { key: "avgAmount", title: "平均客单价", meta: "订单质量", value: `$${formatMoney(summary.avgAmount)}`, icon: Coin, tone: "orange", spark: neutralSpark.value },
  { key: "avgDistance", title: "平均行程距离", meta: "行程效率", value: `${formatMoney(summary.avgDistance)} 英里`, icon: Odometer, tone: "cyan", spark: neutralSpark.value },
  { key: "avgDuration", title: "平均行程时长", meta: "用时表现", value: `${formatMoney(summary.avgDuration)} 分钟`, icon: Timer, tone: "navy", spark: neutralSpark.value },
  { key: "abnormalTrips", title: "异常行程数量", meta: "风险识别", value: formatNumber(summary.abnormalTrips), icon: WarningFilled, tone: "red", spark: tripSpark.value },
]);

const analysisParams = () => ({
  startDate: activeDateRange.value[0],
  endDate: activeDateRange.value[1],
});

const isActiveQuickRange = (range) => activeDateRange.value[0] === range[0] && activeDateRange.value[1] === range[1];

const markChartLoading = (key) => {
  chartStates[key].loading = true;
  chartStates[key].error = "";
  chartStates[key].empty = false;
};

const markChartDone = (key, values) => {
  chartStates[key].loading = false;
  chartStates[key].error = "";
  chartStates[key].empty = !Array.isArray(values) || values.length === 0;
};

const markChartError = (key) => {
  chartStates[key].loading = false;
  chartStates[key].error = "数据加载失败，请稍后重试";
  chartStates[key].empty = false;
};

const getChart = (key, targetRef) => {
  const element = targetRef.value;
  if (!element || element.clientWidth === 0 || element.clientHeight === 0) return null;
  if (!charts[key]) {
    charts[key] = echarts.getInstanceByDom(element) || echarts.init(element);
  }
  return charts[key];
};

const tooltip = {
  backgroundColor: "rgba(15, 23, 42, 0.94)",
  borderColor: "rgba(255, 255, 255, 0.12)",
  borderWidth: 1,
  padding: [10, 12],
  textStyle: { color: "#ffffff", fontSize: 13 },
  extraCssText: "box-shadow: 0 4px 8px rgba(15, 23, 42, 0.16); border-radius: 8px;",
};

const axisLabel = { color: "#62748a", fontSize: 12 };
const axisLine = { lineStyle: { color: "#d8e2ee" } };
const splitLine = { lineStyle: { color: "#edf3f8" } };
const baseGrid = { left: 42, right: 22, bottom: 34, top: 34, containLabel: true };
const chartLegend = {
  top: 0,
  itemWidth: 12,
  itemHeight: 8,
  icon: "roundRect",
  textStyle: { color: "#53657d", fontSize: 12 },
};

const loadSummary = async () => {
  summaryLoading.value = true;
  pageNotice.value = "";
  try {
    const res = await request.get("/api/taxi-analysis/summary", { params: analysisParams() });
    if (res.code === 200) {
      Object.assign(summary, res.data);
    } else {
      pageNotice.value = res.message || "KPI 数据加载失败";
    }
  } catch (error) {
    pageNotice.value = "KPI 数据加载失败，请检查后端服务";
  } finally {
    summaryLoading.value = false;
  }
};

const loadDailyTrend = async () => {
  markChartLoading("dailyTrend");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/daily-trend", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "daily trend failed");

    const dates = res.data.map((item) => item.date);
    const tripCounts = res.data.map((item) => item.tripCount);
    const amounts = res.data.map((item) => item.totalAmount);
    dailyTripTrend.value = tripCounts;
    dailyAmountTrend.value = amounts;
    markChartDone("dailyTrend", [...tripCounts, ...amounts]);
    await nextTick();

    const chart = getChart("dailyTrend", dailyTrendChartRef);
    if (!chart) return;
    if (chartStates.dailyTrend.empty) {
      chart.clear();
      return;
    }
    chart.setOption({
      color: [chartColors.blue, chartColors.orange],
      tooltip: { ...tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: "#b8c6d8" } } },
      legend: { ...chartLegend, data: ["行程数", "成交金额"] },
      grid: { ...baseGrid, top: 48 },
      xAxis: { type: "category", data: dates, axisTick: { show: false }, axisLine, axisLabel: { ...axisLabel, rotate: 22 } },
      yAxis: [
        { type: "value", name: "行程数", nameTextStyle: axisLabel, axisLabel, axisLine, splitLine },
        { type: "value", name: "金额", nameTextStyle: axisLabel, axisLabel, axisLine, splitLine: { show: false } },
      ],
      series: [
        { name: "行程数", type: "line", smooth: true, showSymbol: false, lineStyle: { width: 3 }, areaStyle: { opacity: 0.08 }, data: tripCounts },
        { name: "成交金额", type: "line", smooth: true, showSymbol: false, lineStyle: { width: 3 }, yAxisIndex: 1, data: amounts },
      ],
    }, true);
  } catch (error) {
    markChartError("dailyTrend");
  }
};

const loadHourlyDistribution = async () => {
  markChartLoading("hourly");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/hourly-distribution", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "hourly failed");

    const values = res.data.map((item) => item.tripCount);
    markChartDone("hourly", values);
    await nextTick();
    const chart = getChart("hourly", hourlyChartRef);
    if (!chart) return;
    if (chartStates.hourly.empty) {
      chart.clear();
      return;
    }
    chart.setOption({
      tooltip: { ...tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
      grid: baseGrid,
      xAxis: { type: "category", data: res.data.map((item) => `${item.hour}:00`), axisTick: { show: false }, axisLine, axisLabel },
      yAxis: { type: "value", name: "行程数", nameTextStyle: axisLabel, axisLabel, axisLine, splitLine },
      series: [{ name: "行程数", type: "bar", barWidth: "48%", data: values, itemStyle: { color: makeGradient("#2d7cff", "#b8d1ff"), borderRadius: [7, 7, 0, 0] } }],
    }, true);
  } catch (error) {
    markChartError("hourly");
  }
};

const loadPaymentDistribution = async () => {
  markChartLoading("payment");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/payment-distribution", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "payment failed");

    const values = res.data.map((item) => item.tripCount);
    markChartDone("payment", values);
    await nextTick();
    const chart = getChart("payment", paymentChartRef);
    if (!chart) return;
    if (chartStates.payment.empty) {
      chart.clear();
      return;
    }
    chart.setOption({
      color: [chartColors.blue, chartColors.orange, chartColors.cyan, chartColors.green, chartColors.slate],
      tooltip: { ...tooltip, trigger: "item" },
      legend: { bottom: 0, itemWidth: 10, itemHeight: 8, icon: "roundRect", textStyle: { color: "#53657d", fontSize: 12 } },
      series: [
        {
          name: "支付方式",
          type: "pie",
          radius: ["44%", "62%"],
          center: ["50%", "43%"],
          avoidLabelOverlap: true,
          minShowLabelAngle: 3,
          label: {
            show: true,
            position: "outside",
            alignTo: "labelLine",
            color: "#142033",
            fontSize: 12,
            fontWeight: 600,
            formatter: ({ name, value, percent }) => {
              return `${name}  ${formatNumber(value)}次  ${Number(percent).toFixed(1)}%`;
            },
          },
          labelLine: {
            show: true,
            length: 18,
            length2: 48,
            smooth: true,
            lineStyle: {
              color: "#9fb0c4",
              width: 1,
            },
          },
          emphasis: {
            label: {
              fontSize: 13,
              fontWeight: 700,
            },
          },
          data: res.data.map((item) => ({
            name: item.paymentName,
            value: item.tripCount,
          })),
        },
      ],
    }, true);
  } catch (error) {
    markChartError("payment");
  }
};

const loadPassengerDistribution = async () => {
  markChartLoading("passenger");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/passenger-distribution", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "passenger failed");

    const values = res.data.map((item) => item.tripCount);
    markChartDone("passenger", values);
    await nextTick();
    const chart = getChart("passenger", passengerChartRef);
    if (!chart) return;
    if (chartStates.passenger.empty) {
      chart.clear();
      return;
    }
    chart.setOption({
      tooltip: { ...tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
      grid: baseGrid,
      xAxis: { type: "category", data: res.data.map((item) => `${item.passengerCount}人`), axisTick: { show: false }, axisLine, axisLabel },
      yAxis: { type: "value", name: "行程数", nameTextStyle: axisLabel, axisLabel, axisLine, splitLine },
      series: [{ name: "行程数", type: "bar", barWidth: "42%", data: values, itemStyle: { color: makeGradient("#12a8b8", "#bdeef2"), borderRadius: [7, 7, 0, 0] } }],
    }, true);
  } catch (error) {
    markChartError("passenger");
  }
};

const loadDistanceDistribution = async () => {
  markChartLoading("distance");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/distance-distribution", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "distance failed");

    const values = res.data.map((item) => item.tripCount);
    markChartDone("distance", values);
    await nextTick();
    const chart = getChart("distance", distanceChartRef);
    if (!chart) return;
    if (chartStates.distance.empty) {
      chart.clear();
      return;
    }
    chart.setOption({
      tooltip: { ...tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
      grid: baseGrid,
      xAxis: { type: "category", data: res.data.map((item) => item.range), axisTick: { show: false }, axisLine, axisLabel },
      yAxis: { type: "value", name: "行程数", nameTextStyle: axisLabel, axisLabel, axisLine, splitLine },
      series: [{ name: "行程数", type: "bar", barWidth: "42%", data: values, itemStyle: { color: makeGradient("#0b2f63", "#9eb8dc"), borderRadius: [7, 7, 0, 0] } }],
    }, true);
  } catch (error) {
    markChartError("distance");
  }
};

const loadOverview = async () => {
  await loadSummary();
  await nextTick();
  await Promise.allSettled([
    loadDailyTrend(),
    loadHourlyDistribution(),
    loadPaymentDistribution(),
    loadPassengerDistribution(),
    loadDistanceDistribution(),
  ]);
};

const handleSearch = async () => {
  if (!selectedDateRange.value || selectedDateRange.value.length !== 2) {
    pageNotice.value = "请选择日期范围";
    return;
  }
  activeDateRange.value = [...selectedDateRange.value];
  await loadOverview();
};

const handleReset = async () => {
  selectedDateRange.value = [...DEFAULT_DATE_RANGE];
  activeDateRange.value = [...DEFAULT_DATE_RANGE];
  activeTab.value = "overview";
  await loadOverview();
};

const handleQuickRange = async (item) => {
  selectedDateRange.value = [...item.range];
  activeDateRange.value = [...item.range];
  if (item.heavy) {
    pageNotice.value = "整月数据量较大，加载可能需要较长时间";
  }
  await loadOverview();
};

const stopStatsPolling = () => {
  if (statsPollingTimer.value) {
    clearInterval(statsPollingTimer.value);
    statsPollingTimer.value = null;
  }
};

const checkStatsRefreshStatus = async () => {
  try {
    const res = await request.get("/api/taxi-analysis/stats-status");
    const status = res.data?.status;
    if (status === "completed") {
      stopStatsPolling();
      statsRefreshing.value = false;
      ElMessage.success("聚合统计刷新成功");
      await loadOverview();
    } else if (status === "failed") {
      stopStatsPolling();
      statsRefreshing.value = false;
      pageNotice.value = `聚合统计刷新失败：${res.data?.message || "未知错误"}`;
    }
  } catch (error) {
    stopStatsPolling();
    statsRefreshing.value = false;
    pageNotice.value = "聚合统计刷新状态查询失败";
  }
};

const startStatsPolling = () => {
  stopStatsPolling();
  statsRefreshing.value = true;
  statsPollingTimer.value = window.setInterval(checkStatsRefreshStatus, 2000);
};

const handleRefreshStats = async () => {
  if (statsRefreshing.value) return;

  statsRefreshing.value = true;
  pageNotice.value = "";
  try {
    const res = await request.post("/api/taxi-analysis/stats-refresh");
    if (res.code === 200) {
      ElMessage.info("聚合统计刷新已开始");
      startStatsPolling();
      return;
    }

    if (res.code === 400 && res.message?.includes("正在刷新中")) {
      ElMessage.info("聚合统计正在刷新中，已开始跟踪进度");
      startStatsPolling();
      return;
    }

    statsRefreshing.value = false;
    pageNotice.value = res.message || "聚合统计刷新启动失败";
  } catch (error) {
    statsRefreshing.value = false;
    pageNotice.value = "聚合统计刷新启动失败";
  }
};

const resizeCharts = () => {
  const visibleKeys = activeTab.value === "overview"
    ? ["dailyTrend"]
    : ["hourly", "payment", "passenger", "distance"];
  visibleKeys.forEach((key) => charts[key]?.resize());
};

watch(activeTab, async (tab) => {
  await nextTick();
  if (tab === "overview") {
    await loadDailyTrend();
  } else {
    await Promise.allSettled([
      loadHourlyDistribution(),
      loadPaymentDistribution(),
      loadPassengerDistribution(),
      loadDistanceDistribution(),
    ]);
  }
  await nextTick();
  resizeCharts();
});

onMounted(async () => {
  await loadOverview();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  stopStatsPolling();
  Object.values(charts).forEach((chart) => chart.dispose());
});
</script>

<style scoped>
.overview-page {
  width: 100%;
  max-width: 1760px;
  min-height: calc(100vh - 58px);
  margin: 0 auto;
  padding: 18px 22px 24px;
}

.overview-header,
.chart-card,
.insight-card,
.stat-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #dce6f2;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.06);
}

.overview-header {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) auto;
  align-items: center;
  gap: 18px;
  padding: 16px;
  background:
    linear-gradient(135deg, rgba(29, 99, 216, 0.06), transparent 44%),
    rgba(255, 255, 255, 0.94);
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0b2f63;
  background: #ffffff;
  border: 1px solid #dce6f2;
  box-shadow: 0 4px 8px rgba(29, 99, 216, 0.1);
  font-size: 22px;
}

.overview-header h1 {
  margin: 0;
  color: #142033;
  font-size: 25px;
  line-height: 1.24;
  font-weight: 780;
}

.overview-header p {
  margin-top: 6px;
  color: #53657d;
  font-size: 14px;
  line-height: 1.55;
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.header-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  color: #475569;
  background: #eef5ff;
  font-size: 13px;
  font-weight: 650;
}

.filter-panel {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 9px;
  max-width: 760px;
}

.date-picker {
  width: 286px;
}

.quick-range-group,
.action-group {
  display: inline-flex;
}

.action-group {
  gap: 8px;
}

.refresh-stats-button {
  color: #9a5b00;
  background: #fff6df;
  border-color: #f3d08b;
}

.refresh-stats-button:hover {
  color: #7c4600;
  background: #ffefd1;
  border-color: #e8b956;
}

.page-alert {
  margin-top: 12px;
  border-radius: 10px;
}

.overview-tabs {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  margin-top: 14px;
  border: 1px solid #dce6f2;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
}

.overview-tabs button {
  height: 34px;
  padding: 0 18px;
  border: 0;
  border-radius: 7px;
  color: #53657d;
  background: transparent;
  cursor: pointer;
  font-weight: 720;
  transition: background-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.overview-tabs button:hover {
  color: #1d63d8;
  background: #edf5ff;
}

.overview-tabs button.active {
  color: #ffffff;
  background: #1d63d8;
  box-shadow: 0 3px 6px rgba(29, 99, 216, 0.16);
}

.tab-panel {
  margin-top: 14px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  min-height: 116px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 10px rgba(15, 23, 42, 0.075);
}

.stat-card-main {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #1d63d8;
  background: #eaf2ff;
  font-size: 18px;
}

.stat-card.green .stat-icon { color: #16a34a; background: #e9f8ef; }
.stat-card.orange .stat-icon { color: #b35f00; background: #fff4df; }
.stat-card.cyan .stat-icon { color: #0891b2; background: #e6f7fb; }
.stat-card.navy .stat-icon { color: #0b2f63; background: #e9eef7; }
.stat-card.red .stat-icon { color: #dc2626; background: #fff0f0; }

.stat-copy span {
  display: block;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.stat-copy strong {
  display: block;
  margin-top: 5px;
  color: #142033;
  font-size: 21px;
  line-height: 1.18;
  font-weight: 820;
  word-break: break-word;
}

.stat-copy p {
  margin-top: 5px;
  color: #53657d;
  font-size: 13px;
  font-weight: 650;
}

.stat-spark {
  height: 28px;
  display: flex;
  align-items: flex-end;
  gap: 4px;
}

.stat-spark i {
  width: 6px;
  min-height: 6px;
  border-radius: 999px;
  background: linear-gradient(180deg, #1d63d8, rgba(29, 99, 216, 0.18));
}

.stat-card.green .stat-spark i { background: linear-gradient(180deg, #16a34a, rgba(22, 163, 74, 0.18)); }
.stat-card.orange .stat-spark i { background: linear-gradient(180deg, #f59e0b, rgba(245, 158, 11, 0.2)); }
.stat-card.cyan .stat-spark i { background: linear-gradient(180deg, #0891b2, rgba(8, 145, 178, 0.18)); }
.stat-card.navy .stat-spark i { background: linear-gradient(180deg, #0b2f63, rgba(11, 47, 99, 0.16)); }
.stat-card.red .stat-spark i { background: linear-gradient(180deg, #dc2626, rgba(220, 38, 38, 0.16)); }

.stat-skeleton {
  height: 116px;
  border-radius: 12px;
  background: linear-gradient(90deg, #eef3f8 25%, #f8fbff 37%, #eef3f8 63%);
  background-size: 400% 100%;
  animation: skeletonMove 1.3s ease-in-out infinite;
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(320px, 0.85fr);
  gap: 14px;
  margin-top: 14px;
}

.distribution-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.chart-card {
  padding: 14px;
}

.chart-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.chart-card h2,
.insight-card h2 {
  margin: 0;
  color: #142033;
  font-size: 17px;
  line-height: 1.3;
  font-weight: 780;
}

.chart-card p,
.insight-card p {
  margin-top: 5px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.55;
}

.chart-card-header span {
  flex-shrink: 0;
  min-width: 58px;
  color: #64748b;
  font-size: 12px;
  font-weight: 760;
  text-align: right;
}

.chart-body {
  position: relative;
  min-height: 284px;
}

.chart-layer {
  width: 100%;
  min-height: 284px;
}

.chart-layer.is-muted {
  visibility: hidden;
}

.chart {
  width: 100%;
  height: 284px;
  min-height: 284px;
}

.trend-chart {
  height: 300px;
  min-height: 300px;
}

.chart-state {
  position: absolute;
  inset: 0;
  min-height: 284px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  color: #64748b;
}

.chart-state strong {
  color: #334155;
  font-size: 15px;
}

.chart-state p {
  max-width: 320px;
  margin: 0;
}

.chart-skeleton {
  position: absolute;
  inset: 0;
  min-height: 284px;
  padding: 26px 20px 20px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  align-items: end;
  gap: 14px;
}

.chart-skeleton i {
  border-radius: 8px 8px 3px 3px;
  background: linear-gradient(180deg, #dfeaff, #f3f7fb);
}

.chart-skeleton i:nth-child(1) { height: 44%; }
.chart-skeleton i:nth-child(2) { height: 68%; }
.chart-skeleton i:nth-child(3) { height: 54%; }
.chart-skeleton i:nth-child(4) { height: 82%; }

.insight-card {
  padding: 18px;
  min-height: 100%;
}

.insight-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.insight-card-header span {
  height: 26px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  color: #15803d;
  background: #e9f8ef;
  font-size: 13px;
  font-weight: 760;
}

.insight-card-header span.warning {
  color: #b35f00;
  background: #fff4df;
}

.insight-number {
  margin-top: 26px;
  color: #0b2f63;
  font-size: 46px;
  line-height: 1;
  font-weight: 840;
}

.insight-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 20px;
}

.insight-metrics div {
  padding: 12px;
  border-radius: 10px;
  background: #f6f9fd;
  border: 1px solid #e4edf7;
}

.insight-metrics span {
  display: block;
  color: #64748b;
  font-size: 13px;
  font-weight: 650;
}

.insight-metrics strong {
  display: block;
  margin-top: 5px;
  color: #142033;
  font-size: 18px;
}

@keyframes skeletonMove {
  0% { background-position: 100% 0; }
  100% { background-position: 0 0; }
}

@media (prefers-reduced-motion: reduce) {
  .stat-skeleton {
    animation: none;
  }

  .stat-card,
  .overview-tabs button {
    transition: none;
  }
}

@media (max-width: 1320px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .overview-header,
  .overview-grid,
  .distribution-grid {
    grid-template-columns: 1fr;
  }

  .filter-panel {
    justify-content: flex-start;
    max-width: none;
  }
}

@media (max-width: 760px) {
  .overview-page {
    padding: 12px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .date-picker,
  .quick-range-group,
  .action-group {
    width: 100%;
  }

  .quick-range-group,
  .action-group {
    display: grid;
    grid-template-columns: 1fr;
  }

  .overview-tabs {
    width: 100%;
  }

  .overview-tabs button {
    flex: 1;
  }
}
</style>
