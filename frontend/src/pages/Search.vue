<template>
  <div>
    <h2>药品检索</h2>
    <input v-model="query" placeholder="输入药品名称或关键词" />
    <button @click="search">搜索</button>
    <div v-for="d in drugs" :key="d.drug_id">
      <DrugCard :drug="d" />
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";
import DrugCard from "../components/DrugCard.vue";

const query = ref("");
const drugs = ref<any[]>([]);

async function search() {
  const { data } = await axios.post("http://localhost:8000/drug/search", { query: query.value });
  drugs.value = data;
}
</script>