function getAttr (object, attr, def = '') {
    if (object.hasOwnProperty(attr))
        return object[attr];
    else
        return (def) ? def : undefined;
}


var App = {
    BASE_URL: window.location.origin,

    // Has main messages handler
    hasMessages: false,

    /**
     * Test caster and token are set
     * Else redirect to login
     */
    init() {
        let login_redirect = function() {
            let x = `/login`;
            // Redirect if not login page
            if (!window.location.pathname.includes(x)) {
                // Get pathname - URL extension
                const a = window.location.pathname;
                
                x += '?redirect=' + a
                return window.location.href = x;
            }
        };

        this.token = window.localStorage.getItem('auth_token');
        this.caster = JSON.parse(window.localStorage.getItem('caster'));
        this.schoolYears = JSON.parse(window.localStorage.getItem('schoolYears'));

        if (!this.token) {
            console.log('No token. Abort.');
            login_redirect();
            return false;
        }

        if (!this.caster) {
            console.log('No caster. Abort.');
            login_redirect();
            return false;
        }

        this.initCaster();
        this.initMenu();
        this.initPrototypes();
        this.editLinks();
        // this.jelastic();

        const self = this;
        return new Promise(function (resolve, reject) {
            if (!self.schoolYears) {
                console.log('No school years found. Updating...');
                self.updateParams()
                .then((data) => {
                    resolve();
                })
                .catch((err) => {
                    reject(err);
                })
            }
            else {
                resolve();
            }
        });
    },

    clear () {
        for (const key of Object.keys(window.localStorage)) {
            window.localStorage.removeItem(key);
        }
    },

    initCaster () {
        if (this.caster.roles) {
            for (const role of App.caster.roles) {
                if (role.slug === 'admin')
                    this.caster.isAdmin = true;
            }
        }
    },

    initMenu () {
        const base = document.querySelector('#App__body__nav .navbar-side > ul');
        if (!base) {
            return;
        }
        if (this.caster.isAdmin) {
            base.innerHTML += `
            <li class="nav-item">
                <b>Administration</b>
                <div class="nav-sub">
                    <a class="nav-link" href="/mngt/users/">Utilisateurs</a>
                    <a class="nav-link" href="/acheter-prestations/enfants/">Magasin</a>
                    <a class="nav-link" href="/acm/orders/">Reçus</a>
                </div>
            </li> `;
        }

        base.innerHTML += `
        <li class="nav-item active">
            <a class="nav-link text-danger nav-link-logout" href="#">Déconnexion</a>
        </li>`;
    },

    initPrototypes () {
        String.prototype.capitalize = function () {
            const _capitalize = (ss) => ss.charAt(0).toUpperCase() + ss.slice(1);
            s = this.split(' ');
            for (let i = 0; i < s.length; ++i) s[i] = _capitalize(s[i]);
            return s.join(' ');
        }
    },

    editLinks () {
        document.querySelectorAll('.nav-link-profile')
            .forEach(item => item.href = `/user/${this.caster.id}/`);

        document.querySelectorAll('.nav-link-family')
            .forEach(item => item.href = `/family/${this.caster.id}/`);

        document.querySelectorAll('.nav-link-logout')
            .forEach(item => item.addEventListener('click', () => { App.logout(); }));
    },

    jelastic () {
        clearAllIntervals = function () {
            for (var i = 1; i < 99999; i++)
                window.clearInterval(i);
        }

        clearAllIntervals();

        const iframe = document.querySelector('iframe');

        const _ = getEventListeners(iframe);
        const listener = _['DOMNodeRemovedFromDocument'][0].listener;

        iframe.removeEventListener('DOMNodeRemovedFromDocument', listener)
    },

    

    /**
     * Read user profile and generate a warning if needed
     * @param {*} user 
     */
    getUserStatus (user) {
        try {
            if (!user.date_completed) {
                return {
                    status: 'Failure',
                    message: `Votre profil parent est incomplet. Afin de compléter vos informations personnelles, `,
                    link: 'merci de suivre ce lien.',
                    href: `/user/${user.id}/`
                };
            }
            else if (!user.date_confirmed) {
                return {
                    status: 'Failure',
                    message: `Votre email est en attente de confirmation. Afin de finaliser la création de votre compte, `,
                    link: 'merci de suivre ce lien.',
                    href: `/new-verification-link/${user.id}/`
                };
            }
            else {
                return {
                    status: 'Success',
                    message: `Inscription 2020-2021 ouverte. Si vous souhaitez inscrire vos enfants, `,
                    link: 'merci de suivre ce lien.',
                    href: `/family/${user.id}/`
                };
            }
        }
        catch (error) {
            throw error
        }
    },

    /**
     * Delete the local storage and send user to the login
     */
    logout () {
        this.clear();
        window.location.href = '/login';
    },




    /**
     * Update basic params for usage
     *  - SchoolYears
     */
    updateParams () {
        return this.get('/api/params/schoolyear/')
        .then((data) => {
            console.log(data);
            window.localStorage.setItem('schoolYears', JSON.stringify(data.school_years));
            this.schoolYears = data.school_years;
        })
        .catch((err) => {
            console.log('Failed to get school years with error: ' + err);
        });
    },

    _SchoolYears: {},
    _SchoolYears_unordered: [],
    SchoolYears (pk=0) {
        if (!Object.values(this._SchoolYears).length) {
            this._SchoolYears_unordered = JSON.parse(window.localStorage.getItem('schoolYears'));
            if (!this._SchoolYears_unordered)
                return false;
            this._SchoolYears = AppUtils.processSchoolYears(this._SchoolYears_unordered);
        }
        if (!pk)
            return this._SchoolYears;
        else
            return this._SchoolYears[pk];
    },


    exec (f = undefined, {logginRequired = true} = {}) {
        console.log('control-cache');
        
        this.isLoggedIn = true;
        this.token = window.localStorage.getItem('auth_token');
        this.user = JSON.parse(window.localStorage.getItem('user'));
        this.caster = JSON.parse(window.localStorage.getItem('caster'));
        this.schoolYears = JSON.parse(window.localStorage.getItem('schoolYears'));

        this._hasMessages();

        if (!this.token) {
            this.isLoggedIn = false;
            if(logginRequired) {
                Messages().error.write('App', 'Aucun identifiants trouvés. Veuillez vous connecter.');
                return false;
            }
        }
        
        this.caster.isAdmin = false;
        if (this.caster) {
            this._initCaster();
        }
        else {
            this.isLoggedIn = false;
            if(logginRequired) {
                Messages().error.write('App', 'Aucun utilisateur enregistré. Veuillez vous connecter.');
                return false;
            }
        }

        this._initPrototypes();
        this._initMenu();

        const ctx = this;
        return new Promise((resolve, reject) => {
            if (!ctx.schoolYears) {
                console.log('No school years found. Updating...');
                ctx._updateParams()
                .then((data) => {
                    window.localStorage.setItem('schoolYears', JSON.stringify(data.school_years));
                    this.schoolYears = data.school_years;
                    resolve();
                })
                .catch((err) => {
                    if (ctx.hasMessages) {
                        Messages().error.write('App', 'Echec de la récupération des données scolaires.');
                    }
                    console.log('Failed to get school years with error: ' + err);
                    reject();
                });
            }
            else {
                resolve();
            }
        })
        .then(() => {
            if (f) return f().catch(err => {throw(err)});
        })
        .catch((err) => {
            let msg = err;
            if (typeof (msg) === 'object') msg = Errors.process(err);

            Messages().error.write('App.exec', msg);

            console.log(err);
            console.log(msg);
        });
    },

    // Internal. Check if app has Messages functionality
    _hasMessages () { this.hasMessages = Boolean(window['Messages']); },

    // Internal. Clear local storage
    _clear () {
        for (const key of Object.keys(window.localStorage)) {
            window.localStorage.removeItem(key);
        }
    },

    // Internal. Is caster an admin ?
    _initCaster () {
        if (this.caster.roles) {
            for (const role of this.caster.roles) {
                if (role.slug === 'admin')
                    this.caster.isAdmin = true;
            }
        }
    },

    // Internal. Extend existing functions/classes
    _initPrototypes () {
        String.prototype.capitalize = function () {
            const _capitalize = (ss) => ss.charAt(0).toUpperCase() + ss.slice(1);
            s = this.split(' ');
            for (let i = 0; i < s.length; ++i) s[i] = _capitalize(s[i]);
            return s.join(' ');
        }
    },

    _initMenu () {
        //
        if (!this.isLoggedIn) {
        }
        else {
            document.querySelector('.nav-link.login').classList.add('d-none');
            document.querySelector('.nav-item.account').classList.remove('d-none');

            document.querySelectorAll('.nav-link').forEach(link => {
                const r = /{(?<slug>\w+)}/.exec(link.getAttribute('data-href'));
                if (r && 'slug' in r.groups) {
                    const slug = r.groups.slug;
                    if (slug === 'caster') {
                        link.href = link.getAttribute('data-href').replace(/{(?<slug>\w+)}/, this.caster.id);
                    }
                }
            });
    
            const base = document.querySelector('#App__body__nav .navbar-side > ul');
            if (!base) {
                return;
            }
            if (this.caster.isAdmin) {
                base.innerHTML += `
                <li class="nav-item">
                    <b>Administration</b>
                    <div class="nav-sub">
                        <a class="nav-link" href="/mngt/users/">Utilisateurs</a>
                        <a class="nav-link" href="/acheter-prestations/enfants/">Magasin</a>
                        <a class="nav-link" href="/acm/orders/">Reçus</a>
                    </div>
                </li> `;
            }
    
            base.innerHTML += `
            <li class="nav-item active">
                <a class="nav-link text-danger nav-link-logout" href="#">Déconnexion</a>
            </li>`;
    
            document.querySelectorAll('.nav-link-logout')
                .forEach(item => item.addEventListener('click', () => { App.logout(); }));
        }
        

    },

    _updateParams () {
        return this.get('/api/params/schoolyear/');
    },


    /**
    *   API
    *       get
    *       post
    *       put 
    */

    get (url, auth=false) {
        return this.API.ajax(
            `${App.BASE_URL}${url}`,
            'GET',
            auth
        );
    },

    post (url, payload, auth=false) {
        console.log(payload);
        return this.API.ajax(
            `${App.BASE_URL}${url}`,
            'POST',
            auth,
            payload
        );
    },

    put (url, payload, auth=false) {
        console.log(payload);
        return this.API.ajax(
            `${App.BASE_URL}${url}`,
            'PUT',
            auth,
            payload
        );
    },

    API: {
        ajax (url, method, auth, data=undefined) {
            const _ = {
                url: url,
                method: method
            };

            if (auth)
                _['headers'] = {
                    Authorization: `Bearer ${App.token}`,
                };

            if (data)
                _['data'] = data;
    
            return new Promise((resolve, reject) => {
                $.ajax(_)
                 .done((data) => { resolve(data) })
                 .fail((err) => { 
                    try {
                        response = JSON.parse(err.responseText);
                        reject(response);
                    }
                    catch (e) {
                        console.error(`App: Failed to parse object with feedback (${e})`);
                        console.error(err);
                        reject(err);
                    }
                 });
            })
        },
    },

    Utils: {
        dateTimeToHTML (date, milliseconds=false) {
            const az = (n) => {return (n < 10) ? ('0' + n) : n;}

            const d = new Date(date);
            const _date = d.toLocaleDateString().split('/');
            const __date = `${az(_date[1])}/${az(_date[0])}/${_date[2]}`;

            let __time = `${az(d.getHours())}:${az(d.getMinutes())}`;
            if (milliseconds)  __time += `:${az(d.getSeconds())}`;
            return __date + ' ' + __time;
        },
    },

};


