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
            item-key="name" dark
            show-select
            class="elevation-3"
          >
          </v-data-table>
        <h1 class="title my-3" align="left">Available Charts API Response</h1>

        {{ availableCharts}}
       {{ availableCharts.chart_name}}
       {{ availableCharts.url}}
          
  <v-data-table :headers="chartheaders" :items="availableCharts" :items-per-page="5" :loading="loading" dark class="elevation-1 my-4">
   
  </v-data-table>

 <h1 class="title my-3" align="left">Available Charts from Registry</h1>
<ul>
    <td v-for="(value, propertyName, index) in availableCharts">
        {{ propertyName }}: {{ value }}   
    </td>
  </ul>
          <h1 class="title my-3" align="left">Testing</h1>  
     <v-list>
            <v-list-item v-for=" item  in availableCharts"  :key="item.chart_name">

           <v-checkbox v-model="model"  :label="item"  :value="item"  :value-comparator="comparator"></v-checkbox>
             
           </v-list-item>
          </v-list>

         <h1 class="title my-3" align="left">Installed Workflows</h1>
          <v-checkbox
        v-model="checkbox"
        :label="` ${installedWorkflow}`"
      ></v-checkbox>
      
  
<h1 class="title my-3" align="left">API response Bucket and Hosts</h1>

 
  {{ finaMinioBuckets}}
  

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
    availableCharts: [] as any,
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
     
     
      
    ],
    chartheaders: [
      {
        text: "Chart Name",
        align: "start",

        value: "chart_name",
      },
      { text: "ChartLocation", value: "url" },
     
     
      
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
        
      }, 
    ],
    //chartlist: [
      //{
       // chart: "Sample Chart",
       // url: "www.sampleurl.com",
        
    //  }, 
  //  ],

  }),
  mounted() {
    this.installedWorkFlowDags();
    this.getMinioBuckets();
    this.availableChartsFromRegistry();
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
    availableChartsFromRegistry() {
     
      
      const getChartsAPI = "/backend/api/v1/minio/charts/getcharts/";
      

      request
        .get(getChartsAPI)
        .then((response: any) => {
          
          const chartsList = JSON.stringify(response.data);
          console.log(response.data);
          console.log('____ charts_____________');
           console.log(response);
          console.log('_________________from tfda charts !!!!!!!!!!______________');
          console.log('_________________charts______________');

          this.availableCharts = response.data;
             

          
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