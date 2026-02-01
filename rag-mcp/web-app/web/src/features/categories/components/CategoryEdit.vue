<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal glass">
      <h3>{{ isEditing ? "Edit Category" : "New Category" }}</h3>
      <form @submit.prevent="submit">
        <label>
          Name
          <input v-model="localForm.name" type="text" placeholder="Category name" />
        </label>
        <label class="form-label">
          Description
          <textarea
            v-model="localForm.description"
            rows="10"
            placeholder="Optional description"
          />
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
    default: () => ({ id: null, name: "", description: "" }),
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
