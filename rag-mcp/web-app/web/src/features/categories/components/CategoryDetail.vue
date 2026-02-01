<template>
  <article class="glass-card">
    <h3>{{ category.name }}</h3>
    <p>{{ category.description || "No description yet." }}</p>
    <div class="card-actions">
      <button class="ghost" @click="$emit('edit')">Edit</button>
      <button class="danger" @click="$emit('remove')">Delete</button>
    </div>
  </article>
</template>

<script setup>
defineProps({
  category: {
    type: Object,
    required: true,
  },
});

defineEmits(["edit", "remove"]);
</script>