class User {
    constructor (parent) {
        this.parent = parent;

        this.id = 0;
        this.online_id = 0;

        this.dob = '';
        this.birthplace = '';

        this.job = '';
        this.gender = 0;

        this.last_name = '';
        this.first_name = '';
        this.date_created = '';

        this.is_active = false;
        this.is_auto_password = false;
        this.accept_newsletter = false;

        this.date_created = '';
        this.date_confirmed = '';
        this.date_completed = '';

        this.roles = [];

        this.email = '';

        this.phones = {
            'cell': '',
            'home': '',
            'pro': '',
        };

        this.address = {
            'city': '',
            'zip_code': '',
            'address1': '',
            'address2': '',
        };

        this.password1 = '';
        this.password2 = '';

        this.change_flag = false;

        this.intels = [];

        // Raw data rcvd
        this._data = {};
    }

    
    fromAPI (user) {
        // const _ = JSON.parse(raw);
        // console.log(_);

        this.id         = user.id;
        this.online_id  = user.online_id;

        // New
        this.job = user.job;
        this.gender = user.gender;
        this.birthplace = user.birthplace;
        this.accept_newsletter  = user.accept_newsletter;

        this.dob        = user.dob;
        this.last_name  = user.last_name;
        this.first_name = user.first_name;

        this.is_active          = user.is_active;
        this.is_auto_password   = user.is_auto_password;

        this.date_created       = user.date_created;
        this.date_confirmed     = user.date_confirmed;
        this.date_completed     = user.date_completed;

        this.roles  = user.roles;

        if (user.auth.email)
            this.email = user.auth.email;

        if (user.phones) {
            this.phones = user.phones;
        }

        if (user.address) {
            this.address = {
                'city': user.address['city'],
                'zip_code': user.address['zip_code'],
                'address1': user.address['address1'],
                'address2': user.address['address2'],
            };
        }

        if (user.hasOwnProperty('credit')) {
            this.credit = user.credit;
        }
    }


    init () {
        if (!this.date_confirmed) {
            return 'Compte non vérifier, '
        }
    }


    validate (flag, value) {
        let result = undefined;
        switch (flag) {
            case 'user_last_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.last_name = value.toLocaleUpperCase();
                break;

            case 'user_first_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.first_name = value.capitalize();
                break;

            case 'user_dob':
                result = UserValidation.dob(value);
                if (result.status)
                    this.dob = value;
                break;

            case 'user_birthplace':
                result = UserValidation.name(value, true);
                if (result.status)
                    this.birthplace = value.capitalize();
                break;

            case 'user_job':
                result = UserValidation.name(value, true);
                if (result.status)
                    this.job = value.capitalize();
                break;

            case 'user_gender_m':
                this.gender = 1;
                result = {'status': true};
                break;

            case 'user_gender_f':
                this.gender = 2;
                result = {'status': true};
                break;

            case 'user_gender_t':
                this.gender = 3;
                result = {'status': true};
                break;

            case 'user_phone_cell':
                result = UserValidation.phone(value);
                if (result.status)
                    this.phones.cell = value;
                break;

            case 'user_phone_home':
                result = UserValidation.phone(value);
                if (result.status)
                    this.phones.home = value;
                break;

            case 'user_phone_pro':
                result = UserValidation.phone(value);
                if (result.status)
                    this.phones.pro = value;
                break;

            case 'user_email':
                result = UserValidation.email(value);
                if (result.status)
                    this.email = value;
                break;

            case 'user_address1':
                result = UserValidation.name(value);
                if (result.status)
                    this.address.address1 = value;
                break;

            case 'user_address2':
                result = UserValidation.name(value, true);
                if (result.status)
                    this.address.address2 = value;
                break;

            case 'user_city':
                result = UserValidation.city(value);
                if (result.status)
                    this.address.city = CITIES[value];
                    this.address.zip_code = value;
                break;

            case 'user_accept_newsletter':
                this.accept_newsletter = value;
                result = {'status': true};
                break;

            
            // Login
            case 'login_email':
                result = UserValidation.email(value);
                if (result.status)
                    this.email = value.toLocaleLowerCase();
                console.log(result);
                break;

            case 'login_password':
                result = UserValidation.password(value);
                if (result.status)
                    this.password1 = value;
                break;

            
            // Register
            case 'register_email':
                result = UserValidation.email(value);
                if (result.status)
                    this.email = value.toLocaleLowerCase();
                break;

            case 'register_password1':
                result = UserValidation.password(value);
                if (result.status)
                    if (this.password2 && value != this.password2) {
                        this.password1 = '';
                        return {'status': false, 'message': 'Mot de passe différents.'};
                    }
                    this.password1 = value;
                break;

            case 'register_password2':
                result = UserValidation.password(value);
                if (result.status)
                    if (this.password1 && this.password1 != value) {
                        this.password2 = '';
                        return {'status': false, 'message': 'Mot de passe différents.'};
                    }
                    this.password2 = value;
                break;

            // Add Child 
            case 'child_last_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.last_name = value.toLocaleUpperCase();
                break;

            case 'child_first_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.first_name = value.capitalize();
                break;

            case 'child_dob':
                result = UserValidation.dob(value);
                if (result.status)
                    this.dob = value;
                break;

            case 'child_birthplace':
                result = UserValidation.name(value);
                if (result.status)
                    this.birthplace = value.capitalize();
                break;

            case 'child_gender_m':
                this.gender = 1;
                result = {'status': true};
                break;

            case 'child_gender_f':
                this.gender = 2;
                result = {'status': true};
                break;

            // Record Resp1

            case 'record_resp1_last_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.last_name = value.toLocaleUpperCase();
                break;

            case 'record_resp1_first_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.first_name = value.capitalize();
                break;

            case 'record_resp1_dob':
                result = UserValidation.dob(value);
                if (result.status)
                    this.dob = value;
                break;

            case 'record_resp1_birthplace':
                result = UserValidation.name(value);
                if (result.status)
                    this.birthplace = value.capitalize();
                break;

            case 'record_resp1_job':
                result = UserValidation.name(value);
                if (result.status)
                    this.job = value.capitalize();
                break;

            case 'record_resp1_gender_m':
                this.gender = 1;
                result = {'status': true};
                break;

            case 'record_resp1_gender_f':
                this.gender = 2;
                result = {'status': true};
                break;

            case 'record_resp1_gender_t':
                this.gender = 3;
                result = {'status': true};
                break;

            case 'record_resp1_phone_cell':
                result = UserValidation.phone(value);
                if (result.status)
                    this.phones.cell = value;
                break;

            case 'record_resp1_phone_home':
                result = UserValidation.phone(value);
                if (result.status)
                    this.phones.home = value;
                break;

            case 'record_resp1_phone_pro':
                result = UserValidation.phone(value);
                if (result.status)
                    this.phones.pro = value;
                break;

            case 'record_resp1_email':
                result = UserValidation.email(value);
                if (result.status)
                    this.email = value.toLocaleLowerCase();
                break;

            case 'record_resp1_address1':
                result = UserValidation.name(value);
                if (result.status)
                    this.address.address1 = value;
                break;

            case 'record_resp1_address2':
                result = UserValidation.name(value, true);
                if (result.status)
                    this.address.address2 = value;
                break;

            case 'record_resp1_city':
                result = UserValidation.city(value);
                if (result.status)
                    this.address.city = CITIES[value];
                    this.address.zip_code = value;
                break;


            case 'record_child_last_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.last_name = value.toLocaleUpperCase();
                break;

            case 'record_child_first_name':
                result = UserValidation.name(value);
                if (result.status)
                    this.first_name = value.capitalize();
                break;

            case 'record_child_dob':
                result = UserValidation.dob(value);
                if (result.status)
                    this.dob = value;
                break;

            case 'record_child_birthplace':
                result = UserValidation.name(value);
                if (result.status)
                    this.birthplace = value.capitalize();
                break;

            case 'record_child_gender_m':
                this.gender = 1;
                result = {'status': true};
                break;

            case 'record_child_gender_f':
                this.gender = 2;
                result = {'status': true};
                break;

            default:
                result = {'status': false, 'message': 'Champ non reconnu.'};
                break;
        }
        
        this.change_flag = true;
        return result;
    }


    /**
     * API
     */

    login () {}


    status () {}


    payload () {
        const _ = {
            'id': this.id,
            'online_id': this.online_id,

            'dob': this.dob,
            'job': this.job,
            'birthplace': this.birthplace,
            
            'gender': this.gender,
            'last_name': this.last_name,
            'first_name': this.first_name,

            'email': this.email,
            'phones': this.phones,
            'address': this.address,

            'accept_newsletter': this.accept_newsletter
        }

        return _;
    }


