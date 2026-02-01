<template>
  <div class="card-grid">
    <CategoryDetail
      v-for="category in categories"
      :key="category.id"
      :category="category"
      @edit="() => $emit('edit', category)"
      @remove="() => $emit('remove', category.id)"
    />
  </div>
</template>

<script setup>
import CategoryDetail from "./CategoryDetail.vue";

defineProps({
  categories: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["edit", "remove"]);
</script>