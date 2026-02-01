<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal glass">
      <h3>{{ isEditing ? "Edit Question" : "New Question" }}</h3>
      <form @submit.prevent="submit">
        <label>
          Category
          <select v-model="localForm.cate_id">
            <option disabled value="">Select a category</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
        </label>
        <label>
          Question
          <input v-model="localForm.question" type="text" placeholder="Ask a question" />
        </label>
        <label>
          Answer
          <textarea v-model="localForm.answer" rows="4" placeholder="Provide a clear answer" />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button type="button" class="ghost" @click="$emit('close')">Cancel</button>
          <button type="submit" class="primary">Save</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  initialForm: {
    type: Object,
    default: () => ({ id: null, cate_id: "", question: "", answer: "" }),
  },
  categories: {
    type: Array,
    default: () => [],
  },
  isEditing: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["close", "save"]);

const localForm = ref({ ...props.initialForm });

watch(
  () => props.initialForm,
  (value) => {
    localForm.value = { ...value };
  },
  { deep: true }
);

watch(
  () => props.show,
  (value) => {
    if (value) {
      localForm.value = { ...props.initialForm };
    }
  }
);

const submit = () => {
  emit("save", { ...localForm.value });
};
</script>