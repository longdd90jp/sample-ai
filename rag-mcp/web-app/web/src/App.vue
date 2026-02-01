<template>
  <div class="app-shell">
    <header class="topbar glass">
      <div>
        <p class="eyebrow">FAQ Management</p>
        <h1>Knowledge Base Console</h1>
      </div>
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
    </header>

    <main class="content">
      <CategoryManager v-if="activeTab === 'categories'" />
      <QuestionManager v-else />
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import CategoryManager from "./features/categories/CategoryManager.vue";
import QuestionManager from "./features/questions/QuestionManager.vue";

const activeTab = ref("categories");
</script>