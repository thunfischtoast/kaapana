<template>
  <v-container fluid>
    <v-row align="center">
      <v-col>
        <v-select
            v-model="internalValue"
            :items=options
            :menu-props="{ maxHeight: '400' }"
            label="Select"
            multiple
            :hint="label"
            persistent-hint
            return-object
        ></v-select>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  props: {
    label: String,
    options: Array,
    selected: Array
  },
  data() {
    return {
      internalValue: this.selected
    }
  },
  watch: {
    internalValue(v) {
      this.$emit('input', v)
    }
  }
}
</script>

<style scoped>

</style>