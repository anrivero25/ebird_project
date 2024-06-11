"use strict";

let app = {};

app.data = {    
    data: function() {
        return {
            checklists: [],
            num_birds: 0, 
        };
    },
    methods: {
        save_sightings: function () {
            if (num_birds > 0) {
                axios.post(update_checklist_url, {
                    num_birds: num_birds,
                    
                }).then(function (r) {
                    alert("Checklist successfully saved!");
                });
            } else {
                alert("Please enter a valid number");
            }
        }
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