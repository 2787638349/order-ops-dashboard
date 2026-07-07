<template>
  <div class="analysis-page">
    <section class="analysis-header">
      <div>
        <div class="section-label">区域专题分析</div>
        <h1>区域热点分析</h1>
        <p>基于上车区域 Top10 与下车区域 Top10，观察当前日期范围内的订单热点位置。</p>
        <div class="header-meta">
          <span>当前范围：{{ activeDateRange[0] }} 至 {{ activeDateRange[1] }}</span>
          <span>数据来源：区域 Top10 聚合统计</span>
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
          <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">查询</el-button>
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

    <section class="insight-grid">
      <div v-for="item in insightCards" :key="item.key" class="insight-card" :class="item.tone">
        <div class="insight-icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <div>
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.description }}</p>
        </div>
      </div>
    </section>

    <section class="chart-grid">
      <div class="chart-card">
        <div class="chart-card-header">
          <div>
            <h2>上车区域 Top 10</h2>
            <p>按行程数量排序的上车热点区域</p>
          </div>
          <span>行程数</span>
        </div>
        <div class="chart-body">
          <div v-if="chartStates.pickup.loading" class="chart-skeleton">
            <i v-for="item in 10" :key="item"></i>
          </div>
          <div v-else-if="chartStates.pickup.error" class="chart-state">
            <strong>数据加载失败</strong>
            <p>请稍后重试，或检查后端聚合统计是否可用。</p>
            <el-button size="small" type="primary" @click="loadPickupLocationTop">重试</el-button>
          </div>
          <div v-else-if="chartStates.pickup.empty" class="chart-state">
            <strong>暂无数据</strong>
            <p>当前日期范围下没有上车区域排行数据。</p>
          </div>
          <div ref="pickupChartRef" class="chart region-chart" :class="{ 'is-muted': !isChartReady('pickup') }"></div>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-card-header">
          <div>
            <h2>下车区域 Top 10</h2>
            <p>按行程数量排序的下车热点区域</p>
          </div>
          <span>行程数</span>
        </div>
        <div class="chart-body">
          <div v-if="chartStates.dropoff.loading" class="chart-skeleton">
            <i v-for="item in 10" :key="item"></i>
          </div>
          <div v-else-if="chartStates.dropoff.error" class="chart-state">
            <strong>数据加载失败</strong>
            <p>请稍后重试，或检查后端聚合统计是否可用。</p>
            <el-button size="small" type="primary" @click="loadDropoffLocationTop">重试</el-button>
          </div>
          <div v-else-if="chartStates.dropoff.empty" class="chart-state">
            <strong>暂无数据</strong>
            <p>当前日期范围下没有下车区域排行数据。</p>
          </div>
          <div ref="dropoffChartRef" class="chart region-chart" :class="{ 'is-muted': !isChartReady('dropoff') }"></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { Location, Position, Refresh, Search, TrendCharts } from "@element-plus/icons-vue";
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
  cyan: "#0891b2",
  orange: "#f59e0b",
  muted: "#9bb3cf",
};

const barGradient = (from, to) => new echarts.graphic.LinearGradient(0, 0, 1, 0, [
  { offset: 0, color: from },
  { offset: 1, color: to },
]);

const loading = ref(false);
const pageNotice = ref("");
const selectedDateRange = ref([...DEFAULT_DATE_RANGE]);
const activeDateRange = ref([...DEFAULT_DATE_RANGE]);
const charts = {};

const pickupRows = ref([]);
const dropoffRows = ref([]);
const pickupChartRef = ref(null);
const dropoffChartRef = ref(null);

const chartStates = reactive({
  pickup: { loading: false, error: "", empty: false },
  dropoff: { loading: false, error: "", empty: false },
});

const analysisParams = () => ({
  startDate: activeDateRange.value[0],
  endDate: activeDateRange.value[1],
});

const isActiveQuickRange = (range) => activeDateRange.value[0] === range[0] && activeDateRange.value[1] === range[1];
const formatNumber = (value) => Number(value || 0).toLocaleString();
const hasValues = (values) => values.some((value) => Number(value || 0) > 0);
const isChartReady = (key) => !chartStates[key].loading && !chartStates[key].error && !chartStates[key].empty;

const top3Share = computed(() => {
  const combined = [...pickupRows.value, ...dropoffRows.value]
    .map((item) => Number(item.tripCount || 0))
    .sort((a, b) => b - a);
  const total = combined.reduce((sum, value) => sum + value, 0);
  if (!total) return "暂无数据";
  const top3 = combined.slice(0, 3).reduce((sum, value) => sum + value, 0);
  return `${((top3 / total) * 100).toFixed(1)}%`;
});

