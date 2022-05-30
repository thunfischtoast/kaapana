<template>
  <div>
    <div v-for="[_, propertyValues] in Object.entries(properties)">
      <FilterDropdown
          :label="propertyValues['displayName']"
          :options="propertyValues['options']"
          v-model="propertyValues['selected']"
      />
    </div>
    <Button @click="evaluateQuery">Get Patients</Button>
  </div>

</template>

<script lang="ts">
import FilterDropdown from "@/components/FilterDropdown.vue";

const _props = {
  "00080020 StudyDate_date": {
    displayName: "Study Date",
    key: "key_as_string",
    options: [],
    selected: []
  },
  "00080021 SeriesDate_date": {
    displayName: "Series Date",
    key: "key_as_string",
    options: [],
    selected: []
  },
  "00100010 PatientName_keyword_alphabetic.keyword": {
    displayName: "Patient Name",
    key: "key",
    options: [],
    selected: []
  }
}
export default {
  components: {
    FilterDropdown
  },
  data: () => ({
    baseUrl: "https://" + window.location.href.split("//")[1].split("/")[0],
    data: null,
    properties: _props
  }),
  created() {
    fetch(this.baseUrl + "/elasticsearch/meta-index/_search/")
        .then(response => response.json())
        .then(data => this.data = data);

    Object.entries(this.properties).forEach(([id, value]) => this.getUniqueValues(id, value))
  },
  methods: {
    evaluateQuery() {

      const data = {
        "query": {
          "match": Object.fromEntries(
              Object.entries(this.properties)
                  .filter(([_, value]) => value['selected'].length > 0)
                  .map(([id, value]) => [id, value['selected'].join(" ")])
          )
        }
      }
      console.log(JSON.stringify(data))

      fetch(this.baseUrl + "/elasticsearch/meta-index/_search#/", {
        method: 'POST',
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
      })
          .then(response => response.json())
          .then(data => data)
          .catch(error => console.log('error', error));
    },
    getUniqueValues(id, value) {
      const data = {
        "size": 0,
        "aggs": {
          "langs": {
            "terms": {
              "field": id,
              "size": 500
            }
          }
        }
      }

      fetch(this.baseUrl + "/elasticsearch/meta-index/_search#/", {
        method: 'POST',
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
      })
          .then(response => response.json())
          .then(data =>
              this.properties[id]['options'] = data["aggregations"]["langs"]["buckets"]
                  .map(element => element[value["key"]])
          ).catch(error => console.log('error', error));
    }
  }
};
</script>