    register (onSuccess, onFailure) {
        if (!this.email ||
            !this.password1 ||
            !this.password2) {
            console.log ('Informations incomplètes.');
            return false;
        }

        const payload = {
            'email': this.email,
            'password1': this.password1,
            'password2': this.password2
        };
        App.post('/auth/register/', JSON.stringify(payload), false)
            .then(data => {
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
        return true;
    }


    createChild (onSuccess, onFailure) {
        if (!this.change_flag)
            return 'Aucune modification effectuée.';

        if (!this.gender) {
            return 'Veuillez selectionner un genre.';
        }

        const payload = {
            'dob': this.dob,
            'last_name': this.last_name.toUpperCase(),
            'first_name': this.first_name.capitalize(),
            // 'birthplace': this.birthplace,
            'gender': this.gender
        };
        
        for (const value of Object.values(payload)) {
            if (!value) {
                return 'Tous les champs doivent être remplis.';
            }
        }
        
        payload['parent_id'] = this.parent;
        payload['birthplace'] = this.birthplace.capitalize();
        // return payload;
        return App.post(`/api/children/`, JSON.stringify(payload), true)
            .then(data => {
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (err.message) {
                    if (err.message.includes('Vous n\'êtes pas autorisé à consulter cette page.')) {
                        err['erreur'] = 'Accès interdit à ces informations.';
                    }
                    else if (err.message.includes('does not exist')) {
                        err['erreur'] = 'Famille inconnue.';
                    }
                    else if (err.message.includes('Every fields must be set')) {
                        err['erreur'] = 'Tous les champs doivent être remplis.';
                    }
                    else if (err.message.includes('Slug already exist')) {
                        err['erreur'] = 'L\'enfant existe déjà.';
                    }
                    else {
                        err['erreur'] = 'Une erreur est survenue.'
                    }
                }
                if (onFailure)
                    onFailure(err);
            });
    }


    readUser (pk='', onSuccess=undefined, onFailure=undefined) {
        return App.get(`/api/users/${pk}/`, true)
            .then(data => {
                console.log(data)
                this._data = data;

                this.fromAPI(data.user);
                
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (onFailure)
                    onFailure(err);
            });
    }


    readUsers (onSuccess=undefined, onFailure=undefined) {
        return App.get(`/api/user/`, true)
            .then(data => {
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
    }


    readSibling (ext='', onSuccess=undefined, onFailure=undefined) {
        return App.get(`/api/sibling/${ext}`, true)
            .then(data => {
                console.log(data);                
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
    }


    updateUser (onSuccess, onFailure) {
        if (!this.change_flag)
            return 'Aucune modification enregistrée.';

        const payload = {
            'id': this.id,
            // 'dob': this.dob,
            'gender': this.gender,
            // 'birthplace': this.birthplace,
            'last_name': this.last_name,
            'first_name': this.first_name,
            
            'email': this.email,
            'phones': this.phones,
            'address': this.address,
        };

        if (!this.phones.cell) {
            return 'Numéro de portable obligatoire.';
        }

        if (!this.address.address1) {
            return 'Ligne 1 de l\'adresse obligatoire.';
        }

        if (!this.address.city) {
            return 'Ville de résidence obligatoire.';
        }
        
        for (const value of Object.values(payload)) {
            if (!value) {
                return 'Tous les champs doivent être remplis.';
            }
        }
        
        payload['job'] = this.job;
        payload['accept_newsletter'] = this.accept_newsletter;

        const credit = parseInt(this.credit);

        if (credit) {
            payload['credit'] = credit;
        }

        // POST validation
        // const values = Object.values(payload);
        // for (let value of values) {
        //     if (!value)
        //         return false;
        // }

        // payload['address2'] = this.address.address2;

        return App.put(`/api/user/${this.id}/`, JSON.stringify(payload), true)
            .then(data => {
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
    }


    updateChild (onSuccess, onFailure) {
        console.log('updateChild');
        
        // if (!this.change_flag)
        //     return 'Aucune modification enregistrée.';

        const payload = {
            'id':           this.id,
            'dob':          this.dob,
            'gender':       this.gender,
            'last_name':    this.last_name.capitalize(),
            'first_name':   this.first_name.toUpperCase(),
        };
        
        for (const value of Object.values(payload)) {
            if (!value) {
                return 'Tous les champs doivent être remplis.';
            }
        }

        payload['birthplace'] = this.birthplace.capitalize();

        return App.put(`/api/users/${this.id}/`, JSON.stringify(payload), true)
            .then(data => {
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (onFailure)
                    onFailure(err);
            });
    }


    /**
     * HTML
     */

    html_updateRecord () {
        document.getElementById('record_child_last_name').value = this.last_name;
        document.getElementById('record_child_first_name').value = this.first_name;

        document.getElementById('record_child_dob').value = this.dob;
        document.getElementById('record_child_birthplace').value = this.birthplace;

        document.getElementById('record_child_first_name').value = this.first_name;
        document.getElementById('record_child_first_name').value = this.first_name;
        
        switch (this.gender) {
            case 1:
                document.getElementById('record_child_gender_m').checked = true;
                break;

            case 2:
                document.getElementById('record_child_gender_f').checked = true;
                break;

            case 3:
                document.getElementById('record_child_gender_t').checked = true;
                break;

            default:
                break;
        }        
    }


    html_updateParentRecord () {
        document.getElementById('record_resp1_last_name').value = this.last_name;
        document.getElementById('record_resp1_first_name').value = this.first_name;

        document.getElementById('record_resp1_job').value = this.job;

        document.getElementById('record_resp1_phone_cell').value = this.phones.cell;
        document.getElementById('record_resp1_phone_home').value = this.phones.home;
        document.getElementById('record_resp1_phone_pro').value = this.phones.pro;

        document.getElementById('record_resp1_email').value = this.email;

        document.getElementById('record_resp1_zip').value = this.address['zip_code'];
        document.getElementById('record_resp1_city').value = this.address['zip_code'];
        document.getElementById('record_resp1_address1').value = this.address['address1'];
        document.getElementById('record_resp1_address2').value = this.address['address2'];

        if (this.gender === 1)
            document.getElementById('record_resp1_gender_m').checked = true;
        else if (this.gender === 2)
            document.getElementById('record_resp1_gender_f').checked = true;
        else if (this.gender === 3)
            document.getElementById('record_resp1_gender_t').checked = true;
    }
}


class Intel {
    constructor (parent_id) {
        this.id = 0;
        this.parent_id = parent_id;
        
        this.quotient_1 = 0;
        this.quotient_2 = 0;

        this.recipent_number = '';
        // this.insurance_policy = 0;
        // this.insurance_society = 0;

        this.school_year = 0;

        this.date_created = '';
        this.date_verified = '';
        this.date_last_mod = '';

        // School year
        this.date_start = '';
        this.date_end = '';

        this.is_active = false;
        this.has_changed = false;
    }

    parentId () { return this.parent_id; }
    parentId (id) { this.parent_id = id; }
    
    fromIntel (intel) {
        try {
            this.id = intel.id;

            this.quotient_1         = intel.quotient_1;
            this.quotient_2         = intel.quotient_2;

            this.recipent_number    = intel.recipent_number;
            // this.insurance_policy   = intel.insurance_policy;
            // this.insurance_society   = intel.insurance_society;

            this.school_year        = intel.school_year;

            this.date_created       = this._date(intel.date_created);
            this.date_verified      = this._date(intel.date_verified);
            this.date_last_mod      = this._date(intel.date_last_mod);
        }
        catch (error) {
            console.log('Intel => fromIntel() - Exception found with error: ' + error);
        }
        
    }


    fromSchoolYear (sy) {
        try {
            this.date_start = sy.date_start;
            this.date_end   = sy.date_end;
            this.is_active  = sy.is_active;
        }
        catch (error) {
            console.log('Intel => fromSchoolYear() - Exception found with error: ' + error);
        }
        
    }


    payload () {
        const payload = {
            'parent_id':        this.parent_id,
            
            'quotient_1':       this.quotient_1,
            'quotient_2':       this.quotient_2,

            'recipent_number':  this.recipent_number,
            // 'insurance_policy': this.insurance_policy,
            // 'insurance_society': this.insurance_society,

            'school_year':      this.school_year,

            'date_created':     this.date_created,
            'date_verified':    this.date_verified,
            'date_last_mod':    this.date_last_mod,
        };

        if (!this.recipent_number) {
            return 'Numéro CAF obligatoire.';
        }

        if (!this._verify_number(this.recipent_number))
            return 'Numéro CAF incorrect';
        
        // if (!this._verify_text(this.insurance_policy))
        //     return 'Police d\'assurance incorrect';

        // if (!this._verify_text(this.insurance_society))
        //     return 'Société d\'assurance incorrect';

        // if (!this._verify_quotient(this.quotient_1))
        //     return 'Quotient Q1 incorrect';
        
        // if (!this._verify_quotient(this.quotient_2))
        //     return 'Quotient Q2 incorrect';

        return payload;
    }


    create (onSuccess=undefined, onFailure=undefined) {
        if (!this.has_changed)
            return 'Aucun changement effectué.';
        
        // let payload = {
        //     'parent_id':        this.parent_id,
            
        //     'quotient_1':       this.quotient_1,
        //     'quotient_2':       this.quotient_2,

        //     'recipent_number':  this.recipent_number,
        //     'insurance_policy': this.insurance_policy,
        //     'insurance_society': this.insurance_society,

        //     'school_year':      this.school_year,

        //     'date_created':     this.date_created,
        //     'date_verified':    this.date_verified,
        //     'date_last_mod':    this.date_last_mod,
        // };

        // if (!this._verify_number(this.recipent_number))
        //     return false;
        
        // if (!this._verify_text(this.insurance_policy))
        //     return false;

        // if (!this._verify_text(this.insurance_society))
        //     return false;

        // if (!this._verify_quotient(this.quotient_1))
        //     return false;
        
        // if (!this._verify_quotient(this.quotient_2))
        //     return false;

        let payload = this.payload();

        if (typeof(payload) === 'string') {
            return payload;
        }

        return App.post('/api/user/intel/', JSON.stringify(payload), true)
            .then((data) => {
                console.log(data);
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (onFailure)
                    onFailure(err);
            });
    }


    update (onSuccess=undefined, onFailure=undefined) {
        if (!this.has_changed) {
            return 'Aucun changement effectué.';
        }
        if (!this.id) {
            return 'Identifiant non définie.';
        }

        // let payload = {
        //     'parent_id':        this.parent_id,
            
        //     'quotient_1':       this.quotient_1,
        //     'quotient_2':       this.quotient_2,

        //     'recipent_number':  this.recipent_number,
        //     'insurance_policy': this.insurance_policy,
        //     'insurance_society': this.insurance_society,

        //     'school_year':      this.school_year,

        //     'date_created':     this.date_created,
        //     'date_verified':    this.date_verified,
        //     'date_last_mod':    this.date_last_mod,
        // };

        // if (!this._verify_number(this.recipent_number))
        //     return false;
        
        // if (!this._verify_text(this.insurance_policy))
        //     return false;

        // if (!this._verify_text(this.insurance_society))
        //     return false;

        // if (!this._verify_quotient(this.quotient_1))
        //     return false;
        
        // if (!this._verify_quotient(this.quotient_2))
        //     return false;

        let payload = this.payload();

        if (typeof(payload) === 'string') {
            return payload;
        }

        return App.put(`/api/user/intel/${this.id}/`, JSON.stringify(payload), true)
            .then((data) => {
                console.log(data);
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (onFailure)
                    onFailure(err);
            });
    }    


    _verify_text (text) {
        if (!text || text.length > 128) {
            return false;
        }
        return true;
    }


    _verify_number (number) {
        if (('' + number).length > 19) {
            return false;
        }
        return true;
    }


    _verify_quotient (quotient) {
        if (!quotient) {
            return false;
        }
        if (quotient < 0 || quotient > 3) {
            return false;
        }
        return true;
    }


    _date (date) {
        return date.split('+')[0];
    }
}


class Child {
    constructor (parent_id) {
        this.id = 0;
        this.record_id = 0;
        this.parent_id = parent_id;

        this.last_name = '';
        this.first_name = '';

        this.school = '';
        this.classroom = '';

        this.is_active = false;
        this.has_changed = false;
    }

    parentID () { return this.parent_id; }
    parentID (id) { this.parent_id = id; }
    
    fromChild (child) {
        try {
            this.id = child.id;

            this.last_name = child.last_name;
            this.first_name = child.first_name;

            if (child.record) {
                const record = child.record;

                this.record_id  = record.id;
                this.school     = record.school;
                this.classroom  = record.classroom;
            }

            // this.quotient_1         = child.quotient_1;
            // this.quotient_2         = child.quotient_2;

            // this.recipent_number    = child.recipent_number;
            // this.insurance_policy   = child.insurance_policy;

            // this.school_year        = child.school_year;

            // this.date_created       = this._date(intel.date_created);
            // this.date_verified      = this._date(intel.date_verified);
            // this.date_last_mod      = this._date(intel.date_last_mod);
        }
        catch (error) {
            console.log('Intel => fromIntel() - Exception found with error: ' + error);
        }
        
    }


    fromSchoolYear (sy) {
        try {
            this.date_start = sy.date_start;
            this.date_end   = sy.date_end;
            this.is_active  = sy.is_active;
        }
        catch (error) {
            console.log('Intel => fromSchoolYear() - Exception found with error: ' + error);
        }
        
    }


    create (onSuccess=undefined, onFailure=undefined) {
        if (!this.has_changed)
            return false;
        
        const payload = {
            'parent_id':        this.parent_id,
            
            'quotient_1':       this.quotient_1,
            'quotient_2':       this.quotient_2,

            'recipent_number':  this.recipent_number,
            'insurance_policy': this.insurance_policy,

            'school_year':      this.school_year,

            'date_created':     this.date_created,
            'date_verified':    this.date_verified,
            'date_last_mod':    this.date_last_mod,
        };

        if (!this._verify_number(this.recipent_number))
            return false;
        
        if (!this._verify_number(this.insurance_policy))
            return false;

        if (!this._verify_quotient(this.quotient_1))
            return false;
        
        if (!this._verify_quotient(this.quotient_2))
            return false;

        return App.post('/api/user/intel/', JSON.stringify(payload), true)
            .then((data) => {
                console.log(data);
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (onFailure)
                    onFailure(err);
            });
    }


    update (onSuccess=undefined, onFailure=undefined) {
        if (!this.has_changed || !this.id) 
            return false;

        const payload = {
            'parent_id':        this.parent_id,
            
            'quotient_1':       this.quotient_1,
            'quotient_2':       this.quotient_2,

            'recipent_number':  this.recipent_number,
            'insurance_policy': this.insurance_policy,

            'school_year':      this.school_year,

            'date_created':     this.date_created,
            'date_verified':    this.date_verified,
            'date_last_mod':    this.date_last_mod,
        };

        if (!this._verify_number(this.recipent_number))
            return false;
        
        if (!this._verify_number(this.insurance_policy))
            return false;

        if (!this._verify_quotient(this.quotient_1))
            return false;
        
        if (!this._verify_quotient(this.quotient_2))
            return false;

        return App.put(`/api/user/intel/${this.id}/`, JSON.stringify(payload), true)
            .then((data) => {
                console.log(data);
                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);
                if (onFailure)
                    onFailure(err);
            });
    }    


    _verify_number (number) {
        if (('' + number).length > 19) {
            return false;
        }
        return true;
    }


    _verify_quotient (quotient) {
        if (!quotient) {
            return false;
        }
        if (quotient < 0 || quotient > 3) {
            return false;
        }
        return true;
    }


    _date (date) {
        return date.split('+')[0];
    }


    renderCard () {
        const wrapper = document.querySelector('#Family-wrapper');

        let record_url = `/record/${this.id}/`;
        record_url += (this.record_id) ? `${this.record_id}/` : '';

        let record_summary = (this.record_id) ? `<a class="button button-yellow" target="_blank" href="${record_url}pdf/">Fiche 2020-2021</a>` : '';

        wrapper.innerHTML += `
        <div class="col-md-6 col-sm-6 col-xs-12">
            <article class="Family-card">
                <div class="article-head">
                    <i class="far fa-user"></i>
                </div>
                
                <div class="article-body ${((this.record_id) ? 'success' : 'danger')}">
                    <a href="/mon-profil/${this.id}/" class="child-name">${this.last_name} ${this.first_name}</a>
                    <span class="Card_register text-success"><b>Inscrit</b></span>
                    <span class="Card_register text-danger"><b>Non inscrit</b></span>
                    ${record_summary}
                </div>
            </article>
        </div>`;

        return;

        wrapper.innerHTML += `
        <div class="col-md-6 col-sm-6 col-xs-12">
            <article class="Family-card">
                <div class="article-head">
                    <i class="far fa-user"></i>
                </div>
                
                <div class="article-body ${((this.record_id) ? 'success' : 'danger')}">
                    <a href="/mon-profil/${this.id}/" class="child-name">${this.last_name} ${this.first_name}</a>
                    <span class="Card_register text-success"><b>Inscrit</b></span>
                    <span class="Card_register text-danger"><b>Non inscrit</b></span>
                    <a class="button button-blue" href="${record_url}">Inscription 2020-2021</a>
                    ${record_summary}
                </div>
            </article>
        </div>`;
    }


    _renderCard () {
        const wrapper = document.querySelector('.Family-wrapper');

        const card = document.createElement('a');
        card.className = 'Family-card ' + ((this.record_id) ? 'success' : 'danger');
        // card.target = '_blank';
        card.href = `/intern/user/${this.id}/`;

        card.innerHTML = `
        <b>
            <span class="Card_name">${this.last_name} ${this.first_name}</span> -
            <span class="Card_register text-success">Inscrit</span>
            <span class="Card_register text-danger">Non inscrit</span>
        </b>
        <span class="Card_record" ${(!this.record_id) ? 'style="display: none"' : ''}>
            ${CLASSROOMS[this.classroom]} - ${this.school}
        </span>
        `;

        wrapper.appendChild(card);
    }
}


class Intels {
    constructor (parent_id) {
        this._added = [];
        this._intels = {};
        this.parent_id = parent_id;

        this.has_active = false;
    }

    intel (pk) {
        return this._intels[pk];
    }
    intels () { return this._intels; }

    add (sy) {
        const _ = new Intel(this.parent_id);
        _.fromSchoolYear(sy);
        
        this._intels[0] = _
        return this._intels[0];
    }

    read (onSuccess=undefined, onFailure=undefined) {
        return this._read('', onSuccess, onFailure);
    }

    readByID (pk, onSuccess=undefined, onFailure=undefined) {
        return this._read(pk, onSuccess, onFailure);
    }

    readAll (onSuccess=undefined, onFailure=undefined) {
        return this._read(`?all=true`, onSuccess, onFailure);
    }

    readByParent (parent_pk, onSuccess=undefined, onFailure=undefined) {
        return this._read(`?parent=${parent_pk}`, onSuccess, onFailure);
    }

    // Basic read request
    _read (mod, onSuccess, onFailure) {
        return App.get(`/api/user/intel/${mod}`, true)
            .then((data) => {
                const _ = this.order(data.intels);

                if (typeof(_) === 'object') {
                    reject(_);
                }

                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
    }


    order (intels) {
        const schoolYears = App.SchoolYears();

        if (!schoolYears) {
            // statusDanger('Echec lors de la récupération des années scolaires.');
            return new Error('Echec lors de la récupération des années scolaires.');
        }

        for (const intel of intels) {
            const _ = new Intel(this.parent_id);
            _.fromIntel(intel);

            for (const key of Object.keys(schoolYears)) {
                const sy = schoolYears[key];
                if (sy.id === intel.school_year)
                    _.fromSchoolYear(sy);
            }

            if (_.is_active)
                this.has_active = true;

            this._intels[intel.id] = _;
        }
        return true;
    }


    render (sy, isAdmin=false) {
        const s = sy.date_start.split('-')[0];
        const e = sy.date_end.split('-')[0];

        let base = `
        <div class="History-card" data-school=${sy.id}>
            <b class="card-title">${s} - ${e} ${(sy.is_active) ? '(en cours)' : ''}</b>
            <hr />

            <div class="History-no_data">
                <span><i>Pas de données pour cette année</i></span>
            </div>

            <div class="History-form" ${(!isAdmin) ? 'style="display: none"' : ''}>
                <div class="form-group col-sm-6">
                    <label for="intel_q1"><b>Quotient <span class="intel_s">${s}</span></b></label>
                    <br/>
                    <select id="intel_q1_${sy.id}" name="intel_q1" placeholder="Quotient" onchange="" value="">
                        <option value="0" default>--</option>
                        <option value="1">NE</option>
                        <option value="2">Q2</option>
                        <option value="3">Q1</option>
                    </select>
                </div>

                <div class="form-group col-sm-6">
                    <label for="intel_q2"><b>Quotient <span class="intel_e">${e}</span></b></label>
                    <br/>
                    <select id="intel_q2_${sy.id}" name="intel_q2" placeholder="Quotient" onchange="" value="">
                        <option value="0" default>--</option>
                        <option value="1">NE</option>
                        <option value="2">Q2</option>
                        <option value="3">Q1</option>
                    </select>
                </div>

                <div class="form-group col-sm-6">
                    <label for="intel_rn"><b>Numéro CAF</b></label>
                    <br/>
                    <input id="intel_rn_${sy.id}" name="intel_rn" type="text" placeholder="Numéro CAF" />
                </div>
                <div class="form-group col-sm-6">
                    <label for="intel_ip"><b>Police d'assurance</b></label>
                    <br/>
                    <input id="intel_ip_${sy.id}" name="intel_ip" type="text" placeholder="Police d'assurance" />
                </div>
                </div>
            </div>
        </div>`;
        return base
    }
}


class Sibling {
    constructor () {
        this._parent = 0;

        this._intels = {};
        this._children = {};

        this._intels_created = {};
        this._children_created = {};

        this.has_active_intel = false;

        this._data = {};
    }

    intel (pk)          { return this._intels[pk];}
    intels ()           { return this._intels; }

    intelCreated (pk)   { return this._intels_created[pk];}
    intelsCreated ()    { return this._intels_created; }

    child (pk)          { return this._children[pk];}
    children ()         { return this._children; }

    childCreated (pk)   { return this._children_created[pk];}
    childrenCreated ()  { return this._children_created; }


    add (sy) {
        const _ = new Intel(this.parent_id);
        _.fromSchoolYear(sy);
        
        this._intels[0] = _
        return this._intels[0];
    }

    read (pk, onSuccess=undefined, onFailure=undefined) {
        return this._read(`${pk}/`, onSuccess, onFailure);
    }
    
    readAll (onSuccess=undefined, onFailure=undefined) {
        return this._read(``, onSuccess, onFailure);
    }

    readByChild (user_id, onSuccess=undefined, onFailure=undefined) {
        return this._read(`?child=${user_id}`, onSuccess, onFailure);
    }

    readByParent (user_id, onSuccess=undefined, onFailure=undefined) {
        return this._read(`?parent=${user_id}`, onSuccess, onFailure);
    }

    // Basic read request
    _read (mod, onSuccess, onFailure) {
        return App.get(`/api/sibling/${mod}`, true)
            .then((data) => {
                console.log(data);
                this._data = data;
                
                const _ = this.order(data.sibling);

                if (typeof(_) === 'object') {
                    reject(_);
                }

                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (err.message) {
                    if (err.message.includes('does not exist')) {
                        err['erreur'] = 'Famille inconnue.';
                    }
                }
                if (onFailure)
                    onFailure(err);
            });
    }


    order (sibling) {
        this._parent = sibling.parent;

        for (const child of sibling.children) {
            const _ = new Child();
            _.fromChild(child);
            this._children[child.id] = _;
        }

        const schoolYears = App.SchoolYears();

        if (!schoolYears) {
            // statusDanger('Echec lors de la récupération des années scolaires.');
            return new Error('Echec lors de la récupération des années scolaires.');
        }

        for (const intel of sibling.intels) {
            const _ = new Intel(this.parent);
            _.fromIntel(intel);

            for (const key of Object.keys(schoolYears)) {
                const sy = schoolYears[key];
                if (sy.id === intel.school_year)
                    _.fromSchoolYear(sy);
            }

            if (_.is_active)
                this.has_active_intel = true;

            this._intels[intel.id] = _;
        }
        return true;
    }


    render (sy, isAdmin=false) {
        const s = sy.date_start.split('-')[0];
        const e = sy.date_end.split('-')[0];

        let base = `
        <div class="History-card" data-school=${sy.id}>
            <b class="card-title">${s} - ${e} ${(sy.is_active) ? '(en cours)' : ''}</b>
            <hr />

            <div class="History-no_data">
                <span><i>Pas de données pour cette année</i></span>
            </div>

            <div class="History-form" ${(!isAdmin) ? 'style="display: none"' : 'zzz'}>
                <div class="form-group col-sm-6">
                    <label for="intel_q1"><b>Quotient <span class="intel_s">${s}</span></b></label>
                    <br/>
                    <select id="intel_q1_${sy.id}" name="intel_q1" placeholder="Quotient" onchange="" value="">
                        <option value="0" default>--</option>
                        <option value="1">NE</option>
                        <option value="2">Q2</option>
                        <option value="3">Q1</option>
                    </select>
                </div>

                <div class="form-group col-sm-6">
                    <label for="intel_q2"><b>Quotient <span class="intel_e">${e}</span></b></label>
                    <br/>
                    <select id="intel_q2_${sy.id}" name="intel_q2" placeholder="Quotient" onchange="" value="">
                        <option value="0" default>--</option>
                        <option value="1">NE</option>
                        <option value="2">Q2</option>
                        <option value="3">Q1</option>
                    </select>
                </div>

                <div class="form-group col-sm-6">
                    <label for="intel_rn"><b>Numéro CAF</b></label>
                    <br/>
                    <input id="intel_rn_${sy.id}" name="intel_rn" type="text" placeholder="Numéro CAF" />
                </div>
                <div class="form-group col-sm-6">
                    <label for="intel_ip"><b>Police d'assurance</b></label>
                    <br/>
                    <input id="intel_ip_${sy.id}" name="intel_ip" type="text" placeholder="Police d'assurance" />
                </div>
                </div>
            </div>
        </div>`;
        return base
    }


    renderCardAdd () {
        const wrapper = document.querySelector('#Family-wrapper');
        wrapper.innerHTML += `
        <div class="col-md-4 col-sm-6 col-xs-12">
            <article class="Family-card-Add">
                <div class="article-head">
                </div>

                <div class="article-body">
                    <a class="child-name" onclick="openModal('ChildModal')">
                        <i class="fa fa-plus text-success" aria-hidden="true"></i>
                        Ajouter enfant
                    </a>
                </div>
            </article>
        </div>`;
        return;

        // const wrapper = document.querySelector('.Family-wrapper');
        // wrapper.innerHTML += `
        // <a class="Family-card add" onclick="openModal('ChildModal')">
        //     <b>
        //         <i class="fa fa-plus text-success" aria-hidden="true"></i>
        //         Ajouter enfant
        //     </b>
        // </a>
        // `;
    }
}


class Record {
    constructor () {
        this.id = 0;
        this.child_id = 0;
        this.parent_id = 0;
        this.school_year = 0;

        this.agreement = false;

        // Base record
        this.school = 0;
        this.classroom = 0;
        this.accueil_mati = false;
        this.accueil_midi = false;
        this.accueil_merc = false;
        this.accueil_vacs = false;

        this.insurance_policy = '';
        this.insurance_society = '';

        this.date_created = '';
        this.date_last_mod = '';
        this.date_verified = '';

        // Responsible 2
        this.responsible = {
            job: '',
            gender: 0,
            last_name: '',
            first_name: '',
            
            email: '',

            phone_cell: '',
            phone_home: '',
            phone_pro: '',

            address_zip: '',
            address_city: '',
            address_address1: '',
            address_address2: '',
        };

        // 
        // {names, phones}
        this.recuperaters = new Array(3);
        for (let i = 0; i < 3; ++i) this.recuperaters[i] = {'names': '', 'phones': '', 'quality': ''};

        // Authorizations
        this.authorizations = {
            bath: false,
            image: false,
            sport: false,
            transport: false,
            medical_transport: false,
        };

        this.health = {
            pai:        1,
            asthme:     false,
            allergy_food:       false,
            allergy_drug:       false,
            vaccine_up_to_date: false,
            medical_treatment: false,

            lentilles: false,
            lunettes: false,
            protheses_dentaire: false,
            protheses_auditives: false,

            autres_recommandations: '',
            
            pai_details: '',
            allergy_food_details: '',
            allergy_drug_details: '',
            
            doctor_names: '',
            doctor_phones: '',
        };
        
        this.diseases = {
            'rubeole':      false,   
            'varicelle':    false,   
            'angine':       false,   
            'rhumatisme':   false,   
            'scarlatine':   false,   
            'coqueluche':   false,
            'otite':        false,
            'rougeole':     false,   
            'oreillons':    false,  
        };

        this.is_active = false;
        this.date_end = '';
        this.date_start = '';
    }

    fromAPI (record) {
        try {
            this.id = record.id;
            this.child_id = record.child;
            this.school_year = record.school_year;

            this.agreement = record.agreement;

            this.school = record.school;
            this.classroom = record.classroom;

            this.accueil_mati = record.accueil_mati;
            this.accueil_midi = record.accueil_midi;
            this.accueil_merc = record.accueil_merc;
            this.accueil_vacs = record.accueil_vacs;

            this.insurance_policy = record.insurance_policy;
            this.insurance_society = record.insurance_society;

            this.date_created = record.date_created;
            this.date_last_mod = record.date_last_mod;
            this.date_verified = record.date_verified;

            if (record.health) {
                this.health.pai = record.health.pai;
                this.health.pai_details = record.health.pai_details;

                this.health.asthme = record.health.asthme;

                this.health.allergy_food = record.health.allergy_food;
                this.health.allergy_drug = record.health.allergy_drug;
                this.health.allergy_food_details = record.health.allergy_food_details;
                this.health.allergy_drug_details = record.health.allergy_drug_details;
                
                this.health.lentilles = record.health.lentilles;
                this.health.lunettes = record.health.lunettes;
                this.health.protheses_dentaire = record.health.protheses_dentaire;
                this.health.protheses_auditives = record.health.protheses_auditives;

                this.health.vaccine_up_to_date = record.health.vaccine_up_to_date;
                this.health.medical_treatment = record.health.medical_treatment;
    
                this.health.doctor_names = record.health.doctor_names;
                this.health.doctor_phones = record.health.doctor_phones;

                this.health.autres_recommandations = record.health.autres_recommandations;
            }

            if (record.responsible) {
                this.responsible.job = record.responsible.job;
                this.responsible.gender = record.responsible.gender;
                this.responsible.last_name = record.responsible.last_name;
                this.responsible.first_name = record.responsible.first_name;
                
                this.responsible.email = record.responsible.email;
    
                this.responsible.phone_cell = record.responsible.phone_cell;
                this.responsible.phone_home = record.responsible.phone_home;
                this.responsible.phone_pro = record.responsible.phone_pro;
    
                this.responsible.address_zip = record.responsible.address_zip;
                this.responsible.address_city = record.responsible.address_city;
                this.responsible.address_address1 = record.responsible.address_address1;
                this.responsible.address_address2 = record.responsible.address_address2;
            }

            if (record.recuperaters) {
                for (let i = 0; i < Math.min(record.recuperaters.length, 3); ++i)
                    this.recuperaters[i] = record.recuperaters[i];
            }

            if (record.authorizations) {
                this.authorizations.bath = record.authorizations.bath
                this.authorizations.image = record.authorizations.image
                this.authorizations.sport = record.authorizations.sport
                this.authorizations.transport = record.authorizations.transport
                this.authorizations.medical_transport = record.authorizations.medical_transport
            }
            
            if (record.diseases) {
                this.diseases.rubeole = record.diseases.rubeole;   
                this.diseases.varicelle = record.diseases.varicelle;   
                this.diseases.angine = record.diseases.angine;   
                this.diseases.rhumatisme = record.diseases.rhumatisme;   
                this.diseases.scarlatine = record.diseases.scarlatine;   
                this.diseases.coqueluche = record.diseases.coqueluche;   
                this.diseases.otite = record.diseases.otite;   
                this.diseases.rougeole = record.diseases.rougeole;   
                this.diseases.oreillons = record.diseases.oreillons;  
            }
        }
        catch (error) {
            console.log(error);
        }
    }

    // Update school year data
    fromSchoolYear (sy) {
        try {
            this.is_active = sy.is_active;
            this.date_end = sy.date_end;
            this.date_start = sy.date_start;
        }
        catch (error) {
            
        }
    }

    /**
     * HTML
     */

    // Update record in Records widget in Child user page 
    updateRecordItem () {
        const s = this.date_start.split('-')[0];
        const e = this.date_end.split('-')[0];

        const item = document.querySelector(`.Records-Item[data-school="${this.school_year}"]`);

        if (!item) {
            // Throw error
            console.log('Record.updateRecordItem() => item null');
            return false;
        }

        item.querySelector('.no_data').style = 'display: none';
        item.querySelector('.Record').style = 'display: inherit';

        item.querySelector('.record_school').innerHTML = this.school;
        item.querySelector('.record_classroom').innerHTML = this.classroom;

        return true;
    }


    validate (flag, value) {
        let result = undefined;
        switch (flag) {
            case 'record_classroom':
                result = UserValidation.select(value);
                if (result.status)
                    this.classroom = value;
                break;

            case 'record_school':
                result = UserValidation.select(value);
                if (result.status)
                    this.school = value;
                break;

            case 'record_accueil_mati':
                this.accueil_mati = value;
                result = {'status': true};
                break;

            case 'record_accueil_midi':
                this.accueil_midi = value;
                result = {'status': true};
                break;

            case 'record_accueil_merc':
                this.accueil_merc = value;
                result = {'status': true};
                break;

            case 'record_accueil_vacs':
                this.accueil_vacs = value;
                result = {'status': true};
                break;

            case 'record_insurance_policy':
                result = UserValidation.name(value);
                if (result.status)
                    this.insurance_policy = value;
                break;

            case 'record_insurance_society':
                result = UserValidation.name(value);
                if (result.status)
                    this.insurance_society = value;
                break;

            case 'record_resp2_last_name':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.last_name = value;
                }
                break;

            case 'record_resp2_first_name':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.first_name = value;
                }
                break;

            case 'record_resp2_phone_cell':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.phone_cell = value;
                }
                break;

            case 'record_resp2_phone_home':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.phone_home = value;
                }
                break;

            case 'record_resp2_phone_pro':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.phone_pro = value;
                }
                break;

            case 'record_resp2_email':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.email = value;
                }
                break;

            case 'record_resp2_address1':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.address_address1 = value;
                }
                break;

            case 'record_resp2_address2':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.address_address2 = value;
                }
                break;

            case 'record_resp2_city':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                
                if (!result) {
                    const x = document.querySelector(`option[value="${value}"]`);
                    if (!x) 
                        result = {'status': false, 'message': 'La ville choisie est inconnue.'};
                    else {
                        this.responsible.address_zip = value;
                        this.responsible.address_city = x.innerHTML;
                        document.getElementById('record_resp2_zip').value = value;
                        result = {'status': true}
                    }
                }
                break;

            case 'record_resp2_job':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                if (!result) {
                    result = {'status': true}
                    this.responsible.job = value;
                }
                break;

            case 'record_resp2_gender_m':
                this.responsible.gender = 1;
                result = {'status': true};
                break;

            case 'record_resp2_gender_f':
                this.responsible.gender = 2;
                result = {'status': true};
                break;

            case 'record_resp2_gender_t':
                this.responsible.gender = 3;
                result = {'status': true};
                break;


            case 'record_recup1_names':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[0].names = value;
                }
                break;

            case 'record_recup1_phones':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[0].phones = value;
                }
                break;

            case 'record_recup1_quality':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[0].quality = value;
                }
                break;

