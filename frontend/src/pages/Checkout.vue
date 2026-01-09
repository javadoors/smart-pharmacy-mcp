<template>
  <div class="p-4">
    <h2>订单结算</h2>

    <div v-if="order">
      <h3>订单信息</h3>
      <p>订单号: {{ order.order_id }}</p>
      <p>总金额: {{ order.total }} 元</p>
      <p>支付二维码: <a :href="order.payment_qr" target="_blank">点击支付</a></p>
    </div>

    <div v-if="items.length">
      <h3>订单明细</h3>
      <table border="1" cellpadding="8">
        <thead>
          <tr>
            <th>药品ID</th>
            <th>剂量</th>
            <th>单价</th>
            <th>折扣</th>
            <th>最终价格</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="it in items" :key="it.drug_id">
            <td>{{ it.drug_id }}</td>
            <td>{{ it.dose }}</td>
            <td>{{ it.unit_price }}</td>
            <td>{{ it.discount_rate }}</td>
            <td>{{ it.final_price }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!order">
      <p>暂无订单，请先在症状解析页生成用药清单。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import axios from "axios";

const order = ref<any>(null);
const items = ref<any[]>([]);

onMounted(async () => {
  // 假设后端提供 /order/latest 接口获取最近订单
  const { data } = await axios.get("http://localhost:8000/order/latest?member_id=1");
  order.value = data.order;
  items.value = data.items;
});
</script>