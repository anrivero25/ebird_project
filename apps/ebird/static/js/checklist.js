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
        //------ Helper functions -------------------------------------------------/
        find_specie_index: function(id) {
            return this.checklists.findIndex(specie => specie.id === id);
        },
        
        //------ Event Handling ---------------------------------------------------/
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
        inc_count: function(count, id, specie) {
            let self = this;
            if (count > 0) {
                axios.post(inc_count_url, {
                    count: count,
                    id: id,
                    specie: specie
                }).then(function (r) {
                    console.log("total:", r.data.total)
                    let index = self.find_specie_index(id);
                    if (index !== -1) {
                        self.checklists[index].total_count = r.data.total;
                    }
                    console.log("local total: ", self.checklists[index].total_count)
                });
            }
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