            case 'record_recup2_names':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[1].names = value;
                }
                break;

            case 'record_recup2_phones':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[1].phones = value;
                }
                break;

            case 'record_recup2_quality':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[1].quality = value;
                }
                break;

            case 'record_recup3_names':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[2].names = value;
                }
                break;

            case 'record_recup3_phones':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[2].phones = value;
                }
                break;

            case 'record_recup3_quality':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.recuperaters[2].quality = value;
                }
                break;
            
            
            case 'record_auth_transp_y':
                this.authorizations.medical_transport = true;
                result = {'status': true}
                break;
            case 'record_auth_transp_n':
                this.authorizations.medical_transport = false;
                result = {'status': true}
                break;
            case 'record_auth_image_y':
                this.authorizations.image = true;
                result = {'status': true}
                break;
            case 'record_auth_image_n':
                this.authorizations.image = false;
                result = {'status': true}
                break;

            case 'record_auth_sport_y':
                this.authorizations.sport = true;
                result = {'status': true}
                break;
            case 'record_auth_sport_n':
                this.authorizations.sport = false;
                result = {'status': true}
                break;

            case 'record_auth_bath_y':
                this.authorizations.bath = true;
                result = {'status': true}
                break;
            case 'record_auth_bath_n':
                this.authorizations.bath = false;
                result = {'status': true}
                break;

            case 'record_auth_transpbus_y':
                this.authorizations.transport = true;
                result = {'status': true}
                break;
            case 'record_auth_transpbus_n':
                this.authorizations.transport = false;
                result = {'status': true}
                break;

            
            case 'record_health_vaccine_y':
                this.health.vaccine_up_to_date = true;
                result = {'status': true}
                break;
                
            case 'record_health_vaccine_n':
                this.health.vaccine_up_to_date = false;
                result = {'status': true}
                break;

            case 'record_health_treatment_y':
                this.health.medical_treatment = true;
                result = {'status': true}
                break;

            case 'record_health_treatment_n':
                this.health.medical_treatment = false;
                result = {'status': true}
                break;

            case 'record_health_asthme_y':
                this.health.asthme = true;
                result = {'status': true}
                break;
            case 'record_health_asthme_n':
                this.health.asthme = false;
                result = {'status': true}
                break;

            case 'record_health_drug_y':
                this.health.allergy_drug = true;
                result = {'status': true}
                break;
            case 'record_health_drug_n':
                this.health.allergy_drug = false;
                result = {'status': true}
                break;
            
            case 'record_health_food_y':
                this.health.allergy_food = true;
                result = {'status': true}
                break;
            case 'record_health_food_n':
                this.health.allergy_food = false;
                result = {'status': true}
                break;
            
            case 'record_health_pai_y':
                this.health.pai = 2;
                result = {'status': true}
                break;
            case 'record_health_pai_n':
                this.health.pai = 1;
                result = {'status': true}
                break;
            case 'record_health_pai_ongoing':
                this.health.pai = 3;
                result = {'status': true}
                break;
                
            case 'record_health_lentilles_y':
                this.health.lentilles = true;
                result = {'status': true}
                break;
            case 'record_health_lentilles_n':
                this.health.lentilles = false;
                result = {'status': true}
                break;

            case 'record_health_glass_y':
                this.health.lunettes = true;
                result = {'status': true}
                break;
            case 'record_health_glass_n':
                this.health.lunettes = false;
                result = {'status': true}
                break;

            case 'record_health_audio_y':
                this.health.protheses_auditives = true;
                result = {'status': true}
                break;
            case 'record_health_audio_n':
                this.health.protheses_auditives = false;
                result = {'status': true}
                break;

            case 'record_health_tooth_y':
                this.health.protheses_dentaire = true;
                result = {'status': true}
                break;
            case 'record_health_tooth_n':
                this.health.protheses_dentaire = false;
                result = {'status': true}
                break;

            case 'record_agreement':
                this.agreement = value;
                result = {'status': true}
                break;
            
                
            case 'record_health_pai_details':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.health.pai_details = value;
                }
                break;
            
            case 'record_health_food_details':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.health.allergy_food_details = value;
                }
                break;

            case 'record_health_drug_details':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.health.allergy_drug_details = value;
                }
                break;
              
            case 'record_health_doctor_names':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.health.doctor_names = value;
                }
                break;

            case 'record_health_doctors_phones':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.health.doctor_phones = value;
                }
                break;

            case 'record_health_others':
                if (value.length > 128) result = {'status': false, 'message': 'Le champ doit contenir moins de 128 caractères'};
                else {
                    result = {'status': true}
                    this.health.autres_recommandations = value;
                }
                break;


            case 'record_health_rubeole_y':
                this.diseases.rubeole = true;
                result = {'status': true};
                break;
            case 'record_health_rubeole_n':
                this.diseases.rubeole = false;
                result = {'status': true};
                break;
            case 'record_health_varicelle_y':
                this.diseases.varicelle = true;
                result = {'status': true};
                break;
            case 'record_health_varicelle_n':
                this.diseases.varicelle = false;
                result = {'status': true};
                break;
            case 'record_health_angine_y':
                this.diseases.angine = true;
                result = {'status': true};
                break;
            case 'record_health_angine_n':
                this.diseases.angine = false;
                result = {'status': true};
                break;
            case 'record_health_rhumatisme_y':
                this.diseases.rhumatisme = true;
                result = {'status': true};
                break;
            case 'record_health_rhumatisme_n':
                this.diseases.rhumatisme = false;
                result = {'status': true};
                break;
            case 'record_health_scarlatine_y':
                this.diseases.scarlatine = true;
                result = {'status': true};
                break;
            case 'record_health_scarlatine_n':
                this.diseases.scarlatine = false;
                result = {'status': true};
                break;
            case 'record_health_coqueluche_y':
                this.diseases.coqueluche = true;
                result = {'status': true};
                break;
            case 'record_health_coqueluche_n':
                this.diseases.coqueluche = false;
                result = {'status': true};
                break;
            case 'record_health_otite_y':
                this.diseases.otite = true;
                result = {'status': true};
                break;
            case 'record_health_otite_n':
                this.diseases.otite = false;
                result = {'status': true};
                break;
            case 'record_health_rougeole_y':
                this.diseases.rougeole = true;
                result = {'status': true};
                break;
            case 'record_health_rougeole_n':
                this.diseases.rougeole = false;
                result = {'status': true};
                break;
            case 'record_health_oreillons_y':
                this.diseases.oreillons = true;
                result = {'status': true};
                break;
            case 'record_health_oreillons_n':
                this.diseases.oreillons = false;
                result = {'status': true};
                break;

            default:
                result = {'status': false, 'message': 'Champ non reconnu.'};
                break;
        }
        
        this.change_flag = true;
        return result;
    }

    // Fill inputs in RECORD page
    html_updateRecordData () {
        const checkbox_macro = (cond, id_true, id_false) => {
            if (cond)
                document.getElementById(id_true).checked = true;
            else
                document.getElementById(id_false).checked = true;
        };

        document.getElementById('record_classroom').value = this.classroom;
        document.getElementById('record_school').value = this.school;

        document.getElementById('record_accueil_mati').checked = this.accueil_mati;
        document.getElementById('record_accueil_midi').checked = this.accueil_midi;
        document.getElementById('record_accueil_merc').checked = this.accueil_merc;
        document.getElementById('record_accueil_vacs').checked = this.accueil_vacs;

        document.getElementById('record_resp2_last_name').value = this.responsible.last_name;
        document.getElementById('record_resp2_first_name').value = this.responsible.first_name;

        document.getElementById('record_resp2_phone_cell').value = this.responsible.phone_cell;
        document.getElementById('record_resp2_phone_home').value = this.responsible.phone_home;
        document.getElementById('record_resp2_phone_pro').value = this.responsible.phone_pro;

        document.getElementById('record_resp2_email').value = this.responsible.email;

        document.getElementById('record_resp2_zip').value = this.responsible.address_zip;
        document.getElementById('record_resp2_city').value = this.responsible.address_zip;
        document.getElementById('record_resp2_address1').value = this.responsible.address_address1;
        document.getElementById('record_resp2_address2').value = this.responsible.address_address2;

        document.getElementById('record_insurance_policy').value = this.insurance_policy;
        document.getElementById('record_insurance_society').value = this.insurance_society;

        for (let i = 0; i < Math.min(this.recuperaters.length, 3); ++i) {
            document.getElementById(`record_recup${i + 1}_names`).value = this.recuperaters[i].names;
            document.getElementById(`record_recup${i + 1}_phones`).value = this.recuperaters[i].phones;
            document.getElementById(`record_recup${i + 1}_quality`).value = this.recuperaters[i].quality;
        }


        if (this.id) {
            /**
             * AUTHORIZATIONS
             */
            checkbox_macro(
                this.authorizations.medical_transport,
                'record_auth_transp_y',
                'record_auth_transp_n'
            );
    
            checkbox_macro(
                this.authorizations.image,
                'record_auth_image_y',
                'record_auth_image_n'
            );
    
            checkbox_macro(
                this.authorizations.sport,
                'record_auth_sport_y',
                'record_auth_sport_n'
            );
    
            checkbox_macro(
                this.authorizations.bath,
                'record_auth_bath_y',
                'record_auth_bath_n'
            );
    
            checkbox_macro(
                this.authorizations.transport,
                'record_auth_transpbus_y',
                'record_auth_transpbus_n'
            );
            
            /**
             * HEALTH
             */
    
            checkbox_macro(
                this.health.vaccine_up_to_date,
                'record_health_vaccine_y',
                'record_health_vaccine_n'
            );
            
            checkbox_macro(
                this.health.medical_treatment,
                'record_health_treatment_y',
                'record_health_treatment_n'
            );
            
            /**
             * DiSEASES
             */
            
            checkbox_macro(
                this.diseases.rubeole,
                'record_health_rubeole_y',
                'record_health_rubeole_n'
            );
                
            checkbox_macro(
                this.diseases.varicelle,
                'record_health_varicelle_y',
                'record_health_varicelle_n'
            );
            
            checkbox_macro(
                this.diseases.angine,
                'record_health_angine_y',
                'record_health_angine_n'
            );
    
            checkbox_macro(
                this.diseases.rhumatisme,
                'record_health_rhumatisme_y',
                'record_health_rhumatisme_n'
            );
    
            checkbox_macro(
                this.diseases.scarlatine,
                'record_health_scarlatine_y',
                'record_health_scarlatine_n'
            );
    
            checkbox_macro(
                this.diseases.coqueluche,
                'record_health_coqueluche_y',
                'record_health_coqueluche_n'
            );
    
            checkbox_macro(
                this.diseases.otite,
                'record_health_otite_y',
                'record_health_otite_n'
            );
    
            checkbox_macro(
                this.diseases.rougeole,
                'record_health_rougeole_y',
                'record_health_rougeole_n'
            );
    
            checkbox_macro(
                this.diseases.oreillons,
                'record_health_oreillons_y',
                'record_health_oreillons_n'
            );
    
            
            /**
             * ASTHME & ALLERGIES 
             */
    
            checkbox_macro(
                this.health.asthme,
                'record_health_asthme_y',
                'record_health_asthme_n'
            );
    
            checkbox_macro(
                this.health.allergy_drug,
                'record_health_drug_y',
                'record_health_drug_n'
            );
    
            document.getElementById('record_health_drug_details').value = this.health.allergy_drug_details;
    
            checkbox_macro(
                this.health.allergy_food,
                'record_health_food_y',
                'record_health_food_n'
            );
    
            document.getElementById('record_health_food_details').value = this.health.allergy_food_details;
            
            /**
             * DOCTOR
             */
            document.getElementById('record_health_doctor_names').value = this.health.doctor_names;
            document.getElementById('record_health_doctors_phones').value = this.health.doctor_phones;
    
    
            /**
             * PAI
             */
            switch (this.health.pai) {
                case 2:
                    document.getElementById('record_health_pai_y').checked = true;
                    break;
    
                case 3:
                    document.getElementById('record_health_pai_ongoing').checked = true;
                    break;
    
                default:
                    document.getElementById('record_health_pai_n').checked = true;
                    break;
            }
    
            document.getElementById('record_health_pai_details').value = this.health.pai_details;
    
            /**
             * OTHERS
             */
    
            checkbox_macro(
                this.health.lentilles,
                'record_health_lentilles_y',
                'record_health_lentilles_n'
            );
    
            checkbox_macro(
                this.health.lunettes,
                'record_health_glass_y',
                'record_health_glass_n'
            );
    
            checkbox_macro(
                this.health.protheses_auditives,
                'record_health_audio_y',
                'record_health_audio_n'
            );
    
            checkbox_macro(
                this.health.protheses_dentaire,
                'record_health_tooth_y',
                'record_health_tooth_n'
            );
    
            document.getElementById('record_health_others').value = this.health.autres_recommandations;
    
            /**
             * AGREEMENT
             */
    
            if (this.agreement)
                document.getElementById('record_agreement').checked = true;
        }

    }

    // API
    // Basic read request
    payload () {
        const _date = function (str) {
            if (str === 'None')
                return '';
            return str.split('+')[0];
        };

        if (!this.agreement) {
            throw 'Veuillez donner votre accord.';
        }

        const types = [
            Boolean(this.accueil_mati),
            Boolean(this.accueil_midi),
            Boolean(this.accueil_merc),
            Boolean(this.accueil_vacs)
        ];

        if (!types.includes(true)) {
            throw 'Aucun type d\'accueil choisi.';
        }

        if (!this.school) throw 'Veuillez choisir une école valide.';
        if (!this.classroom) throw 'Veuillez choisir une classe valide.';

        if (!this.insurance_society) throw 'Veuillez choisir une société d\'assurance.';
        if (!this.insurance_policy) throw 'Veuillez choisir une police d\'assurance.';

        // Recuperater 1
        for (const x of Object.values(this.recuperaters[0])) if (!x) throw 'Veuillez préciser au moins une personne autorisée à récuperer votre enfant (Noms, numéros, qualité).';


        // Radios
        this.payload_validate_radios();

        const _ = {
            id:             this.id,
            child_id:       this.child_id,
            school_year:    this.school_year,

            agreement:      this.agreement,

            // Base record
            school: this.school,
            classroom: this.classroom,

            accueil_mati: this.accueil_mati,
            accueil_midi: this.accueil_midi,
            accueil_merc: this.accueil_merc,
            accueil_vacs: this.accueil_vacs,
            
            insurance_policy: this.insurance_policy,
            insurance_society: this.insurance_society,

            // date_created:   _date(this.date_created),
            // date_last_mod:  _date(this.date_last_mod),
            // date_verified:  _date(this.date_verified),

            // Responsible 2
            responsible: {
                job:        this.responsible.job,
                email:      this.responsible.email,
                gender:     this.responsible.gender,
                last_name:  this.responsible.last_name,
                first_name: this.responsible.first_name,

                phone_cell:     this.responsible.phone_cell,
                phone_home:     this.responsible.phone_home,
                phone_pro:      this.responsible.phone_pro,

                address_zip:        this.responsible.address_zip,
                address_city:       this.responsible.address_city,
                address_address1:   this.responsible.address_address1,
                address_address2:   this.responsible.address_address2,
            },

            // Authorizations
            authorizations: {
                bath: this.authorizations.bath,
                image: this.authorizations.image,
                sport: this.authorizations.sport,
                transport: this.authorizations.transport,
                medical_transport: this.authorizations.medical_transport
            },

            health: {
                pai:                this.health.pai,
                asthme:             this.health.asthme,
                allergy_food:       this.health.allergy_food,
                allergy_drug:       this.health.allergy_drug,
                vaccine_up_to_date: this.health.vaccine_up_to_date,
                medical_treatment:  this.health.medical_treatment,

                lunettes:               this.health.lunettes,
                lentilles:              this.health.lentilles,
                protheses_dentaire:     this.health.protheses_dentaire,
                protheses_auditives:    this.health.protheses_auditives,
                
                pai_details:            this.health.pai_details,
                allergy_food_details:   this.health.allergy_food_details,
                allergy_drug_details:   this.health.allergy_drug_details,
                
                doctor_names:   this.health.doctor_names,
                doctor_phones:  this.health.doctor_phones,
                
                autres_recommandations: this.health.autres_recommandations,
            },

            diseases: {
                'rubeole':      this.diseases.rubeole,   
                'varicelle':    this.diseases.varicelle,   
                'angine':       this.diseases.angine,   
                'rhumatisme':   this.diseases.rhumatisme,   
                'scarlatine':   this.diseases.scarlatine,   
                'coqueluche':   this.diseases.coqueluche,   
                'otite':        this.diseases.otite,   
                'rougeole':     this.diseases.rougeole,   
                'oreillons':    this.diseases.oreillons,  
            },
        }

        _['recuperaters'] = [];
        for (const recuperater of this.recuperaters) {
            if (recuperater.names && recuperater.phones) {
                _['recuperaters'].push(recuperater);
            }
        }

        return _;  
    }


    payload_validate_radios () {
        const names = {
            'record_auth_transp':           {'message': 'Autorisation de transport pour raison de santé'},
            'record_auth_image':            {'message': 'Droit à l\'image'},
            'record_health_vaccine':        {'message': 'Votre enfant est-il à jour de ses vaccins obligatoires ?'},
            'record_health_treatment':      {'message': 'Votre enfant suit-il un traitement médical ?'},
            'record_health_rubeole':        {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_varicelle':      {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_angine':         {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_rhumatisme':     {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_scarlatine':     {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_coqueluche':     {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_otite':          {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_rougeole':       {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_oreillons':      {'message': 'Votre enfant a t\'il déjà eu les maladies suivantes ?'},
            'record_health_asthme':         {'message': 'Votre enfant est-il asthmatique ?'},
            'record_health_drug':           {'message': 'Votre enfant fait-il des allergies à certains médicaments ?'},
            'record_health_food':           {'message': 'Votre enfant est-il allergique à certains aliments ?'},
            'record_health_pai':            {'message': 'Votre enfant fait-il l\'objet d\'un Projet d\'Accueil Individualisé ? (PAI)'},
            'record_health_lentilles':      {'message': 'Votre enfant porte t\'il des lentilles ?'},
            'record_health_glass':          {'message': 'Votre enfant porte t\'il des lunettes ?'},
            'record_health_audio':          {'message': 'Votre enfant porte t\'il des prothèses auditives ?'},
            'record_health_tooth':          {'message': 'Votre enfant porte t\'il des prothèses ou autres appareils dentaires ?'},
            'record_auth_sport':            {'message': 'J\'autorise mon enfant à participer aux activités physiques et sportives'},
            'record_auth_bath':             {'message': 'J\'autorise mon enfant à participer aux baignades surveillées'},
            'record_auth_transpbus':        {'message': 'Autorisation de transport en véhicule de service et car de location'},
        };

        const error = 'Veuillez renseigner la mension suivante:';

        for (const key of Object.keys(names)) {
            let checked = false;
            document.querySelectorAll(`input[name="${key}"]`)
                .forEach(e => {
                    if (e.checked)
                        checked = true;
                });
            
            if (!checked) {
                throw `${error} "${names[key]['message']}"`;
            }
        }

        return true;
    }


    read (pk, onSuccess, onFailure) {
        const self = this;

        return App.get(`/api/record/${pk}/`, true)
            .then((data) => {
                self.fromAPI(data.record);

                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
    }


    create (onSuccess, onFailure) {        
        const self = this;

        const payload = this.payload();

        return App.post(`/api/record/`, JSON.stringify(payload), true)
            .then((data) => {
                console.log(data);

                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);

                if (onFailure)
                    onFailure(err);
            });
    }

    
    update (onSuccess, onFailure) {        
        const self = this;

        const payload = this.payload();

        return App.put(`/api/record/${this.id}/`, JSON.stringify(payload), true)
            .then((data) => {
                console.log(data);

                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                console.log(err);

                if (onFailure)
                    onFailure(err);
            });
    }

}


class Records {
    constructor () {
        this._data = {};
        this._records = {};
    }


    records () { return this._records; }


    read (pk, onSuccess=undefined, onFailure=undefined) {
        return this._read(`${pk}/`, onSuccess, onFailure);
    }
    
    readAll (onSuccess=undefined, onFailure=undefined) {
        return this._read(``, onSuccess, onFailure);
    }

    readByChild (user_id, onSuccess=undefined, onFailure=undefined) {
        return this._read(`?child=${user_id}`, onSuccess, onFailure);
    }

    readByParent (user_id, onSuccess=undefined, onFailure=undefined) {
        return this._read(`?parent=${user_id}`, onSuccess, onFailure);
    }

    // Basic read request
    _read (mod, onSuccess, onFailure) {
        return App.get(`/api/record/${mod}`, true)
            .then((data) => {
                console.log(data);
                this._data = data;

                let _ = undefined;

                if (data.record)
                    _ = this.order([data.record]);
                else if (data.records)
                    _ = this.order(data.records);
                else
                    reject('No record(s) found.');

                if (typeof(_) === 'object') {
                    reject(_);
                }

                if (onSuccess)
                    onSuccess(data);
            })
            .catch(err => {
                if (onFailure)
                    onFailure(err);
            });
    }


    order (records) {
        for (const record of records) {
            const _ = new Record();

            _.fromAPI(record);

            for (const sy of App._SchoolYears_unordered) {
                if (sy.id === record.school_year)
                    _.fromSchoolYear(sy);
            }

            this._records[record.id] = _;           
        }

        return true;
    }


    renderRecordItem (sy) {
        const s = sy.date_start.split('-')[0];
        const e = sy.date_end.split('-')[0];

        return `
        <div class="Records-Item" data-school="${sy.id}">
            <div class="wrapper-title">
                <p class="title">Inscription: ${s} - ${e} ${(sy.is_active) ? '(active)' : ''}</p>
            </div>
            <div class="wrapper-content">
                <span class="no_data"><i>Pas de données pour cette année</i></span>
                <div class="Record" style="display:none">
                    <b>Ecole:</b> <span class="record_school"></span>
                    <b>Classe:</b> <span class="record_classroom"></span>
                </div>
                <button class="button button-cyan">Ajouter</button>
            </div>

        </div>`;
    }
}


const IntelHistoryTemplate = {

    render (title, intel, active=false) {
        /**
         * title {
         *  s   - Year start
         *  e   - Year end
         * }
         */
        let q1 = 0;
        let q2 = 0;
        let rn = 0;
        let ip = 0;

        const has_intel = Boolean(Object.keys(intel).length);

        let base = `
        <div class="History-card">
            <b class="card-title">${title.s} - ${title.e} ${(active) ? '(en cours)' : ''}</b>
            <hr />
        `;
        
        if (has_intel) {
            try {
                q1 = intel.quotient_1;
                q2 = intel.quotient_2;
                
                rn = intel.recipent_number;
                ip = intel.insurance_policy;
            }
            catch (error) {
                return false;
            }

            base += `
                <div class="History-form">
                    <div class="form-group col-sm-6">
                        <label for="intel_q1"><b>Quotient <span class="intel_s">${title.s}</span></b></label>
                        <br/>
                        <select id="intel_q1" placeholder="Quotient" onchange="" value="${q1}">
                            <option value="0" default>--</option>
                            <option value="1">NE</option>
                            <option value="2">Q2</option>
                            <option value="3">Q1</option>
                        </select>
                    </div>

                    <div class="form-group col-sm-6">
                        <label for="intel_q2"><b>Quotient <span class="intel_e">${title.e}</span></b></label>
                        <br/>
                        <select id="intel_q2" placeholder="Quotient" onchange="" value="${q2}">
                            <option value="0" default>--</option>
                            <option value="1">NE</option>
                            <option value="2">Q2</option>
                            <option value="3">Q1</option>
                        </select>
                    </div>

                    <div class="form-group col-sm-6">
                        <label for="intel_rn"><b>Numéro CAF</b></label>
                        <br/>
                        <input id="intel_rn" type="text" placeholder="Numéro CAF" onchange="profile_onChange(this)" value="${rn}" />
                    </div>
                    <div class="form-group col-sm-6">
                        <label for="intel_ip"><b>Police d'assurance</b></label>
                        <br/>
                        <input id="intel_ip" type="text" placeholder="Police d'assurance" onchange="profile_onChange(this)" value="${ip}" />
                    </div>
                </div>
            </div>`;
        }
        else {
            base += `
                <div class="History-no_data">
                    <span><i>Pas de données pour cette année</i></span>
                </div>
            </div>`;
        }

        return base
    },
};


function birthDate (_dateBirth) {
    const d = new Date();
    const dateBirth = new Date(_dateBirth);

    let age = d.getFullYear() - dateBirth.getFullYear();
    const _month = d.getMonth() - dateBirth.getMonth();
    if (_month === 0) {
        const day = d.getDate() - dateBirth.getDate();
        if (day > 0)
            age -= 1;
    }
    else if (_month > 0) {
        age -= 1;
    }
    return age;
}


const UserValidation = {
    name (value, optional=false) {
        if (!value && !optional) {
            return {'status': false, 'message': 'Le champ ne peux pas être vide.'};
        }
        if (value.length > 128) {
            return {'status': false, 'message': 'Le champ contient trop de caractères.'};
        }
        return {'status': true};
    },

    password (value) {
        if (!value) {
            return {'status': false, 'message': 'Le champ ne peux pas être vide.'};
        }
        if (value.length < 8) {
            return {'status': false, 'message': 'Le champ doit contenir au moins 8 caractères.'};
        }
        if (value.length > 128) {
            return {'status': false, 'message': 'Le champ contient trop de caractères.'};
        }
        return {'status': true};
    },
    
    dob (value) {
        if (!value) {
            return {'status': false, 'message': 'Le champ ne peux pas être vide.'};
        }
        // if (birthDate(value) < 18)
        //     return {'status': false, 'message': 'Age inférieur à 18 ans.'}
        return {'status': true};
    },

    phone (value) {
        if (!value) {
            return {'status': false, 'message': 'Le champ ne peux pas être vide.'};
        }

        // !value.match(/^([+][\d]{1,3})?(0{1})?([1-9][\d]{8})$/)
        if (!value.replace(/ /g, '').match(/^(0{1})?([1-9][\d]{8})$/)) {
            return {'status': false, 'message': 'Numéro de téléphone incorrect.'};
        }
        return {'status': true};
    },

    email (value) {
        if (!value) {
            return {'status': false, 'message': 'Le champ ne peux pas être vide.'};
        }
        // !value.match(/^([+][\d]{1,3})?(0{1})?([1-9][\d]{8})$/)
        if (!value.match(/^((?!\.)[\w-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$/)) {
            return {'status': false, 'message': 'Adresse email incorrect.'};
        }
        return {'status': true};
    },

    select (value) {
        if (value === '0') {
            return {'status': false, 'message': 'Veuillez faire un choix.'};
        }
        // if (!CITIES[value]) {
        //     return {'status': false, 'message': 'La commune choisie est invalide.'};
        // }
        return {'status': true};
    }, 
    
    city (value) {
        if (value === '0') {
            return {'status': false, 'message': 'Veuillez choisir une commune.'};
        }
        if (!CITIES[value]) {
            return {'status': false, 'message': 'La commune choisie est invalide.'};
        }
        return {'status': true};
    }, 
};


const CITIES = {
    '97216': 'L\'Ajoupa-Bouillon',
    '97217': 'Les Anses-d\'Arlet',
    '97218': 'Basse-Pointe',
    '97222': 'Bellefontaine',
    '97221': 'Le Carbet',
    '97222': 'Case-Pilote',
    '97223': 'Le Diamant',
    '97224': 'Ducos',
    '97250': 'Fonds-Saint-Denis',
    '97200': 'Fort-de-France',
    '97240': 'Le François',
    '97218': 'Grand\'Rivière',
    '97213': 'Gros-Morne',
    '97232': 'Le Lamentin',
    '97214': 'Le Lorrain',
    '97218': 'Macouba',
    '97225': 'Le Marigot',
    '97290': 'Le Marin',
    '97260': 'Le Morne-Rouge',
    '97226': 'Le Morne-Vert',
    '97250': 'Le Prêcheur',
    '97211': 'Rivière-Pilote',
    '97215': 'Rivière-Salée',
    '97231': 'Le Robert',
    '97227': 'Sainte-Anne',
    '97228': 'Sainte-Luce',
    '97230': 'Sainte-Marie',
    '97270': 'Saint-Esprit',
    '97212': 'Saint-Joseph',
    '97250': 'Saint-Pierre',
    '97233': 'Schœlcher',
    '97220': 'La Trinité',
    '97229': 'Les Trois-Îlets',
    '97280': 'Le Vauclin'
};


const UserTests = {

    record_payload () {
        return {
            'child_id':             21,
            'parent_id':            20,
            'school_year':          16,

            'school':               'HM',
            'classroom':            1,

            'pai':                  1,
            'asthme':               false,

            'allergy_food':         false,
            'allergy_drug':         false,
            'allergy_food_details': '',
            'allergy_drug_details': '',
        };
    },

    record_read (ext='') {
        return App.get('/api/record/' + ext, true)
            .then(data => console.log(data))
            .catch(err => console.log(err)); 
    },

    record_create (payload) {
        return App.post('/api/record/', JSON.stringify(payload), true)
            .then(data => console.log(data))
            .catch(err => console.log(err));
    },

    record_update (pk, payload) {
        return App.put(`/api/record/${pk}/`, JSON.stringify(payload), true)
            .then(data => console.log(data))
            .catch(err => console.log(err));
    },

    record_read_macro () {
        console.log('Read all...');
        this.record_read();

        console.log('Read one...');
        this.record_read('1/');

        console.log('Read by parent...');
        // this.record_read('?parent=');
    },

    record_create_macro (payload) {
        console.log('Create last year...');
        this.record_create(payload);

        console.log('Create any year...')
        payload.school_year = 200;
        this.record_create(payload);
    }
};


const CLASSROOMS = [
    '<i>pas de classe</i>',
    'STP',
    'SP',
    'SM',
    'SG',
    'CP',
    'CE1',
    'CE2',
    'CM1',
    'CM2',
    '6ème',
];

const QUOTIENT = [
    'NE',
    'NE',
    'Q2',
    'Q1',
];

const PAI = [
    '<i>pas de PAI renseigné</i>',
    'NON',
    'OUI',
    'EN COURS',

]