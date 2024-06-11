"use strict";

let app = {};

app.data = {    
    data: function() {
        return {
            checklists: [],
            search_query: "",
            search_results: [],
        };
    },
    computed: {
        table_data: function () {
            return this.search_results.length > 0 ? this.search_results : this.checklists;
        }    
    },
    methods: {
       //------ Event Handling ---------------------------------------------------/
        search: function () {
            let self = this; 
            if (self.search_query.length > 0) {
                axios.get(search_my_species_url, {params: {q: this.search_query}})
                    .then(function (r) {
                        self.search_results = r.data.results;
                        console.log("Search results;", r.data.results)
                });
            } else {
                self.search_results = [];
            }
        },
        delete_checklist: function (id, specie, count) {
            let self = this; 
            if (confirm("Are you sure you want to delete this checklist?")) {
                axios.post(delete_checklist_url, {
                    id: id,
                    specie: specie,
                    count: count
                }).then(function (r) {
                    // Update local checklist to be consistent with the database
                    self.checklists = r.data.user_checklists;
                    console.log("user_checklists after DELETE: ", r.data.user_checklists)
                }).catch(function (e) {
                    console.error("ERROR: deleting checklist", e)
                });
            }
        }, 
    }
};

app.vue = Vue.createApp(app.data).mount("#app");

app.load_data = function () {
    axios.get(load_user_checklists_url).then(function (r) {
        app.vue.checklists = r.data.data;
        console.log("user_checklists: ", r.data.data)
    });
}

app.load_data();