<template>
  <v-card flat>
    <v-card-title>
      <h2>{{ id }}</h2>
    </v-card-title>
    <img :src="imageUrl" ref="img" v-show="loaded">
    <div class="waiting" v-if="!loaded">
      <v-progress-linear :indeterminate="true" height="5"></v-progress-linear>
      <div>Waiting for image</div>
    </div>
    <div class="error" v-if="error">
      <div>An error occurred loading the image</div>
    </div>
    <!--
    <v-card-actions>
      <v-btn
        flat
        v-if="loaded || error"
        @click="refresh">Refresh</v-btn>
    </v-card-actions>
    -->
  </v-card>
</template>

<script>
import { dataUrl } from './util.js';

export default {
  name: 'camera',

  props: {
    id: {
      type: String,
      required: true
    },
    refreshInterval: {
      type: Number,
      default: 5
    }
  },

  data() {
    return {
      loaded: false,
      error: null,
      ver: 1,
      saving: false
    };
  },

  computed: {
    imageUrl() {
      return dataUrl('/detected/' + this.id + '.png?' + this.ver);
    }
  },

  mounted() {
    const img = this.$refs.img;
    img.onload = this.onLoad;
    img.onerror = this.onError;
    img.onabort = this.onAbort;
  },

  methods: {
    refresh(progress) {
      if (progress) {
        this.loaded = false;
      }
      this.error = null;
      this.ver += 1;
    },

    onLoad(e) {
      this.loaded = true;
      this.saving = false;
      this.error = null;
      const vm = this;
      setTimeout(function() {
        vm.refresh(false);
      }, this.refreshInterval * 1000);
    },

    onError(e) {
      // ignore, assuming 404
    },

    onAbort(e) {
      console.log('ABORT', e);
      this.error = e;
    }
  }
};
</script>

<style scoped>
img {
  padding: 0 16px;
  max-width: 100%;
}

.waiting, .error {
  padding: 0 16px;
  margin-bottom: 16px;
}
</style>
