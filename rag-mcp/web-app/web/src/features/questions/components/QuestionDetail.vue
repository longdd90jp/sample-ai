<template>
  <details class="question-item glass-card">
    <summary>
      <div>
        <p class="question-title">{{ question.question }}</p>
        <span class="badge">{{ categoryLabel(question.cate_id) }}</span>
      </div>
      <span class="meta">{{ formatDate(question.created_at) }}</span>
    </summary>
    <div class="answer">
      <p>{{ question.answer }}</p>
      <div class="card-actions">
        <button class="ghost" @click="$emit('edit')">Edit</button>
        <button class="danger" @click="$emit('remove')">Delete</button>
      </div>
    </div>
  </details>
</template>

<script setup>
defineProps({
  question: {
    type: Object,
    required: true,
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