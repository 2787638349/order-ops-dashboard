<template>
  <div class="trip-page">
    <section class="trip-header">
      <div>
        <div class="section-label">行程明细管理</div>
        <h1>行程记录管理</h1>
        <p>查询、筛选、导入导出 NYC Yellow Taxi 行程明细，并查看异常行程原因。</p>
      </div>

      <div class="header-actions">
        <el-upload :show-file-list="false" :http-request="handleImport" accept=".csv">
          <el-button :icon="Upload" :loading="importLoading">导入 CSV</el-button>
        </el-upload>
        <el-button type="primary" :icon="Download" :loading="exportLoading" @click="handleExport">
          导出 CSV
        </el-button>
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

    <section class="filter-card">
      <div class="filter-heading">
        <div>
          <h2>高级筛选</h2>
          <p>按行程编号、日期、区域、金额、距离和异常状态过滤记录。</p>
        </div>
        <div class="filter-actions">
          <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </div>
      </div>

      <el-form :model="filters" label-position="top" class="filter-form">
        <el-form-item label="行程编号">
          <el-input v-model="filters.tripNo" clearable placeholder="输入 tripNo" />
        </el-form-item>

        <el-form-item label="支付方式">
          <el-select v-model="filters.paymentType" clearable placeholder="全部">
            <el-option label="信用卡" :value="1" />
            <el-option label="现金" :value="2" />
            <el-option label="免费" :value="3" />
            <el-option label="争议" :value="4" />
            <el-option label="未知" :value="5" />
            <el-option label="作废" :value="6" />
          </el-select>
        </el-form-item>

        <el-form-item label="乘客数">
          <el-input-number v-model="filters.passengerCount" :min="0" controls-position="right" class="full-input" />
        </el-form-item>

        <el-form-item label="上车区域 ID">
          <el-input v-model="filters.pickupLocationId" clearable placeholder="PULocationID" />
        </el-form-item>

        <el-form-item label="下车区域 ID">
          <el-input v-model="filters.dropoffLocationId" clearable placeholder="DOLocationID" />
        </el-form-item>

        <el-form-item label="是否异常">
          <el-select v-model="filters.isAbnormal" clearable placeholder="全部">
            <el-option label="正常" value="false" />
            <el-option label="异常" value="true" />
          </el-select>
        </el-form-item>

        <el-form-item label="上车日期" class="date-field">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="date-range"
          />
        </el-form-item>

        <el-form-item label="距离范围">
          <div class="range-inputs">
            <el-input v-model="filters.minDistance" clearable placeholder="最小" />
            <span>至</span>
            <el-input v-model="filters.maxDistance" clearable placeholder="最大" />
          </div>
        </el-form-item>

        <el-form-item label="金额范围">
          <div class="range-inputs">
            <el-input v-model="filters.minAmount" clearable placeholder="最小" />
            <span>至</span>
            <el-input v-model="filters.maxAmount" clearable placeholder="最大" />
          </div>
        </el-form-item>
      </el-form>
    </section>

    <section class="table-card">
      <div class="table-toolbar">
        <div>
          <h2>行程明细表</h2>
          <span>共 {{ pagination.total.toLocaleString() }} 条记录</span>
        </div>
        <div class="table-summary">
          <span>当前页 {{ tripList.length }} 条</span>
          <span>异常 {{ currentPageAbnormalCount }} 条</span>
          <span>第 {{ pagination.page }} 页</span>
        </div>
      </div>

      <el-table
        :data="tripList"
        v-loading="loading"
        border
        height="520"
        class="trip-table"
        empty-text="暂无行程数据"
      >
        <el-table-column prop="tripNo" label="行程编号" min-width="170" fixed="left" />
        <el-table-column prop="vendorId" label="供应商" width="86" />
        <el-table-column prop="pickupTime" label="上车时间" min-width="165" class-name="time-cell" />
        <el-table-column prop="dropoffTime" label="下车时间" min-width="165" class-name="time-cell" />
        <el-table-column prop="passengerCount" label="乘客数" width="86" />
        <el-table-column prop="tripDistance" label="距离" width="96" align="right" class-name="number-cell">
          <template #default="{ row }">{{ formatMoney(row.tripDistance) }}</template>
        </el-table-column>
        <el-table-column label="上车区域" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ formatLocation(row, "pickup") }}</template>
        </el-table-column>
        <el-table-column label="下车区域" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ formatLocation(row, "dropoff") }}</template>
        </el-table-column>
        <el-table-column prop="paymentType" label="支付方式" width="104">
          <template #default="{ row }">{{ getPaymentText(row.paymentType) }}</template>
        </el-table-column>
        <el-table-column prop="fareAmount" label="车费" width="98" align="right" class-name="number-cell">
          <template #default="{ row }">${{ formatMoney(row.fareAmount) }}</template>
        </el-table-column>
        <el-table-column prop="tipAmount" label="小费" width="98" align="right" class-name="number-cell">
          <template #default="{ row }">${{ formatMoney(row.tipAmount) }}</template>
        </el-table-column>
        <el-table-column prop="totalAmount" label="总金额" width="108" align="right" class-name="number-cell">
          <template #default="{ row }">${{ formatMoney(row.totalAmount) }}</template>
        </el-table-column>
        <el-table-column prop="tripDurationMin" label="时长" width="104" align="right" class-name="number-cell">
          <template #default="{ row }">{{ formatMoney(row.tripDurationMin) }} 分钟</template>
        </el-table-column>
        <el-table-column prop="isAbnormal" label="状态" width="92" fixed="right">
          <template #default="{ row }">
            <el-tag :class="row.isAbnormal ? 'status-danger' : 'status-success'" effect="light" round>
              {{ row.isAbnormal ? "异常" : "正常" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="异常原因" min-width="260" show-overflow-tooltip fixed="right">
          <template #default="{ row }">
            <span :class="row.isAbnormal ? 'reason-danger' : 'reason-muted'">
              {{ row.abnormalReason || "无" }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTrips"
          @current-change="loadTrips"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { Download, Refresh, Search, Upload } from "@element-plus/icons-vue";
import request from "../api/request";

const API_BASE = "http://127.0.0.1:5000";

const loading = ref(false);
const importLoading = ref(false);
const exportLoading = ref(false);
const tripList = ref([]);
const pageNotice = ref("");

const filters = reactive({
  tripNo: "",
  paymentType: "",
  passengerCount: undefined,
  pickupLocationId: "",
  dropoffLocationId: "",
  dateRange: [],
  minDistance: "",
  maxDistance: "",
  minAmount: "",
  maxAmount: "",
  isAbnormal: "",
});

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
});

const paymentMap = {
  1: "信用卡",
  2: "现金",
  3: "免费",
  4: "争议",
  5: "未知",
  6: "作废",
};

const currentPageAbnormalCount = computed(() => tripList.value.filter((item) => item.isAbnormal).length);

const getPaymentText = (value) => paymentMap[value] || "未知";
const formatMoney = (value) => Number(value || 0).toFixed(2);

const formatLocation = (row, type) => {
  const borough = row[`${type}Borough`];
  const zone = row[`${type}ZoneName`];
  const id = row[`${type}LocationId`];
  const name = row[`${type}LocationName`];

  if (borough && zone) {
    return `${borough} - ${zone} (${id})`;
  }

  return name || `Location ${id}`;
};

const cleanParams = (params) => {
  const result = {};
  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== undefined && value !== null) {
      result[key] = value;
    }
  });
  return result;
};