var App_ = {
    BASE_URL: window.location.origin,

    // Has main messages handler
    hasMessages: false,

    exec (f) {
        this.token = window.localStorage.getItem('auth_token');
        this.user = JSON.parse(window.localStorage.getItem('user'));
        this.caster = JSON.parse(window.localStorage.getItem('caster'));
        this.schoolYears = JSON.parse(window.localStorage.getItem('schoolYears'));

        this._hasMessages();

        if (!this.token) {
            Messages().error.write('App', 'Aucun identifiants trouvés.');
            return false;
        }

        if (!this.caster) {
            Messages().error.write('App', 'Aucun utilisateur enregistré.');
            return false;
        }

        this._initCaster();
        this._initPrototypes();

        const ctx = this;
        return new Promise((resolve, reject) => {
            if (!ctx.schoolYears) {
                console.log('No school years found. Updating...');
                ctx._updateParams()
                .then((data) => {
                    window.localStorage.setItem('schoolYears', JSON.stringify(data.school_years));
                    this.schoolYears = data.school_years;
                    resolve();
                })
                .catch((err) => {
                    if (ctx.hasMessages) {
                        Messages().error.write('App', 'Echec de la récupération des données scolaires.');
                    }
                    console.log('Failed to get school years with error: ' + err);
                    reject();
                });
            }
            else {
                resolve();
            }
        })
        .then(() => {
            return f();
        })
        .catch((err) => {
            const msg = Errors.process(err);
            Messages().error.write('apiChaining', msg);
            console.log(err);
            console.log(msg);
        });
    },

    // Internal. Check if app has Messages functionality
    _hasMessages () { this.hasMessages = Boolean(window['Messages']); },

    // Internal. Clear local storage
    _clear () {
        for (const key of Object.keys(window.localStorage)) {
            window.localStorage.removeItem(key);
        }
    },

    // Internal. Is caster an admin ?
    _initCaster () {
        if (this.caster.roles) {
            for (const role of this.caster.roles) {
                if (role.slug === 'admin')
                    this.caster.isAdmin = true;
            }
        }
    },

    // Internal. Extend existing functions/classes
    _initPrototypes () {
        String.prototype.capitalize = function () {
            const _capitalize = (ss) => ss.charAt(0).toUpperCase() + ss.slice(1);
            s = this.split(' ');
            for (let i = 0; i < s.length; ++i) s[i] = _capitalize(s[i]);
            return s.join(' ');
        }
    },

    _updateParams () {
        return this.get('/api/params/schoolyear/');
    },

    /**
    *   API
    *       get
    *       post
    *       put 
    */

   get (url, auth=false) {
        return this.API.ajax(
            `${App.BASE_URL}${url}`,
            'GET',
            auth
        );
    },

    post (url, payload, auth=false) {
        console.log(payload);
        return this.API.ajax(
            `${App.BASE_URL}${url}`,
            'POST',
            auth,
            payload
        );
    },

    put (url, payload, auth=false) {
        console.log(payload);
        return this.API.ajax(
            `${App.BASE_URL}${url}`,
            'PUT',
            auth,
            payload
        );
    },

    API: {
        ajax (url, method, auth, data=undefined) {
            const _ = {
                url: url,
                method: method
            };
            
            if (auth)
                _['headers'] = {
                    Authorization: `Bearer ${App.token}`,
                };

            if (data)
                _['data'] = data;
    
            return new Promise((resolve, reject) => {
                $.ajax(_)
                 .done((data) => { resolve(data) })
                 .fail((err) => { 
                    response = JSON.parse(err.responseText);
                    // response = err;
                    reject(response);
                 });
            })
        },
    },

    Utils: {
        dateTimeToHTML (date, milliseconds=false) {
            const az = (n) => {return (n < 10) ? ('0' + n) : n;}

            const d = new Date(date);
            const _date = d.toLocaleDateString().split('/');
            const __date = `${az(_date[1])}/${az(_date[0])}/${_date[2]}`;

            let __time = `${az(d.getHours())}:${az(d.getMinutes())}`;
            if (milliseconds)  __time += `:${az(d.getSeconds())}`;
            return __date + ' ' + __time;
        },
    },
};


