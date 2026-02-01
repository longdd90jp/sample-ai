<template>
  <section class="panel glass">
    <div class="panel-header">
      <div>
        <h2>Categories</h2>
        <p class="muted">Organize your FAQ knowledge base by theme.</p>
      </div>
      <button class="primary" @click="openCreate">New Category</button>
    </div>

    <div v-if="loading" class="muted">Loading categories...</div>
    <div v-else-if="categories.length === 0" class="empty-state">
      <h3>No categories yet</h3>
      <p>Create the first category to get started.</p>
      <button class="primary compact" @click="openCreate">Create Category</button>
    </div>

    <CategoryList
      v-else
      :categories="categories"
      @edit="openEdit"
      @remove="removeCategory"
    />

    <CategoryEdit
      :show="showForm"
      :initial-form="form"
      :is-editing="isEditing"
      :error="error"
      @close="closeForm"
      @save="saveCategory"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import api from "../../api";
import CategoryEdit from "./components/CategoryEdit.vue";
import CategoryList from "./components/CategoryList.vue";

const categories = ref([]);
const loading = ref(false);
const showForm = ref(false);
const error = ref("");
const form = ref({
  id: null,
  name: "",
  description: "",
});

const isEditing = computed(() => Boolean(form.value.id));

const resetForm = () => {
  form.value = { id: null, name: "", description: "" };
  error.value = "";
};

const loadCategories = async () => {
  loading.value = true;
  try {
    const { data } = await api.get("/categories");
    categories.value = data.map((item) => ({
      ...item,
      id: item.id ?? item._id,
    }));
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const openCreate = () => {
  resetForm();
  showForm.value = true;
};

const openEdit = (category) => {
  form.value = {
    id: category.id,
    name: category.name,
    description: category.description || "",
  };
  error.value = "";
  showForm.value = true;
};

const closeForm = () => {
  showForm.value = false;
  resetForm();
};

const saveCategory = async (payload) => {
  if (!payload.name.trim()) {
    error.value = "Name is required.";
    return;
  }
  try {
    if (payload.id) {
      await api.put(`/categories/${payload.id}`, {
        name: payload.name,
        description: payload.description,
      });
    } else {
      await api.post("/categories", {
        name: payload.name,
        description: payload.description,
      });
    }
    await loadCategories();
    closeForm();
  } catch (err) {
    console.error(err);
    error.value = "Unable to save category.";
  }
};

const removeCategory = async (id) => {
  if (!confirm("Delete this category?")) {
    return;
  }
  try {
    await api.delete(`/categories/${id}`);
    await loadCategories();
  } catch (err) {
    console.error(err);
  }
};

onMounted(loadCategories);
</script>
