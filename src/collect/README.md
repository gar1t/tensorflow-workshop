# collect

Web application used to collect images from one or more cameras.

## Build Setup

``` bash
# install dependencies
npm install

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# build for production and view the bundle analyzer report
npm run build --report
```

For a detailed explanation on how things work, check out the
[guide](http://vuejs-templates.github.io/webpack/) and [docs for
vue-loader](http://vuejs.github.io/vue-loader).

## Configuration

Configuration should be in this form:

``` json
{
  "cameras": {
    "camera-1": {
      "host": "192.168.1.108",
      "user": "...",
      "password": ..."
    },
    ...
  }
}
```
