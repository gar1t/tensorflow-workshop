<template>
  <v-app>
    <v-content>
      <v-card class="elevation-3" height="100%">
        <v-toolbar dark color="primary">
          <v-toolbar-title>Collect Images</v-toolbar-title>
          <v-spacer />
          <v-btn flat @click="refreshAll">Refresh all</v-btn>
        </v-toolbar>
        <v-card-text class="content-body">
          <v-container fluid>
            <v-layout row wrap>
              <v-flex
                offset-sm1 sm10 offset-md0 md6 lg4
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
    },

    refreshAll() {
      this.$refs.cameras.forEach(c => c.refresh());
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
