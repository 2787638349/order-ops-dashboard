<template>
  <div class="order-page">
    <div class="page-title">
      <div>
        <h2>订单管理</h2>
        <p>支持订单查询、新增、编辑和删除</p>
      </div>

      <div class="page-actions">
        <el-upload
          :show-file-list="false"
          :http-request="handleImport"
          accept=".csv"
        >
          <el-button :loading="importLoading">
            导入 CSV
          </el-button>
        </el-upload>

        <el-button :loading="exportLoading" @click="handleExport">
          导出 CSV
        </el-button>

        <el-button type="primary" @click="handleAdd">
          新增订单
        </el-button>
      </div>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="订单编号">
          <el-input
            v-model="filters.orderNo"
            placeholder="请输入订单编号"
            clearable
            style="width: 180px"
          />
        </el-form-item>

        <el-form-item label="城市">
          <el-input
            v-model="filters.city"
            placeholder="请输入城市"
            clearable
            style="width: 160px"
          />
        </el-form-item>

        <el-form-item label="订单状态">
          <el-select
            v-model="filters.orderStatus"
            placeholder="请选择状态"
            clearable
            style="width: 160px"
          >
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="待处理" value="pending" />
          </el-select>
        </el-form-item>

        <el-form-item label="下单日期">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table
        :data="orderList"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="orderNo" label="订单编号" min-width="160" />
        <el-table-column prop="userId" label="用户ID" width="110" />
        <el-table-column prop="city" label="城市" width="90" />
        <el-table-column prop="startLocation" label="起点" width="110" />
        <el-table-column prop="endLocation" label="终点" width="110" />

        <el-table-column prop="orderAmount" label="金额" width="100">
          <template #default="{ row }">
            ¥{{ row.orderAmount }}
          </template>
        </el-table-column>

        <el-table-column prop="orderStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.orderStatus)" effect="light">
              {{ getStatusText(row.orderStatus) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="paymentMethod" label="支付方式" width="110" />
        <el-table-column prop="orderTime" label="下单时间" min-width="170" />

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
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
          @size-change="loadOrders"
          @current-change="loadOrders"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="620px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
      >
        <el-form-item label="订单编号" prop="orderNo">
          <el-input v-model="form.orderNo" placeholder="请输入订单编号" />
        </el-form-item>

        <el-form-item label="用户ID" prop="userId">
          <el-input v-model="form.userId" placeholder="请输入用户ID" />
        </el-form-item>

        <el-form-item label="城市" prop="city">
          <el-select
            v-model="form.city"
            placeholder="请选择城市"
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option label="北京" value="北京" />
            <el-option label="上海" value="上海" />
            <el-option label="广州" value="广州" />
            <el-option label="深圳" value="深圳" />
            <el-option label="杭州" value="杭州" />
            <el-option label="成都" value="成都" />
            <el-option label="武汉" value="武汉" />
            <el-option label="南京" value="南京" />
          </el-select>
        </el-form-item>

        <el-form-item label="起点" prop="startLocation">
          <el-input v-model="form.startLocation" placeholder="请输入起点" />
        </el-form-item>

        <el-form-item label="终点" prop="endLocation">
          <el-input v-model="form.endLocation" placeholder="请输入终点" />
        </el-form-item>

        <el-form-item label="订单金额" prop="orderAmount">
          <el-input-number
            v-model="form.orderAmount"
            :min="0"
            :precision="2"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="订单状态" prop="orderStatus">
          <el-select
            v-model="form.orderStatus"
            placeholder="请选择订单状态"
            style="width: 100%"
          >
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="待处理" value="pending" />
          </el-select>
        </el-form-item>

        <el-form-item label="支付方式" prop="paymentMethod">
          <el-select
            v-model="form.paymentMethod"
            placeholder="请选择支付方式"
            clearable
            style="width: 100%"
          >
            <el-option label="微信支付" value="微信支付" />
            <el-option label="支付宝" value="支付宝" />
            <el-option label="银行卡" value="银行卡" />
            <el-option label="余额支付" value="余额支付" />
          </el-select>
        </el-form-item>

        <el-form-item label="下单时间" prop="orderTime">
          <el-date-picker
            v-model="form.orderTime"
            type="datetime"
            placeholder="请选择下单时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "../api/request";

const loading = ref(false);
const submitLoading = ref(false);
const importLoading = ref(false);
const exportLoading = ref(false);
const orderList = ref([]);

const dialogVisible = ref(false);
const dialogTitle = ref("新增订单");
const formRef = ref(null);

const filters = reactive({
  orderNo: "",
  city: "",
  orderStatus: "",
  dateRange: [],
});

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
});

const form = reactive({
  id: null,
  orderNo: "",
  userId: "",
  city: "",
  startLocation: "",
  endLocation: "",
  orderAmount: 0,
  orderStatus: "completed",
  paymentMethod: "",
  orderTime: "",
});

const rules = {
  orderNo: [{ required: true, message: "请输入订单编号", trigger: "blur" }],
  userId: [{ required: true, message: "请输入用户ID", trigger: "blur" }],
  city: [{ required: true, message: "请选择城市", trigger: "change" }],
  startLocation: [{ required: true, message: "请输入起点", trigger: "blur" }],
  endLocation: [{ required: true, message: "请输入终点", trigger: "blur" }],
  orderAmount: [{ required: true, message: "请输入订单金额", trigger: "change" }],
  orderStatus: [{ required: true, message: "请选择订单状态", trigger: "change" }],
  orderTime: [{ required: true, message: "请选择下单时间", trigger: "change" }],
};

