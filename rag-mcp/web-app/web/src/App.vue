<template>
  <div class="app-shell">
    <header class="topbar glass">
      <div>
        <p class="eyebrow">FAQ Management</p>
        <h1>Knowledge Base Console</h1>
      </div>
      <div class="topbar-actions">
        <nav class="tab-group">
          <button
            class="tab"
            :class="{ active: activeTab === 'categories' }"
            @click="activeTab = 'categories'"
          >
            Categories
          </button>
          <button
            class="tab"
            :class="{ active: activeTab === 'questions' }"
            @click="activeTab = 'questions'"
          >
            Questions
          </button>
        </nav>
        <div class="theme-toggle">
          <span>{{ themeLabel }}</span>
          <button class="ghost" @click="toggleTheme">
            Switch
          </button>
        </div>
      </div>
    </header>

    <main class="content">
      <CategoryManager v-if="activeTab === 'categories'" />
      <QuestionManager v-else />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import CategoryManager from "./features/categories/CategoryManager.vue";
import QuestionManager from "./features/questions/QuestionManager.vue";

const activeTab = ref("categories");
const theme = ref("light");

const applyTheme = () => {
  document.documentElement.setAttribute("data-theme", theme.value);
};

const toggleTheme = () => {
  theme.value = theme.value === "light" ? "dark" : "light";
  localStorage.setItem("faq-theme", theme.value);
  applyTheme();
};

const themeLabel = computed(() => (theme.value === "light" ? "Light" : "Dark"));

onMounted(() => {
  theme.value = localStorage.getItem("faq-theme") || "light";
  applyTheme();
});
</script>
