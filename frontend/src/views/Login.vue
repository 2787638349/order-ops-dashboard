<template>
  <div class="login-page">
    <section class="login-showcase">
      <div class="showcase-badge">NYC Yellow Taxi 订单运营分析</div>
      <h1>出行平台订单运营分析系统</h1>
      <p>聚合订单趋势、区域热点、异常行程和行程明细，让出租车运营数据更容易被理解和展示。</p>

      <div class="showcase-grid">
        <div class="showcase-card primary-card">
          <span>订单趋势</span>
          <strong>每日行程变化</strong>
          <div class="bar-preview" aria-hidden="true">
            <i v-for="height in [42, 64, 52, 78, 68, 88, 76]" :key="height" :style="{ height: `${height}%` }"></i>
          </div>
        </div>
        <div class="showcase-card">
          <span>成交统计</span>
          <strong>金额 / 客单价</strong>
          <em>随日期范围更新</em>
        </div>
        <div class="showcase-card warning">
          <span>异常识别</span>
          <strong>异常行程原因</strong>
          <em>支持明细追踪</em>
        </div>
        <div class="showcase-card">
          <span>区域分析</span>
          <strong>上车 / 下车 Top10</strong>
          <em>排行榜图表</em>
        </div>
      </div>
    </section>

    <section class="login-card">
      <div class="login-logo">
        <el-icon><Van /></el-icon>
      </div>

      <div class="login-header">
        <h2>登录分析后台</h2>
        <p>使用演示账号进入订单运营数据看板。</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="login-form">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            placeholder="请输入密码"
            type="password"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="login-button"
          :loading="loading"
          @click="handleLogin"
        >
          登录系统
        </el-button>
      </el-form>

      <div class="login-tip">
        <span>演示账号</span>
        <strong>admin / 123456</strong>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { Lock, User, Van } from "@element-plus/icons-vue";
import request from "../api/request";

const emit = defineEmits(["login-success"]);

const loading = ref(false);
const formRef = ref(null);

const form = reactive({
  username: "admin",
  password: "123456",
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();

  loading.value = true;

  try {
    const res = await request.post("/api/auth/login", {
      username: form.username,
      password: form.password,
    });

    if (res.code === 200) {
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("username", res.data.username);

      ElMessage.success("登录成功");
      emit("login-success");
    } else {
      ElMessage.error(res.message || "登录失败");
    }
  } catch (error) {
    ElMessage.error("用户名或密码错误");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 40px 48px;
  display: grid;
  grid-template-columns: minmax(460px, 660px) 420px;
  align-items: center;
  justify-content: center;
  gap: 58px;
  background:
    radial-gradient(circle at 16% 18%, rgba(29, 99, 216, 0.16), transparent 28%),
    radial-gradient(circle at 84% 14%, rgba(245, 158, 11, 0.11), transparent 24%),
    linear-gradient(135deg, #edf4fb 0%, #f8fbff 48%, #e7eef7 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, transparent 18%, rgba(29, 99, 216, 0.07) 18.2%, transparent 18.7%),
    linear-gradient(300deg, transparent 62%, rgba(245, 158, 11, 0.08) 62.2%, transparent 62.7%);
}

.login-showcase,
.login-card {
  position: relative;
  z-index: 1;
}

.showcase-badge {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  color: #1d63d8;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid #dce6f2;
  font-size: 13px;
  font-weight: 760;
}

.login-showcase h1 {
  margin-top: 18px;
  color: #082b5f;
  font-size: 44px;
  line-height: 1.08;
  font-weight: 820;
}

.login-showcase p {
  max-width: 560px;
  margin-top: 16px;
  color: #53657d;
  font-size: 16px;
  line-height: 1.8;
}

.showcase-grid {
  width: min(580px, 100%);
  margin-top: 30px;
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 12px;
}

.showcase-card {
  min-height: 108px;
  padding: 15px;
  border: 1px solid #dce6f2;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.06);
}

.primary-card {
  grid-row: span 2;
}

.showcase-card.warning {
  border-color: #f3d08b;
  background: rgba(255, 247, 226, 0.9);
}

.showcase-card span,
.showcase-card em {
  display: block;
  color: #64748b;
  font-size: 13px;
  font-style: normal;
  font-weight: 700;
}

.showcase-card strong {
  display: block;
  margin-top: 8px;
  color: #142033;
  font-size: 19px;
  line-height: 1.25;
  font-weight: 800;
}

.showcase-card em {
  margin-top: 18px;
}

.bar-preview {
  height: 124px;
  margin-top: 22px;
  display: flex;
  align-items: flex-end;
  gap: 9px;
}

.bar-preview i {
  flex: 1;
  min-width: 10px;
  border-radius: 999px 999px 4px 4px;
  background: linear-gradient(180deg, #2d7cff, rgba(45, 124, 255, 0.18));
}

.login-card {
  width: 420px;
  padding: 30px 34px 28px;
  border: 1px solid #dce6f2;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 4px 8px rgba(15, 23, 42, 0.08);
}

.login-logo {
  width: 70px;
  height: 70px;
  margin: -8px auto 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  border: 1px solid #dce6f2;
  background: #ffffff;
  color: #082b5f;
  font-size: 30px;
  box-shadow: 0 4px 8px rgba(29, 99, 216, 0.14);
}

.login-header {
  margin: 18px 0 22px;
  text-align: center;
}

.login-header h2 {
  color: #142033;
  font-size: 28px;
  line-height: 1.25;
  font-weight: 820;
}

.login-header p {
  margin-top: 8px;
  color: #64748b;
  font-size: 14px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-form-item__label) {
  color: #53657d;
  font-size: 14px;
  font-weight: 700;
  line-height: 20px;
  margin-bottom: 7px;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 42px;
  border-radius: 10px;
}

.login-button {
  width: 100%;
  height: 44px;
  margin-top: 4px;
  border-radius: 10px;
  font-weight: 800;
  box-shadow: 0 4px 8px rgba(29, 99, 216, 0.18);
}

.login-tip {
  margin-top: 18px;
  padding: 12px 14px;
  border: 1px solid #f3d08b;
  background: #fff7df;
  border-radius: 10px;
}

.login-tip span {
  display: block;
  color: #9a5b00;
  font-size: 13px;
  font-weight: 800;
}

.login-tip strong {
  display: block;
  margin-top: 4px;
  color: #142033;
  font-size: 15px;
}

@media (max-width: 980px) {
  .login-page {
    grid-template-columns: 1fr;
    gap: 28px;
    padding: 28px 18px;
  }

  .login-showcase {
    max-width: 640px;
    margin: 0 auto;
  }

  .login-card {
    width: min(420px, 100%);
    margin: 0 auto;
  }
}

@media (max-width: 640px) {
  .login-showcase h1 {
    font-size: 36px;
  }

  .showcase-grid {
    grid-template-columns: 1fr;
  }

  .primary-card {
    grid-row: auto;
  }
}
</style>
