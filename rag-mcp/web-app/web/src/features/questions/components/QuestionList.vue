<template>
  <div class="accordion">
    <QuestionDetail
      v-for="question in questions"
      :key="question.id"
      :question="question"
      :category-label="categoryLabel"
      :format-date="formatDate"
      @edit="() => $emit('edit', question)"
      @remove="() => $emit('remove', question.id)"
    />
  </div>
</template>

<script setup>
import QuestionDetail from "./QuestionDetail.vue";

defineProps({
  questions: {
    type: Array,
    default: () => [],
  },
  categoryLabel: {
    type: Function,
    required: true,
  },
  formatDate: {
    type: Function,
    required: true,
  },
});

defineEmits(["edit", "remove"]);
</script>