const getStatusText = (status) => {
  const map = {
    completed: "已完成",
    cancelled: "已取消",
    pending: "待处理",
  };

  return map[status] || status;
};

const getStatusType = (status) => {
  const map = {
    completed: "success",
    cancelled: "danger",
    pending: "warning",
  };

  return map[status] || "info";
};

const generateOrderNo = () => {
  const now = new Date();

  const pad = (num) => String(num).padStart(2, "0");

  const year = now.getFullYear();
  const month = pad(now.getMonth() + 1);
  const day = pad(now.getDate());
  const hour = pad(now.getHours());
  const minute = pad(now.getMinutes());
  const second = pad(now.getSeconds());
  const random = Math.floor(Math.random() * 900 + 100);

  return `OD${year}${month}${day}${hour}${minute}${second}${random}`;
};

const resetForm = () => {
  Object.assign(form, {
    id: null,
    orderNo: generateOrderNo(),
    userId: `U${Math.floor(Math.random() * 90000 + 10000)}`,
    city: "",
    startLocation: "",
    endLocation: "",
    orderAmount: 0,
    orderStatus: "completed",
    paymentMethod: "",
    orderTime: "",
  });

  formRef.value?.clearValidate?.();
};

const loadOrders = async () => {
  loading.value = true;

  try {
    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      orderNo: filters.orderNo || undefined,
      city: filters.city || undefined,
      orderStatus: filters.orderStatus || undefined,
      startDate: filters.dateRange?.[0] || undefined,
      endDate: filters.dateRange?.[1] || undefined,
    };

    const res = await request.get("/api/orders", { params });

    if (res.code === 200) {
      orderList.value = res.data.list;
      pagination.total = res.data.total;
    } else {
      ElMessage.error(res.message || "获取订单列表失败");
    }
  } catch (error) {
    ElMessage.error("订单列表接口请求失败");
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.page = 1;
  loadOrders();
};

const handleReset = () => {
  filters.orderNo = "";
  filters.city = "";
  filters.orderStatus = "";
  filters.dateRange = [];

  pagination.page = 1;
  loadOrders();
};

const handleAdd = () => {
  dialogTitle.value = "新增订单";
  resetForm();
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  dialogTitle.value = "编辑订单";

  Object.assign(form, {
    id: row.id,
    orderNo: row.orderNo,
    userId: row.userId,
    city: row.city,
    startLocation: row.startLocation,
    endLocation: row.endLocation,
    orderAmount: row.orderAmount,
    orderStatus: row.orderStatus,
    paymentMethod: row.paymentMethod,
    orderTime: row.orderTime,
  });

  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();

  submitLoading.value = true;

  try {
    const payload = {
      orderNo: form.orderNo,
      userId: form.userId,
      city: form.city,
      startLocation: form.startLocation,
      endLocation: form.endLocation,
      orderAmount: form.orderAmount,
      orderStatus: form.orderStatus,
      paymentMethod: form.paymentMethod,
      orderTime: form.orderTime,
    };

    const res = form.id
      ? await request.put(`/api/orders/${form.id}`, payload)
      : await request.post("/api/orders", payload);

    if (res.code === 200) {
      ElMessage.success(res.message || "保存成功");
      dialogVisible.value = false;
      loadOrders();
    } else {
      ElMessage.error(res.message || "保存失败");
    }
  } catch (error) {
    ElMessage.error("保存订单失败");
  } finally {
    submitLoading.value = false;
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除订单 ${row.orderNo} 吗？`,
      "删除确认",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    const res = await request.delete(`/api/orders/${row.id}`);

    if (res.code === 200) {
      ElMessage.success("删除成功");
      loadOrders();
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除订单失败");
    }
  }
};

onMounted(() => {
  loadOrders();
});

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

    const res = await request.post("/api/orders/import", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    if (res.code === 200) {
      const createdCount = res.data?.createdCount ?? 0;
      const skippedCount = res.data?.skippedCount ?? 0;

      ElMessage.success(
        `导入成功：新增 ${createdCount} 条，跳过 ${skippedCount} 条`
      );

      pagination.page = 1;
      loadOrders();
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

    if (filters.orderNo) {
      params.append("orderNo", filters.orderNo);
    }

    if (filters.city) {
      params.append("city", filters.city);
    }

    if (filters.orderStatus) {
      params.append("orderStatus", filters.orderStatus);
    }

    if (filters.dateRange?.[0]) {
      params.append("startDate", filters.dateRange[0]);
    }

    if (filters.dateRange?.[1]) {
      params.append("endDate", filters.dateRange[1]);
    }

    const queryString = params.toString();

    const url = queryString
      ? `http://127.0.0.1:5000/api/orders/export?${queryString}`
      : "http://127.0.0.1:5000/api/orders/export";

    const link = document.createElement("a");

    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");

    link.href = url;
    link.download = `orders_export_${year}${month}${day}.csv`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    ElMessage.success("导出成功");
  } catch (error) {
    console.error("导出 CSV 失败：", error);
    ElMessage.error("导出 CSV 失败");
  } finally {
    setTimeout(() => {
      exportLoading.value = false;
    }, 500);
  }
};

</script>

<style scoped>
.order-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding: 16px 20px;
  box-sizing: border-box;
}

.page-title {
  background: white;
  border-radius: 12px;
  padding: 18px 22px;
  margin-bottom: 16px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title h2 {
  margin: 0;
  font-size: 22px;
  color: #1f2937;
}

.page-title p {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.filter-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.table-card {
  border-radius: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>