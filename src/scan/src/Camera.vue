<template>
  <div>
    <v-card flat>
      <v-card-title>
        <h2>{{ id }}</h2>
      </v-card-title>
      <img ref="img" class="normal" v-show="loaded" @click.stop="openImage">
      <div class="waiting" v-if="!loaded">
        <v-progress-linear :indeterminate="true" height="5"></v-progress-linear>
        <div>Waiting for image</div>
      </div>
    </v-card>
    <v-dialog v-model="fullscreen">
      <v-btn flat icon dark large @click="fullscreen = false"><v-icon large>close</v-icon></v-btn>
      <img ref="fullscreenImg" class="fullscreen">
    </v-dialog>
  </div>
</template>

<script>
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
      fullscreen: false
    };
  },

  methods: {
    clearImage() {
      this.loaded = false;
      this.$refs.img.src = '';
    },

    setImage(encoded) {
      this.$refs.img.src = encoded;
      this.loaded = true;
    },

    openImage() {
      this.$refs.fullscreenImg.src = this.$refs.img.src;
      this.fullscreen = true;
    }
  }
};
</script>

<style>
.dialog {
  box-shadow: none;
  display: inline-block;
  width: unset;
  position: relative;
}
</style>

<style scoped>
img.normal {
  padding: 0 16px;
  max-width: 100%;
  cursor: pointer;
}

.waiting {
  padding: 0 16px;
  margin-bottom: 16px;
}

.dialog button {
  position: absolute;
  right: 0;
}
</style>
