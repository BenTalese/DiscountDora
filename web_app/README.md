# Discount Dora (discount-dora)

Your grocery explorer!

## Install the dependencies
```bash
yarn
# or
npm install
```

### Start the app in development mode (hot-code reloading, error reporting, etc.)
```bash
quasar dev
```


### Lint the files
```bash
yarn lint
# or
npm run lint
```


### Format the files
```bash
yarn format
# or
npm run format
```


### Build the app for production
```bash
quasar build
```

### Customize the configuration
See [Configuring quasar.config.js](https://v2.quasar.dev/quasar-cli-vite/quasar-config-js).

### Camera scanning (Data → Barcodes & QR)

The barcode/QR scan overlay uses `@zxing/browser`, which needs the browser's
`getUserMedia` API. Browsers gate that on a **secure context** — it works
freely on `http://localhost` and `http://127.0.0.1` during development, but
any other hostname (LAN IP, ngrok tunnel, production deploy) must serve the
app over **HTTPS** or the camera button will silently fail with a permission
error.

For a quick LAN test on phones / tablets, point a local HTTPS proxy (e.g.
`caddy reverse-proxy --to localhost:5174`) at the dev server and visit it
on your other device.