const insightCards = computed(() => {
  const pickupTop = pickupRows.value[0];
  const dropoffTop = dropoffRows.value[0];

  return [
    {
      key: "pickup",
      label: "最热门上车区域",
      value: pickupTop?.name || "暂无数据",
      description: pickupTop ? `${formatNumber(pickupTop.tripCount)} 次行程` : "等待上车区域 Top10 数据",
      icon: Location,
      tone: "blue",
    },
    {
      key: "dropoff",
      label: "最热门下车区域",
      value: dropoffTop?.name || "暂无数据",
      description: dropoffTop ? `${formatNumber(dropoffTop.tripCount)} 次行程` : "等待下车区域 Top10 数据",
      icon: Position,
      tone: "cyan",
    },
    {
      key: "concentration",
      label: "热点集中度",
      value: top3Share.value,
      description: "Top3 在当前 Top10 样本中的占比",
      icon: TrendCharts,
      tone: "orange",
    },
  ];
});

const markLoading = (key) => {
  chartStates[key].loading = true;
  chartStates[key].error = "";
  chartStates[key].empty = false;
};

const markDone = (key, values) => {
  chartStates[key].loading = false;
  chartStates[key].error = "";
  chartStates[key].empty = !Array.isArray(values) || values.length === 0;
};

const markError = (key) => {
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

const regionGrid = {
  left: 180,
  right: 48,
  bottom: 40,
  top: 40,
  containLabel: true,
};

const axisLabel = { color: "#62748a", fontSize: 12 };
const splitLine = { lineStyle: { color: "#edf3f8" } };

const formatRegionRows = (rows, nameKey, idKey) => {
  return [...rows]
    .map((item) => ({
      name: item[nameKey] || String(item[idKey] || ""),
      tripCount: Number(item.tripCount || 0),
    }))
    .sort((a, b) => b.tripCount - a.tripCount);
};

const rankedBarColor = (index) => {
  if (index === 0) return barGradient("#ffb33c", "#f59e0b");
  if (index === 1) return barGradient("#2d7cff", chartColors.blue);
  if (index === 2) return barGradient("#22b8c3", chartColors.cyan);
  return barGradient("#c9d8ea", chartColors.muted);
};

const regionTooltipFormatter = (params) => {
  const item = Array.isArray(params) ? params[0] : params;
  return `${item.name}<br/>行程数：${formatNumber(item.value)}`;
};

const setRegionChartOption = (chart, rows) => {
  const names = rows.map((item) => item.name);
  const values = rows.map((item) => item.tripCount);

  chart.setOption({
    tooltip: { ...tooltip, trigger: "axis", axisPointer: { type: "shadow" }, formatter: regionTooltipFormatter },
    grid: regionGrid,
    xAxis: {
      type: "value",
      axisLabel,
      splitLine,
      axisLine: { lineStyle: { color: "#d8e2ee" } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: names,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#d8e2ee" } },
      axisLabel: {
        color: "#475569",
        fontSize: 12,
        interval: 0,
        width: 160,
        overflow: "truncate",
      },
    },
    series: [
      {
        name: "行程数",
        type: "bar",
        barWidth: 16,
        data: values.map((value, index) => ({
          value,
          itemStyle: { color: rankedBarColor(index), borderRadius: [0, 8, 8, 0] },
        })),
        label: {
          show: true,
          position: "right",
          color: "#53657d",
          fontSize: 12,
          fontWeight: 700,
          formatter: ({ value }) => formatNumber(value),
        },
      },
    ],
  }, true);
};

const loadPickupLocationTop = async () => {
  markLoading("pickup");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/pickup-location-top", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "pickup failed");

    pickupRows.value = formatRegionRows(res.data, "pickupLocationName", "pickupLocationId");
    markDone("pickup", pickupRows.value.map((item) => item.tripCount));
    await nextTick();
    const chart = getChart("pickup", pickupChartRef);
    if (!chart) return;
    if (chartStates.pickup.empty) {
      chart.clear();
      return;
    }
    setRegionChartOption(chart, pickupRows.value);
  } catch (error) {
    markError("pickup");
  }
};

const loadDropoffLocationTop = async () => {
  markLoading("dropoff");
  await nextTick();
  try {
    const res = await request.get("/api/taxi-analysis/dropoff-location-top", { params: analysisParams() });
    if (res.code !== 200) throw new Error(res.message || "dropoff failed");

    dropoffRows.value = formatRegionRows(res.data, "dropoffLocationName", "dropoffLocationId");
    markDone("dropoff", dropoffRows.value.map((item) => item.tripCount));
    await nextTick();
    const chart = getChart("dropoff", dropoffChartRef);
    if (!chart) return;
    if (chartStates.dropoff.empty) {
      chart.clear();
      return;
    }
    setRegionChartOption(chart, dropoffRows.value);
  } catch (error) {
    markError("dropoff");
  }
};

const loadAnalysis = async () => {
  loading.value = true;
  pageNotice.value = "";
  try {
    await Promise.allSettled([
      loadPickupLocationTop(),
      loadDropoffLocationTop(),
    ]);
  } finally {
    loading.value = false;
  }
};

const handleSearch = async () => {
  if (!selectedDateRange.value || selectedDateRange.value.length !== 2) {
    pageNotice.value = "请选择日期范围";
    return;
  }
  activeDateRange.value = [...selectedDateRange.value];
  await loadAnalysis();
};

const handleReset = async () => {
  selectedDateRange.value = [...DEFAULT_DATE_RANGE];
  activeDateRange.value = [...DEFAULT_DATE_RANGE];
  await loadAnalysis();
};

const handleQuickRange = async (item) => {
  selectedDateRange.value = [...item.range];
  activeDateRange.value = [...item.range];
  if (item.heavy) {
    pageNotice.value = "整月数据量较大，加载可能需要较长时间";
  }
  await loadAnalysis();
};

const resizeCharts = () => {
  Object.values(charts).forEach((chart) => chart.resize());
};

onMounted(async () => {
  await loadAnalysis();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  Object.values(charts).forEach((chart) => chart.dispose());
});
</script>

<style scoped>
.analysis-page {
  width: 100%;
  max-width: 1760px;
  min-height: calc(100vh - 58px);
  margin: 0 auto;
  padding: 18px 22px 24px;
}

.analysis-header,
.insight-card,
.chart-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #dce6f2;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.06);
}

