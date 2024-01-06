import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// import ErrorPopup from './components/ErrorPopup.vue'

import 'bootstrap/dist/css/bootstrap.css'
// import './assets/main.css'

const app = createApp(App)

app.config.errorHandler = (err, vm, info) => {
    console.error('Global Error Handler:', err, vm, info);
    // alert(err);
    return false;
};
// app.component('ErrorPopup', ErrorPopup);

app.use(router)

app.mount('#app')
