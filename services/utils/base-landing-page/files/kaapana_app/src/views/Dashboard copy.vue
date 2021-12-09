<template>
  <v-container>
    <v-text-field
      v-model="search"
      label="Search"
      single-line
      hide-details
    ></v-text-field>
    <v-layout v-resize="onResize" column style="padding-top: 56px">
      <div id="app">
        <h1 class="title my-3" align="left">Data Set Information</h1>
        <v-app id="inspire">
          <v-data-table
            v-model="datasetInformation"
            :headers="headers"
            :items="datalist"
            :single-select="singleSelect"
            :search="search"
            item-key="name"
            show-select
            class="elevation-3"
          >
          </v-data-table>

          

          <h1 class="title my-3" align="left">Installed Workflows</h1>
          <v-checkbox
        v-model="checkbox"
        :label="` ${installedWorkflow}`"
      ></v-checkbox>
      
  
<h1 class="title my-3" align="left">Test API NEW</h1>
<option v-for="(bucketName, index) in finaMinioBuckets" v-bind:value="bucketName.bucket_name" v-bind:selected="index === 0">
  {{ bucketName }} - {{ bucketName }}
  {{ finaMinioBuckets }}
<v-checkbox
        v-model="checkbox"
        :label="` ${bucketName.bucket_name}`"
      ></v-checkbox>

</option>

           <div class="text-center pt-2">
            <v-btn color="primary" dark @click.stop="dialog = true">
              Preview & Submit
            </v-btn>  </div>
            <v-dialog v-model="dialog" max-width="590">
              <v-card>
                <v-card-title class="headline">
                  Please Confirm
                </v-card-title>

                <v-card-text>
                  <div id="preview">
                    <h3>Selected Workflow Set</h3>

                    <ul>
                      <li v-for="category in datasetInformation">
                        {{ category.name }}
                      </li>
                      <li>
                        {{ installedWorkflow }}
                      </li> 
                    </ul>
                  </div>
                </v-card-text>

                <v-card-actions>
                  <v-spacer></v-spacer>

                  <v-btn color="red darken-1" text @click="dialog = false">
                    Disagree
                  </v-btn>

                  <v-btn color="green darken-1" text  @click="predict">
                    Agree 
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-row>
        </v-app>
      </div>
    </v-layout>
    
  </v-container>
  
</template>
 


<script lang="ts">
import Vue from "vue";
import request from "@/request";
import { mapGetters } from "vuex";
import storage from "local-storage-fallback";
import kaapanaApiService from "@/common/kaapanaApi.service";
import { LOGIN, LOGOUT, CHECK_AUTH } from "@/store/actions.type";
import axios from "axios";

export default Vue.extend({
  data: () => ({
    singleSelect: false,
    singleSelects: true,
    datasetInformation: [],
    installedWorkflow: [] as any,
    finaMinioBuckets: [] as any,
 

    checkbox: false,
  
    search: "",
    dialog: false,
   

    headers: [
      {
        text: "Data Set",
        align: "start",
        sortable: false,
        value: "name",
      },
      { text: "Data Provider", value: "dataprovider" },
      { text: "Data Size (GB)", value: "datasize" },
      { text: "Data Modification Date", value: "modificationdate" },
      { text: "Data Format", value: "dataformat" },
    ],
    headersWorkfLow: [
      {
        text: "Work Flow",
        align: "start",
        sortable: false,
        value: "name",
      },
      { text: "Workflow Provider", value: "workflowprovider" },
      { text: "Workflow Modification Date", value: "wfmodificationdate" },
    ],
    datalist: [
      {
        name: "Segmentation DataSet For Cohort PZ34TK",
        dataprovider: "RadplanBio",
        datasize: 6.0,
        modificationdate: "09-No-2021",
        dataformat: "CSV",
      },

      
      
    ],
  }),
  mounted() {
    this.installedWorkFlowDags();
    this.getMinioBuckets();
  },

  methods: {
    login() {
      this.$store
        .dispatch(LOGIN)
        .then(() => this.$router.push({ name: "home" }));
    },
    logout() {
      this.$store.dispatch(LOGOUT);
    },

    getMinioBuckets() {
     
      //const getMinioBucketsAPI = "/backend/api/v1/minio/buckets";
      const getMinioBucketsAPI = "/backend/api/v1/minio/bucketsandhosts/";
      

      request
        .get(getMinioBucketsAPI)
        .then((response: any) => {
          
          const bucketsList = JSON.stringify(response.data);
          console.log(response.data);
          console.log('____ hahahaah_____________');
           console.log(response);
          console.log('_________________from tfda backendssss !!!!!!!!!!______________');
          console.log('_________________$$$$$$$$$$$$$$______________');
          
          //JSON.parse(bucketsList, (key, value) => {
            // console.log(key);
            //if (key.includes("a")) {
          //console.log(value);

              this.finaMinioBuckets = response.data;
              //this.finaMinioBuckets = JSON.stringify(response.data);
             
            //}
         // });

          
        })
        .catch((err: any) => {
          
          console.log(err);
        });
    },
    installedWorkFlowDags() {
      const installedWorkFlowDagsResult = "/flow/kaapana/api/getdags";

      request
        .get(installedWorkFlowDagsResult)
        .then((response: any) => {
          
          const myObjStr = JSON.stringify(response.data);
          JSON.parse(myObjStr, (key, value) => {
            // console.log(key);
            if (key.includes("a")) {
              

              this.installedWorkflow = key;
            }
          });

          
        })
        .catch((err: any) => {
          
          console.log(err);
        });
    },

    

    onResize() {
      
    },
    predict() {
      const article = {
        "get-tfda-data": {
          bucket_name: "tfda-test",
          action_operator_dirs: ["example"],
        },
        "tfda-calculations": { tfda_epochs: 3 },
        "put-tfda-data": { bucket_name: "tfda-heidelberg" },
      };
      const airflow_url = "/flow/kaapana/api/trigger/tfda-diabetes-prediction";
      request
        .post(airflow_url, article)
        .then((response) => {
          console.log("Api response: ", response.data);
          //this.snackbar = true;
          //this.snacktext = snacktext;
          //this.snackbar = {
         // message: "Workflow Submitted Successfully !",
          //color: "green",
          //show: true,
          //};
         alert('Workflow submitted Successfully, output will be available in Minio. Track Progress via Airflow.')
          
        })
        .catch((error) => {
          //this.errorMessage = error.message;
          console.error("There was an error!", error);
        });
    },
  },
});
</script>

<style lang="scss">
a {
  text-decoration: none;
}
#preview {
  padding: 10px 20px;
  border: 1px dotted #ccc;
  margin: 30px 0;
}
</style>