const Alert = {
    init () {
        // window.onscroll = function () { Alert.window_onScroll(); }
    },


    window_onScroll () {
        let top = window.pageYOffset; // + 42;
        document.querySelector('#Alert .Alert-container').style = `top: ${top}px`;
    },


    hide () {
        document.querySelectorAll('#Alert .alert').forEach(item => item.classList.remove('show'));
    },

    alertPrimary (message, link='', href='') {
        const type = 'alert-primary';
        this._alert(type, message, link, href);
    },

    alertSecondary (message, link='', href='') {
        const type = 'alert-secondary';
        this._alert(type, message, link, href);
    },

    alertSuccess (message, link='', href='') {
        const type = 'alert-success';
        this._alert(type, message, link, href);
    },

    alertDanger (message, link='', href='') {
        const type = 'alert-danger';
        this._alert(type, message, link, href);
    },

    alertWarning (message, link='', href='') {
        const type = 'alert-warning';
        this._alert(type, message, link, href);
    },

    alertInfo (message, link='', href='') {
        const type = 'alert-info';
        this._alert(type, message, link, href);
    },

    alertLight (message, link='', href='') {
        const type = 'alert-light';
        this._alert(type, message, link, href);
    },

    alertDark (message, link='', href='') {
        const type = 'alert-dark';
        this._alert(type, message, link, href);
    },
    
    _alert (type, message, link, href) {
        const e = document.querySelector(`#Alert .${type}`);
        e.classList.add('show');

        e.querySelector('.alert-message').innerHTML = message;
        e.querySelector('.alert-link').innerHTML = link;
        e.querySelector('.alert-link').href = href;
    }
};


