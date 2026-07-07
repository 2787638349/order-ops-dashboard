<template>
  <Login v-if="!isLogin" @login-success="handleLoginSuccess" />

  <div v-else class="app-shell">
    <header class="top-bar">
      <button class="brand" type="button" aria-label="纽约黄出租运营分析">
        <div class="brand-mark">
          <el-icon><Van /></el-icon>
        </div>
        <div class="brand-copy">
          <span class="brand-title">出租车运营分析后台</span>
          <span class="brand-subtitle">NYC Yellow Taxi 订单数据后台</span>
        </div>
      </button>

      <el-menu
        mode="horizontal"
        :default-active="activePage"
        class="top-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="taxi-overview">
          <el-icon><DataBoard /></el-icon>
          <span>运营概览</span>
        </el-menu-item>
        <el-menu-item index="taxi-analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>专题/区域分析</span>
        </el-menu-item>
        <el-menu-item index="taxi-trips">
          <el-icon><Tickets /></el-icon>
          <span>行程记录管理</span>
        </el-menu-item>
      </el-menu>

      <div class="user-area">
        <div class="user-chip">
          <el-icon><User /></el-icon>
          <span>{{ username }}</span>
        </div>
        <el-button text class="logout-button" :icon="SwitchButton" @click="handleLogout">
          退出
        </el-button>
      </div>
    </header>

    <main class="page-main">
      <TaxiOverview v-if="activePage === 'taxi-overview'" />
      <TaxiAnalysis v-if="activePage === 'taxi-analysis'" />
      <TaxiTripManage v-if="activePage === 'taxi-trips'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { DataBoard, SwitchButton, Tickets, TrendCharts, User, Van } from "@element-plus/icons-vue";

import Login from "./views/Login.vue";
import TaxiAnalysis from "./views/TaxiAnalysis.vue";
import TaxiOverview from "./views/TaxiOverview.vue";
import TaxiTripManage from "./views/TaxiTripManage.vue";

const activePage = ref("taxi-overview");
const isLogin = ref(!!localStorage.getItem("token"));
const username = ref(localStorage.getItem("username") || "admin");

const handleMenuSelect = (index) => {
  activePage.value = index;
};

const handleLoginSuccess = () => {
  isLogin.value = true;
  username.value = localStorage.getItem("username") || "admin";
  activePage.value = "taxi-overview";
};

const handleLogout = async () => {
  await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
    confirmButtonText: "退出",
    cancelButtonText: "取消",
    type: "warning",
  });

  localStorage.removeItem("token");
  localStorage.removeItem("username");

  isLogin.value = false;
  activePage.value = "taxi-overview";

  ElMessage.success("已退出登录");
};
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  color: var(--text-primary);
}

.top-bar {
  height: 58px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(220, 230, 242, 0.9);
  display: grid;
  grid-template-columns: minmax(306px, auto) 1fr auto;
  align-items: center;
  gap: 24px;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 20;
  box-shadow: 0 3px 8px rgba(12, 30, 59, 0.055);
  backdrop-filter: blur(14px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: default;
  text-align: left;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--primary-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 21px;
  box-shadow: 0 4px 8px rgba(21, 88, 214, 0.12);
  position: relative;
  border: 1px solid rgba(220, 230, 242, 0.92);
}

.brand-mark::after {
  content: "";
  position: absolute;
  right: -3px;
  bottom: -3px;
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: var(--accent);
  border: 2px solid #ffffff;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-title {
  font-size: 18px;
  font-weight: 860;
  color: var(--text-primary);
  line-height: 1.1;
  white-space: nowrap;
}

.brand-subtitle {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.top-menu {
  height: 58px;
  border-bottom: none;
  background: transparent;
  min-width: 0;
}

.top-menu :deep(.el-menu-item) {
  height: 58px;
  line-height: 58px;
  margin: 0 3px;
  padding: 0 16px;
  border-bottom: none;
  border-radius: 0;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 680;
  gap: 7px;
  position: relative;
  transition: color 0.18s ease, background-color 0.18s ease;
}

.top-menu :deep(.el-menu-item::after) {
  content: "";
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 9px;
  height: 3px;
  border-radius: 999px;
  background: transparent;
  transition: background-color 0.18s ease;
}

.top-menu :deep(.el-menu-item:hover) {
  color: var(--primary);
  background: rgba(23, 92, 211, 0.055);
}

.top-menu :deep(.el-menu-item.is-active) {
  color: var(--primary);
  background: linear-gradient(180deg, rgba(23, 92, 211, 0.08), rgba(23, 92, 211, 0));
}

.top-menu :deep(.el-menu-item.is-active::after) {
  background: var(--primary);
}

.top-menu :deep(.el-icon) {
  margin-right: 2px;
  font-size: 17px;
}

.user-area {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.user-chip {
  height: 34px;
  padding: 0 13px;
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  color: var(--text-secondary);
  background: rgba(247, 250, 255, 0.9);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
}

.logout-button {
  min-height: 34px;
  color: var(--text-muted);
  padding: 0 8px;
}

.logout-button:hover {
  color: var(--primary);
  background: rgba(23, 92, 211, 0.06);
}

.page-main {
  min-height: calc(100vh - 58px);
}

@media (max-width: 1120px) {
  .top-bar {
    grid-template-columns: 1fr auto;
    height: auto;
    min-height: 58px;
    padding: 8px 14px;
  }

  .top-menu {
    grid-column: 1 / -1;
    order: 3;
    overflow-x: auto;
  }
}

@media (max-width: 640px) {
  .brand-subtitle {
    display: none;
  }

  .top-menu :deep(.el-menu-item) {
    padding: 0 12px;
  }
}
</style>
