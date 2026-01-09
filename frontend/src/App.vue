<template>
  <div class="p-4">
    <h2>症状解析与下单</h2>
    <textarea v-model="symptom" rows="4" placeholder="输入症状..."></textarea>
    <button @click="submit">生成用药清单</button>

    <div v-if="resp">
      <h3>用药清单</h3>
      <pre>{{ resp.plan }}</pre>
      <h3>价格与库存</h3>
      <pre>{{ resp.items }}</pre>
      <h3>订单</h3>
      <pre>{{ resp.order }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";
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