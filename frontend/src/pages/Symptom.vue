<template>
  <div>
    <h2>症状解析</h2>
    <textarea v-model="symptom" rows="4"></textarea>
    <button @click="submit">生成用药清单</button>
    <ExplainPanel v-if="resp" :plan="resp.plan" :items="resp.items" />
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";
import ExplainPanel from "../components/ExplainPanel.vue";

const symptom = ref("");
const resp = ref<any>(null);

async function submit() {
  const { data } = await axios.post("http://localhost:8000/symptom/plan", {
    symptom: symptom.value,
    user_ctx: { pregnant: false, prescription_uploaded: false, fever_celsius: 37.5 },
    member_tier: "gold",
    member_id: 1
  });
  resp.value = data;
}
</script>