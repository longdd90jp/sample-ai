<template>
  <section class="panel glass">
    <div class="panel-header">
      <div>
        <h2>Questions</h2>
        <p class="muted">Curate answers and keep everything searchable.</p>
      </div>
      <button class="primary" @click="openCreate">New Question</button>
    </div>

    <QuestionFilter
      :categories="categories"
      v-model:selected="selectedCategory"
    />

    <div v-if="loading" class="muted">Loading questions...</div>
    <div v-else-if="questions.length === 0" class="empty-state">
      <h3>No questions yet</h3>
      <p>Add a question and connect it to a category.</p>
      <button class="primary compact compact-center" @click="openCreate">
        Create Question
      </button>
    </div>

    <QuestionList
      v-else
      :questions="filteredQuestions"
      :category-label="categoryLabel"
      :format-date="formatDate"
      @edit="openEdit"
      @remove="removeQuestion"
    />

    <QuestionEdit
      :show="showForm"
      :initial-form="form"
      :categories="categories"
      :is-editing="isEditing"
      :error="error"
      @close="closeForm"
      @save="saveQuestion"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import api from "../../api";
import QuestionEdit from "./components/QuestionEdit.vue";
import QuestionFilter from "./components/QuestionFilter.vue";
import QuestionList from "./components/QuestionList.vue";

const categories = ref([]);
const questions = ref([]);
const loading = ref(false);
const showForm = ref(false);
const error = ref("");
const selectedCategory = ref("all");
const form = ref({
  id: null,
  cate_id: "",
  question: "",
  answer: "",
});

const isEditing = computed(() => Boolean(form.value.id));

const categoryMap = computed(() => {
  return categories.value.reduce((acc, category) => {
    acc[category.id] = category.name;
    return acc;
  }, {});
});

const filteredQuestions = computed(() => {
  if (selectedCategory.value === "all") {
    return questions.value;
  }
  return questions.value.filter((item) => item.cate_id === selectedCategory.value);
});

const loadData = async () => {
  loading.value = true;
  try {
    const [categoryRes, questionRes] = await Promise.all([
      api.get("/categories"),
      api.get("/questions"),
    ]);
    categories.value = categoryRes.data.map((item) => ({
      ...item,
      id: item.id ?? item._id,
    }));
    questions.value = questionRes.data;
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.value = { id: null, cate_id: "", question: "", answer: "" };
  error.value = "";
};

const openCreate = () => {
  resetForm();
  showForm.value = true;
};

const openEdit = (question) => {
  form.value = {
    id: question.id,
    cate_id: question.cate_id,
    question: question.question,
    answer: question.answer,
  };
  error.value = "";
  showForm.value = true;
};

const closeForm = () => {
  showForm.value = false;
  resetForm();
};

const saveQuestion = async (payload) => {
  if (!payload.cate_id) {
    error.value = "Please select a category.";
    return;
  }
  if (!payload.question.trim() || !payload.answer.trim()) {
    error.value = "Question and answer are required.";
    return;
  }
  try {
    if (payload.id) {
      await api.put(`/questions/${payload.id}`, {
        cate_id: payload.cate_id,
        question: payload.question,
        answer: payload.answer,
      });
    } else {
      await api.post("/questions", {
        cate_id: payload.cate_id,
        question: payload.question,
        answer: payload.answer,
      });
    }
    await loadData();
    closeForm();
  } catch (err) {
    console.error(err);
    error.value = "Unable to save question.";
  }
};

const removeQuestion = async (id) => {
  if (!confirm("Delete this question?")) {
    return;
  }
  try {
    await api.delete(`/questions/${id}`);
    await loadData();
  } catch (err) {
    console.error(err);
  }
};

const categoryLabel = (cateId) => {
  return categoryMap.value[cateId] || "Uncategorized";
};

const formatDate = (value) => {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

onMounted(loadData);
</script>