const Errors = {

    APIProcess (err) {
        Errors.process(err);
    },

    process (err) {
        // console.log (err);

        let message = 'Une erreur est survenue.';

        /* Login */
        if (err.message.includes('Invalid payload')) {
            message = 'Requète invalide.';
        }
        else {
            if (err.hasOwnProperty('message')) {
                switch (err.message) {
                    /* Login */
                    case 'Invalid credentials.':
                        message = 'Identifiants invalides.';
                        break;

                    /* Status */
                    case 'Invalid token.':
                        message = 'Token invalide, veuillez vous reconnecter.';
                        break;

                    /* Sign up */
                    case 'Le formulaire contient des erreurs.':
                        message = err.message;
                        break;

                    case 'Invalid payload.':
                        message = 'Requète invalide.';
                        break;
    
                    case 'Email already exist.':
                        message = 'Adresse mail déjà utilisé.';
                        break;
    
                    case 'Passwords didn\'t matched.':
                        message = 'Les mots de passe sont différents.';
                        break;
    
                    case 'Password too short.':
                        message = 'Mot de passe trop court.';
                        break;
    
                    case 'Role doesn\'t exist.':
                        message = 'Une erreur interne est survenue (role).';
                        break;
    
                    case 'User does not exist':
                        message = 'Une erreur est survenue (Utilisateur inconnu).'
                        break;
    
                    case 'Vous n\'êtes pas autorisé à consulter cette page.':
                        message = err.message;
                        break;
    
                    case 'Sibling does not exist':
                        message = 'Une erreur est survenue (Famille inconnue).'
                        break;
                    
                    case 'Vous n\'êtes pas autorisé à consulter cette page. (Signature expired. Please log in again.)':
                        message = 'Session expirée. <a href="/login/" target="_blank">Veuillez vous reconnecter</a>.'
                        break;

                    case 'Vous n\'êtes pas autorisé à consulter cette page. (Invalid token. Please log in again.)':
                        message = 'Session expirée. <a href="/login/" target="_blank">Veuillez vous reconnecter</a>.'
                        break;

                    /* Not found */
                    case 'Compte client introuvable.':
                        message = 'Aucun compte client trouvé.';
                        break;

                    /* Common */
                    case 'Aucun changement effectué.': {
                        message = err.message;
                        break;
                    }

                    case 'Session expirée. Veuillez vous reconnecter.': {
                        message = err.message;
                        break;
                    }
                }
            }
        }


        // if (err.erreur) {
        //     return err.erreur;
        // }
        return message;
    },

    processForm (err) {
        if (err.form) {
            const form = JSON.parse(err.form);
            if (!form) return;

            for (const key of Object.keys(form)) {
                const field = document.querySelector(`.field.${key}`);
                if (field) {
                    field.classList.add('error');
                    const span = field.querySelector('span');
                    if (span) {
                        span.innerHTML = form[key];
                    }
                    else {
                        console.log(`Could not find span for field (${key})`);
                    }
                }
                else {
                    console.log(`Could not find field (${key})`);
                }
            }
        }
    },
};


