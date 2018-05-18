<template>
  <v-app>
    <v-content>
      <v-card class="elevation-3" height="100%">
        <v-toolbar dark color="primary">
          <v-toolbar-title>Scanner</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="content-body">
          <v-container fluid>
            <v-layout row wrap>
              <v-flex
                md12 lg6
                v-for="key in cameras"
                :key="key">
                <camera :id="key" ref="cameras" />
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-content>
  </v-app>
</template>

<script>
import Camera from './Camera.vue';
import { fetchData } from './util.js';

export default {
  name: 'App',

  components: {
    Camera
  },

  data() {
    return {
      cameras: []
    };
  },

  created() {
    this.initCameras();
  },

  methods: {
    initCameras() {
      const vm = this;
      fetchData('/cameras', function(cameras) {
        vm.cameras = cameras;
      });
    }
  }
};
</script>

<style scoped>
.content-body {
  padding-top: 0;
}

.content-body > .container {
  padding: 6px 12px;
}

@media only screen and (max-width: 599px) {
  .content-body {
    padding: 0;
  }

  .content-body > .container {
    padding: 6px;
  }
}
</style>
