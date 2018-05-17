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
    <v-card-actions>
      <v-btn
        v-if="loaded"
        :disabled="saving"
        color="orange darken-2" dark
        @click="save">Save</v-btn>
      <v-btn
        flat
        v-if="loaded || error"
        @click="refresh">Refresh</v-btn>
    </v-card-actions>
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
      return dataUrl('/cameras/' + this.id + '/img.jpg?' + this.ver);
    }
  },

  mounted() {
    const img = this.$refs.img;
    img.onload = this.onLoad;
    img.onerror = this.onError;
    img.onabort = this.onAbort;
  },

  methods: {
    refresh() {
      this.loaded = false;
      this.error = null;
      this.ver += 1;
    },

    save() {
      const vm = this;
      const saveUrl = dataUrl('/cameras/' + this.id + '/save');
      this.saving = true;
      fetch(saveUrl, {method: 'post'}).then(function() {
        vm.refresh();
      });
    },

    onLoad(e) {
      this.loaded = true;
      this.saving = false;
      this.error = null;
    },

    onError(e) {
      console.log('ERROR', e);
      this.error = e;
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
