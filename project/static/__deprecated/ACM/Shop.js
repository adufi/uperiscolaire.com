const Shop = {

    url_id: 0,
    main_id: 0,

    // parent

    init () {
        this.readIDFromURL();
        if (!this.getMainID()) {
            throw ('Impossible de trouver un ID valide.');
        } 
        return true;


        return new Promise((resolve, reject) => {
            resolve(1);
        })
        .then(() => {
            // this.apiChaining();
        });
    },

    readIDFromURL () {
        const ps = window.location.pathname.split('/');
        if (ps && ps.length) {
            let psx = '';

            if (ps[ps.length - 2]) {
                psx = ps[ps.length - 2];
            }
            else if (ps[ps.length - 1]) {
                psx = ps[ps.length - 1];
            }
            else {
                return;
            }

            if (!(this.url_id = parseInt(psx))) {
                this.url_id = 0;
            }
        }
    },

    getMainID () {
        if (!this.url_id) {
            this.main_id = App.caster.id;
            if (!this.main_id) {
                return false;
            }
        }
        else {
            this.main_id = this.url_id;
        }
        return true;
    },

    apiChaining () {
        if (!this.main_id) {
            Alert.alertDanger('Impossible de trouver un ID valide.');
            return false;
        }

        return new Promise(function (resolve, reject) {
            App.get('/api/params/product/')
            .then((data) => {
                try{
                    console.log(data);
                    schoolYear = data.school_year;
                    productHelper.init(data.products);
                }
                catch (error) {
                    reject(error);
                }
                resolve(1);
            })
            .catch(err => reject(err))
        })
        .then (function (result) {
            return child.readUser(
                child_id,
                (data) => console.log(data),
                (err) => console.log(err)
                // readUser_onSuccess,
                // readUser_onFailure
            );
        })
        .then (function (result) {
            console.log(result);
            return sibling.readByChild(
                child_id,
                (data) => console.log(data),
                (err) => console.log(err)
                // readSibling_onSuccess,
                // readSibling_onFailure
            );
        })
        .then (function (result) {
            console.log(result);
            return records.readByParent(
                sibling._parent,
                (data) => console.log(data),
                (err) => console.log(err)
                // readRecords_onSuccess,
                // readRecords_onFailure
            );
        })
        .then (function (result) {
            console.log(sibling);
            return parent.readUser(
                sibling._parent,
                (data) => console.log(data),
                (err) => console.log(err)
                // readRecords_onSuccess,
                // readRecords_onFailure
            );
        })
        .then ((data) => {
            console.log(data);
            run();
        })
        .catch ((err) => {
            console.log(err);
        })
    },

};