const buildQueryParams = () => cleanParams({
  page: pagination.page,
  pageSize: pagination.pageSize,
  tripNo: filters.tripNo,
  paymentType: filters.paymentType,
  passengerCount: filters.passengerCount,
  pickupLocationId: filters.pickupLocationId,
  dropoffLocationId: filters.dropoffLocationId,
  startDate: filters.dateRange?.[0],
  endDate: filters.dateRange?.[1],
  minDistance: filters.minDistance,
  maxDistance: filters.maxDistance,
  minAmount: filters.minAmount,
  maxAmount: filters.maxAmount,
  isAbnormal: filters.isAbnormal,
});

const loadTrips = async () => {
  loading.value = true;
  pageNotice.value = "";

  try {
    const res = await request.get("/api/taxi-trips", {
      params: buildQueryParams(),
    });

    if (res.code === 200) {
      tripList.value = res.data.list;
      pagination.total = res.data.total;
      pagination.page = res.data.page;
      pagination.pageSize = res.data.pageSize;
    } else {
      pageNotice.value = res.message || "获取行程列表失败";
    }
  } catch (error) {
    pageNotice.value = "行程列表接口请求失败，请检查后端服务";
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.page = 1;
  loadTrips();
};

const handleReset = () => {
  Object.assign(filters, {
    tripNo: "",
    paymentType: "",
    passengerCount: undefined,
    pickupLocationId: "",
    dropoffLocationId: "",
    dateRange: [],
    minDistance: "",
    maxDistance: "",
    minAmount: "",
    maxAmount: "",
    isAbnormal: "",
  });

  pagination.page = 1;
  loadTrips();
};

const handleImport = async (options) => {
  const file = options.file;

  if (!file.name.toLowerCase().endsWith(".csv")) {
    ElMessage.error("请上传 CSV 文件");
    return;
  }

  importLoading.value = true;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await request.post("/api/taxi-trips/import", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    if (res.code === 200) {
      const createdCount = res.data?.createdCount ?? 0;
      const skippedCount = res.data?.skippedCount ?? 0;
      const abnormalCount = res.data?.abnormalCount ?? 0;

      ElMessage.success(`导入成功：新增 ${createdCount} 条，跳过 ${skippedCount} 条，异常 ${abnormalCount} 条`);
      pagination.page = 1;
      loadTrips();
    } else {
      ElMessage.error(res.message || "导入失败");
    }
  } catch (error) {
    ElMessage.error("CSV 导入失败");
  } finally {
    importLoading.value = false;
  }
};

const handleExport = () => {
  exportLoading.value = true;

  try {
    const params = new URLSearchParams();
    const token = localStorage.getItem("token");

    if (token) {
      params.append("token", token);
    }

    const queryParams = buildQueryParams();
    delete queryParams.page;
    delete queryParams.pageSize;

    Object.entries(queryParams).forEach(([key, value]) => {
      params.append(key, value);
    });

    const queryString = params.toString();
    const url = `${API_BASE}/api/taxi-trips/export${queryString ? `?${queryString}` : ""}`;
    const link = document.createElement("a");
    const now = new Date();
    const dateText = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}`;

    link.href = url;
    link.download = `taxi_trips_export_${dateText}.csv`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    ElMessage.success("导出成功");
  } catch (error) {
    ElMessage.error("导出 CSV 失败");
  } finally {
    setTimeout(() => {
      exportLoading.value = false;
    }, 500);
  }
};

onMounted(() => {
  loadTrips();
});
</script>

<style scoped>
.trip-page {
  width: 100%;
  max-width: 1760px;
  min-height: calc(100vh - 58px);
  margin: 0 auto;
  padding: 18px 22px 24px;
}

.trip-header,
.filter-card,
.table-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #dce6f2;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.06);
}

.trip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.trip-header h1 {
  margin: 6px 0 0;
  color: #142033;
  font-size: 25px;
  line-height: 1.24;
  font-weight: 780;
}

.trip-header p {
  margin-top: 6px;
  color: #53657d;
  font-size: 14px;
  line-height: 1.55;
}

.header-actions,
.filter-actions,
.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-alert {
  margin-top: 12px;
  border-radius: 10px;
}

.filter-card {
  margin-top: 14px;
  padding: 14px 14px 4px;
}

.filter-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}

.filter-heading h2 {
  color: #142033;
  font-size: 17px;
  font-weight: 780;
}

.filter-heading p {
  margin-top: 5px;
  color: #64748b;
  font-size: 13px;
}

.filter-form {
  display: grid;
  grid-template-columns: repeat(6, minmax(132px, 1fr));
  gap: 0 10px;
  align-items: end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.filter-form :deep(.el-form-item__label) {
  color: #53657d;
  font-size: 14px;
  font-weight: 700;
  line-height: 18px;
  margin-bottom: 6px;
}

.full-input,
.date-range {
  width: 100%;
}

.date-field {
  grid-column: span 2;
}

.range-inputs {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 22px 1fr;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.table-card {
  margin-top: 14px;
  padding: 14px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}

.table-toolbar h2 {
  color: #142033;
  font-size: 17px;
  font-weight: 780;
}

.table-toolbar span {
  color: #64748b;
  font-size: 13px;
  font-weight: 650;
}

.table-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.table-summary span {
  min-height: 26px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #eef5ff;
  color: #475569;
}

.trip-table {
  border-radius: 10px;
  overflow: hidden;
  border-color: #dce6f2;
}

.trip-table :deep(.el-table__inner-wrapper::before) {
  background-color: #dce6f2;
}

.trip-table :deep(.el-table__header th) {
  background: #f2f6fb;
  color: #334155;
  font-size: 13px;
  font-weight: 760;
}

.trip-table :deep(.el-table__cell) {
  padding: 7px 0;
  border-color: #e7eef7;
}

.trip-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: #f7fbff;
}

.trip-table :deep(.time-cell),
.trip-table :deep(.number-cell) {
  font-variant-numeric: tabular-nums;
}

.trip-table :deep(.number-cell) {
  color: #24344d;
  font-weight: 650;
}

.status-success,
.status-danger {
  border: 0;
  font-weight: 760;
}

.status-success {
  color: #15803d;
  background: #e9f8ef;
}

.status-danger {
  color: #b4232d;
  background: #fff0f0;
}

.reason-danger {
  color: #b4232d;
  font-weight: 650;
}

.reason-muted {
  color: #94a3b8;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

@media (max-width: 1180px) {
  .filter-form {
    grid-template-columns: repeat(3, minmax(150px, 1fr));
  }

  .date-field {
    grid-column: span 3;
  }
}

@media (max-width: 760px) {
  .trip-page {
    padding: 12px;
  }

  .trip-header,
  .filter-heading,
  .table-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-form {
    grid-template-columns: 1fr;
  }

  .date-field {
    grid-column: auto;
  }

  .header-actions,
  .filter-actions,
  .table-summary {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
