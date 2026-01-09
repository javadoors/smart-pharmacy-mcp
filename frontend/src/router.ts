import { createRouter, createWebHistory } from "vue-router";
import Search from "./pages/Search.vue";
import Symptom from "./pages/Symptom.vue";
import Checkout from "./pages/Checkout.vue";

const routes = [
  { path: "/", component: Search },
  { path: "/symptom", component: Symptom },
  { path: "/checkout", component: Checkout }
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});