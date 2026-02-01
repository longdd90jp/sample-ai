<template>
  <div class="filter-row">
    <label>
      Filter by Category
      <select v-model="model">
        <option value="all">All categories</option>
        <option v-for="category in categories" :key="category.id" :value="category.id">
          {{ category.name }}
        </option>
      </select>
    </label>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  categories: {
    type: Array,
    default: () => [],
  },
  selected: {
    type: String,
    default: "all",
  },
});

const emit = defineEmits(["update:selected"]);

const model = computed({
  get: () => props.selected,
  set: (value) => emit("update:selected", value),
});
</script>