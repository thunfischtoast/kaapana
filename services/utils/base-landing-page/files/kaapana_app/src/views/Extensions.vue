<template lang="pug">
.workflow-applications
  v-container(grid-list-lg, text-left)
    v-card
      v-card-title
        v-row
          v-col(cols="12", sm="5")
            span Applications and workflows &nbsp;
              v-tooltip(bottom="")
                template(v-slot:activator="{ on, attrs }")
                  v-icon(
                    @click="updateExtensions()",
                    color="primary",
                    dark="",
                    v-bind="attrs",
                    v-on="on"
                  )
                    | mdi-cloud-download-outline
                span By clicking on this icon it will try to download the latest extensions.
            br
            span(style="font-size: 14px") On 
              a(href="https://kaapana.readthedocs.io/", target="_blank") readthedocs
              |
              | you find a description of each extension
          v-col(cols="12", sm="2")
            v-select(
              label="Kind",
              :items="['All', 'Workflows', 'Applications']",
              v-model="extensionKind",
              hide-details=""
            )
          v-col(cols="12", sm="2")
            v-select(
              label="Version",
              :items="['All', 'Stable', 'Experimental']",
              v-model="extensionExperimental",
              hide-details=""
            )
          v-col(cols="12", sm="3")
            v-text-field(
              v-model="search",
              append-icon="mdi-magnify",
              label="Search",
              hide-details=""
            )

      v-data-table.elevation-1(
        :headers="headers",
        :items="filteredLaunchedAppLinks",
        :items-per-page="20",
        :loading="loading",
        :search="search",
        sort-by="releaseName",
        loading-text="Waiting a few seconds..."
      )
        template(v-slot:item.releaseName="{ item }")
          span {{ item.releaseName }} &nbsp;
            a(
              :href="link",
              target="_blank",
              v-for="link in item.links",
              :key="item.link"
            )
              v-icon(color="primary") mdi-open-in-new
        template(v-slot:item.versions="{ item }") 
          v-select(
            v-if="item.installed === 'no'",
            :items="item.versions",
            v-model="item.version",
            hide-details=""
          )
          span(v-if="item.installed === 'yes'") {{ item.version }}
        template(v-slot:item.successful="{ item }")
          v-progress-circular(
            v-if="item.successful === 'pending'",
            indeterminate,
            color="primary"
          )
          v-icon(v-if="item.successful === 'yes'", color="green") mdi-check-circle
          v-icon(v-if="item.successful === 'no'", color="red") mdi-alert-circle
        template(v-slot:item.kind="{ item }")
          v-tooltip(bottom="", v-if="item.kind === 'dag'")
            template(v-slot:activator="{ on, attrs }")
              v-icon(color="primary", dark="", v-bind="attrs", v-on="on")
                | mdi-chart-timeline-variant
            span A workflow or algorithm that will be added to Airflow DAGs
          v-tooltip(bottom="", v-if="item.kind === 'application'")
            template(v-slot:activator="{ on, attrs }")
              v-icon(color="primary", dark="", v-bind="attrs", v-on="on")
                | mdi-laptop
            span An application to work with
        template(v-slot:item.experimental="{ item }")
          v-tooltip(bottom="", v-if="item.experimental === 'yes'")
            template(v-slot:activator="{ on, attrs }")
              v-icon(color="primary", dark="", v-bind="attrs", v-on="on")
                | mdi-test-tube
            span Experimental extension or DAG, not tested yet!
        template(v-slot:item.installed="{ item }")
          v-btn(
            @click="deleteChart(item)",
            color="primary",
            min-width = "160px",
            v-if="item.installed === 'yes' && item.successful !== 'pending' && item.successful !== 'justLaunched'"
          ) 
            span(v-if="item.multiinstallable === 'yes'") Delete
            span(v-if="item.multiinstallable === 'no'") Uninstall
          v-btn(
            @click="installChart(item)",
            color="primary",
            min-width = "160px",
            v-if="item.installed === 'no' && item.successful !== 'pending'"
          ) 
            span(v-if="item.multiinstallable === 'yes'") Launch
            span(v-if="item.multiinstallable === 'no'") Install
          v-btn(
            color="primary",
            min-width = "160px",
            disabled=true,
            v-if="item.successful === 'justLaunched'"
          ) 
            span() Launched
          v-menu(:close-on-content-click='false' v-if="item.successful === 'pending'")
            template(v-slot:activator='{ on, attrs }')
              v-btn(color="primary", min-width="160px", v-bind='attrs' v-on='on')
                | Pending
                v-icon mdi-chevron-down
            v-card(max-width="300px" text-left)
              v-card-title Pending states
              v-card-text In case your installation gets stuck in the "pending" state there is most probably something wrong with the helm chart. In that case you can here force to delete/uninstall the extension.
              v-card-actions
                v-btn(
                  @click="deleteChart(item, helmCommandAddons='--no-hooks');",
                  color="primary",
                  min-width="160px",
                ) 
                  span(v-if="item.multiinstallable === 'yes'") Delete forcefully
                  span(v-if="item.multiinstallable === 'no'") Uninstall forcefully
