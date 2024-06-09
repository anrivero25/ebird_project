"use strict";

let app = {};

app.data = {    
    data: function() {
        return {
            checklists: [],
            search_query: "",
            search_results: [],
            count: 0
        };
    },
    computed: {
        table_data: function () {
            return this.search_results.length > 0 ? this.search_results : this.checklists;
        }    
    },
    methods: {
        search: function () {
            let self = this; 
            if (self.search_query.length > 0) {
                axios.get(search_species_url, {params: {q: this.search_query}})
                    .then(function (r) {
                        self.search_results = r.data.results;
                        console.log("Search results;", r.data.results)
                });
            } else {
                self.search_results = [];
            }
        },
        logId: function(id) {
            console.log("ID:",id);
        },
        inc_count: function(count) {
            console.log("count:", this.count);
        }
    }
};

app.vue = Vue.createApp(app.data).mount("#app");

app.load_data = function () {
    axios.get(load_checklists_url).then(function (r) {
        app.vue.checklists = r.data.data;
        console.log("Data", r.data.data); 
    });
}

app.load_data();