.analysis-header {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) auto;
  align-items: center;
  gap: 18px;
  padding: 16px;
  background:
    linear-gradient(135deg, rgba(29, 99, 216, 0.06), transparent 44%),
    rgba(255, 255, 255, 0.94);
}

.section-label {
  color: #1d63d8;
  font-size: 13px;
  font-weight: 760;
}

.analysis-header h1 {
  margin: 6px 0 0;
  color: #142033;
  font-size: 25px;
  line-height: 1.24;
  font-weight: 780;
}

.analysis-header p {
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
  min-height: 26px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
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

.page-alert {
  margin-top: 12px;
  border-radius: 10px;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.insight-card {
  min-height: 112px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 13px;
}

.insight-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #1d63d8;
  background: #eaf2ff;
  font-size: 20px;
}

.insight-card.cyan .insight-icon {
  color: #0891b2;
  background: #e6f7fb;
}

.insight-card.orange .insight-icon {
  color: #b35f00;
  background: #fff4df;
}

.insight-card span {
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.insight-card strong {
  display: block;
  margin-top: 7px;
  color: #142033;
  font-size: 20px;
  line-height: 1.25;
  font-weight: 820;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.insight-card p {
  margin-top: 6px;
  color: #53657d;
  font-size: 13px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.chart-card {
  padding: 14px;
}

.chart-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.chart-card h2 {
  margin: 0;
  color: #142033;
  font-size: 17px;
  line-height: 1.3;
  font-weight: 780;
}

.chart-card p {
  margin-top: 5px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.55;
}

.chart-card-header span {
  color: #64748b;
  font-size: 12px;
  font-weight: 760;
  white-space: nowrap;
}

.chart-body {
  position: relative;
  min-height: 420px;
}

.chart {
  width: 100%;
  height: 420px;
  min-height: 420px;
}

.chart.is-muted {
  visibility: hidden;
}

.chart-state {
  position: absolute;
  inset: 0;
  min-height: 420px;
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
  min-height: 420px;
  display: grid;
  grid-template-rows: repeat(10, 1fr);
  gap: 10px;
  padding: 12px 28px 12px 12px;
}

.chart-skeleton i {
  border-radius: 999px;
  background: linear-gradient(90deg, #dfeaff, #f3f7fb);
}

.chart-skeleton i:nth-child(1) { width: 96%; }
.chart-skeleton i:nth-child(2) { width: 88%; }
.chart-skeleton i:nth-child(3) { width: 80%; }
.chart-skeleton i:nth-child(4) { width: 72%; }
.chart-skeleton i:nth-child(5) { width: 66%; }
.chart-skeleton i:nth-child(6) { width: 58%; }
.chart-skeleton i:nth-child(7) { width: 52%; }
.chart-skeleton i:nth-child(8) { width: 46%; }
.chart-skeleton i:nth-child(9) { width: 40%; }
.chart-skeleton i:nth-child(10) { width: 34%; }

@media (max-width: 1100px) {
  .analysis-header,
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .filter-panel {
    justify-content: flex-start;
    max-width: none;
  }
}

@media (max-width: 760px) {
  .analysis-page {
    padding: 12px;
  }

  .insight-grid {
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
}
</style>