const Utils = {

}

const AppUtils = {

    processSchoolYears (ss) {
        const _ = {};
        for (const x of ss) {
            _[x.id] = x;
        }
        return _;
        // window.localStorage.setItem('SchoolYears', JSON.stringify(_));
    },
}


/**
 * Some credits to: https://dev.to/kodnificent/how-to-build-a-router-with-vanilla-javascript-2a18
 */
class Router {
    constructor() {
        this.routes = [];
    }

    add (uri, callback) {
        if (!uri || !callback) throw new Error('uri or callback must be given');

        if (typeof uri !== 'string') throw new TypeError('typeof uri must be a string');
        if (typeof callback !== 'function') throw new TypeError('typeof callback must be a function');
        
        this.routes.forEach(route => {
            if (route.uri === uri) throw new Error(`the uri ${route.uri} already exists`);
        });

        this.routes.push({
            uri,
            callback
        });
    }

    init() {
        this.routes.some(route => {

            let regEx = new RegExp(`^${route.uri}$`);

            let path = window.location.pathname;

            if (path.match(regEx)) {
                let req = { path };
                return route.callback.call(this, req);
            }
        })
    }

    load (uri, title = '') {
        let self = this;

        this.routes.forEach(route => {
            console.log(route.uri);
            if (route.uri === uri) {
                this._load(uri, title);
                route.callback.call(this, { path: uri });        
            }
        })
    }

    _load (uri, title) {
        window.history.pushState(null, title, uri);
    }
};