</template>

<script lang="ts">
import Vue from "vue";
import request from "@/request";
import { mapGetters } from "vuex";
import kaapanaApiService from "@/common/kaapanaApi.service";

export default Vue.extend({
  data: () => ({
    loading: true,
    polling: 0,
    launchedAppLinks: [] as any,
    search: "",
    extensionExperimental: "Stable",
    extensionKind: "All",
    headers: [
      {
        text: "Name",
        align: "start",
        value: "releaseName",
      },
      {
        text: "Version",
        align: "start",
        value: "versions",
      },
      {
        text: "Kind",
        align: "start",
        value: "kind",
      },
      {
        text: "Description",
        align: "start",
        value: "description",
      },
      {
        text: "Helm Status",
        align: "start",
        value: "helmStatus",
      },
      {
        text: "Kube Status",
        align: "start",
        value: "kubeStatus",
      },
      {
        text: "Experimental",
        align: "start",
        value: "experimental",
      },
      {
        text: "Ready",
        align: "start",
        value: "successful",
      },
      { text: "Action", value: "installed" },
    ],
  }),
  created() {},
  mounted() {
    this.getHelmCharts();
    this.startExtensionsInterval()
  },
  computed: {
    filteredLaunchedAppLinks(): any {
      if (this.launchedAppLinks !== null) {
        return this.launchedAppLinks.filter((i: any) => {
          let devFilter = true;
          let kindFilter = true;

          if (this.extensionExperimental == "Stable" && i.experimental === "yes") {
            devFilter = false;
          } else if (this.extensionExperimental == "Experimental" && i.experimental === "no") {
            devFilter = false;
          }

          if (this.extensionKind == "Workflows" && i.kind === "application") {
            kindFilter = false;
          } else if (this.extensionKind == "Applications" && i.kind === "dag") {
            kindFilter = false;
          }
          return devFilter && kindFilter;
        });
      } else {
        this.loading = true;
        return [];
      }
    },

    ...mapGetters([
      "currentUser",
      "isAuthenticated",
      "commonData",
      "launchApplicationData",
      "availableApplications",
    ]),
  },
  methods: {
    getHelmCharts() {
      let params = {
        repo: "kaapana-public",
      };
      kaapanaApiService
        .helmApiGet("/extensions", params)
        .then((response: any) => {
          this.launchedAppLinks = response.data;
          if (this.launchedAppLinks !== null) {
            this.loading = false;
          }
        })
        .catch((err: any) => {
          this.loading = false;
          console.log(err);
        });
    },
    startExtensionsInterval() {
      this.polling = window.setInterval(() => {
        this.getHelmCharts();
      }, 5000);
    },
    clearExtensionsInterval() {
      window.clearInterval(this.polling);
    },
    updateExtensions() {
      this.loading = true;
      this.clearExtensionsInterval();
      this.startExtensionsInterval();
      kaapanaApiService
        .helmApiGet("/update-extensions", {})
        .then((response: any) => {
          this.loading = false;
          console.log(response.data);
        })
        .catch((err: any) => {
          this.loading = false;
          console.log(err);
        });
    },
    deleteChart(item: any, helmCommandAddons: any = '') {
      let params = {
        release_name: item.releaseName,
        release_version: item.version,
        helm_command_addons: helmCommandAddons
      };
      this.loading = true;
      this.clearExtensionsInterval();
      this.startExtensionsInterval();
      kaapanaApiService
        .helmApiGet("/helm-delete-chart", params)
        .then((response: any) => {
          item.installed = "no";
          item.successful = "pending";
        })
        .catch((err: any) => {
          this.loading = false;
          console.log(err);
        });
    },

    installChart(item: any) {
      let payload = {
        name: item.name,
        version: item.version,
        keywords: item.keywords,
      };
      this.loading = true;
      this.clearExtensionsInterval();
      this.startExtensionsInterval();
      kaapanaApiService
        .helmApiPost("/helm-install-chart", payload)
        .then((response: any) => {
          item.installed = "yes";
          if (item.multiinstallable === 'yes') {
            item.successful = "justLaunched";
          } else {
            item.successful = "pending";
          }
        })
        .catch((err: any) => {
          this.loading = false;
          console.log(err);
        });
    },
  },
  beforeDestroy() {
    this.clearExtensionsInterval()
  },
});
</script>

<style lang="scss">
a {
  text-decoration: none;
}
</style>
